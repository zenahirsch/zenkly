from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='zenkly',
    version='0.1.24',
    packages=find_packages(),
    description='CLI for Zendesk admin tasks',
    long_description=long_description,
    long_description_content_type="text/markdown",
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
        'gitpython',
        'tabulate',
    ],
    entry_points='''
        [console_scripts]
        zenkly=zenkly.scripts.zenkly:cli
    ''',
    python_requires='>=3.6',
)