from setuptools import *

setup(
    name='jslssa',
    version='1.5.3',
    description='Morris Water Maze Search Strategy Analysis',
    url='https://github.com/Norton50/JSL',
    author='Matthew Cooke',
    author_email='matthew.cooke@alumni.ubc.ca',
    license='GNU',
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Science/Research',

        'Natural Language :: English',

        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        'Topic :: Scientific/Engineering :: Information Analysis',

        'Programming Language :: Python :: 3.5',
    ],
    keywords='morris water maze jason snyder lab search strategy strategies analysis',
    packages=find_packages(),
    install_requires=[
        'xlrd',
        'plotly',
        'pillow',
        'matplotlib',
    ],
    entry_points={
       'gui_scripts': [
           'jslSearch = SearchStrategyAnalysis.__main__:main',
           'jslssa = SearchStrategyAnalysis.__main__:main',
       ],
    }
)
