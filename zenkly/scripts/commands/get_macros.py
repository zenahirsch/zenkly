import csv
import click
import simplejson as json
from ..utilities import get_all_macros, parse_actions_for_csv


@click.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default='.')
@click.option('--filename', type=click.STRING, default='macros')
@click.option('--format', type=click.Choice(['json', 'csv'], case_sensitive=False), default='json')
@click.option('--category', type=click.STRING)
@click.option('--active_only', is_flag=True)
@click.pass_context
def get_macros(ctx, directory, filename, format, category, active_only):
    """Get all macros and save to file."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    macros = get_all_macros(config=ctx.obj['configuration'], category=category, active_only=active_only)
    path = '%s/%s.%s' % (directory, filename, format)

    with open(path, 'w') as outfile:
        if format.lower() == 'csv':
            fieldnames = set()
            formatted_macros = []

            # format each macro and append to list of formatted macros
            for macro in macros:
                parsed_actions = parse_actions_for_csv(macro['actions'])
                macro.pop('actions', None)  # remove old actions key
                macro = {**macro, **parsed_actions}  # combine the macro with parsed actions

                # add the macro category
                macro_category = macro['title'].split('::')[0]
                macro['macro_category'] = macro_category

                fieldnames.update(macro.keys(), parsed_actions.keys())
                formatted_macros.append(macro)

            fieldnames = sorted(fieldnames, reverse=True)  # put all the 'action:' columns at the end

            # move id and title to first and second columns, respectively
            old_id_index = fieldnames.index('id')
            old_title_index = fieldnames.index('title')
            fieldnames.insert(0, fieldnames.pop(old_id_index))
            fieldnames.insert(1, fieldnames.pop(old_title_index))

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for macro in formatted_macros:
                writer.writerow(macro)
        else:
            json.dump({'macros': macros}, outfile, indent=2)

    click.echo('Macros saved to %s' % path)
