# Copyright 2020 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_library(
  dependencies=[
    '3rdparty/python:dataclasses',
    'src/python/pants/engine/legacy:structs',
    'src/python/pants/engine:rules',
    'src/python/pants/rules/core',
  ],
  tags = {"partially_type_checked"},
)

python_tests(
  name='tests',
  sources=globs('*_test.py', exclude=[globs('*_integration_test.py')]),
  dependencies=[
    ':test_runner',
  ]
)
