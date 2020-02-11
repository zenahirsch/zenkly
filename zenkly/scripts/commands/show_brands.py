import click
from tabulate import tabulate
from ..utilities import get_all_brands


@click.command()
@click.pass_context
def show_brands(ctx):
    """Show brands as tabular data."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    brands = get_all_brands(config=ctx.obj['configuration'])

    headers = ['Name', 'ID', 'Subdomain', 'Brand URL', 'HC State', 'Active?', 'Host Mapping']
    table = []
    for brand in brands:
        table.append([
            brand['name'],
            brand['id'],
            brand['subdomain'],
            brand['brand_url'],
            brand['help_center_state'],
            brand['active'],
            brand['host_mapping']])

    click.echo(tabulate(table, headers=headers))
