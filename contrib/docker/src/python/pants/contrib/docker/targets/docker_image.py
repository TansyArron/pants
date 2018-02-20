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

from pants.base.payload import Payload
from pants.base.payload_field import PrimitiveField
from pants.build_graph.target import Target


class DockerServiceImageTarget(Target):

  def __init__(self, payload=None, image_repo=None, layers=None, service_config=None, base_image=None, **kwargs):
    self._layer_specs = layers or []
    self._service_config_spec = service_config
    self._base_image_spec = base_image
    payload = payload or Payload()
    payload.add_fields({
      'image_repo': PrimitiveField(image_repo),
    })
    super(DockerServiceImageTarget, self).__init__(payload=payload, **kwargs)

  @property
  def image_repo(self):
    return self.payload.image_repo

  @property
  def traversable_dependency_specs(self):
    for spec in super(DockerServiceImageTarget, self).traversable_dependency_specs:
      yield spec
    for layer_spec in self._layer_specs:
      yield layer_spec
    if self._service_config_spec:
      yield self._service_config_spec
    if self._base_image_spec:
      yield self._base_image_spec

  @property
  def layers(self):
    return [
      self._build_graph.get_target_from_spec(layer_spec, relative_to=self.address.spec_path)
      for layer_spec in self._layer_specs
    ]

  @property
  def base_image(self):
    if not self._base_image_spec:
      return None
    return self._build_graph.get_target_from_spec(self._base_image_spec, relative_to=self.address.spec_path)

  @property
  def service_config(self):
    if not self._service_config_spec:
      return None
    return self._build_graph.get_target_from_spec(self._service_config_spec, relative_to=self.address.spec_path)
