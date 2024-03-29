import os

from setuptools import setup

ref = os.getenv('GITHUB_REF', '')
if ref.startswith('refs/tags/'):
    version = ref.replace('refs/tags/', '')
else:
    version = '0.0'


def read(fname: str) -> str:
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ndef',
    version=version,
    description='NDEF (NFC Data Exchange Format) parser and verifier',
    long_description=read('README.rst'),
    author='Amir Szekely',
    author_email='kichik+pyndef@gmail.com',
    url='http://github.com/kichik/pyndef',
    license='zlib/libpng',
    package_data={'ndef': ['py.typed']},
    packages=['ndef'],
    test_suite='tests',
    zip_safe=True,
    install_requires=['six'],
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: zlib/libpng License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
