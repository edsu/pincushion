import logging
import shutil
from pathlib import Path

from pytest import fixture

from pincushion import historypin

logging.basicConfig(filename="test.log", level=logging.INFO)


@fixture
def archive_dir():
    d = Path("./test-archive")
    if d.is_dir():
        shutil.rmtree(d)
    d.mkdir()
    yield d


def test_data(archive_dir):
    data = historypin.get_data(user_id=120327)

    assert "user" in data

    assert "collections" in data
    assert len(data["collections"]) > 0

    assert "tours" in data
    assert len(data["tours"]) > 0

    assert "pins" in data
    assert len(data["pins"]) > 0
