#!/usr/bin/env python3
"""
Setup file for VOT1 package.
"""

from setuptools import setup, find_packages
import os
import re

# Read the version from __init__.py
with open(os.path.join("src", "vot1", "__init__.py"), "r") as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

# Parse development requirements
dev_requirements = [
    'pytest>=7.0.0',
    'pytest-cov>=3.0.0',
    'black>=22.3.0',
    'isort>=5.10.1',
    'mypy>=0.950',
    'flake8>=4.0.1',
]

setup(
    name="vot1",
    version=version,  # Use the version from __init__.py
    author="Village Of Thousands",
    author_email="contact@villageofthousands.io",
    description="Advanced self-improving system with memory management, OWL reasoning, and visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/villageofthousands/vot1",
    project_urls={
        "Bug Tracker": "https://github.com/villageofthousands/vot1/issues",
        "Documentation": "https://villageofthousands.io/docs",
        "Source Code": "https://github.com/villageofthousands/vot1",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
        'test': ['pytest>=7.0.0', 'pytest-cov>=3.0.0'],
        'docs': ['sphinx>=5.0.0', 'sphinx-rtd-theme>=1.0.0'],
    },
    entry_points={
        "console_scripts": [
            "vot1-dashboard=vot1.dashboard.server:main",
            "vot1-memory=vot1.memory.cli:main",
            "vot1-improve=vot1.self_improvement.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
