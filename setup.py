#!/usr/bin/env python
import pathlib

import setuptools

package_name = "tloen"


def read_version():
    root_path = pathlib.Path(__file__).parent
    version_path = root_path / package_name / "_version.py"
    with version_path.open() as file_pointer:
        file_contents = file_pointer.read()
    local_dict = {}
    exec(file_contents, None, local_dict)
    return local_dict["__version__"]


version = read_version()

install_requires = [
    "aiohttp",
    "Cython >= 0.29.0",
    "prompt-toolkit >= 3.0.0",
    "pymonome >= 0.9.0",
    "python-rtmidi",
    "sly",
    "supriya",
    "urwid >= 2.1.0",
]

extras_require = {
    "test": [
        "black == 19.10b0",  # Trailing comma behavior in 20.x needs work
        "flake8 >= 3.9.0",
        "isort >= 5.8.0",
        "mypy >= 0.800",
        "pytest >= 6.2.0",
        "pytest-asyncio >= 0.14.0",
        "pytest-cov >= 2.11.0",
        "pytest-helpers-namespace >= 2019.1.8",
        "pytest-mock >= 3.5.0",
        "pytest-rerunfailures >= 9.1.0",
        "pytest-timeout >= 1.4.0",
    ],
}

with open("README.md", "r") as file_pointer:
    long_description = file_pointer.read()

classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: MacOS",
    "Operating System :: POSIX",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Artistic Software",
    "Topic :: Multimedia :: Sound/Audio :: Sound Synthesis",
]

keywords = [
    "audio",
    "dsp",
    "music composition",
    "scsynth",
    "supercollider",
    "synthesis",
]


if __name__ == "__main__":
    setuptools.setup(
        author="Josiah Wolf Oberholtzer",
        author_email="josiah.oberholtzer@gmail.com",
        classifiers=classifiers,
        description="Supriya's DAW",
        extras_require=extras_require,
        include_package_data=True,
        install_requires=install_requires,
        keywords=keywords,
        license="MIT",
        long_description=long_description,
        name=package_name,
        packages=[package_name],
        url=f"https://github.com/josiah-wolf-oberholtzer/{package_name}",
        version=version,
        zip_safe=False,
    )
