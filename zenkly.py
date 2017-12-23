import os
import errno
import json
import configparser
import click
import requests


APP_NAME = 'zenkly'

def get(config, url):
    r = requests.get(url, auth=(config['email'], config['password']))
    res = r.json()

    if 'error' in res:
        raise click.UsageError(res['error'])

    return res


def put(config, url, data):
    r = requests.put(url, auth=(config['email'], config['password']), json=data)

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


def put_macros(config, data):
    entries = (
        'title', 'active', 'actions', 'restriction', 
        'description', 'attachments'
    )

    for m in data['macros']:
        url = 'https://%s.zendesk.com/api/v2/macros/%d.json' % (config['subdomain'], m['id'])
        macro = { 'macro': { k: m[k] for k in m if k in entries } }
        res = put(config, url, macro)
        click.echo(res)


@click.group()
@click.option('--profile', type=click.STRING, default='default')
@click.pass_context
def cli(ctx, profile):
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
        data = json.load(infile)
    
    res = put_macros(config=ctx.obj['configuration'], data=data)
    click.echo(res)