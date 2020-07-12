"""
Test the encounter picker methods.

By: Filip Gökstorp (Saintis-Dreadmist), 2020
"""
import os
import io

python = "python3"
log_file = "tests/test_log.txt"
character = "Saintis"


def test_pick_encounter_raw(script_runner, tmpdir):
    path = tmpdir.strpath

    stdin = io.StringIO("1")
    ret = script_runner.run(python, "track_damage_taken.py", log_file, character, "-v", "--path", path, stdin=stdin)

    assert ret.success
    assert ret.stderr == ""

    assert (
        ret.stdout
        == """\
Found the following encounters:

   0)  Whole log
   1)  Onyxia

Encounter to analyse: 175.331 0
179.096 0
191.155 0
192.777 0
193.58 0
193.979 0
193.979 0
"""
    )
    _, _, filenames = next(os.walk(tmpdir))

    assert len(filenames) == 2
    assert f"{character}_health_deficit.png" in filenames
    assert f"{character}_damage_taken.png" in filenames


def test_pick_encounter_api(script_runner, tmpdir):
    path = tmpdir.strpath

    stdin = io.StringIO("1")
    ret = script_runner.run(python, "track_damage_taken.py", log_file, character, "-v", "--path", path, stdin=stdin)

    assert ret.success
    assert ret.stderr == ""

    assert (
        ret.stdout
        == """\
Found the following encounters:

   0)  Whole log
   1)  Onyxia

Encounter to analyse: 175.331 0
179.096 0
191.155 0
192.777 0
193.58 0
193.979 0
193.979 0
"""
    )
    _, _, filenames = next(os.walk(tmpdir))

    assert len(filenames) == 2
    assert f"{character}_health_deficit.png" in filenames
    assert f"{character}_damage_taken.png" in filenames
