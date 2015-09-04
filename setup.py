import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "btmitm",
    version = "0.1.0",
    author = "Conor Patrick",
    author_email = "conorpp94@gmail.com",
    description = ("A man-in-the-middle tool for doing active Bluetooth analysis. "),
    license = "BSD",
    keywords = "Bluetooth man-in-the-middle mitm btmitm",
    url = "",
    packages=['btmitm',],
    scripts=['scripts/btmitm', 'scripts/replace_bluetoothd', 'scripts/bluez_simple_agent_nouser'],
    long_description=read('README.md').replace('#',''),
    classifiers=[
        "Development Status :: 2 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
