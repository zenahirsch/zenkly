import os
import click
import simplejson as json
from ..utilities import post_all_macros


@click.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default='.', prompt=True)
@click.option('--filename', type=click.STRING, required=True, prompt=True)
@click.pass_context
def add_macros(ctx, directory, filename):
    """Create macros from file."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    path = '%s/%s' % (directory, filename)

    if not os.path.exists(path):
        raise click.FileError(path, hint='File does not exist')

    with open(path, 'r') as infile:
        try:
            data = json.load(infile)
        except ValueError as e:
            raise click.UsageError('There was a problem loading %s: %s' % (path, e))

    if 'macros' not in data:
        raise click.UsageError('Missing `macros` key in %s' % path)

    if not type(data['macros']) is list:
        raise click.UsageError('Key `macros` in %s must be a list' % path)

    click.confirm('Are you sure you want to add %d macros?' % len(data['macros']), abort=True)

    post_all_macros(config=ctx.obj['configuration'], data=data['macros'])
