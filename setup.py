
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='nba-games-classifier', 
    version='0.1.0',

    description='Simple Python package allowing to determine which NBA games are worth to be seen.',
    long_description=long_description,

    author='Adam Wilk',
    author_email='adam.wilk@outlook.com',

    package_dir={'': 'src'},
    packages=find_packages(where='src'),

    python_requires='>=3.5',
    install_requires=['requests', 'python-dateutil', 'numpy', 'pandas'],

    project_urls={
        'Bug Reports': 'https://github.com/adam-w/nba-games-classifier/issues',
        'Source': 'https://github.com/adam-w/nba-games-classifier',
    },
)