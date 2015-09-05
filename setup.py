import os,sys
from distutils.core import setup, Extension

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

mods = list()

mods.append(Extension('clone',
    include_dirs=["/usr/include/python"+sys.version],
    libraries=['bluetooth'],
    extra_compile_args=['-O3'],
    sources=['lib/' + x for x in ['bdaddr.c', 'oui.c', 'btmitm_clone.c']]))


mods.append(Extension('blocksdp',
    include_dirs=[],
    libraries=[],
    extra_compile_args=[],
    sources=['lib/' + x for x in ['blocksdp.c']]))


setup(
    name = "libbtproxy",
    version = "0.1",
    author = "Conor Patrick",
    author_email = "conorpp94@gmail.com",
    description = ("A man-in-the-middle tool for doing active Bluetooth analysis. "),
    license = "BSD",
    keywords = "Bluetooth man-in-the-middle mitm btmitm proxy libbtproxy",
    ext_modules=mods,
    url = "https://github.com/conorpp/btproxy",
    packages=['libbtproxy',],
    scripts=['scripts/btproxy', 'scripts/replace_bluetoothd', 'scripts/bluez_simple_agent_nouser'],
    long_description=read('README.md').replace('#',''),
    install_requires=['pybluez>=0.21'],
    classifiers=[
        "Development Status :: 2 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
