# coding=utf-8
# Copyright 2017 Foursquare Labs Inc. All Rights Reserved.

from __future__ import (
  absolute_import,
  division,
  generators,
  nested_scopes,
  print_function,
  unicode_literals,
  with_statement,
)

from pants.task.task import Task

from pants.contrib.docker.products.docker_image import DockerImageProduct
from pants.contrib.docker.products.layer_product import LayerDigestMap, LayerProduct
from pants.contrib.docker.targets.docker_service_app import DockerServiceAppTarget
from pants.contrib.docker.util.docker_registry_client import DockerRegistryClient


class DockerPublishImageTask(Task):

  @classmethod
  def prepare(cls, options, round_manager):
    super(DockerPublishImageTask, cls).prepare(options, round_manager)
    round_manager.require_data(DockerImageProduct)
    round_manager.require_data(LayerDigestMap)

  @classmethod
  def implementation_version(cls):
    return super(
      DockerPublishImageTask, cls).implementation_version() + [('DockerPublishImageTask', 1)]

  @property
  def layer_products(self):
    return self.context.products.get_data(LayerProduct, init_func=dict)

  @property
  def docker_image_products(self):
    return self.context.products.get_data(DockerImageProduct, init_func=dict)

  @property
  def layer_digest_map(self):
    return self.context.products.get_data(LayerDigestMap, init_func=dict)

  @property
  def registry(self):
    return DockerRegistryClient('https://docker-registry.foo.com')

  def execute(self):
    docker_app_targets = self.context.targets(predicate=lambda t: isinstance(t, DockerServiceAppTarget))
    for docker_app_target in docker_app_targets:
      docker_image_product = self.docker_image_products[docker_app_target]
      image_repo = docker_app_target.docker_service_image.image_repo
      image_digest = docker_image_product.manifest_digest
      for layer_descriptor in docker_image_product.layer_descriptors:
        layer_product = self.layer_digest_map[layer_descriptor['digest']]
        self.registry.ensure_layer_present(
          image_repo=image_repo,
          layer_digest=layer_product.digest,
          layer_path=layer_product.tar_path,
          mount_source_repo=layer_product.canonical_image_repo,
        )
      self.registry.ensure_config_present(
        image_repo=image_repo,
        config_digest=docker_image_product.config_digest,
        config_path=docker_image_product.config_path,
      )
      self.registry.ensure_image_manifest_present(
        image_repo=image_repo,
        manifest_digest=docker_image_product.manifest_digest,
        manifest_path=docker_image_product.manifest_path,
      )
      image_uri = '{registry}/{image_repo}@{image_digest}'.format(
        registry='docker-registry.prod.foursquare.com',
        image_repo=image_repo,
        image_digest=image_digest,
      )

      print(image_uri)
