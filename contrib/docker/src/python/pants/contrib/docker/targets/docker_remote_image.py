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


class DockerRemoteImageTarget(Target):

  def __init__(self, payload=None, repo=None, ref=None, **kwargs):
    payload = payload or Payload()
    payload.add_fields({
      'repo': PrimitiveField(repo),
      'ref': PrimitiveField(ref),
    })
    super(DockerRemoteImageTarget, self).__init__(payload=payload, **kwargs)

  @property
  def repo(self):
    return self.payload.repo

  @property
  def ref(self):
    return self.payload.ref
