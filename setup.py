"""
Setuptools based setup module
"""
from setuptools import setup, find_packages


setup(
    name='coscine_gui',
    version='0.1.0',
    description='Small tkinter based GUI for the coscine pip package.',

    author='Niklas Siemer',
    author_email='siemer@mpie.de',
    license='BSD',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],

    keywords='coscine_gui',
    packages=find_packages(exclude=["*tests*"]),
    install_requires=[        
        'coscine',
    ],
)
