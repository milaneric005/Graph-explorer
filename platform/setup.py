from setuptools import setup, find_packages

setup(
    name="graph-platform",
    version="0.1",
    packages=find_packages(),
    install_requires=["graph-api"],
    zip_safe=False,
)

