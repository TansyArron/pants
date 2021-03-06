# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

target(
  name = 'tasks',
  dependencies = [
    ':benchmark_run',
    ':binary_create',
    ':bootstrap_jvm_tools',
    ':bundle_create',
    ':checkstyle',
    ':classpath_products',
    ':classpath_util',
    ':ivy_imports',
    ':ivy_resolve',
    ':ivy_utils',
    ':junit_run',
    ':jvm_platform_analysis',
    ':jvm_platform_analysis_integration',
    ':jvm_run',
    ':resources_task',
    ':prepare_resources',
    ':prepare_services',
    ':scalastyle',
    ':unpack_jars',
    'tests/python/pants_test/backend/jvm/tasks/jvm_compile',
  ]
)

python_tests(
  name = 'binary_create',
  sources = ['test_binary_create.py'],
  dependencies = [
    'src/python/pants/backend/core:plugin',
    'src/python/pants/backend/jvm:plugin',
    'src/python/pants/backend/jvm/tasks:binary_create',
    'tests/python/pants_test/jvm:jvm_tool_task_test_base',
  ]
)

python_tests(
  name = 'bootstrap_jvm_tools',
  sources = ['test_bootstrap_jvm_tools.py'],
  dependencies = [
    'src/python/pants/backend/core/tasks:task',
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/tasks:bootstrap_jvm_tools',
    'src/python/pants/backend/jvm/tasks:jvm_tool_task_mixin',
    'src/python/pants/java:executor',
    'src/python/pants/java/jar:shader',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test/jvm:jvm_tool_task_test_base',
  ]
)

python_tests(
  name = 'benchmark_run',
  sources = ['test_benchmark_run.py'],
  dependencies = [
    'src/python/pants/backend/jvm/tasks:benchmark_run',
    'src/python/pants/base:exceptions',
    'src/python/pants/base:target',
    'tests/python/pants_test/jvm:jvm_tool_task_test_base',
  ]
)

python_tests(
  name = 'bundle_create',
  sources = ['test_bundle_create.py'],
  dependencies = [
    'src/python/pants/backend/core:plugin',
    'src/python/pants/backend/jvm:plugin',
    'src/python/pants/backend/jvm/tasks:binary_create',
    'tests/python/pants_test/jvm:jvm_tool_task_test_base',
  ]
)

python_tests(
  name = 'checkstyle',
  sources = ['test_checkstyle.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:java',
    'src/python/pants/backend/jvm/tasks:checkstyle',
    'src/python/pants/base:address',
    'src/python/pants/base:build_file_aliases',
    'src/python/pants/base:exceptions',
    'tests/python/pants_test/jvm:nailgun_task_test_base',
    'tests/python/pants_test/tasks:task_test_base',
  ]
)

python_tests(
  name = 'checkstyle_integration',
  sources = ['test_checkstyle_integration.py'],
  dependencies = [
    'src/python/pants/util:contextutil',
    'tests/python/pants_test:int-test',
  ]
)

python_tests(
  name = 'classpath_products',
  sources = ['test_classpath_products.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/tasks:classpath_products',
    'src/python/pants/backend/jvm:artifact',
    'src/python/pants/backend/jvm:repository',
    'tests/python/pants_test:base_test',
  ]
)


python_tests(
  name = 'classpath_util',
  sources = ['test_classpath_util.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/base:exceptions',
    'src/python/pants/goal:products',
    'tests/python/pants_test:base_test',
  ]
)

python_tests(
  name = 'ivy_imports',
  sources = ['test_ivy_imports.py'],
  dependencies = [
    'src/python/pants/backend/core/targets:common',
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/tasks:ivy_imports',
    'src/python/pants/base:build_file_aliases',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test/jvm:nailgun_task_test_base',
  ]
)

python_tests(
  name = 'ivy_resolve',
  sources = ['test_ivy_resolve.py'],
  dependencies = [
    '3rdparty/python/twitter/commons:twitter.common.collections',
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/targets:scala',
    'src/python/pants/backend/jvm/tasks:ivy_resolve',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test/jvm:nailgun_task_test_base',
  ]
)

