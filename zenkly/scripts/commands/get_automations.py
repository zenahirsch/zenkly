import csv
import click
import simplejson as json
from ..utilities import get_all_automations, parse_actions_for_csv, parse_conditions_for_csv


@click.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default='.')
@click.option('--filename', type=click.STRING, default='triggers')
@click.option('--format', type=click.Choice(['json', 'csv'], case_sensitive=False), default='json')
@click.option('--active_only', is_flag=True)
@click.pass_context
def get_automations(ctx, directory, filename, format, active_only):
    """Get all automations and save to file."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    automations = get_all_automations(config=ctx.obj['configuration'], active_only=active_only)
    path = '%s/%s.%s' % (directory, filename, format)

    with open(path, 'w') as outfile:
        if format.lower() == 'csv':
            fieldnames = set()
            formatted_automations = []

            # format each trigger and append to list of formatted automations
            for automation in automations:
                parsed_actions = parse_actions_for_csv(automation['actions'])
                automation.pop('actions', None)  # remove old actions key
                automation = {**automation, **parsed_actions}  # combine the trigger with parsed actions

                parsed_conditions = parse_conditions_for_csv(automation['conditions'])
                automation.pop('conditions', None)
                automation = {**automation, **parsed_conditions}

                fieldnames.update(automation.keys(), parsed_actions.keys(), parsed_conditions.keys())
                fieldnames.update()

                formatted_automations.append(automation)

            fieldnames = sorted(fieldnames, reverse=True)  # put all the 'action:' columns at the end

            # move id and title to first and second columns, respectively
            old_id_index = fieldnames.index('id')
            old_title_index = fieldnames.index('title')
            fieldnames.insert(0, fieldnames.pop(old_id_index))
            fieldnames.insert(1, fieldnames.pop(old_title_index))

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for automation in formatted_automations:
                writer.writerow(automation)
        else:
            json.dump({'automations': automations}, outfile, indent=2)

    click.echo('Automations saved to %s' % path)
