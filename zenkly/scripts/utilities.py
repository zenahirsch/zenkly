import click
import requests
import time
import threading
from functools import wraps


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


@rate_limited(1)
def post(config, url, data):
    r = requests.post(
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


def post_all_macros(config, data):
    entries = (
        'title', 'active', 'actions', 'restriction',
        'description', 'attachments'
    )

    failed = []

    with click.progressbar(length=len(data), label='Adding macros...') as bar:
        for m in data:
            macro = {'macro': {k: m[k] for k in m if k in entries}}

            url = 'https://%s.zendesk.com/api/v2/macros.json' % config['subdomain']

            click.echo(macro)
            '''
            try:
                post(config, url, macro)
            except click.UsageError as e:
                failed.append((m['id'], e.message))

            bar.update(1)

        click.secho('\n\nAddition complete!')

        click.secho('\nThe following macros could not be added: ', fg='red', bold=True)
        for f in failed:
            click.secho('%d (%s)' % (f[0], f[1]), fg='red')
        '''


def put_all_macros(config, data):
    entries = (
        'title', 'active', 'actions', 'restriction',
        'description', 'attachments'
    )

    failed = []

    with click.progressbar(length=len(data), label='Updating macros...') as bar:
        for m in data:
            macro = {'macro': {k: m[k] for k in m if k in entries}}

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
