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
from tarfile import SYMTYPE, TarFile, TarInfo

from pants.util.dirutil import fast_relpath


def map_build_path_to_tar_path(source_dir, tar_root):
  """Return a dictionary of tar internal path to source file location.

  For example, if `/tmp/test` contains `foo/bar.txt`:
  ```
  map_build_path_to_tar_path(source_dir='/tmp/test', tar_root='/data/app')
  ```
  returns:
  {'/data/app/foo/bar.txt': '/tmp/test/foo/bar.txt'}

  Note: This function will not include empty directories.
  """
  tar_location_to_source_location = {}
  for root, _, files in os.walk(source_dir):
    for file_name in files:
      abs_path = os.path.join(root, file_name)
      relpath = fast_relpath(abs_path, source_dir)
      destination_path = os.path.join(tar_root, relpath)
      tar_location_to_source_location[destination_path] = os.path.realpath(abs_path)
  return tar_location_to_source_location


def filter_tar_info(tarinfo):
  """Canonicalize all metadata"""
  tarinfo.uid = 0
  tarinfo.gid = 0
  tarinfo.uname = 'root'
  tarinfo.gname = 'root'
  tarinfo.mtime = 0
  return tarinfo


def symlink_tar_info(symlink_tar_location, symlink_target):
  """Create tar info for symlinks.

  For example:
  ```
  with TarFile('/tmp/test.tar', 'w') as tar:
    sym = symlink_tar_info('/data/app/my_app/foo.jar', '/data/deps/foo.jar')
    tar.addfile(sym)
  ```
  results in tar file like this:
  $ tar tvf /tmp/test.tar
  lrw-r--r--  0 root   root        0 Dec 31  1969 data/app/my_app/foo.jar -> /data/deps/foo.jar

  This doesn't protect against broken symlinks as it is intended to be used in the creation of symlinks where the target
  does not exist on disk at the time of tar creation.

  Leading / will be stripped from the `symlink_tar_location` because paths within tars are always relative to the root
  of the tarfile. However, `symlink_target` is not modified and should usually be an absolute path.
  """
  tarinfo = filter_tar_info(TarInfo(name=symlink_tar_location.lstrip('/')))
  tarinfo.type = SYMTYPE
  tarinfo.linkname = symlink_target
  return tarinfo


def create_stable_tar(tarfile_location, tar_location_to_source_location, symlinks=None):
  """Produces a stable tar from the contents of a directory and an optional map of symlink.

  The resulting tar will contain the lexicographically sorted contents of the source location, followed by the
  lexicographically sorted symlinks. The metainfo of the contents will be canonicalized:

  $ tar tvf /tmp/test.tar
  -rw-r--r--  0 root   root        0 Dec 31  1969 data/app/foo/bar.txt

  This keeps the digest of the layer consistent if the input is stable. When creating docker layers this prevents
  pushing layers to the registry more often than we need to. In the context of a docker container, this metadata is not
  useful. Permissions are preserved.
  """
  symlinks = symlinks or {}
  sorted_symlink_tuples = sorted(symlinks.items())
  tar_file = TarFile(tarfile_location, 'w')
  sorted_location_tuples = sorted(tar_location_to_source_location.items())
  with tar_file as tar:
    for destination_path, source_path in sorted_location_tuples:
      tar.add(name=source_path, arcname=destination_path, filter=filter_tar_info)
    for symlink_tar_location, symlink_target in sorted_symlink_tuples:
      sym = symlink_tar_info(symlink_tar_location, symlink_target)
      tar.addfile(sym)
  return tarfile_location


def create_stable_tar_from_directory(source_dir, tar_root, tarfile_location, symlinks=None):
  """Takes a directory and produces a stable tar.

  source_dir: The directory to make the tar from.
  tar_root: A path within the tar which will be prepended to the source paths relative to the `source_dir`.
  tarfile_location: The location to write the tarfile
  symlinks: a dictionary mapping the location of the symlink file within the tar to the location of the symlink target

  For example, if `/tmp/test` contains `foo/bar.txt`:
  ```
  create_stable_tar_from_directory(
    source_dir='/tmp/test/',
    tar_root='/data/app',
    tarfile_location='/tmp/test.tar',
    symlinks = {'/data/app/my_app/foo.jar': '/data/deps/foo.jar'},
  )
  ```

  results in a tarfile with the contents:
  $ tar tvf /tmp/test.tar
  -rw-r--r--  0 root   root        0 Dec 31  1969 data/app/foo/bar.txt
  lrw-r--r--  0 root   root        0 Dec 31  1969 data/app/my_app/foo.jar -> /data/deps/foo.jar
  """
  return create_stable_tar(
    tarfile_location=tarfile_location,
    tar_location_to_source_location=map_build_path_to_tar_path(source_dir, tar_root,),
    symlinks=symlinks,
  )
