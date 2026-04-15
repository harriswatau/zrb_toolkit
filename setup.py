from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="zrb-toolkit",
    version="0.1.0",
    author="Harris Wang",
    author_email="harrisw@athabascau.ca",
    description="Zoned Role-Based framework for enterprise systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hongxueharriswang/zrb_toolkit",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "sqlalchemy>=2.0",
        "pydantic>=2.0",
        "click>=8.0",
        "cachetools>=5.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8",
    ],
    extras_require={
        "django": ["Django>=3.2"],
        "flask": ["Flask>=2.0"],
        "admin": ["flask", "flask-restx"],  # for admin API
    },
    entry_points={
        "console_scripts": [
            "zrb=zrb.cli.main:cli",
        ],
    },
)
