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
with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setup(
    name="vot1",
    version=version,
    author="kabrony",
    author_email="info@kabrony.com",
    description="Enhanced Claude Integration System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kabrony/vot1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vot1-setup=vot1.cli.setup:main",
            "vot1-doctor=vot1.cli.doctor:main",
        ],
    },
    keywords="claude, anthropic, llm, ai, github, feedback",
    project_urls={
        "Bug Reports": "https://github.com/kabrony/vot1/issues",
        "Source": "https://github.com/kabrony/vot1",
        "Documentation": "https://github.com/kabrony/vot1/wiki",
    },
) 