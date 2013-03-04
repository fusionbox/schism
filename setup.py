from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='schism',
      version='0.1',
      description='Setup and configure webfaction sites with xmlrpc.',
      long_description=readme(),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
      ],
      keywords='webfaction xmlrpc configuration setup',
      url='https://github.com/davesque/schism',
      author='David Sanders',
      author_email='davesque@gmail.com',
      license='MIT',
      packages=['schism'],
      scripts=['bin/schism'],
      install_requires=[
          'pyyaml==3.10',
      ],
      zip_safe=False)
