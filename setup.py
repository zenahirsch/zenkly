from setuptools import setup


setup(
    name='zenkly',
    version='0.1',
    py_modules=['zenkly'],
    install_requires=[
        'Click',
        'requests',
    ],
    entry_points='''
        [console_scripts]
        zenkly=zenkly:cli
    ''',
)