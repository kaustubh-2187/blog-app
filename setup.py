from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="BlogAI",
    version="0.1",
    author="Kaustubh Kamble",
    packages=find_packages(),
    install_requires=requirements,
)