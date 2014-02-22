import os

from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ndef',
    version='0.1',
    description='NDEF (NFC Data Exchange Format) parser and verifier',
    long_description=read('README.rst'),
    author='Amir Szekely',
    author_email='kichik+pyndef@gmail.com',
    url='http://github.com/kichik/pyndef',
    license='zlib/libpng',
    packages=['ndef'],
    test_suite='tests',
    zip_safe=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: zlib/libpng License",
        "Programming Language :: Python :: 2.7",
    ],
)