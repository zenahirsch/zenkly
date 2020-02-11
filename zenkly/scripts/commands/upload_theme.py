import click
from ..utilities import post_theme_import_job, post_theme


@click.command()
@click.option('--brand-id', type=click.STRING, required=True, prompt=True)
@click.option('--file', type=click.File(mode='r'), required=True, prompt=True)
@click.pass_context
def upload_theme(ctx, brand_id, file):
    """Upload help center theme zip file."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    click.confirm('Are you sure you want to upload this theme file [\033[36m%s\033[39m]?' % file.name, abort=True)

    job_data = post_theme_import_job(config=ctx.obj['configuration'], brand_id=brand_id)

    response = post_theme(config=ctx.obj['configuration'],
                          storage_url=job_data['upload']['url'],
                          parameters=job_data['upload']['parameters'],
                          file=file)

    click.secho(response)
