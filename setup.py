# coding: utf-8
import io
import os
import sys

from setuptools import setup, find_packages

with io.open('VERSION', 'r') as fd:
    VERSION = fd.read().rstrip()

requires = (
    'nextgisweb',
    'exif==1.3.4'
)

entry_points = {
    'nextgisweb.packages': [
        'nextgisweb_panorama = nextgisweb_panorama:pkginfo',
    ],

    'nextgisweb.amd_packages': [
        'nextgisweb_panorama = nextgisweb_panorama:amd_packages',
    ],

}

setup(
    name='nextgisweb_panorama',
    version=VERSION,
    description="nextgisweb_panorama",
    long_description="",
    classifiers=[],
    keywords='',
    author='',
    author_email='',
    url='https://github.com/it-thematic/nextgisweb_panorama.git',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points=entry_points,
)
