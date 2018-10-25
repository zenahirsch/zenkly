import os
from time import time
import click
from ..utilities import get_all_locales, get_all_hc_by_type, write_jsons


@click.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default='.')
@click.pass_context
def backup_guide(ctx, directory):
    """Backup Guide categories, sections and articles."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    # Get all of the available locales within Zendesk
    locale_data = get_all_locales(config=ctx.obj['configuration'])
    locales = [l['locale'].lower() for l in locale_data]

    backup_time = int(time())

    for locale in locales:
        for type in ['articles', 'sections', 'categories']:
            data = get_all_hc_by_type(config=ctx.obj['configuration'], locale=locale, type=type)

            output_path = os.path.join(directory, 'backup_%s' % backup_time, locale)
            filename = '%s.json' % type

            write_json(output_path=output_path, filename=filename, data=data)
