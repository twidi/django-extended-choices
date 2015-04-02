from os.path import abspath, dirname, join
from setuptools import setup, find_packages

from extended_choices import __version__


def read_relative_file(filename):
    """Returns contents of the given file, which path is supposed relative
    to this module."""
    with open(join(dirname(abspath(__file__)), filename)) as f:
        return f.read()


setup(
    name="django-extended-choices",
    version=__version__,
    license="GPL",
    description="Little helper application to improve django choices"
    "(for fields)",
    long_description=read_relative_file('README.rst'),
    url="https://github.com/twidi/django-extended-choices",
    author='Stephane "Twidi" Angel',
    author_email="s.angel@twidi.com",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7"
    ]
)
