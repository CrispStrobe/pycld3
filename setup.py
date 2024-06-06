#!/usr/bin/env python

import os
import platform
import shutil
import subprocess
from distutils.command.build import build
from os import makedirs, path

from setuptools import Extension, setup
from Cython.Build import cythonize

use_cython_val = os.environ.get("USE_CYTHON")
USE_CYTHON = use_cython_val is not None and use_cython_val not in ("0", "false", "False")

HERE = path.abspath(path.dirname(__file__))

# Resolve dynamic paths
brew_prefix = subprocess.check_output(['brew', '--prefix']).decode().strip()
protobuf_include = subprocess.check_output(['brew', '--prefix', 'protobuf']).decode().strip() + '/include'
abseil_include = subprocess.check_output(['brew', '--prefix', 'abseil']).decode().strip() + '/include'
protobuf_lib = subprocess.check_output(['brew', '--prefix', 'protobuf']).decode().strip() + '/lib'

# List of source filenames, relative to the distribution root
SOURCES = [
    "src/base.cc",
    "src/cld_3/protos/feature_extractor.pb.cc",
    "src/cld_3/protos/sentence.pb.cc",
    "src/cld_3/protos/task_spec.pb.cc",
    "src/embedding_feature_extractor.cc",
    "src/embedding_network.cc",
    "src/feature_extractor.cc",
    "src/feature_types.cc",
    "src/fml_parser.cc",
    "src/lang_id_nn_params.cc",
    "src/language_identifier_features.cc",
    "src/nnet_language_identifier.cc",
    "src/registry.cc",
    "src/relevant_script_feature.cc",
    "src/script_span/fixunicodevalue.cc",
    "src/script_span/generated_entities.cc",
    "src/script_span/generated_ulscript.cc",
    "src/script_span/getonescriptspan.cc",
    "src/script_span/offsetmap.cc",
    "src/script_span/text_processing.cc",
    "src/script_span/utf8statetable.cc",
    "src/sentence_features.cc",
    "src/task_context.cc",
    "src/task_context_params.cc",
    "src/unicodetext.cc",
    "src/utils.cc",
    "src/workspace.cc",
]

if USE_CYTHON:
    SOURCES.insert(0, "cld3/pycld3.pyx")
else:
    SOURCES.insert(0, "cld3/pycld3.cpp")

# List of directories to search for C/C++ header files
INCLUDES = [
    "/usr/local/include/",
    path.join(HERE, "src/"),
    path.join(HERE, "src/cld_3/protos/"),
    f"{brew_prefix}/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/include/python3.11/",
    path.join(HERE, "src"),
    protobuf_include,  # Protobuf include directory
    abseil_include,    # Abseil include directory
]

# List of library names to link against
LIBRARIES = ["protobuf"]

# List of directories to search for libraries
LIBRARY_DIRS = [
    protobuf_lib,
]

# Describe extension modules
kwargs = dict(
    sources=SOURCES,
    include_dirs=INCLUDES,
    libraries=LIBRARIES,
    library_dirs=LIBRARY_DIRS,
    language="c++",
)
plat = platform.system()
if plat == "Darwin":
    kwargs["extra_compile_args"] = ["-std=c++17", "-stdlib=libc++"]
    kwargs["extra_link_args"] = ["-stdlib=libc++"]
elif plat != "Windows":
    kwargs["extra_compile_args"] = ["-std=c++17"]

ext = [
    Extension("cld3._cld3", **kwargs)
]

# .proto files define protocol buffer message formats
PROTOS = ["sentence.proto", "feature_extractor.proto", "task_spec.proto"]

class BuildProtobuf(build):
    """Compile protocol buffers via `protoc` compiler."""

    def run(self):
        if shutil.which("protoc") is None:
            raise RuntimeError(
                "The Protobuf compiler, `protoc`, which is required for"
                " building this package, could not be found.\n"
                "See https://github.com/protocolbuffers/protobuf for"
                " information on installing Protobuf."
            )
        protobuf_dir = path.join(HERE, "src/cld_3/protos/")
        if not path.exists(protobuf_dir):
            print("Creating dirs at \033[1m{}\033[0;0m".format(protobuf_dir))
            makedirs(protobuf_dir)
        command = ["protoc"]
        command.extend(PROTOS)
        command.append("--cpp_out={}".format(path.join(HERE, "src/cld_3/protos/")))
        print("Running \033[1m{}\033[0;0m".format(" ".join(command)))
        subprocess.run(command, check=True, cwd=path.join(HERE, "src/"))
        build.run(self)

CLASSIFIERS = [
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: C++",
    "Development Status :: 3 - Alpha",
    "Topic :: Text Processing :: Linguistic",
    "Intended Audience :: Developers",
]

def find_version(filepath):
    version = None
    with open(filepath) as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.partition("=")[-1].strip().strip("'\"")
    if not version:
        raise RuntimeError("Could not find version in __init__.py")
    return version

if __name__ == "__main__":
    if USE_CYTHON:
        extensions = cythonize(ext, compiler_directives={'language_level': "3"})
    else:
        extensions = ext
    setup(
        name="pycld3",
        version=find_version("cld3/__init__.py"),
        cmdclass={"build": BuildProtobuf},
        author="Brad Solomon",
        author_email="bsolomon@protonmail.com",
        description="CLD3 Python bindings",
        long_description=open(path.join(HERE, "README.md"), encoding="utf-8").read(),
        long_description_content_type="text/markdown",
        license="Apache 2.0",
        keywords=["cld3", "cffi", "language", "langdetect", "cld", "nlp"],
        url="https://github.com/bsolomon1124/pycld3",
        ext_modules=extensions,
        python_requires=">2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*",
        classifiers=CLASSIFIERS,
        zip_safe=False,
        packages=["cld3"],
    )
