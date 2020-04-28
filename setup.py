"""setup.py file for dyb-toymc package."""

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "VERSION")) as f:
    version = f.read()

setup(
    name="dyb-toymc",
    version=version,
    description="Sam Kohn's Daya Bay Toy Monte Carlo",
    url="https://github.com/samkohn/dyb-toymc",
    author="Sam Kohn",
    author_email="skohn@lbl.gov",
    packages=find_packages(),
    install_requires=["numpy >= 1.18"],
)
