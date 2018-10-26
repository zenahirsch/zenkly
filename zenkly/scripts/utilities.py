import os
import errno
import json
import click
import requests
import time
import shutil
import threading
from functools import wraps
import git
from .constants import VALID_HC_TYPES


def rate_limited(max_per_second: int):
    """
    Rate-limits the decorated function locally, for one process.
    :param max_per_second: the number of requests allowed per second
    :return: the decorated function
    """
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
    """
    GET the provided endpoint.
    :param config: context config
    :param url: the url to GET
    :return:
    """
    r = requests.get(
        url,
        auth=(config['email'], config['password'])
    )

    # Check for HTTP errors (4xx, 5xx).
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise click.ClickException(err)

    # Attempt to parse JSON. If valid JSON contains an error, raise it.
    # If JSON is invalid, raise the error.
    try:
        res = r.json()
        if 'error' in res:
            raise click.ClickException(res['error'])
    except ValueError as err:
        raise click.ClickException(err)

    return res


@rate_limited(1)
def put(config, url, data):
    """
    PUT data to the provided endpoint.
    :param config: context config
    :param url: the url to PUT data to
    :param data: the data to PUT
    :return:
    """
    r = requests.put(
        url,
        auth=(config['email'], config['password']),
        json=data
    )

    # Check for HTTP errors (4xx, 5xx).
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise click.ClickException(err)

    # Attempt to parse JSON. If valid JSON contains an error, raise it.
    # If JSON is invalid, raise the error.
    try:
        res = r.json()
        if 'error' in res:
            raise click.ClickException(res['error'])
    except ValueError as err:
        raise click.ClickException(err)

    return res


@rate_limited(1)
def post(config, url, data):
    """
    POST data to the provided endpoint.
    :param config: context config
    :param url: the url to POST the data to
    :param data: the data to POST
    :return:
    """
    r = requests.post(
        url,
        auth=(config['email'], config['password']),
        json=data
    )

    # Check for HTTP errors (4xx, 5xx).
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise click.ClickException(err)

    # Attempt to parse JSON. If valid JSON contains an error, raise it.
    # If JSON is invalid, raise the error.
    try:
        res = r.json()
        if 'error' in res:
            raise click.ClickException(res['error'])
    except ValueError as err:
        raise click.ClickException(err)

    return res


def get_all_macros(config):
    """
    Get all pages of macros from Zendesk.
    :param config: context config
    :return: list of macro objects
    """
    url = 'https://%s.zendesk.com/api/v2/macros.json' % config['subdomain']
    res = get(config, url)
    all = res['macros']

    with click.progressbar(length=res['count'], label='Getting macros...') as bar:
        bar.update(len(res['macros']))

        while res['next_page']:
            res = get(config, res['next_page'])
            all = all + res['macros']
            bar.update(len(res['macros']))

    return all


def post_all_macros(config, data):
    """
    Create macros in Zendesk.
    :param config: context config
    :param data: the macro data to POST
    """
    entries = (
        'title', 'active', 'actions', 'restriction',
        'description', 'attachments'
    )

    succeeded = []
    failed = []

    with click.progressbar(length=len(data), label='Adding macros...') as bar:
        for m in data:
            macro = {'macro': {k: m[k] for k in m if k in entries}}

            url = 'https://%s.zendesk.com/api/v2/macros.json' % config['subdomain']

            try:
                res = post(config, url, macro)
                succeeded.append((m['id'], res['macro']['id']))
            except click.ClickException as err:
                failed.append((m['id'], err.message))  # Record failures

            bar.update(1)

        click.secho('\n\nAddition complete!')

        if succeeded:
            click.secho('\nThe following macros were added: ', fg='green', bold=True)
            for s in succeeded:
                click.secho('%d (new id: %d)' % (s[0], s[1]), fg='green')

        if failed:
            click.secho('\nThe following macros could not be added: ', fg='red', bold=True)
            for f in failed:
                click.secho('%d (%s)' % (f[0], f[1]), fg='red')


def put_all_macros(config, data):
    """
    Update macros in Zendesk.
    :param config: context config
    :param data: the macro data to PUT
    """
    entries = (
        'title', 'active', 'actions', 'restriction',
        'description', 'attachments'
    )

    succeeded = []
    failed = []

    with click.progressbar(length=len(data), label='Updating macros...') as bar:
        for m in data:
            macro = {'macro': {k: m[k] for k in m if k in entries}}

            url = 'https://%s.zendesk.com/api/v2/macros/%d.json' % (config['subdomain'], m['id'])

            try:
                put(config, url, macro)
                succeeded.append(m['id'])
            except click.ClickException as err:
                failed.append((m['id'], err.message))  # Record failures

            bar.update(1)

        click.secho('\n\nUpdate complete!')

        if succeeded:
            click.secho('\nThe following macros were updated: ', fg='green', bold=True)
            for s in succeeded:
                click.secho('%d' % s, fg='green')

        if failed:
            click.secho('\nThe following macros could not be updated: ', fg='red', bold=True)
            for f in failed:
                click.secho('%d (%s)' % (f[0], f[1]), fg='red')


def get_all_locales(config):
    url = 'https://%s.zendesk.com/api/v2/locales.json' % config['subdomain']
    res = get(config, url)
    all_locales = res['locales']

    with click.progressbar(length=res['count'], label='Getting locales...') as bar:
        bar.update(len(res['locales']))

        while res['next_page']:
            res = get(config, res['next_page'])
            all_locales.append(res['locales'])
            bar.update(len(res['locales']))

    return all_locales


def get_all_hc_by_type(config, type):
    """
    Get all help center content by type (articles, sections, categories).
    :param config:
    :param type:
    :return:
    """
    if type not in VALID_HC_TYPES:
        raise ValueError('Type must be one of %r' % VALID_HC_TYPES)

    click.echo('Getting %s with translations...' % type)

    all_data = []

    url = 'https://%s.zendesk.com/api/v2/help_center/%s.json?include=translations&per_page=100' % (config['subdomain'], type)

    res = get(config, url)
    all_data.append(res[type])

    with click.progressbar(length=res['count']) as bar:
        bar.update(len(res[type]))

        while res['next_page']:  # Get all pages
            res = get(config, res['next_page'])
            all_data.append(res[type])
            bar.update(len(res[type]))

    return all_data


def confirm_or_create_path(path):
    # Check if path exists, and create it if it doesn't.
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise


def write_json(output_path, filename, data):
    destination = os.path.join(output_path, filename)

    click.echo('Writing data to %s' % click.format_filename(destination))

    confirm_or_create_path(output_path)

    with click.open_file(destination, 'w') as f:
        json.dump(data, f, indent=4)


def archive_directory(path):
    click.echo('Archiving directory: %s' % click.format_filename(path, shorten=True))
    archive_name = shutil.make_archive(path, 'zip', path)  # Zip up the directory at path
    shutil.rmtree(path)  # Delete unzipped directory

    return archive_name


def push_archive_to_remote(repo_dir, remote_name, archive_path, backup_time):
    click.echo('Finding repository at %s' % click.format_filename(repo_dir))
    repo = git.Repo(repo_dir)

    click.echo('Staging %s' % archive_path)
    repo.index.add([archive_path])

    commit_msg = 'Add backup @ %s' % backup_time
    click.echo('Committing with message: %s' % commit_msg)
    repo.index.commit(commit_msg)

    click.echo('Pushing to remote %s' % remote_name)
    origin = repo.remote(remote_name)
    origin.push()

