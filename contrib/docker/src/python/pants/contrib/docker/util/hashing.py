# coding=utf-8
# Copyright 2017 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (
  absolute_import,
  division,
  generators,
  nested_scopes,
  print_function,
  unicode_literals,
  with_statement,
)

import hashlib
import io


def stream_sha256(path, blocksize=io.DEFAULT_BUFFER_SIZE):
  """Provide the sha256 hash of a large file"""
  hasher = hashlib.sha256()
  with open(path, 'rb') as f:
    while True:
      buf = f.read(blocksize)
      if not buf:
        break
      hasher.update(buf)
  return hasher.hexdigest()


class ContentDigestMismatch(Exception):
  """Content does not match expected digest"""


def check_file_sha256(file_path, digest):
  """Check file contents against expected digest

  This function expects the path to a docker layer tar and the `digest` given by docker, with the format:
  `sha256:deadbeafdeadbeefdeadbeafdeadbeefdeadbeafdeadbeefdeadbeafdeadbeef`
  """
  _, expected_sha256 = digest.split(':')
  file_sha256 = stream_sha256(file_path)
  if not file_sha256.lower() == expected_sha256.lower():
    raise ContentDigestMismatch(
      'file at path {file_path} had sha {file_sha256}. Expected {expected_sha256}'.format(
        file_path=file_path,
        file_sha256=file_sha256,
        expected_sha256=expected_sha256,
      )
    )
  return True
