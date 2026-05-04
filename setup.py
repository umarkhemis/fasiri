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
    packages=find_packages(include=["fasiri", "fasiri.*"]),
    python_requires=">=3.9",
    install_requires=["httpx>=0.27.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Text Processing :: Linguistic",
    ],
)
