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

import os
from tempfile import mkdtemp
import unittest

from pants.util.dirutil import safe_rmtree

from pants.contrib.docker.util.hashing import (
  ContentDigestMismatch,
  check_file_sha256,
  stream_sha256,
)


class TestHashing(unittest.TestCase):

  def setUp(self):
    self.source_dir = mkdtemp()

  def tearDown(self):
    safe_rmtree(self.source_dir)

  def make_source_file(self, filename, content):
    abs_path = os.path.join(self.source_dir, filename)
    with open(abs_path, 'wb') as f:
      f.write(content)
    return os.path.realpath(abs_path)

  def test_stream_sha256(self):
    test_file = self.make_source_file(filename='test_foo.txt', content='foo')
    file_sha256 = stream_sha256(test_file)
    expected_sha256 = '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'
    self.assertEquals(file_sha256, expected_sha256)

  def test_check_file_sha256_succeeds(self):
    test_file = self.make_source_file(filename='test_foo.txt', content='foo')
    digest = 'sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'
    self.assertTrue(check_file_sha256(test_file, digest))

  def test_check_file_sha256_fails(self):
    test_file = self.make_source_file(filename='test_foo.txt', content='bad content')
    bad_digest = 'sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'
    with self.assertRaises(ContentDigestMismatch):
      check_file_sha256(test_file, bad_digest)
