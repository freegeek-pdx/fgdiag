#!/usr/bin/env python

"""Install script for Free Geek Diagnostics

FIXME: docs are included in the tarball, but not installed anywhere.
 (Maybe this is okay. Package maintainers can install the docs?)
"""

# Should these lists be auto-generated?
packages = [
    "fgdiag",
    "fgdiag.lib",
    "fgdiag.disk",
    "fgdiag.keyboard",
    "fgdiag.modem",
    ]

scripts = [
    "diag-disk",
    "diag-modem",
    "diag-cd"
    ]

scripts = ["bin/" + i for i in scripts]

import fgdiag

from distutils.core import setup
setup(name="fgdiag",
      version=fgdiag.__version__,
      author="Free Geek",
      author_email="coders@lists.freegeek.org",
      maintainer="Kevin Turner",
      maintainer_email="kevin@freegeek.org",
      url="http://www.freegeek.org/?FIXME",
      description="Free Geek Hardware Diagnostics",
#      long_description="FIXME",
# As long as we're deploying with Python 2.2 distutils, we can't include
# classifiers.
#       classifiers=[
#     "Development Status :: 3 - Alpha",
#     "Environment :: Console",
#     "Intended Audience :: Information Technology",
#     "License :: OSI Approved :: GNU General Public License (GPL)",
#     "Operating System :: POSIX :: Linux",
#     "Programming Language :: Python",
#     "Topic :: System :: Hardware",
#     ],
      packages=packages,
      scripts=scripts,
      )
