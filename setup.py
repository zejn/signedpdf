from setuptools import setup, find_packages

setup(name='signedpdf',
      version='0.1',
      description='Digitally sign PDF documents.',
      author='Gasper Zejn',
      author_email='zejn+signedpdf@owca.info',
      url='http://github.com/zejn/signedpdf',
      packages=find_packages(),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Topic :: Office/Business',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'License :: OSI Approved :: BSD License'
        ]
     )
