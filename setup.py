from setuptools import setup, find_packages


setup(
    name='zenkly',
    version='0.1.12',
    packages=find_packages(),
    description='CLI for Zendesk admin tasks',
    author='Zena Hirsch',
    author_email='hirsch.zena@gmail.com',
    url='https://github.com/zenahirsch/zenkly',
    include_package_data=True,
    package_data={'zenkly': ['schemas/*.schema']},
    install_requires=[
        'Click',
        'simplejson',
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