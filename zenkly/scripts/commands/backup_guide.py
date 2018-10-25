import click


@click.command()
@click.pass_context
def backup_guide(ctx):
    """Backup Guide sections and articles."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    click.echo('Backing up!')
