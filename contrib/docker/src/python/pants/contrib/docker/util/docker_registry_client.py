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

import io
from urlparse import parse_qs, urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from pants.contrib.docker.util.hashing import check_file_sha256
from pants.contrib.docker.util.stream_upload import iterable_to_stream, stream_copy


ONE_MEGABYTE = 2 ** 20

# We should really not be doing this. Make sure we have certs distributed.
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class DockerRegistryClient(object):
  def __init__(self, registry_url):
    self.registry_url = registry_url
    self.session = requests.Session()
    self.session.mount(self.registry_url, HTTPAdapter(max_retries=3))

  def _entity_url(self, image_repo, entity_type, entity_ref):
    return '{registry_url}/v2/{image_repo}/{entity_type}/{entity_ref}'.format(
      registry_url=self.registry_url,
      image_repo=image_repo,
      entity_type=entity_type,
      entity_ref=entity_ref,
    )

  def blob_url(self, image_repo, digest):
    return self._entity_url(image_repo=image_repo, entity_type='blobs', entity_ref=digest)

  def blob_exists(self, image_repo, digest):
    return self._entity_exists(
      entity_url=self.blob_url(image_repo=image_repo, digest=digest),
    )

  def _start_upload_url(self, image_repo):
    return '{registry_url}/v2/{image_repo}/blobs/uploads/'.format(
      registry_url=self.registry_url,
      image_repo=image_repo,
    )

  def monolithic_upload(self, image_repo, digest, source_file_path, content_type):
    response = requests.post(self._start_upload_url(image_repo=image_repo), verify=False)
    url = response.headers['Location']
    headers = {
      'Content-Type': content_type,
    }
    parsed_upload_url = urlparse(url)
    parsed_query_dict = parse_qs(parsed_upload_url.query, strict_parsing=True)
    parsed_query_dict['digest'] = digest
    upload_url = urlunparse((
      parsed_upload_url.scheme, parsed_upload_url.netloc, parsed_upload_url.path,
      '', '', '',
    ))

    def chunk_iter():
      with open(source_file_path, 'rb') as f:
        while True:
          buf = f.read(ONE_MEGABYTE)
          if not buf:
            return
          yield buf

    response = self.session.put(
      upload_url,
      headers=headers,
      params=parsed_query_dict,
      stream=True,
      verify=False,
      data=chunk_iter()
    )
    response.raise_for_status()

  def _entity_exists(self, entity_url):
    response = requests.head(entity_url, verify=False)
    if response.status_code == 404:
      return False
    elif 200 <= response.status_code < 400:
      return True
    else:
      response.raise_for_status()
      raise Exception

  def ensure_base_layers_mounted(self, source_image_repo, source_image_ref, dest_image_repo):
    layer_tuples = self.get_image_layers(image_repo=source_image_repo, image_ref=source_image_ref)
    for manifest_layer, _ in layer_tuples:
      digest = manifest_layer['digest']
      if not self.blob_exists(image_repo=dest_image_repo, digest=digest):
        self.mount_layer(
          image_repo=dest_image_repo,
          digest=digest,
          mount_source_repo=source_image_repo,
        )

  def ensure_image_manifest_present(self, image_repo, manifest_digest, manifest_path):
    entity_url = self._entity_url(image_repo=image_repo, entity_type='manifests', entity_ref=manifest_digest)
    if self._entity_exists(entity_url=entity_url):
      return
    headers = {
      'Content-Type': 'application/vnd.docker.distribution.manifest.v2+json',
    }
    with open(manifest_path, 'rb') as f:
      response = requests.put(url=entity_url, headers=headers, verify=False, data=f)
    response.raise_for_status()

  def ensure_layer_present(self, image_repo, layer_digest, layer_path, mount_source_repo=None):
    """ Ensure the layer is present in the docker registry, push it to the registry if needed.

    If the layer has a canonical docker repo, make sure it is present in that repo and
    then mount it to the repo of the image we are pushing.
    """
    if self.blob_exists(image_repo=image_repo, digest=layer_digest):
      return
    if mount_source_repo:
      self.ensure_layer_present(image_repo=mount_source_repo, layer_digest=layer_digest, layer_path=layer_path)
      self.mount_layer(image_repo=image_repo, digest=layer_digest, mount_source_repo=mount_source_repo)
    self.monolithic_upload(
      image_repo=image_repo,
      digest=layer_digest,
      source_file_path=layer_path,
      content_type='application/octet-stream',
    )

  def mount_layer(self, image_repo, digest, mount_source_repo):
    params = {
      'mount': digest,
      'from': mount_source_repo,
    }
    start_upload_url = self._start_upload_url(image_repo=image_repo)
    response = requests.post(start_upload_url, params=params, verify=False)
    response.raise_for_status()
    if response.status_code != 201:
      raise Exception

  def ensure_config_present(self, image_repo, config_digest, config_path):
    if self.blob_exists(image_repo=image_repo, digest=config_digest):
      return
    self.monolithic_upload(
      image_repo=image_repo,
      digest=config_digest,
      source_file_path=config_path,
      content_type='application/vnd.docker.container.image.v1+json',
    )

  def _get_image_manifest_response(self, image_repo, image_ref):
    url = self._entity_url(image_repo=image_repo, entity_type='manifests', entity_ref=image_ref)
    headers = {
      'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response

  def get_image_manifest_json(self, image_repo, image_ref):
    return self._get_image_manifest_response(image_repo=image_repo, image_ref=image_ref).json()

  def get_image_manifest_content(self, image_repo, image_ref):
    return self._get_image_manifest_response(image_repo=image_repo, image_ref=image_ref).content

  def _get_image_config_response_from_digest(self, image_repo, config_digest):
    url = self.blob_url(image_repo=image_repo, digest=config_digest)
    response = requests.get(url, verify=False)
    response.raise_for_status()
    return response

  def _get_image_config_response(self, image_repo, image_ref):
    image_manifest_json = self.get_image_manifest_json(image_repo=image_repo, image_ref=image_ref).json()
    config_digest = image_manifest_json['config']['digest']
    return self._get_image_config_response_from_digest(image_repo=image_repo, config_digest=config_digest)

  def get_image_config_json(self, image_repo, image_ref):
    return self._get_image_config_response(image_repo=image_repo, image_ref=image_ref).json()

  def get_image_config_content(self, image_repo, image_ref):
    return self._get_image_config_response(image_repo=image_repo, image_ref=image_ref).content

  def get_image_layers(self, image_repo, image_ref):
    manifest = self.get_image_manifest_json(image_repo=image_repo, image_ref=image_ref)
    config_digest = manifest['config']['digest']
    config = self._get_image_config_response_from_digest(image_repo=image_repo, config_digest=config_digest).json()
    manifest_layers = manifest['layers']
    diff_id_layers = config['rootfs']['diff_ids']
    return list(zip(manifest_layers, diff_id_layers))

  def download_image_layer(self, image_repo, layer_digest, layer_tar_path):
    url = self.blob_url(image_repo=image_repo, digest=layer_digest)
    with open(layer_tar_path, 'wb') as f:
      response = requests.get(url, stream=True, verify=False)
      response.raise_for_status()
      source = iterable_to_stream(response.iter_content(chunk_size=io.DEFAULT_BUFFER_SIZE))
      stream_copy(source=source, dest=f)
    check_file_sha256(layer_tar_path, layer_digest)
    return response.headers['Content-Type']
