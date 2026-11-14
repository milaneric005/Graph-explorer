from setuptools import setup, find_packages

setup(
    name="graph-source-one",
    version="0.1",
    packages=find_packages(),
    install_requires=["graph-api"],
    entry_points={
        "graph.data_source": ["source_one=source_one.plugin:SourceOne"],
    },
    zip_safe=False,
)

