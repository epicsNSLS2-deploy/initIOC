from setuptools import setup


setup(
    name='initADIOC',
    version='0.1.0',
    author='Jakub Wlodek',
    author_email='jwlodek@bnl.gov',
    desription='A python utility for initializing new areaDetector IOCs from binary bundles.',
    license='BSD 3-Clause',
    keywords='areaDetector cli ioc epics',
    py_modules=['initIOCs'],
    entry_points={
        'console_scripts' : [
            'initADIOC = initIOCs:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)