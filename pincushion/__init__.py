import json
import logging
import pathlib

import click
from pincushion import historypin, archive


@click.group()
def cli():
    """
    Create an archive for Historypin resources.
    """
    logging.basicConfig(filename='pincushion.log', level=logging.INFO)
    pass

@cli.command('user')
@click.argument('user_id')
@click.option('--archive-dir', default="archive")
def user(user_id: int, archive_dir: str):
    """
    Create an archive for a given Historypin User ID.
    """
    archive_dir = pathlib.Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)

    data = historypin.get_data(user_id)
    data_path = archive_dir / "data.json"
    json.dump(data, data_path.open('w'), indent=2)

    archive.Generator(archive_dir).generate()


@cli.command()
@click.argument('archive_dir')
def generate(archive_dir):
    """
    Regenerate the archive using a directory containing the data.json.
    """
    generator = archive.Generator(archive_dir)
    generator.generate()


if __name__ == "__main__":
    cli()
