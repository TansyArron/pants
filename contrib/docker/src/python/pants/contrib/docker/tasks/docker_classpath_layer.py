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
from tarfile import TarFile

from pants.backend.jvm.targets.jar_library import JarLibrary
from pants.task.task import Task

from pants.contrib.docker.products.layer_product import LayerDigestMap, LayerProduct
from pants.contrib.docker.targets.docker_layer import DockerClasspathLayerTarget
from pants.contrib.docker.util.tar import filter_tar_info
from fsqio.pants.ivy.global_classpath_task_mixin import GlobalClasspathTaskMixin


class DockerClasspathLayerTask(GlobalClasspathTaskMixin, Task):

  SYNTHETIC_TARGET_NAME = 'global_classpath_layer_bag'

  @classmethod
  def product_types(cls):
    return [LayerProduct, LayerDigestMap]

  @classmethod
  def prepare(cls, options, round_manager):
    super(DockerClasspathLayerTask, cls).prepare(options, round_manager)
    round_manager.require_data('consolidated_classpath')

  @classmethod
  def implementation_version(cls):
    return super(
      DockerClasspathLayerTask, cls).implementation_version() + [('DockerClasspathLayerTask', 9)]

  @classmethod
  def maybe_add_dependency_edges(cls, build_graph, original_targets, synthetic_target):
    classpath_layers = [t for t in original_targets if isinstance(t, DockerClasspathLayerTarget)]
    for layer in classpath_layers:
      build_graph.inject_dependency(layer.address, synthetic_target.address)

  @property
  def cache_target_dirs(self):
    return True

  @property
  def global_classpath_targets(self):
    return self.context.targets(predicate=lambda t: isinstance(t, DockerClasspathLayerTarget))

  def execute(self):
    products = self.context.products
    if not self.global_classpath_targets:
      return
    invalidation_context = self.invalidated(
      targets=self.global_classpath_targets,
      invalidate_dependents=True,
    )
    with invalidation_context as invalidation_check:
      for vt in invalidation_check.invalid_vts:
        self.create_layer(vt)
        vt.update()

    layer_products = products.safe_create_data(LayerProduct, init_func=dict)
    layer_digest_map = products.safe_create_data(LayerDigestMap, init_func=dict)
    for vt in invalidation_check.all_vts:
      if vt.target in layer_products:
        raise Exception
      layer_product = LayerProduct(vt.results_dir)
      layer_products[vt.target] = layer_product
      layer_digest_map[layer_product.digest] = layer_product

  def create_layer(self, vt):
    def dest_path_for_jar(jar_file):
      jar_name = os.path.basename(jar_file)
      return os.path.join(vt.target.base_dir, jar_name)
    consolidated_classpath = self.context.products.get_data('consolidated_classpath')
    jar_targets = [t for t in vt.target.closure() if isinstance(t, JarLibrary)]
    all_jar_paths = [
      j.cache_path for _, j in consolidated_classpath.get_artifact_classpath_entries_for_targets(jar_targets)
    ]
    tar_path = os.path.join(vt.results_dir, LayerProduct.LAYER_TAR_FILE_NAME)
    tar_file = TarFile(tar_path, 'w')
    with tar_file as tar:
      for jar_file in all_jar_paths:
        tar.add(
          name=os.path.realpath(jar_file),
          arcname=dest_path_for_jar(jar_file),
          filter=filter_tar_info,
        )
    LayerProduct.write_metadata_json(vt.results_dir, canonical_image_repo=vt.target.canonical_docker_repo)
