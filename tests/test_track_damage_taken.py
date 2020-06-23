"""Test the track_damage script."""
import os

python = "python3"
log_file = "tests/test_log.txt"
character = "Saintis"


def test_track_raid_damage(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "track_damage_taken.py", log_file, "-e", "1", "-v", "--path", path, "--raid")

    assert ret.success
    assert ret.stderr == ""

    out = ret.stdout
    out_lines = out.split("\n")
    assert out_lines[-2] == "251.576 -27494"

    _, _, filenames = next(os.walk(tmpdir))

    assert len(filenames) == 1
    assert f"raid_damage.png" in filenames


def test_track_raid_damage_no_character(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "track_damage_taken.py", log_file, character, "-e", "1", "-v", "--path", path, "--raid")

    assert ret.success
    assert ret.stderr == ""

    out = ret.stdout
    out_lines = out.split("\n")
    assert out_lines[-2] == "251.576 -42797"

    _, _, filenames = next(os.walk(tmpdir))

    assert len(filenames) == 1
    assert f"raid_damage_no_{character}.png" in filenames


def test_track_character_damage(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "track_damage_taken.py", log_file, character, "-e", "1", "-v", "--path", path)

    assert ret.success
    assert ret.stderr == ""

    assert (
        ret.stdout
        == """\
162.518 -2009
174.245 -774
178.01 0
179.506 -1343
190.069 -1161
191.691 -873
192.494 -102
192.893 0
192.893 0
"""
    )
    _, _, filenames = next(os.walk(tmpdir))

    assert len(filenames) == 2
    assert f"{character}_health_deficit.png" in filenames
    assert f"{character}_damage_taken.png" in filenames
