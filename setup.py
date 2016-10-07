#!/usr/bin/env python
try:
    from setuptools import setup
    args = {}
except ImportError:
    from distutils.core import setup
    print("""\
*** WARNING: setuptools is not found.  Using distutils...
""")

from setuptools import setup
try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

from os import path
setup(name='acorn',
      version='0.0.12',
      description='Automated computational research notebook.',
      long_description= "" if not path.isfile("README.md") else read_md('README.md'),
      author='Conrad W Rosenbrock',
      author_email='rosenbrockc@gmail.com',
      url='https://github.com/rosenbrockc/acorn',
      license='MIT',
      setup_requires=['pytest-runner',],
      tests_require=['pytest', 'numpy', 'scipy', 'sklearn', 'pandas'],
      install_requires=[
          "argparse",
          "pyparsing",
          "termcolor",
          "six"
      ],
      packages=['acorn', 'acorn.logging', 'acorn.subclass', 'acorn.analyze',
                'acorn.scipy', 'acorn.sklearn', 'acorn.matplotlib'],
      scripts=['acorn/acrn.py'],
      package_data={'acorn': ['config/*.cfg', 'config/*.json']},
      include_package_data=True,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: MacOS',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Topic :: Scientific/Engineering',
      ],
     )
