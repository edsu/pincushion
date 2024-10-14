import json
import logging
import pathlib
from io import TextIOWrapper
from pathlib import Path

import click
from pincushion import historypin, archive


@click.group()
def cli():
    """
    Create an archive for Historypin resources.
    """
    logging.basicConfig(filename="pincushion.log", level=logging.INFO)


@cli.command("user")
@click.option("--user-id", help="A Historypin User ID", type=int)
@click.option(
    "--archive-path",
    help="Where to write the archive files",
    type=click.Path(),
    default="archive",
)
def user(user_id: int, archive_path: click.Path):
    """
    Create an archive for a given Historypin User ID. This is probably the
    command you will want to be using.
    """
    click.echo(f"Generating archive for user-id: {user_id}")
    archive_dir = pathlib.Path(str(archive_path))
    archive_dir.mkdir(parents=True, exist_ok=True)

    data = historypin.get_data(user_id)
    data_path = archive_dir / "data.json"
    json.dump(data, data_path.open("w"), indent=2)

    archive.ArchiveGenerator(archive_dir).generate()


@cli.command()
@click.option("--archive-path")
def regenerate(archive_path: str):
    """
    Regenerate the archive using a directory containing a data.json file. This
    can be useful if improvements are made to the static site generation, and
    you don't want to have to refetch all the data from Historypin.
    """
    generator = archive.ArchiveGenerator(Path(archive_path))
    generator.generate()


@cli.command("data")
@click.option("--user-id", help="A Historypin User ID", type=int)
@click.option(
    "--output", help="Where to write the data", type=click.File("w"), required=True
)
def data(user_id: int, output: TextIOWrapper):
    """
    Download the JSON metadata for a Historypin user.
    """
    data = historypin.get_data(user_id)
    output.write(json.dumps(data, indent=2))


@cli.command("media")
@click.option(
    "--archive-path",
    help="An existing archive directory",
    type=click.Path(file_okay=False),
)
def media(archive_path: str):
    """
    Download the media for a given archive. This can be useful for testing.
    """
    generator = archive.ArchiveGenerator(Path(archive_path))
    generator.download_media()


if __name__ == "__main__":
    cli()
