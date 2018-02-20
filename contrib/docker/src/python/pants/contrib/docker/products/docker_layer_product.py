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

from pants.util.memo import memoized_property

from pants.contrib.docker.util.hashing import check_file_sha256, stream_sha256


class LayerDigestMap(object):
  pass


class ResolvedLayerProducts(object):
  LAYERS_LIST_FILENAME = 'layer_list.json'

  def __init__(self, cache_dir):
    self._cache_dir = cache_dir

  @classmethod
  def write_layer_dir_list(cls, cache_dir, layer_dir_list):
    layer_list_path = os.path.join(cache_dir, cls.LAYERS_LIST_FILENAME)
    with open(layer_list_path, 'wb') as f:
      json.dump(layer_dir_list, f)

  @memoized_property
  def layer_products(self):
    layers_list_path = os.path.join(self._cache_dir, self.LAYERS_LIST_FILENAME)
    with open(layers_list_path, 'rb') as f:
      layer_filepath_list = json.load(f)

    def layer_product_iter():
      for layer_path in layer_filepath_list:
        yield LayerProduct(os.path.join(self._cache_dir, layer_path))
    return list(layer_product_iter())


class LayerProduct(object):
  LAYER_TAR_FILE_NAME = 'layer.tar'
  METADATA_PATH = 'metadata.json'

  @classmethod
  def write_metadata_json(
    cls,
    results_dir,
    diff_id_digest=None,
    media_type='application/vnd.docker.image.rootfs.diff.tar',
    canonical_image_repo=None,
  ):
    tar_path = os.path.join(results_dir, cls.LAYER_TAR_FILE_NAME)
    metadata_path = os.path.join(results_dir, cls.METADATA_PATH)
    digest = 'sha256:{}'.format(stream_sha256(tar_path))
    diff_id_digest = diff_id_digest or digest
    metadata = {
      'media_type': media_type,
      'size': os.path.getsize(tar_path),
      'digest': digest,
      'diff_id_digest': diff_id_digest,
      'canonical_image_repo': canonical_image_repo,
    }
    with open(metadata_path, 'wb') as f:
      json.dump(metadata, f)
    return cls(results_dir)

  def __init__(self, cache_dir):
    self._cache_dir = cache_dir

  @memoized_property
  def metadata(self):
    metadata_path = os.path.join(self._cache_dir, self.METADATA_PATH)
    with open(metadata_path, 'rb') as f:
      return json.load(f)

  @property
  def tar_path(self):
    return os.path.join(self._cache_dir, self.LAYER_TAR_FILE_NAME)

  @property
  def digest(self):
    return self.metadata['digest']

  @property
  def size(self):
    return self.metadata['size']

  @property
  def media_type(self):
    return self.metadata['media_type']

  @property
  def diff_id_digest(self):
    return self.metadata['diff_id_digest']

  @property
  def canonical_image_repo(self):
    return self.metadata['canonical_image_repo']

  @property
  def descriptor(self):
    return {
      'mediaType': self.media_type,
      'size': self.size,
      'digest': self.digest,
    }

  def validate_tar(self):
    if os.path.getsize(self.tar_path) != self.size:
      raise Exception
    return check_file_sha256(self.tar_path, self.digest)
