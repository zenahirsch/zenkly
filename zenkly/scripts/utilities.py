import os
import csv
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
def get(config, url, params={}):
    """
    GET the provided endpoint.
    :param config: context config
    :param url: the url to GET
    :return:
    """
    r = requests.get(
        url,
        params=params,
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
def post(config, url, data={}):
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
        json=data,
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
def post_form_data(config, url, data={}, files={}):
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
        data=data,
        files=files
    )

    # Check for HTTP errors (4xx, 5xx).
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise click.ClickException(err)

    return r


def post_theme_import_job(config, brand_id):
    """
    Create help center theme import job.
    :param config: context config
    :param brand_id: the brand id for the relevant help center
    :return: job json
    """
    url = f"https://{config['subdomain']}.zendesk.com/api/v2/guide/theming/jobs/themes/imports"

    data = {
        'job': {
            'attributes': {
                'brand_id': brand_id,
                'format': 'zip',
            }
        }
    }

    res = post(config, url, data)

    return res['job']


def get_theme_job(config, job_id):
    """
    Retrieve job data (for polling)
    :param config: context config
    :param job_id: the job id to retrieve
    :return: job json
    """
    url = f"https://{config['subdomain']}.zendesk.com/api/v2/guide/theming/jobs/{job_id}"

    res = get(config, url)

    return res['job']

def post_theme(config, storage_url, parameters, files):
    """
    POST the theme zip file to the provided storage url
    :param config: context config
    :param storage_url: the storage url provided by import job response
    :param parameters: the parameters provided by the import job response
    :param files: theme zip file data
    :return:
    """
    data = {**parameters}

    res = post_form_data(config, storage_url, data=data, files=files)

    return res


def get_all_themes(config, brand_id):
    """
    Get all themes for the given brand id.
    :param config: context config
    :param brand_id: the brand id for the relevant help center
    :return list: list of all themes
    """
    url = f"https://{config['subdomain']}.zendesk.com/api/guide/theming/{brand_id}/themes.json"
    res = get(config, url)

    return res['themes']


def publish_theme(config, brand_id, theme_id):
    """
    Publish the given theme for the given brand.
    :param config: context config
    :param brand_id: the brand id
    :param theme_id: the theme id
    :return:
    """
    url = f"https://{config['subdomain']}.zendesk.com/api/guide/theming/{brand_id}/themes/{theme_id}/publish.json"
    res = post(config, url)

    return res['theme']


def get_all_macros(config, category=None, active_only=False):
    """
    Get all pages of macros from Zendesk.
    :param config: context config
    :param category: only get macros from this category
    :param active: flag to only include active macros
    :return:
    """
    url = f"https://{config['subdomain']}.zendesk.com/api/v2/macros.json"
    params = {}

    if active_only:
        params['active'] = 'true'

    if category:
        params['category'] = category

    res = get(config, url, params=params)
    all = res['macros']

    with click.progressbar(length=res['count'], label='Getting macros...') as bar:
        bar.update(len(res['macros']))

        while res['next_page']:
            res = get(config, res['next_page'], params=params)
            all = all + res['macros']
            bar.update(len(res['macros']))

    return all


def get_all_triggers(config, category_id=None, active_only=False):
    """
    Get all pages of triggers from Zendesk.
    :param config: context config
    :param category_id: only get triggers from this category
    :param active: flag to only include active triggers
    :return:
    """
    url = f"https://{config['subdomain']}.zendesk.com/api/v2/triggers.json"
    params = {}

    if active_only:
        params['active'] = 'true'

    if category_id:
        params['category_id'] = category_id

    res = get(config, url, params=params)
    all = res['triggers']

    with click.progressbar(length=res['count'], label='Getting triggers...') as bar:
        bar.update(len(res['triggers']))

        while res['next_page']:
            res = get(config, res['next_page'], params=params)
            all = all + res['triggers']
            bar.update(len(res['triggers']))

    return all


def get_all_automations(config, active_only=False):
    """
    Get all pages of automations from Zendesk.
    :param config: context config
    :param active: flag to only include active automations
    :return:
    """
    url = f"https://{config['subdomain']}.zendesk.com/api/v2/automations.json"
    params = {}

    if active_only:
        params['active'] = 'true'

    res = get(config, url, params=params)
    all = res['automations']

    with click.progressbar(length=res['count'], label='Getting automations...') as bar:
        bar.update(len(res['automations']))

        while res['next_page']:
            res = get(config, res['next_page'], params=params)
            all = all + res['automations']
            bar.update(len(res['automations']))

    return all

