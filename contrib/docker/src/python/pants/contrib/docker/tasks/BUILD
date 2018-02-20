# coding=utf-8

python_library(
  name = 'docker_classpath_layer',
  sources = ['docker_classpath_layer.py', '__init__.py'],
  dependencies = [
    'pants/contrib/docker/products:layer_product',
    'pants/contrib/docker/targets:docker_layer',
    'pants/contrib/docker/util:tar',
    'src/python/fsqio/pants/ivy',
  ],
)

python_library(
  name = 'docker_service_image',
  sources = ['docker_service_image.py', '__init__.py'],
  dependencies = [
    '3rdparty/python:six',
    'pants/contrib/docker/products:docker_image_product',
    'pants/contrib/docker/products:layer_product',
    'pants/contrib/docker/targets:docker_service_app',
    'pants/contrib/docker/util:hashing',
    'pants/contrib/docker/util:tar',
  ],
)

python_library(
  name = 'docker_publish_image',
  sources = ['docker_publish_image.py', '__init__.py'],
  dependencies = [
    'pants/contrib/docker/products:docker_image_product',
    'pants/contrib/docker/products:layer_product',
    'pants/contrib/docker/util:docker-registry-client',
  ],
)

python_library(
  name = 'docker_local_publish',
  sources = ['docker_local_publish.py', '__init__.py'],
  dependencies = [
    'pants/contrib/docker/products:docker_image_product',
    'pants/contrib/docker/products:layer_product',
    'pants/contrib/docker/targets:docker_service_app',
  ],
)

python_library(
  name = 'docker_service_layer',
  sources = ['docker_service_layer.py', '__init__.py'],
  dependencies = [
    '3rdparty/python:twitter.common.collections',
    'pants/contrib/docker/products:layer_product',
    'pants/contrib/docker/targets:docker_layer',
    'pants/contrib/docker/util:tar',
  ],
)

python_library(
  name = 'docker_resolve_remote_image',
  sources = ['docker_resolve_remote_image.py', '__init__.py'],
  dependencies = [
    'pants/contrib/docker/products:layer_product',
    'pants/contrib/docker/targets:docker_remote_image',
    'pants/contrib/docker/util:docker-registry-client',
  ],
)
