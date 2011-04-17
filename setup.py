from os import path
from setuptools import setup, find_packages

from extended_choices import VERSION

with open(path.join(path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

setup(
    name="django-extended-choices",
    version=".".join(map(str, VERSION)),
    license="GPL",
    description="Little helper application to improve django choices (for fields)",
    long_description=readme,
    url="https://github.com/twidi/django-extended-choices",
    author="Stephane Angel",
    author_email="s.angel@twidi.com",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
       "Development Status :: 3 - Alpha",
       "Operating System :: OS Independent",
       "License :: OSI Approved :: GNU General Public License (GPL)",
       "Intended Audience :: Developers",
       "Programming Language :: Python :: 2.5",
       "Programming Language :: Python :: 2.6",
       "Programming Language :: Python :: 2.7"
    ]
)
