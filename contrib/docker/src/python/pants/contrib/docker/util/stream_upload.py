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

import sys
from urlparse import parse_qs, urlparse, urlunparse

import requests
import io
import logging

ONE_MEGABYTE = 2 ** 20


logger = logging.getLogger(__name__)


def iterable_to_stream(iterable, buffer_size=io.DEFAULT_BUFFER_SIZE):
  """
  Lets you use an iterable (e.g. a generator) that yields bytestrings as a read-only input stream.

  The stream implements Python 3's newer I/O API (available in Python 2's io module).
  For efficiency, the stream is buffered.

  From: http://stackoverflow.com/questions/6657820/python-convert-an-iterable-to-a-stream
  """
  class IterStream(io.RawIOBase):
    def __init__(self):
      self.leftover = None

    def readable(self):
      return True

    def readinto(self, b):
      try:
        l = len(b)  # We're supposed to return at most this much
        chunk = self.leftover or next(iterable)
        output, self.leftover = chunk[:l], chunk[l:]
        b[:len(output)] = output
        return len(output)
      except StopIteration:
        return 0    # indicate EOF

  return io.BufferedReader(IterStream(), buffer_size=buffer_size)


def stream_copy(source, dest):
  while True:
    chunk = source.read(io.DEFAULT_BUFFER_SIZE)
    if not chunk:
      break
    dest.write(chunk)
  dest.flush()


def finish_upload(url, digest):
  parsed_upload_url = urlparse(url)
  parsed_query_dict = parse_qs(parsed_upload_url.query, strict_parsing=True)
  parsed_query_dict['digest'] = digest
  headers = {
    'Content-Type': 'application/octet-stream',
  }
  upload_url = urlunparse((parsed_upload_url.scheme, parsed_upload_url.netloc, parsed_upload_url.path, '', '', ''))
  response = requests.put(upload_url, headers=headers, params=parsed_query_dict, verify=False)
  response.raise_for_status()


def chunk_iter(file_handle, blocksize):
  offset = 0
  while True:
    buf = file_handle.read(blocksize)
    if not buf:
      finish_upload(url, digest)
      return
    chunk_size = len(buf)
    end_of_range = offset + chunk_size - 1


def stream_upload(url, path, digest, blocksize=50 * ONE_MEGABYTE):
  # PATCH /v2/<name>/blobs/uploads/<uuid>
  session = requests.Session()
  with open(path, 'rb') as f:
    offset = 0
    while True:
      buf = f.read(blocksize)
      if not buf:
        finish_upload(url, digest)
        return
      chunk_size = len(buf)
      end_of_range = offset + chunk_size - 1
      headers = {
        'Content-Length': str(chunk_size),
        'Content-Range': '{}-{}'.format(offset, end_of_range),
        'Content-Type': 'application/octet-stream',
      }
      response = session.patch(url, headers=headers, stream=True, verify=False, data=buf)
      response.raise_for_status()
      sys.stderr.write('.')
      url = response.headers['Location']
      offset += chunk_size
