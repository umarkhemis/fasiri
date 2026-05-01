"""
Fasiri Python SDK – setup.py

Install locally:   pip install -e sdk/
Publish to PyPI:   python -m build && twine upload dist/*
"""
from setuptools import setup, find_packages

setup(
    name="fasiri",
    version="1.0.0",
    description="Official Python SDK for the Fasiri African language translation API",
    long_description=open("sdk/README_SDK.md").read(),
    long_description_content_type="text/markdown",
    author="Beta-Tech Labs",
    url="https://github.com/umarkhemis/fasiri",
    license="MIT",
    package_dir={"": "sdk"},
    packages=find_packages(where="sdk"),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.27.0",
    ],
    extras_require={
        "async": ["httpx>=0.27.0"],
        "dev": ["pytest>=8.0", "pytest-asyncio>=0.23", "respx>=0.21"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="african languages translation nlp swahili yoruba luganda sunbird khaya fasiri",
)
