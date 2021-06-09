import csv
import click
import simplejson as json
from ..utilities import get_all_triggers, parse_actions_for_csv, parse_conditions_for_csv


@click.command()
@click.option('--directory', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
              default='.')
@click.option('--filename', type=click.STRING, default='triggers')
@click.option('--format', type=click.Choice(['json', 'csv'], case_sensitive=False), default='json')
@click.option('--category_id', type=click.INT)
@click.option('--active_only', is_flag=True)
@click.pass_context
def get_triggers(ctx, directory, filename, format, category_id, active_only):
    """Get all triggers and save to file."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    triggers = get_all_triggers(config=ctx.obj['configuration'], category_id=category_id, active_only=active_only)
    path = '%s/%s.%s' % (directory, filename, format)

    with open(path, 'w') as outfile:
        if format.lower() == 'csv':
            fieldnames = set()
            formatted_triggers = []

            # format each trigger and append to list of formatted triggers
            for trigger in triggers:
                parsed_actions = parse_actions_for_csv(trigger['actions'])
                trigger.pop('actions', None)  # remove old actions key
                trigger = {**trigger, **parsed_actions}  # combine the trigger with parsed actions

                parsed_conditions = parse_conditions_for_csv(trigger['conditions'])
                trigger.pop('conditions', None)
                trigger = {**trigger, **parsed_conditions}

                fieldnames.update(trigger.keys(), parsed_actions.keys(), parsed_conditions.keys())
                fieldnames.update()

                formatted_triggers.append(trigger)

            fieldnames = sorted(fieldnames, reverse=True)  # put all the 'action:' columns at the end

            # move id and title to first and second columns, respectively
            old_id_index = fieldnames.index('id')
            old_title_index = fieldnames.index('title')
            fieldnames.insert(0, fieldnames.pop(old_id_index))
            fieldnames.insert(1, fieldnames.pop(old_title_index))

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for trigger in formatted_triggers:
                writer.writerow(trigger)
        else:
            json.dump({'triggers': triggers}, outfile, indent=2)

    click.echo('Triggers saved to %s' % path)