def get_all_views(config, group_id=None, active_only=False, access=None):
    """
    Get all pages of automations from Zendesk.
    :param config: context config
    :param group_id: only views belonging to given group
    :param active: flag to only include active automations
    :param access: only views with given access. May be "personal", "shared", or "account"
    :return:
    """
    url = f"https://{config['subdomain']}.zendesk.com/api/v2/views.json"
    params = {}

    if group_id:
        params['group_id'] = group_id

    if active_only:
        params['active'] = 'true'

    if access:
        params['access'] = access

    res = get(config, url, params=params)
    all = res['views']

    with click.progressbar(length=res['count'], label='Getting views...') as bar:
        bar.update(len(res['views']))

        while res['next_page']:
            res = get(config, res['next_page'], params=params)
            all = all + res['views']
            bar.update(len(res['views']))

    print(len(all))
    return all


def parse_actions_for_csv(actions):
    parsed_actions = {}

    for action in actions:
        action_field = action['field']
        action_value = action['value']

        key_name = f"action:{action_field}"

        if not key_name in parsed_actions:
            parsed_actions[key_name] = []

        parsed_actions[key_name].append(action_value)

    return parsed_actions


def parse_conditions_for_csv(conditions):
    parsed_conditions = {}

    for condition in conditions['all']:
        key_name = f"condition:all:{condition['field']}"

        if not key_name in parsed_conditions:
            parsed_conditions[key_name] = []

        parsed_conditions[key_name].append(f"{condition['operator']} {condition['value']}")

    for condition in conditions['any']:
        key_name = f"condition:any:{condition['field']}"

        if not key_name in parsed_conditions:
            parsed_conditions[key_name] = []

        parsed_conditions[key_name].append(f"{condition['operator']} {condition['value']}")

    return parsed_conditions


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

            url = f"https://{config['subdomain']}.zendesk.com/api/v2/macros.json"

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
                click.secho(f"{s[0]} (new id: {s[1]})", fg='green')

        if failed:
            click.secho('\nThe following macros could not be added: ', fg='red', bold=True)
            for f in failed:
                click.secho(f"{f[0]} ({f[1]})", fg='red')


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

            url = f"https://{config['subdomain']}.zendesk.com/api/v2/macros/{m['id']}.json"

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
                click.secho(s, fg='green')

        if failed:
            click.secho('\nThe following macros could not be updated: ', fg='red', bold=True)
            for f in failed:
                click.secho(f"{f[0]} ({f[1]})", fg='red')


def get_all_locales(config):
    url = f"https://{config['subdomain']}.zendesk.com/api/v2/locales.json"
    res = get(config, url)
    all_locales = res['locales']

    with click.progressbar(length=res['count'], label='Getting locales...') as bar:
        bar.update(len(res['locales']))

        while res['next_page']:
            res = get(config, res['next_page'])
            all_locales.append(res['locales'])
            bar.update(len(res['locales']))

    return all_locales


def get_all_hc_by_type(config, guide_type):
    """
    Get all help center content by type (articles, sections, categories).
    :param config:
    :param guide_type:
    :return:
    """
    if guide_type not in VALID_HC_TYPES:
        raise ValueError(f"Type must be one of {VALID_HC_TYPES}")

    click.echo(f"Getting {guide_type} with translations...")

    all_data = []

    url = f"https://{config['subdomain']}.zendesk.com/api/v2/help_center/{guide_type}.json?include=translations"
    res = get(config, url)

    all_data = all_data + res[guide_type]

    with click.progressbar(length=res['count']) as bar:
        bar.update(len(res[guide_type]))

        while res['next_page']:  # Get all pages
            res = get(config, res['next_page'])
            all_data = all_data + res[guide_type]
            bar.update(len(res[guide_type]))

    return all_data


def get_all_brands(config):
    url = f"https://{config['subdomain']}.zendesk.com/api/v2/brands.json"
    res = get(config, url)

    return res['brands']


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

    click.echo(f"Writing data to {click.format_filename(destination)}")

    confirm_or_create_path(output_path)

    with click.open_file(destination, 'w') as f:
        json.dump(data, f, indent=4)


def write_csv(output_path, filename, data):
    destination = os.path.join(output_path, filename)

    click.echo(f"Writing data to {click.format_filename(destination)}")

    confirm_or_create_path(output_path)

    with click.open_file(destination, 'w') as f:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for d in data:
            writer.writerow(d)


def archive_directory(path):
    click.echo(f"Archiving directory: {click.format_filename(path, shorten=True)}")
    archive_name = shutil.make_archive(path, 'zip', path)  # Zip up the directory at path
    shutil.rmtree(path)  # Delete unzipped directory

    return archive_name


def push_archive_to_remote(repo_dir, remote_name, archive_path, backup_time):
    click.echo(f"Finding repository at {click.format_filename(repo_dir)}")
    repo = git.Repo(repo_dir)

    click.echo(f"Staging {archive_path}")
    repo.index.add([archive_path])

    commit_msg = f"Add backup @ {backup_time}"
    click.echo(f"Committing with message: {commit_msg}")
    repo.index.commit(commit_msg)

    click.echo(f"Pushing to remote {remote_name}")
    origin = repo.remote(remote_name)
    origin.push()

