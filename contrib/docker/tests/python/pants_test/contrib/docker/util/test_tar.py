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
from tarfile import TarFile
from tempfile import mkdtemp
import unittest

from pants.util.dirutil import safe_mkdir, safe_rmtree

from pants.contrib.docker.util.hashing import stream_sha256
from pants.contrib.docker.util.tar import create_stable_tar, map_build_path_to_tar_path


class TestTarUtil(unittest.TestCase):

  def setUp(self):
    self.source_dir = mkdtemp()
    self.tarfile_location = mkdtemp()
    self.tar_path = os.path.join(self.tarfile_location, 'test.tar')

    # Create contents
    self.source_realpath_a = self.make_source_file('a/b/c.txt', content='bar')
    self.source_realpath_b = self.make_source_file('B/c/d.txt', content='foo')

    # Empty directory. This should be totally ignored by the tar util.
    safe_mkdir(os.path.join(self.source_dir, 'empty'))

  def tearDown(self):
    safe_rmtree(self.source_dir)
    safe_rmtree(self.tarfile_location)

  def make_source_file(self, relpath, content):
    abs_path = os.path.join(self.source_dir, relpath)
    safe_mkdir(os.path.dirname(abs_path))
    with open(abs_path, 'wb') as f:
      f.write(content)
    return os.path.realpath(abs_path)

  def get_tar_paths(self, tarfile_location):
    with TarFile.open(tarfile_location) as tar:
      return tar.getnames()

  def test_map_build_path_to_tar_path(self):
    self.assertDictEqual(
      map_build_path_to_tar_path(self.source_dir, tar_root='/data/app'),
      {
        '/data/app/a/b/c.txt': self.source_realpath_a,
        '/data/app/B/c/d.txt': self.source_realpath_b,
      },
    )
    self.assertDictEqual(
      map_build_path_to_tar_path(self.source_dir, tar_root='/'),
      {
        '/a/b/c.txt': self.source_realpath_a,
        '/B/c/d.txt': self.source_realpath_b,
      },
    )
    self.assertDictEqual(
      map_build_path_to_tar_path(self.source_dir, tar_root=''),
      {
        'a/b/c.txt': self.source_realpath_a,
        'B/c/d.txt': self.source_realpath_b,
      },
    )

  def test_create_stable_tar_contents(self):
    """Check that the tar includes the files we expect, in the order we expect.

    Check that the sha256 of the tar is as expected, meaning the tarinfo is stable.
    """
    created_tar_path = create_stable_tar(
      tarfile_location=self.tar_path,
      tar_location_to_source_location=map_build_path_to_tar_path(self.source_dir, tar_root='/data/app'),
      symlinks=None,
    )
    expected_contents = ['data/app/B/c/d.txt', 'data/app/a/b/c.txt']
    self.assertListEqual(self.get_tar_paths(created_tar_path), expected_contents)

    expected_sha256 = 'aeb2e9a07236f596375e21684e00e9adddbdac3a9e7414511a3e23647786b536'
    tar_sha256 = stream_sha256(created_tar_path)
    self.assertEqual(tar_sha256, expected_sha256)

    created_tar_path = create_stable_tar(
      tarfile_location=self.tar_path,
      tar_location_to_source_location=map_build_path_to_tar_path(self.source_dir, tar_root='/data/app'),
      symlinks={
        '/data/app/symlink.jar': 'foo/bar/symlink.jar'
      },
    )
    expected_contents = ['data/app/B/c/d.txt', 'data/app/a/b/c.txt', 'data/app/symlink.jar']
    self.assertListEqual(self.get_tar_paths(created_tar_path), expected_contents)

    expected_sha256 = '83b1d7da9b321e3a5033af2e238b2809f97d0901430df0105b61c837e836ab46'
    tar_sha256 = stream_sha256(created_tar_path)
    self.assertEqual(tar_sha256, expected_sha256)
