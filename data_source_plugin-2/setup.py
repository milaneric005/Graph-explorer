from setuptools import setup, find_packages

setup(
    name="graph-source-two",
    version="0.1",
    packages=find_packages(),
    install_requires=["graph-api"],
    entry_points={
        "graph.data_source": ["source_two=source_two.plugin:SourceTwo"],
    },
    zip_safe=False,
)

