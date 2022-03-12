from setuptools import setup
from Cython.Build import cythonize

setup(
    name='World Test',
    ext_modules=cythonize("worlds.pyx"),
    zip_safe=False,
)

