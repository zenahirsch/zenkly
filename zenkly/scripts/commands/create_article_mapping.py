import os
from time import time
import json
import shutil
import click
from zenkly.scripts.utilities import write_json


@click.command()
@click.option('--old-backup-file', type=click.File(), required=True)
@click.option('--new-backup-file', type=click.File(), required=True)
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default='.')
@click.pass_context
def create_article_mapping(ctx, directory, old_backup_file, new_backup_file):
    """Generate a JSON object with mapping based on provided backup files."""
    mapping_time = int(time())

    mapping = {}

    old_data = json.load(old_backup_file)
    new_data = json.load(new_backup_file)

    for o in old_data:
        old_id = o['id']
        old_title = o['name']

        for n in new_data:
            new_id = n['id']
            new_title = n['name']

            if old_title == new_title:
                mapping[old_id] = str(new_id)

    filename = 'mapping_%s.json' % mapping_time

    write_json(output_path=directory, filename=filename, data=mapping)

    click.secho('Done!', fg='green')
