import csv
import click
import simplejson as json
from ..utilities import get_all_views, parse_conditions_for_csv


@click.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default='.')
@click.option('--filename', type=click.STRING, default='views')
@click.option('--format', type=click.Choice(['json', 'csv'], case_sensitive=False), default='json')
@click.option('--group', type=click.INT)
@click.option('--active_only', is_flag=True)
@click.option('--access', type=click.Choice(['personal', 'shared', 'account'], case_sensitive=False), default=None)
@click.pass_context
def get_views(ctx, directory, filename, format, group, active_only, access):
    """Get all automations and save to file."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    views = get_all_views(config=ctx.obj['configuration'], group_id=group, active_only=active_only, access=access)
    path = '%s/%s.%s' % (directory, filename, format)

    with open(path, 'w') as outfile:
        if format.lower() == 'csv':
            fieldnames = set()
            formatted_views = []

            # format each view and append to list of formatted views
            for view in views:
                parsed_conditions = parse_conditions_for_csv(view['conditions'])
                view.pop('conditions', None)
                view = {**view, **parsed_conditions}

                fieldnames.update(view.keys(), parsed_conditions.keys())
                formatted_views.append(view)

            fieldnames = sorted(fieldnames, reverse=True)  # put all the 'action:' columns at the end

            # move id and title to first and second columns, respectively
            old_id_index = fieldnames.index('id')
            old_title_index = fieldnames.index('title')
            fieldnames.insert(0, fieldnames.pop(old_id_index))
            fieldnames.insert(1, fieldnames.pop(old_title_index))

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for view in formatted_views:
                writer.writerow(view)
        else:
            json.dump({'views': views}, outfile, indent=2)

    click.echo('Views saved to %s' % path)
