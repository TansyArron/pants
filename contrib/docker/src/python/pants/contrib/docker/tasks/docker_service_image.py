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

import json
import os
import shutil
from tempfile import mkdtemp
import time

from pants.base.fingerprint_strategy import TaskIdentityFingerprintStrategy
from pants.task.task import Task
from pants.util.dirutil import safe_mkdir, safe_rmtree
from pants.util.memo import memoized_property
import six

from pants.contrib.docker.products.docker_image import DockerImageProduct
from pants.contrib.docker.products.layer_product import (
  LayerDigestMap,
  LayerProduct,
  ResolvedLayerProducts,
)
from pants.contrib.docker.targets.docker_service_app import DockerServiceAppTarget
from pants.contrib.docker.util.hashing import stream_sha256
from pants.contrib.docker.util.tar import create_stable_tar_from_directory


class DockerServiceImageTask(Task):

  @classmethod
  def product_types(cls):
    return [DockerImageProduct, LayerDigestMap]

  @classmethod
  def prepare(cls, options, round_manager):
    super(DockerServiceImageTask, cls).prepare(options, round_manager)
    round_manager.require_data(LayerProduct)
    round_manager.require_data(ResolvedLayerProducts)

  @classmethod
  def implementation_version(cls):
    return super(
      DockerServiceImageTask, cls).implementation_version() + [('DockerServiceImageTask', 6)]

  @property
  def cache_target_dirs(self):
    return True

  @property
  def resolved_layer_products(self):
    return self.context.products.get_data(ResolvedLayerProducts, init_func=dict)

  @property
  def layer_products(self):
    return self.context.products.get_data(LayerProduct, init_func=dict)

  @property
  def layer_digest_map(self):
    return self.context.products.get_data(LayerDigestMap, init_func=dict)

  @memoized_property
  def app_image_targets(self):
    return self.context.targets(predicate=lambda t: isinstance(t, DockerServiceAppTarget))

  def execute(self):
    invalidation_context = self.invalidated(
      targets=self.app_image_targets,
      invalidate_dependents=True,
      fingerprint_strategy=TaskIdentityFingerprintStrategy(self),
    )
    with invalidation_context as invalidation_check:
      for vt in invalidation_check.invalid_vts:
        self.write_image_manifest(vt)
        vt.update()
    product_dict = self.context.products.safe_create_data(DockerImageProduct, init_func=dict)
    for vt in invalidation_check.all_vts:
      if vt.target in product_dict:
        raise Exception
      image_product = DockerImageProduct(vt.results_dir)
      product_dict[vt.target] = image_product
      for layer_product in image_product.extra_layers:
        self.layer_digest_map[layer_product.digest] = layer_product

  def app_config_for_env(self, target):
    service_config_product = self.service_config_products[target.docker_service_image.service_config]
    service_config_for_env = service_config_product.config_from_env(target.environment)
    app_config = service_config_for_env.app(target.app_name)
    return app_config

  def config_labels(self, target):
    pass
  #   app_config = self.app_config_for_env(target).get_json_dict()
  #   app_config_for_env = app_config[target.environment]

  #   def maybe_stringify(value):
  #     if not isinstance(value, six.string_types):
  #       return str(value)
  #     return value
  #   labels = {k: maybe_stringify(v) for k, v in app_labels.items()}
  #   # Add the full jsonc for the app as well, for aurora hacking
  #   raw_config = self.service_config_products[target.docker_service_image.service_config].raw_config
  #   labels['raw_config'] = json.dumps(raw_config)
  #   return labels

  def image_config(self, target, layers):
    return {
      "architecture": "amd64",
      "os": "linux",
      'Labels': self.config_labels(target),
      "rootfs": {
        "diff_ids": self.diff_ids(layers),
        "type": "layers",
      },
    }

  def layer_products_for_target(self, vt, extra_layers=None):
    extra_layers = extra_layers or []

    def target_layers_iter():
      base_image = vt.target.docker_service_image.base_image
      if base_image is not None:
        for layer_product in self.resolved_layer_products[base_image].layer_products:
          yield layer_product
      for layer in vt.target.docker_service_image.layers:
        yield self.layer_products[layer]
      for layer_product in extra_layers:
        yield layer_product
    return list(target_layers_iter())

  def diff_ids(self, layers):
    return [
      layer_product.diff_id_digest
      for layer_product in layers
    ]

  def manifest_layer_descriptors(self, layers):
    return [
      layer_product.descriptor
      for layer_product in layers
    ]

  def partial_image_manifest(self, layers):
    return {
      'layers': self.manifest_layer_descriptors(layers),
      'mediaType': 'application/vnd.docker.distribution.manifest.v2+json',
      'schemaVersion': 2,
    }

  def write_image_manifest(self, vt):
    extra_layers = [self.jvm_runner_layer(vt)]
    layers = self.layer_products_for_target(vt, extra_layers=extra_layers)
    return DockerImageProduct.write_image_manifest(
      cache_dir=vt.results_dir,
      config=self.image_config(vt.target, layers),
      manifest_without_config_descriptor=self.partial_image_manifest(layers),
      extra_layers=extra_layers,
    )

  def jvm_runner_layer(self, vt):
    return self.write_runner_layer(vt)

  def write_runner_layer(self, vt):
    temp_dir = mkdtemp()
    try:
      return self.create_runner_layer(vt, temp_dir)
    finally:
      safe_rmtree(temp_dir)

  def create_runner_layer(self, vt, temp_dir):
    data_app_dir = os.path.join(temp_dir, 'data/app/')
    safe_mkdir(data_app_dir)

    # .get_json_dict()[target.environment]
    app = self.app_config_for_env(vt.target)
    extras = dict(
      build_time=str(int(time.time())),
      build_version='version',
      env=vt.target.environment,
      app=json.loads(app.to_json()),
      bundle_name=app.service.build.app_name,
      jar_name=app.service.build.jar_name,
    )
    with open(os.path.join(data_app_dir, 'jvm-runner-defaults.json'), 'wb') as f:
      json.dump(extras, f)
    shutil.copy2('build-support/docker/jvm_runner.py', data_app_dir)
    tarfile_tmp_location = os.path.join(temp_dir, 'layer.tar')
    create_stable_tar_from_directory(
      source_dir=data_app_dir,
      tar_root='data/app',
      tarfile_location=tarfile_tmp_location,
    )
    layer_sha256 = stream_sha256(tarfile_tmp_location)
    layer_dir = os.path.join(vt.results_dir, 'sha256:{}'.format(layer_sha256))
    safe_mkdir(layer_dir)
    shutil.copy2(tarfile_tmp_location, layer_dir)
    return LayerProduct.write_metadata_json(layer_dir)
