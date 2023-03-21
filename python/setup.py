#!/usr/bin/env python

from pathlib import Path

from setuptools import find_packages, setup


def requires(filename):
    p = Path(__file__).parent / filename
    return [line for line in p.open("r").readlines() if not line.startswith("--") and not line.startswith("#")]


base_requires = requires("bril_utils/requirements.txt")

setup(
    name="bril_utils",
    version="0.1",
    description="bril go brr",
    author="Mateusz Bieganski",
    author_email="bieganski.m@wp.pl",
    packages=find_packages(),
    platforms=["Linux"],
    install_requires=base_requires,
    extras_require={},
)
