from pathlib import Path

from click.testing import CliRunner

import pincushion


def test_user(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        pincushion.user, ["--user-id", "120327", "--archive-path", tmp_path]
    )
    assert result.exit_code == 0
    assert (tmp_path / "index.html").is_file()
    assert (tmp_path / "data.json").is_file()
    assert (tmp_path / "user.jpg").is_file()
    assert (tmp_path / "collections" / "san-francisco-1906-2" / "index.html").is_file()
    assert (tmp_path / "collections" / "san-francisco-1906-2" / "image.jpg").is_file()
    assert (tmp_path / "pins" / "1190430" / "index.html").is_file()
    assert (tmp_path / "pins" / "1190430" / "image.jpg").is_file()
