from setuptools import setup, find_packages

setup(
    name="graph-viz-simple",
    version="0.1",
    packages=find_packages(),
    install_requires=["graph-api", "jinja2"],
    entry_points={
        "graph.visualizer": ["simple_viz=simple_viz.plugin:SimpleVisualizer"],
    },
    zip_safe=False,
)

