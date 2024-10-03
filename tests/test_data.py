import logging

from pincushion import historypin

logging.basicConfig(filename="test.log", level=logging.INFO)


def test_data():
    data = historypin.get_data(user_id=120327)

    assert "user" in data

    assert "collections" in data
    assert len(data["collections"]) > 0

    assert "tours" in data
    assert len(data["tours"]) > 0

    assert "pins" in data
    assert len(data["pins"]) > 0
