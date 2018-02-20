# coding=utf-8

python_library(
  name = 'image_product',
  sources = ['image_product.py', '__init__.py'],
  dependencies = [
    ':layer_product',
    'pants/contrib/docker/util:hashing',
  ],
)

python_library(
  name = 'layer_product',
  sources = ['layer_product.py', '__init__.py'],
  dependencies = [
    'pants/contrib/docker/util:hashing',
  ],
)
