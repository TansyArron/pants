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

from pants.backend.jvm.targets.jvm_app import BundleField
from pants.base.payload import Payload
from pants.base.payload_field import PrimitiveField
from pants.build_graph.target import Target


class DockerLayer(Target):
  def __init__(self, payload=None, base_dir=None, canonical_docker_repo=None, **kwargs):
    payload = payload or Payload()
    payload.add_fields({
      'base_dir': PrimitiveField(base_dir),
      'canonical_docker_repo': PrimitiveField(canonical_docker_repo),
    })
    super(DockerLayer, self).__init__(payload=payload, **kwargs)

  @property
  def base_dir(self):
    return self.payload.base_dir

  @property
  def canonical_docker_repo(self):
    return self.payload.canonical_docker_repo


class DockerClasspathLayerTarget(DockerLayer):
  pass


class DockerServiceLayerTarget(DockerLayer):
  def __init__(self, payload=None, bundle_name=None, binary=None, bundles=None, **kwargs):
    self._binary_spec = binary
    payload = payload or Payload()
    payload.add_fields({
      'bundles': BundleField(bundles or []),
      'bundle_name': PrimitiveField(bundle_name),
    })
    super(DockerServiceLayerTarget, self).__init__(payload=payload, **kwargs)

  @property
  def traversable_dependency_specs(self):
    for spec in super(DockerServiceLayerTarget, self).traversable_dependency_specs:
      yield spec
    if self._binary_spec:
      yield self._binary_spec

  @property
  def bundle_name(self):
    return self.payload.bundle_name

  @property
  def bundles(self):
    return self.payload.bundles

  @property
  def binary(self):
    if not self._binary_spec:
      return None
    return self._build_graph.get_target_from_spec(self._binary_spec, relative_to=self.address.spec_path)
