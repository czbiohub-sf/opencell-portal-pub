#!/usr/bin/env python

import setuptools

setuptools.setup(
    name='opencell',
    author='Keith Cheveralls',
    description='Opencell processing tools and backend',
    url='https://github.com/czbiohub/opencell',
    packages=setuptools.find_packages(),
    python_requires='>3.7',
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'ocdb = opencell.cli.database:main',
            'ocmd = opencell.cli.metadata:main',
            'ocmi = opencell.cli.microscopy:main',
            'ocms = opencell.cli.mass_spec:main',
            'ocapi = opencell.api.app:main',
        ]
    },
    extras_require={
        "dev": [
            "alembic==1.4.3",
            "black==19.10b0",
            "flake8==3.7.9",
            "pre-commit==2.0.1",
            "pytest==5.3.4",
            "dragonfly_automation @ git+ssh://git@github.com/czbiohub/dragonfly-automation.git",
        ],
        "facs": ["FlowCytometryTools"],
    },
)
