import json
import logging
import shutil
from pathlib import Path

from pytest import fixture

import pincushion

logging.basicConfig(filename='test.log', level=logging.INFO)

@fixture
def archive_dir():
    d = Path('./test-archive')
    if d.is_dir():
        shutil.rmtree(d)
    d.mkdir()
    yield d

def test_run(archive_dir):
    pincushion.main(user_id=11670, archive_dir=archive_dir)

    data_path = archive_dir / "data.json"
    assert data_path.is_file()

    data = json.load(data_path.open())
    assert 'user' in data

    assert 'collections' in data
    assert len(data['collections']) > 0

    assert 'tours' in data
    assert len(data['tours']) > 0

    assert 'pins' in data
    assert len(data['pins']) > 0

    

