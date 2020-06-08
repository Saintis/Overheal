"""Test for the scripts."""
import os
import pytest

python = "python3"
log_file = "tests/test_log.txt"
character = "Saintis"


@pytest.mark.script_launch_mode('subprocess')
def test_overheal_table(script_runner):
    ret = script_runner.run(python, "overheal_table.py", log_file, character)
    assert ret.success
    assert ret.stderr == ""

    assert ret.stdout == """\
   id  Spell name                     #H    No OH   Any OH  Half OH  Full OH    % OHd
10917  Flash Heal (Rank 7)            15    60.0%    40.0%    26.7%    13.3%    25.1%
 2055  Heal (Rank 2)                   5     0.0%   100.0%    20.0%    20.0%    38.8%
 2061  Flash Heal (Rank 1)            18    61.1%    38.9%    11.1%    11.1%    17.5%
 9474  Flash Heal (Rank 4)             5    80.0%    20.0%     0.0%     0.0%     0.1%
 6063  Heal (Rank 3)                   8    62.5%    37.5%    25.0%    12.5%    21.8%
 2053  Lesser Heal (Rank 3)            1   100.0%     0.0%     0.0%     0.0%     0.0%
-------------------------------------------------------------------------------------
       Total Spell                    52    57.7%    42.3%    17.3%    11.5%    22.5%

   id  Periodic name                  #H    No OH   Any OH  Half OH  Full OH    % OHd
10929  Renew (Rank 9)                  5    80.0%    20.0%    20.0%    20.0%    20.0%
-------------------------------------------------------------------------------------
       Total Periodic                  5    80.0%    20.0%    20.0%    20.0%    20.0%
"""


@pytest.mark.script_launch_mode('subprocess')
def test_overheal_crit(script_runner):
    ret = script_runner.run(python, "overheal_crit.py", log_file, character)
    assert ret.success
    assert ret.stderr == ""

    assert ret.stdout == """\
Crits:
  Flash Heal (Rank 1)           :   3 /  18 crits (16.7%); (17.5% OH), Crit H:  268 ( 111 +  157 oh)  (58.7% oh), 1% crit gives +1.1 healing eq to  +2.4 h ( +2.6 at 0% crit).
  Flash Heal (Rank 4)           :   0 /   5 crits ( 0.0%); ( 0.1% OH)
  Flash Heal (Rank 7)           :   2 /  15 crits (13.3%); (25.1% OH), Crit H:  606 ( 307 +  299 oh)  (49.4% oh), 1% crit gives +3.1 healing eq to  +6.7 h ( +7.1 at 0% crit).
  Heal (Rank 2)                 :   2 /   5 crits (40.0%); (38.8% OH), Crit H:  540 ( 150 +  390 oh)  (72.3% oh), 1% crit gives +1.5 healing eq to  +1.5 h ( +1.7 at 0% crit).
  Heal (Rank 3)                 :   1 /   8 crits (12.5%); (21.8% OH), Crit H:  622 ( 350 +  272 oh)  (43.7% oh), 1% crit gives +3.5 healing eq to  +3.8 h ( +4.1 at 0% crit).
  Lesser Heal (Rank 3)          :   0 /   1 crits ( 0.0%); ( 0.0% OH)

  Overall / Average             :   8 /  52 crits (15.4%); (22.5% OH), Crit H:  465 ( 199 +  265 oh)  (57.1% oh), 1% crit gives +2.0 healing eq to  +3.1 h ( +3.4 at 0% crit).
"""


@pytest.mark.script_launch_mode('subprocess')
def test_overheal_cdf(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "overheal_cdf.py", log_file, character, "--path", path)

    assert ret.success
    assert ret.stderr == ""

    assert ret.stdout == ""
    _, _, filenames = next(os.walk(tmpdir))

    expected_ids = (10917, 2055, 2061, 9474, 6063, 2053, 10929)
    expected_files = (f"{character}_cdf_{i}.png" for i in expected_ids)

    assert len(filenames) == len(expected_ids)

    for f in expected_files:
        assert f in filenames


@pytest.mark.script_launch_mode('subprocess')
def test_overheal_probability(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "overheal_probability.py", log_file, character, "--path", path)

    assert ret.success
    assert ret.stderr == ""
    assert ret.stdout == ""

    _, _, filenames = next(os.walk(tmpdir))

    # check probability
    expected_ids = (10917, 2055, 2061, 9474, 6063, 2053, 10929)
    expected_files = (f"{character}_probability_{i}.png" for i in expected_ids)

    assert len(filenames) == len(expected_ids), print(filenames)

    for f in expected_files:
        assert f in filenames

    # check likelihood
    tmpdir /= "likelihood"
    _, _, filenames = next(os.walk(tmpdir))

    expected_files = (f"{character}_likelihood_{i}.png" for i in expected_ids)

    assert len(filenames) == len(expected_ids)

    for f in expected_files:
        assert f in filenames


@pytest.mark.script_launch_mode('subprocess')
def test_overheal_summary(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "overheal_summary.py", log_file, character, "--path", path)

    assert ret.success
    assert ret.stderr == ""
    assert ret.stdout == ""

    _, _, filenames = next(os.walk(tmpdir))

    assert 1 == len(filenames)

    assert f"{character}_summary.png" in filenames


@pytest.mark.script_launch_mode('subprocess')
def test_overheal_plot(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "overheal_plot.py", log_file, character, "--path", path)

    assert ret.success
    assert ret.stderr == ""

    assert ret.stdout == ""
    _, _, filenames = next(os.walk(tmpdir))

    expected_ids = (10917, 2055, 2061, 9474, 6063, 2053, 10929)
    expected_files = (f"{character}_overheal_{i}.png" for i in expected_ids)

    assert len(filenames) == len(expected_ids), print(filenames)

    for f in expected_files:
        assert f in filenames
