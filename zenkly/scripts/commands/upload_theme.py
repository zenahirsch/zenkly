import time
from functools import reduce
import click
from ..utilities import post_theme_import_job, post_theme, get_theme_job


@click.command()
@click.option('--brand-id', type=click.STRING, required=True, prompt=True)
@click.option('--file', type=click.File(mode='rb'), required=True, prompt=True)
@click.pass_context
def upload_theme(ctx, brand_id, file):
    """Upload help center theme zip file."""
    if ctx.obj['configuration'] == {}:
        raise click.UsageError('No configuration found. Try `zenkly configure`', ctx=ctx)

    click.confirm('Are you sure you want to upload this theme file [\033[36m%s\033[39m]?' % file.name, abort=True)

    job = post_theme_import_job(config=ctx.obj['configuration'], brand_id=brand_id)

    files = {'file': file}

    post_theme(config=ctx.obj['configuration'],
               storage_url=job['data']['upload']['url'],
               parameters=job['data']['upload']['parameters'],
               files=files)

    job_status = 'pending'
    click.secho('Waiting for upload job to complete...')

    while job_status == 'pending':
        time.sleep(1)
        job = get_theme_job(config=ctx.obj['configuration'], job_id=job['id'])
        job_status = job['status']

        if job_status == 'completed':
            click.secho('Complete!')

        if job_status == 'failed':
            errors = reduce(lambda x, y: x + f"\n  {y['title']}: {y['code']}", job['errors'], '  ')
            raise click.ClickException(f"The theme job failed: {click.style(errors, fg='red')}")
