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
from subprocess import check_call
from tarfile import TarFile
from tempfile import mkdtemp

from pants.task.task import Task
from pants.util.dirutil import safe_rmtree

from pants.contrib.docker.products.docker_image import DockerImageProduct
from pants.contrib.docker.products.layer_product import LayerDigestMap, LayerProduct
from pants.contrib.docker.targets.docker_service_app import DockerServiceAppTarget


def strip_digest_prefix(digest, prefix='sha256:'):
  if not digest.startswith(prefix):
    raise Exception
  return digest[len(prefix):]


class DockerLocalPublishTask(Task):

  @classmethod
  def prepare(cls, options, round_manager):
    super(DockerLocalPublishTask, cls).prepare(options, round_manager)
    round_manager.require_data(DockerImageProduct)
    round_manager.require_data(LayerDigestMap)

  @classmethod
  def implementation_version(cls):
    return super(
      DockerLocalPublishTask, cls).implementation_version() + [('DockerLocalPublishTask', 1)]

  @property
  def layer_products(self):
    return self.context.products.get_data(LayerProduct, init_func=dict)

  @property
  def docker_image_products(self):
    return self.context.products.get_data(DockerImageProduct, init_func=dict)

  @property
  def layer_digest_map(self):
    return self.context.products.get_data(LayerDigestMap, init_func=dict)

  def execute(self):
    docker_app_targets = self.context.targets(predicate=lambda t: isinstance(t, DockerServiceAppTarget))
    for docker_app_target in docker_app_targets:
      docker_image_product = self.docker_image_products[docker_app_target]
      temp_dir = mkdtemp()
      try:
        tar_path = self.create_image_tar(temp_dir, docker_image_product)
        self.docker_load(tar_path)
      finally:
        safe_rmtree(temp_dir)

  def docker_load(self, tar_path):
    check_call(['docker', 'load', '--input', tar_path])

  def create_image_tar(self, temp_dir, docker_image_product):
    tar_path = os.path.join(temp_dir, 'image.tar')
    tar_file = TarFile(tar_path, 'w')
    config_dest_path = '{}.json'.format(strip_digest_prefix(docker_image_product.config_digest))
    manifest = {
      'Layers': [],
      'Config': config_dest_path,
    }

    with tar_file as tar:
      tar.add(name=docker_image_product.config_path, arcname=config_dest_path)
      layers = manifest['Layers']
      for layer_descriptor in docker_image_product.layer_descriptors:
        layer_product = self.layer_digest_map[layer_descriptor['digest']]
        layer_dest_path = os.path.join(strip_digest_prefix(layer_product.digest), 'layer.tar')
        layers.append(layer_dest_path)
        tar.add(name=layer_product.tar_path, arcname=layer_dest_path)
      temp_manifest_path = os.path.join(temp_dir, 'manifest.json')
      with open(temp_manifest_path, 'wb') as f:
        json.dump([manifest], f)
      tar.add(name=temp_manifest_path, arcname='manifest.json')
    return tar_path
