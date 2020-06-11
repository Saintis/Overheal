"""Test for evaluate 3t1 scritp."""

python = "python3"
log_file = "tests/test_log.txt"
character = "Saintis"


def test_evaluate_3t1(script_runner):
    ret = script_runner.run(python, "evaluate_3t1.py", log_file, character, "-e", "1")
    assert ret.success
    assert ret.stderr == ""

    assert (
        ret.stdout
        == """\
Evaluation of 3T1  (Onyxia, 253s)
  Used Flash Heal 38 times.
  Found 5 back-to-back casts after a Flash Heal (within 0.1s) (13.2%).
  3T1 is potentially worth 0.5s of casting (0 more Flash Heals).
"""
    )
