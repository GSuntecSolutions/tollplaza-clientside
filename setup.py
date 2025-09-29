# /root/NextjsApps/firstbackend/setup.py
from setuptools import setup, find_packages

setup(
    name="firstbackend",
    version="0.1.0",
    description="Backend for AI toll system",
    packages=find_packages(),
    install_requires=[
        "pymongo",
        "celery",
        "redis",
        "python-dotenv"
    ],
)