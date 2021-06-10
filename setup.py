from setuptools import setup


# read the contents of README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='hyperspace',
    version='0.0.0.1',
    author='MakUrSpace, LLC',
    author_email='hello@makurspace.com',
    description='Summon, Traverse and Create all the Spaces!',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/makurspace/hyperspace',
    install_requires=[],
    packages=["hyperspace"],
    pakcage_date={'hyperspace': ['html_templates/*.html', 'javascript_templates/*.js']},
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
