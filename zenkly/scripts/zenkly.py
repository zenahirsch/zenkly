import os
import errno
import simplejson as json
import configparser
import click
import requests
import logging
import jsonschema
import time
import threading
from functools import wraps


APP_NAME = 'zenkly'

def rate_limited(max_per_second: int):
    """Rate-limits the decorated function locally, for one process."""
    lock = threading.Lock()
    min_interval = 1.0 / max_per_second

    def decorate(func):
        last_time_called = time.perf_counter()

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            lock.acquire()
            nonlocal last_time_called
            try:
                elapsed = time.perf_counter() - last_time_called
                left_to_wait = min_interval - elapsed
                if left_to_wait > 0:
                    time.sleep(left_to_wait)

                return func(*args, **kwargs)
            finally:
                last_time_called = time.perf_counter()
                lock.release()

        return rate_limited_function

    return decorate

@rate_limited(1)
def get(config, url):
    r = requests.get(
        url, 
        auth=(config['email'], config['password'])
    )

    try:
        res = r.json()
        if 'error' in res:
            raise click.UsageError(res['error'])
    except ValueError:
        res = r.text

    if 'error' in res:
        raise click.UsageError(res['error'])

    return res

@rate_limited(1)
def put(config, url, data):
    r = requests.put(
        url, 
        auth=(config['email'], config['password']),
        json=data
    )

    try:
        res = r.json()
        if 'error' in res:
            raise click.UsageError(res['error'])
    except ValueError:
        res = r.text

    return res


def get_all_macros(config):
    url = 'https://%s.zendesk.com/api/v2/macros.json' % config['subdomain']
    res = get(config, url)
    all = res['macros']

    with click.progressbar(length=res['count'], label='Getting macros...') as bar:
        bar.update(len(res['macros']))

        while (res['next_page']):
            res = get(config, res['next_page'])
            all = all + res['macros']
            bar.update(len(res['macros']))

    return all


def put_all_macros(config, data):
    entries = (
        'title', 'active', 'actions', 'restriction', 
        'description', 'attachments'
    )

    failed = []

    schemas_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'schemas'))

    with open(os.path.join(schemas_dir, 'macro.schema'), 'r') as schema_file:
        macro_schema = json.load(schema_file)

    with click.progressbar(length=len(data), label='Updating macros...') as bar:
        for m in data:
            macro = { 'macro': { k: m[k] for k in m if k in entries } }
            try:
                jsonschema.validate(macro, macro_schema)
            except jsonschema.exceptions.ValidationError as e:
                raise click.UsageError('Invalid macro format for update: %s' % e.message)

            url = 'https://%s.zendesk.com/api/v2/macros/%d.json' % (config['subdomain'], m['id'])

            try:
                put(config, url, macro)
            except click.UsageError as e:
                failed.append((m['id'], e.message))

            bar.update(1)
        
        click.secho('\n\nUpdate complete!')

        click.secho('\nThe following macros could not be updated: ', fg='red', bold=True)
        for f in failed:
            click.secho('%d (%s)' % (f[0], f[1]), fg='red')


@click.group()
@click.option('--profile', type=click.STRING, default='default')
@click.option('--debug', is_flag=True)
@click.pass_context
def cli(ctx, profile, debug):
    if debug:
        try:
            from http.client import HTTPConnection
        except ImportError:
            from httplib import HTTPConnection
        HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    if ctx.obj == None:
        ctx.obj = {}

    ctx.obj['profile'] = profile
    ctx.obj['configuration'] = {}

    conf_path = os.path.join(click.get_app_dir(APP_NAME), 'config.ini')
    config = configparser.ConfigParser()
    config.read([conf_path])

    if (profile in config):
        for key in config[profile]:
            ctx.obj['configuration'][key] = config[profile][key]


@cli.command()
@click.option('--subdomain', type=click.STRING, prompt=True)
@click.option('--email', type=click.STRING, prompt=True)
@click.option('--password', type=click.STRING, prompt=True, hide_input=True)
@click.pass_context
def configure(ctx, subdomain, email, password):
    """Configure Zendesk authentication."""
    profile = ctx.obj['profile']

    conf_path = os.path.join(click.get_app_dir(APP_NAME), 'config.ini')
    config = configparser.ConfigParser()
    config.read([conf_path])

    try:
        config.add_section(profile)
    except configparser.DuplicateSectionError:
        click.confirm('That profile already exists. Overwrite?', abort=True)

    config.set(profile, 'Subdomain', subdomain)
    config.set(profile, 'Email', email)
    config.set(profile, 'Password', password)

    try:
        os.makedirs(click.get_app_dir(APP_NAME))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    with open(conf_path, 'w') as configfile:
        config.write(configfile)


@cli.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True), default='.')
@click.option('--filename', type=click.STRING, default='macros.json')
@click.pass_context
def get_macros(ctx, directory, filename):
    """Get all macros and save to file."""
    if (ctx.obj['configuration'] == {}):
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    macros = get_all_macros(config=ctx.obj['configuration'])
    path = '%s/%s' % (directory, filename)
    
    with open(path, 'w') as outfile:
        json.dump({ "macros": macros }, outfile, indent=2)

    click.echo('Macros saved to %s' % path)


@cli.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True), default='.', prompt=True)
@click.option('--filename', type=click.STRING, default='macros_edited.json', prompt=True)
@click.pass_context
def update_macros(ctx, directory, filename):
    """Update all macros from file."""
    if (ctx.obj['configuration'] == {}):
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    path = '%s/%s' % (directory, filename)

    if not os.path.exists(path):
        raise click.FileError(path, hint='File does not exist')

    with open(path, 'r') as infile:
        try:
            data = json.load(infile)
        except ValueError as e:
            raise click.UsageError('There was a problem loading %s: %s' % (path, e))
    
    if not 'macros' in data:
        raise click.UsageError('Missing `macros` key in %s' % path)

    if not type(data['macros']) is list:
        raise click.UsageError('Key `macros` in %s must be a list' % path)
    
    put_all_macros(config=ctx.obj['configuration'], data=data['macros'])