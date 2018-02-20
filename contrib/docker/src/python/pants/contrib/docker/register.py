# coding=utf-8
# Copyright 2017 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from pants.goal.task_registrar import TaskRegistrar as task
from pants.build_graph.build_file_aliases import BuildFileAliases
from pants.contrib.docker.targets.docker_image import DockerImage
from pants.contrib.docker.targets.docker_layer import (
  DockerClasspathLayerTarget,
  DockerServiceLayerTarget,
)
from pants.contrib.docker.targets.docker_remote_image import DockerRemoteImageTarget
from pants.contrib.docker.targets.docker_service_app import DockerServiceAppTarget
from pants.contrib.docker.targets.docker_service_image import DockerServiceImageTarget
from pants.contrib.docker.tasks.docker_classpath_layer import DockerClasspathLayerTask
from pants.contrib.docker.tasks.docker_local_publish import DockerLocalPublishTask
from pants.contrib.docker.tasks.docker_publish_image import DockerPublishImageTask
from pants.contrib.docker.tasks.docker_resolve_remote_image import DockerResolveRemoteImageTask
from pants.contrib.docker.tasks.docker_service_image import DockerServiceImageTask
from pants.contrib.docker.tasks.docker_service_layer import DockerServiceLayerTask


def build_file_aliases():
  return BuildFileAliases(
    targets={
      'docker_remote_image': DockerRemoteImageTarget,
      'docker_classpath_layer': DockerClasspathLayerTarget,
      'docker_image': DockerImage,
      'docker_service_app': DockerServiceAppTarget,
      'docker_service_image': DockerServiceImageTarget,
    },
    objects={},
    context_aware_object_factories={}
  )


def register_goals():
  task(
    name='docker-classpath-layer',
    action=DockerClasspathLayerTask,
  ).install()

  task(
    name='docker-service-layer',
    action=DockerServiceLayerTask,
  ).install()

  task(
    name='docker-service-image',
    action=DockerServiceImageTask,
  ).install()

  task(
    name='docker-publish',
    action=DockerPublishImageTask,
  ).install()

  task(
    name='docker-local-publish',
    action=DockerLocalPublishTask,
  ).install()

  task(
    name='docker-resolve-remote-image',
    action=DockerResolveRemoteImageTask,
  ).install()

