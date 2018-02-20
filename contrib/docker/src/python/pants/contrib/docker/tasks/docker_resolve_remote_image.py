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

import os

from pants.task.task import Task
from pants.util.dirutil import safe_mkdir

from pants.contrib.docker.products.layer_product import (
  LayerDigestMap,
  LayerProduct,
  ResolvedLayerProducts,
)
from pants.contrib.docker.targets.docker_remote_image import DockerRemoteImageTarget
from pants.contrib.docker.util.docker_registry_client import DockerRegistryClient


class DockerResolveRemoteImageTask(Task):

  @classmethod
  def product_types(cls):
    return [ResolvedLayerProducts, LayerDigestMap]

  @classmethod
  def prepare(cls, options, round_manager):
    super(DockerResolveRemoteImageTask, cls).prepare(options, round_manager)

  @classmethod
  def implementation_version(cls):
    return super(
      DockerResolveRemoteImageTask, cls).implementation_version() + [('DockerResolveRemoteImageTask', 0)]

  @property
  def cache_target_dirs(self):
    return True

  @property
  def registry(self):
    # TODO(Tansy): Registry url should be configured in the ini or a subsystem.
    return DockerRegistryClient('https://docker-registry.foo.com')

  @property
  def remote_image_targets(self):
    return self.context.targets(predicate=lambda t: isinstance(t, DockerRemoteImageTarget))

  def execute(self):
    products = self.context.products
    invalidation_context = self.invalidated(
      targets=self.remote_image_targets,
      invalidate_dependents=True,
    )
    with invalidation_context as invalidation_check:
      for vt in invalidation_check.invalid_vts:
        self.download_base_layers(
          image_repo=vt.target.repo,
          image_ref=vt.target.ref,
          results_dir=vt.results_dir
        )
        vt.update()
    layer_digest_map = self.context.products.safe_create_data(LayerDigestMap, init_func=dict)
    product_dict = products.safe_create_data(ResolvedLayerProducts, init_func=dict)
    for vt in invalidation_check.all_vts:
      if vt.target in product_dict:
        raise Exception
      resolved_layer_products = ResolvedLayerProducts(vt.results_dir)
      product_dict[vt.target] = resolved_layer_products
      for layer in resolved_layer_products.layer_products:
        layer_digest_map[layer.digest] = layer

  def download_base_layers(self, image_repo, image_ref, results_dir):
    base_layers = []
    image_layers = self.registry.get_image_layers(image_repo, image_ref)
    for layer_descriptor, diff_id_digest in image_layers:
      digest = layer_descriptor['digest']
      layer_dir = os.path.join(results_dir, digest)
      safe_mkdir(layer_dir)
      layer_tar_path = os.path.join(layer_dir, 'layer.tar')
      content_type = self.registry.download_image_layer(
        image_repo=image_repo,
        layer_digest=digest,
        layer_tar_path=layer_tar_path,
      )
      LayerProduct.write_metadata_json(
        results_dir=layer_dir,
        diff_id_digest=diff_id_digest,
        canonical_image_repo=image_repo,
        media_type=content_type,
      )
      base_layers.append(digest)
    ResolvedLayerProducts.write_layer_dir_list(cache_dir=results_dir, layer_dir_list=base_layers)
