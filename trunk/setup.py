#!/usr/bin/env python

from distutils.core import setup
from distutils.command.install_data import install_data

from os.path import join

# make sure data files are installed in the package dir
class install_data_package(install_data):
    def finalize_options (self):
        self.set_undefined_options('install',
            ('install_lib', 'install_dir')
        )
        install_data.finalize_options(self)


setup(name="Infogreater",
      version="0.0.3",
      description="Infogreater is pseudo-mindmapping software",
      url="http://twistedmatrix.com/trac/infogreater",
      author="Christopher Armstrong",
      author_email="radix@twistedmatrix.com",
      packages=['infogreater',
                'infogreater.nodes',
                'infogreater.gtkgoodies'],
      scripts=['bin/infogreater'],
      cmdclass={'install_data': install_data_package,
                },
      data_files=[('infogreater', [join('infogreater', 'info.glade')])
                  ],
      )
