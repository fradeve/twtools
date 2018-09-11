from codecs import open
from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='twtools',
    version='0.1',
    description='A set of minimal tools to get info from TimeWarrior.',
    long_description=long_description,
    url='https://github.com/fradeve/timewarrior-tools',
    author='Francesco de Virgilio',
    author_email='fradeve@inventati.org',
    license='GNU GPL v3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Time Tracking',
        'License :: OSI Approved :: GPLv3',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='timewarrior tracking',
    install_requires=['pandas', 'Click==6.7', 'matplotlib', 'numpy'],
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    entry_points={
        'console_scripts': [
            'twcurrent=twtools.twparser:print_current_task',
            'twstop=twtools.twparser:stop_task',
            'twstart=twtools.twparser:start_task',
            'twstats=twtools.twstats:run',
        ],
    },
)
