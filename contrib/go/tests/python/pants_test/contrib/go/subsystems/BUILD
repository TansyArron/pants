# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

target(
  name='subsystems',
  dependencies=[
    ':go_distribution',
  ]
)

python_tests(
  name='go_distribution',
  sources=['test_go_distribution.py'],
  dependencies=[
    'contrib/go/src/python/pants/contrib/go/subsystems:go_distribution',
    'tests/python/pants_test/subsystem:subsystem_utils',
  ]
)
