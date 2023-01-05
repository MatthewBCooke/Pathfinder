from setuptools import *

with open('README.md', encoding="utf8") as f:
    long_description = f.read()

setup(
    name='jsl-pathfinder',
    version='1.4.4',
    description='Morris Water Maze Search Strategy Analysis',
    url='https://github.com/MatthewBCooke/Pathfinder',
    author='Matthew Cooke',
    author_email='matthew.cooke@ubc.ca',
    license='GNU',
    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Science/Research',

        'Natural Language :: English',

        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        'Topic :: Scientific/Engineering :: Information Analysis',

        'Programming Language :: Python :: 3.5',
    ],
    keywords='morris water maze jason snyder lab search strategy strategies analysis',
    packages=find_packages(),
    install_requires=[
        'xlrd == 1.2.0',
        'plotly',
        'pillow',
        'matplotlib',
        'scipy',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    entry_points={
       'gui_scripts': [
           'pathfinder = SearchStrategyAnalysis.Pathfinder:main',
       ],
    }
)
