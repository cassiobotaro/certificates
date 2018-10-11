from setuptools import setup

setup(name='cetificates',
      version='0.0.2',
      license='Apache License 2.0',
      packages=['certificates'],
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'certificates = certificates.cli:main',
          ]
      }
)
