# coding=utf-8

from __future__ import (
  absolute_import,
  division,
  generators,
  nested_scopes,
  print_function,
  unicode_literals,
  with_statement,
)

import os
import shutil
from tempfile import mkdtemp

from pants.backend.jvm.tasks.classpath_products import ClasspathEntry, ClasspathUtil
from pants.backend.jvm.tasks.jvm_binary_task import JvmBinaryTask
from pants.base.exceptions import TaskError
from pants.util.dirutil import safe_mkdir, safe_rmtree
from twitter.common.collections import OrderedSet

from pants.contrib.docker.products.layer_product import LayerDigestMap, LayerProduct
from pants.contrib.docker.targets.docker_layer import DockerServiceLayerTarget
from pants.contrib.docker.util.tar import create_stable_tar_from_directory


class DockerServiceLayerTask(JvmBinaryTask):
  """Create a layer containing an application bundle."""

  APPLICATION_ROOT = '/data/app'

  @classmethod
  def prepare(cls, options, round_manager):
    super(DockerServiceLayerTask, cls).prepare(options, round_manager)
    round_manager.require('consolidated_classpath')

  @classmethod
  def implementation_version(cls):
    return super(DockerServiceLayerTask, cls).implementation_version() + [('DockerServiceLayerTask', 0)]

  @classmethod
  def product_types(cls):
    return [LayerProduct, LayerDigestMap]

  @property
  def cache_target_dirs(self):
    return True

  @property
  def jvm_app_layer_targets(self):
    return self.context.targets(predicate=lambda t: isinstance(t, DockerServiceLayerTarget))

  def execute(self):
    products = self.context.products
    invalidation_context = self.invalidated(
      targets=self.jvm_app_layer_targets,
      invalidate_dependents=True,
    )
    with invalidation_context as invalidation_check:
      for vt in invalidation_check.invalid_vts:
        temp_dir = mkdtemp()
        try:
          self.create_layer(vt, temp_dir)
        finally:
          safe_rmtree(temp_dir)
        vt.update()

    product_dict = products.safe_create_data(LayerProduct, init_func=dict)
    layer_digest_map = products.safe_create_data(LayerDigestMap, init_func=dict)
    for vt in invalidation_check.all_vts:
      if vt.target in product_dict:
        raise Exception
      layer_product = LayerProduct(vt.results_dir)
      product_dict[vt.target] = layer_product
      layer_digest_map[layer_product.digest] = layer_product

  def create_layer(self, vt, temp_dir_path):
    """Construct a directory with the file structure and context."""
    app_root = os.path.join(self.APPLICATION_ROOT, vt.target.bundle_name)

    deps_dir = os.path.join(temp_dir_path, 'data/deps')
    data_app_dir = os.path.join(temp_dir_path, 'data/app')
    bundle_dir = os.path.join(data_app_dir, vt.target.bundle_name)
    resources_dir = os.path.join(bundle_dir, 'resources')
    libs_dir = os.path.join(bundle_dir, 'libs')
    safe_mkdir(deps_dir)
    safe_mkdir(libs_dir)
    safe_mkdir(resources_dir)

    jar_libs = self.get_third_party_jars(vt.target)
    third_party_symlink_map = self.create_third_party_symlink_map(app_root, jar_libs)
    self.copy_bundles(vt.target, bundle_dir)

    classpath = self.create_classpath(
      targets=vt.target.closure(bfs=True),
      classpath_products=self.context.products.get_data('consolidated_classpath'),
      base_dir=libs_dir,
      excludes=vt.target.binary.deploy_excludes,
    )
    classpath.update([os.path.join(libs_dir, jar) for jar in sorted(jar_libs)])
    classpath.update([resources_dir])
    binary_jar_file = '{}.jar'.format(vt.target.binary.name)
    application_binary = os.path.join(bundle_dir, binary_jar_file)
    with self.monolithic_jar(vt.target.binary, application_binary, manifest_classpath=classpath) as jar:
      self.add_main_manifest_entry(jar, vt.target.binary)

    create_stable_tar_from_directory(
      source_dir=data_app_dir,
      tar_root=os.path.join(self.APPLICATION_ROOT),
      tarfile_location=os.path.join(vt.results_dir, LayerProduct.LAYER_TAR_FILE_NAME),
      symlinks=third_party_symlink_map,
    )
    LayerProduct.write_metadata_json(vt.results_dir)

  def create_classpath(self, targets, classpath_products, base_dir, excludes=None):
    """Create a classpath for this jvm_app"""
    # TODO(mateo): I worked with twitter and these products are now in the classpath. But to consume
    # this class would have to move downstream of 'bundle'. I would like to break the consolidate_classpath into
    # its own task so it could run right after compile (which needs the loose sources due to
    # incremental compiler deficiency).
    classpath = OrderedSet()
    target_to_classpath = ClasspathUtil.classpath_by_targets(targets, classpath_products)
    processed_entries = set()

    for target, classpath_entries_for_target in target_to_classpath.items():
      classpath_entries_for_target = filter(ClasspathEntry.is_internal_classpath_entry, classpath_entries_for_target)

      for (index, entry) in enumerate(classpath_entries_for_target):
        if entry.is_excluded_by(excludes) or entry in processed_entries:
          continue
        processed_entries.add(entry)
        if os.path.isdir(entry.path):
          ext = '.jar'
        else:
          _, ext = os.path.splitext(entry.path)
        base_name = '{target_id}-{index}{ext}'.format(target_id=target.id, index=index, ext=ext)
        jar_path = os.path.join(base_dir, base_name)
        # if not os.path.exists(entry.path):
        #   raise MissingClasspathEntryError(
        #     'Could not find {src} when attempting to link it into the {dst}'.format(src=entry.path, dst=jar_path)
        #   )
        # Create jar files out of any loose directories.
        if os.path.isdir(entry.path):
          with self.open_jar(jar_path, overwrite=True, compressed=False) as jar:
            jar.write(entry.path)
        else:
          shutil.copy2(entry.path, jar_path)
        classpath.update([jar_path])
    return classpath

  def get_third_party_jars(self, target):
    """Get a list of this app's 3rdparty dependencies.
    
    All 3rdparty jars are included in the docker_classpath_layer, so we symlink only the jars we need into the 
    jvm_apps classpath.
    """
    runtime_classpath = self.context.products.get_data('runtime_classpath')
    third_party_jars = runtime_classpath.get_artifact_classpath_entries_for_targets(target.closure(bfs=True))
    return [os.path.basename(artifact.path) for _, artifact in third_party_jars]

  def create_third_party_symlink_map(self, app_root, jar_libs):
    """Construct a map of symlinks to create from the lib directory of this app to the location of all 3rdparty jars."""
    return {
      os.path.join(app_root, 'libs', jar_name): os.path.join('/data/deps', jar_name)
      for jar_name in jar_libs
    }

  def copy_bundles(self, target, dest_dir):
    """Copy in every file in the app's bundles."""
    for bundle in target.bundles:
      self.copy_bundle(bundle, dest_dir)

  def copy_bundle(self, bundle, dest_dir):
    for path, relpath in bundle.filemap.items():
      bundle_path = os.path.join(dest_dir, relpath)
      if not os.path.exists(path):
        raise TaskError('Given path: {} does not exist in bundle'.format(path))
      safe_mkdir(os.path.dirname(bundle_path))
      shutil.copy2(path, bundle_path)
