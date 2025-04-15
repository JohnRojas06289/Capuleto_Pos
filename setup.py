#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

# Leer la descripción larga desde README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Leer los requisitos desde requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="pos_system",
    version="1.0.0",
    author="Sistema POS",
    author_email="info@sistemapos.example.com",
    description="Sistema de punto de venta (POS) para negocios minoristas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ejemplo/pos_system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pos_system=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["resources/*", "config/*"],
    },
)