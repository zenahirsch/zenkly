import os
from time import time
from pathlib import Path
import click
from ..utilities import get_all_hc_by_type, write_json, archive_directory, push_archive_to_remote


@click.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default=str(Path.home()))
@click.option('--backup-remotely', is_flag=True)
@click.option('--remote-name', type=click.STRING, default='origin')
@click.pass_context
def backup_guide(ctx, directory, backup_remotely, remote_name):
    """Backup Guide categories, sections and articles."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    backup_time = int(time())

    for t in ['articles', 'sections', 'categories']:
        try:
            data = get_all_hc_by_type(config=ctx.obj['configuration'], guide_type=t)
        except ValueError as err:
            raise click.ClickException(err)

        output_path = os.path.join(directory, 'backup_%s' % backup_time)
        filename = '%s.json' % t

        write_json(output_path=output_path, filename=filename, data=data)

    archive_path = archive_directory(output_path)

    if backup_remotely:
        push_archive_to_remote(repo_dir=directory, remote_name=remote_name, archive_path=archive_path,
                               backup_time=backup_time)

    click.secho('Done!', fg='green')
