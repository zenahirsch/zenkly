import os
import configparser
import click
import logging
from .constants import APP_NAME

from .commands.configure import configure
from .commands.get_macros import get_macros
from .commands.get_triggers import get_triggers
from .commands.get_automations import get_automations
from .commands.get_views import get_views
from .commands.update_macros import update_macros
from .commands.add_macros import add_macros
from .commands.backup_guide import backup_guide
from .commands.create_article_mapping import create_article_mapping
from .commands.upload_theme import upload_theme
from .commands.show_brands import show_brands


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
        requests_log = logging.getLogger('requests.packages.urllib3')
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    if ctx.obj is None:
        ctx.obj = {}

    ctx.obj['profile'] = profile
    ctx.obj['configuration'] = {}

    conf_path = os.path.join(click.get_app_dir(APP_NAME), 'config.ini')
    config = configparser.ConfigParser()
    config.read([conf_path])

    if profile in config:
        for key in config[profile]:
            ctx.obj['configuration'][key] = config[profile][key]


cli.add_command(configure)
cli.add_command(get_macros)
cli.add_command(get_triggers)
cli.add_command(get_automations)
cli.add_command(get_views)
cli.add_command(update_macros)
cli.add_command(add_macros)
cli.add_command(backup_guide)
cli.add_command(create_article_mapping)
cli.add_command(upload_theme)
cli.add_command(show_brands)
