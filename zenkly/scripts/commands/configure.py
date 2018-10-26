import os
import errno
import configparser
import click
from ..constants import APP_NAME


@click.command()
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
        click.echo('Config written to %s' % click.format_filename(conf_path))
