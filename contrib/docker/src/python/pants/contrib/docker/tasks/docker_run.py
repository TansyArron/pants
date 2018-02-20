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

# from pants.contrib.docker.products.docker_image import DockerLocalImageProduct
from pants.contrib.docker.targets.docker_service_app import DockerServiceImageTarget


class DockerRunImageTask(Task):

  @classmethod
  def prepare(cls, options, round_manager):
    super(DockerRunImageTask, cls).prepare(options, round_manager)
    round_manager.require_data('DockerLocalImageProduct')

  @classmethod
  def implementation_version(cls):
    return super(
      DockerRunImageTask, cls).implementation_version() + [('DockerRunImageTask', 1)]

  @property
  def docker_local_image_products(self):
    return self.context.products.get_data('DockerLocalImageProduct', init_func=dict)

  def execute(self):
    # TODO(Tansy): Check docker app is installed
    docker_image_targets = self.context.targets(predicate=lambda t: isinstance(t, DockerServiceImageTarget))
    docker_run_command = ['docker', 'run']
    for docker_image_target in docker_image_targets:
      docker_local_image_ref = self.docker_local_image_products[docker_image_target]

      image_uri = '{registry}/{image_repo}@{image_digest}'.format(
        registry='docker-registry.foo.com',
        image_repo=image_repo,
        image_digest=image_digest,
      )

      print(image_uri)
