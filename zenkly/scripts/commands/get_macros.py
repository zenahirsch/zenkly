import click
import simplejson as json
from ..utilities import get_all_macros


@click.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default='.')
@click.option('--filename', type=click.STRING, default='macros.json')
@click.pass_context
def get_macros(ctx, directory, filename):
    """Get all macros and save to file."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    macros = get_all_macros(config=ctx.obj['configuration'])
    path = '%s/%s' % (directory, filename)

    with open(path, 'w') as outfile:
        json.dump({'macros': macros}, outfile, indent=2)

    click.echo('Macros saved to %s' % path)
