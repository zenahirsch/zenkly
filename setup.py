from setuptools import setup, find_packages


setup(
    name='zenkly',
    version='0.1.5',
    packages=find_packages(),
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
        zenkly=zenkly.scripts.zenkly:cli
    ''',
)