# setup.py

from setuptools import setup, find_packages

setup(
    name="pyparser",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "pyparser=pyparser.cli:run"
        ]
    },
    description="CLI tool for parsing Python files into structured JSON (classes, functions, imports, variables)",
    author="Your Name",
    license="MIT"
)
