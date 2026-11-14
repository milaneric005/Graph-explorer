from setuptools import setup, find_packages

setup(
    name="graph-viz-block",
    version="0.1",
    packages=find_packages(),
    install_requires=["graph-api", "jinja2"],
    entry_points={
        "graph.visualizer": ["block_viz=block_viz.plugin:BlockVisualizer"],
    },
    zip_safe=False,
)

