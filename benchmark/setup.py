import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="raft_benchmark",
    version="0.0.1",
    author="Zonglin Peng",
    description=("A dockerized framework to run raft and client"),
    python_requires=">=3.7,",
    packages=["."],
    install_requires=["docker==5.0.3", "matplotlib==3.5.1", "scipy", "regex", "black"],
    long_description=read("README.md"),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "raft_benchmark = benchmark.raft_benchmark:main",
            "plot = log.plot.plot:main",
        ]
    },
)
