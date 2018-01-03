from setuptools import setup


setup(
    name='zenkly',
    version='0.1.1',
    py_modules=['zenkly'],
    description='CLI for Zendesk admin tasks',
    author='Zena Hirsch',
    author_email='hirsch.zena@gmail.com',
    url='https://github.com/zenahirsch/zenkly',
    install_requires=[
        'Click',
        'requests',
        'jsonschema',
        'colorama',
        'configparser',
    ],
    entry_points='''
        [console_scripts]
        zenkly=zenkly:cli
    ''',
)