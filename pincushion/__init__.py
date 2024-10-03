import json
import logging
import pathlib
from io import TextIOWrapper

import click
from pincushion import historypin, archive


@click.group()
def cli():
    """
    Create an archive for Historypin resources.
    """
    logging.basicConfig(filename="pincushion.log", level=logging.INFO)
    pass


@cli.command("user")
@click.option("--user-id", "A Historypin User ID", type=int)
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
    archive_dir = pathlib.Path(str(archive_path))
    archive_dir.mkdir(parents=True, exist_ok=True)

    data = historypin.get_data(user_id)
    data_path = archive_dir / "data.json"
    json.dump(data, data_path.open("w"), indent=2)

    archive.Generator(archive_dir).generate()


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


@cli.command()
@click.option("--archive-dir")
def generate(archive_dir: str):
    """
    Generate the archive using a directory containing a data.json file. This
    can be useful if improvements are made to the static site generation, but
    you don't want to have to refetch all the data from Historypin again.
    """
    generator = archive.Generator(archive_dir)
    generator.generate()


if __name__ == "__main__":
    cli()