python_tests(
  name = 'ivy_utils',
  sources = ['test_ivy_utils.py'],
  dependencies = [
    '3rdparty/python:mock',
    'src/python/pants/backend/core:plugin',
    'src/python/pants/backend/jvm:plugin',
    'src/python/pants/backend/jvm:ivy_utils',
    'src/python/pants/ivy',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test:base_test',
    'tests/python/pants_test/base:context_utils',
  ]
)

python_tests(
  name = 'jvm_platform_analysis',
  sources = ['test_jvm_platform_analysis.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/tasks:jvm_platform_analysis',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test/tasks:task_test_base',
  ]
)

python_tests(
  name = 'jvm_platform_analysis_integration',
  sources = ['test_jvm_platform_analysis_integration.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/tasks:jvm_platform_analysis',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test:int-test',
  ]
)

python_tests(
  name = 'junit_run',
  sources = ['test_junit_run.py'],
  dependencies = [
    'src/python/pants/backend/core/targets:common',
    'src/python/pants/backend/jvm/targets:java',
    'src/python/pants/backend/jvm/tasks:junit_run',
    'src/python/pants/backend/python/tasks:python',
    'src/python/pants/base:build_file_aliases',
    'src/python/pants/base:exceptions',
    'src/python/pants/goal:products',
    'src/python/pants/ivy',
    'src/python/pants/java/distribution:distribution',
    'src/python/pants/java:executor',
    'tests/python/pants_test/jvm:jvm_tool_task_test_base',
    'tests/python/pants_test/subsystem:subsystem_utils',
  ]
)

python_tests(
  name = 'jvm_run',
  sources = ['test_jvm_run.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/tasks:jvm_run',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test/tasks:task_test_base',
  ]
)

python_tests(
  name = 'jvm_binary_integration',
  sources = ['test_jvm_binary_integration.py'],
  dependencies = [
    'src/python/pants/base:build_environment',
    'tests/python/pants_test:int-test',
  ],
)

python_tests(
  name = 'resources_task',
  sources = ['test_resources_task.py'],
  dependencies = [
    'src/python/pants/backend/jvm/tasks:resources_task',
    'src/python/pants/base:fingerprint_strategy',
    'src/python/pants/base:payload',
    'src/python/pants/base:payload_field',
    'src/python/pants/base:target',
    'src/python/pants/goal:products',
    'src/python/pants/util:dirutil',
    'tests/python/pants_test/tasks:task_test_base',
  ]
)

python_tests(
  name = 'prepare_resources',
  sources = ['test_prepare_resources.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:java',
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/targets:scala',
    'src/python/pants/backend/jvm/tasks:prepare_resources',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test/tasks:task_test_base',
  ]
)

python_tests(
  name = 'prepare_services',
  sources = ['test_prepare_services.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:java',
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/targets:scala',
    'src/python/pants/backend/jvm/tasks:prepare_services',
    'src/python/pants/util:contextutil',
    'tests/python/pants_test/tasks:task_test_base',
  ]
)

python_tests(
  name = 'scalastyle',
  sources = ['test_scalastyle.py'],
  dependencies = [
    'src/python/pants/backend/jvm/targets:java',
    'src/python/pants/backend/jvm/targets:scala',
    'src/python/pants/backend/jvm/tasks:scalastyle',
    'src/python/pants/base:address',
    'src/python/pants/base:build_file_aliases',
    'src/python/pants/base:exceptions',
    'tests/python/pants_test/jvm:nailgun_task_test_base',
    'tests/python/pants_test/tasks:task_test_base',
  ]
)

python_tests(
  name = 'scala_repl_integration',
  sources = ['test_scala_repl_integration.py'],
  dependencies = [
    'tests/python/pants_test:int-test',
  ],
)

python_tests(
  name = 'unpack_jars',
  sources = ['test_unpack_jars.py'],
  dependencies = [
    'src/python/pants/backend/core/targets:common',
    'src/python/pants/backend/jvm/targets:jvm',
    'src/python/pants/backend/jvm/tasks:unpack_jars',
    'src/python/pants/base:target',
    'tests/python/pants_test/tasks:task_test_base',
  ]
)
