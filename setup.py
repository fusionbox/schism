from setuptools import setup

VERSION = '0.2'


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='schism',
      version=VERSION,
      description='Setup and configure webfaction sites over xmlrpc.',
      long_description=readme(),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
      ],
      keywords='webfaction api xmlrpc automatic configuration setup',
      url='https://github.com/davesque/schism',
      author='David Sanders',
      author_email='davesque@gmail.com',
      license='MIT',
      packages=['schism'],
      scripts=['bin/schism'],
      install_requires=[
          'pyyaml==3.10',
      ],
      test_suite='nose.collector',
      setup_requires=[
          'nose==1.2.1',
          'mock==1.0.1',
      ],
      zip_safe=False)
