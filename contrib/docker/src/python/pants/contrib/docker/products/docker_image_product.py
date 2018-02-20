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

from pants.base.payload_field import stable_json_dumps
from pants.util.memo import memoized_property

from pants.contrib.docker.products.layer_product import LayerProduct
from pants.contrib.docker.util.hashing import stream_sha256


class DockerImageProduct(object):
  MANIFEST_JSON_FILE_NAME = 'manifest.json'
  CONFIG_JSON_FILE_NAME = 'config.json'
  METADATA_JSON_FILE_NAME = 'metadata.json'

  @classmethod
  def write_image_manifest(cls, cache_dir, config, manifest_without_config_descriptor, extra_layers=None):
    extra_layers = extra_layers or []

    config_stable_json = stable_json_dumps(config)
    config_blob_path = os.path.join(cache_dir, cls.CONFIG_JSON_FILE_NAME)
    with open(config_blob_path, 'wb') as f:
      f.write(config_stable_json)
    config_digest = 'sha256:{}'.format(stream_sha256(config_blob_path))
    manifest_without_config_descriptor['config'] = {
      "mediaType": "application/vnd.docker.container.image.v1+json",
      "size": len(config_stable_json),
      "digest": config_digest,
    }
    manifest_stable_json = stable_json_dumps(manifest_without_config_descriptor)
    manifest_blob_path = os.path.join(cache_dir, cls.MANIFEST_JSON_FILE_NAME)
    with open(manifest_blob_path, 'wb') as f:
      f.write(manifest_stable_json)
    manifest_digest = 'sha256:{}'.format(stream_sha256(manifest_blob_path))
    metadata = {
      'manifest_digest': manifest_digest,
      'config_digest': config_digest,
      'extra_layers': [layer_product.digest for layer_product in extra_layers],
    }
    with open(os.path.join(cache_dir, cls.METADATA_JSON_FILE_NAME), 'wb') as f:
      json.dump(metadata, f)

  def __init__(self, cache_dir):
    self._cache_dir = cache_dir

  @memoized_property
  def metadata(self):
    with open(os.path.join(self._cache_dir, self.METADATA_JSON_FILE_NAME), 'rb') as f:
      return json.load(f)

  @property
  def extra_layers(self):
    def layer_product_iter():
      for layer_path in self.metadata['extra_layers']:
        yield LayerProduct(os.path.join(self._cache_dir, layer_path))
    return list(layer_product_iter())

  @property
  def manifest_digest(self):
    return self.metadata['manifest_digest']

  @property
  def config_digest(self):
    return self.metadata['config_digest']

  @property
  def manifest_path(self):
    return os.path.join(self._cache_dir, self.MANIFEST_JSON_FILE_NAME)

  @property
  def config_path(self):
    return os.path.join(self._cache_dir, self.CONFIG_JSON_FILE_NAME)

  @memoized_property
  def manifest(self):
    with open(self.manifest_path, 'rb') as f:
      return json.load(f)

  @property
  def layer_descriptors(self):
    return self.manifest['layers']


class DockerLocalImageRef(object):
  pass
