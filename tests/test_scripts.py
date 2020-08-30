"""
Tests for the scripts.

By: Filip Gökstorp (Saintis-Dreadmist), 2020
"""
import os
import pytest

python = "python3"
log_file = "tests/test_log.txt"
wcl_report = "https://classic.warcraftlogs.com/reports/xtj2mVgQXFp4n9RT"
character = "Saintis"


def test_overheal_table(script_runner):
    ret = script_runner.run(python, "overheal_table.py", log_file, character, "-e", "0")
    assert ret.success
    assert ret.stderr == ""

    assert (
        ret.stdout
        == """\

     id  Spell name                     #H    No OH   Any OH  Half OH  Full OH    % OHd
  10917  Flash Heal (Rank 7)            15    60.0%    40.0%    26.7%    13.3%    25.1%
   2055  Heal (Rank 2)                   5     0.0%   100.0%    20.0%    20.0%    38.8%
   2061  Flash Heal (Rank 1)            18    61.1%    38.9%    11.1%    11.1%    17.5%
   9474  Flash Heal (Rank 4)             5    80.0%    20.0%     0.0%     0.0%     0.1%
   6063  Heal (Rank 3)                   8    62.5%    37.5%    25.0%    12.5%    21.8%
   2053  Lesser Heal (Rank 3)            1   100.0%     0.0%     0.0%     0.0%     0.0%
  10929  Renew (Rank 9)                  5    80.0%    20.0%    20.0%    20.0%    20.0%
  -------------------------------------------------------------------------------------
         Total Spell                    57    59.6%    40.4%    17.5%    12.3%    22.4%

"""
    )


def test_overheal_table_api(script_runner):
    ret = script_runner.run(python, "overheal_table.py", wcl_report, character, "-e", "0")
    assert ret.success
    assert ret.stderr == ""

    assert (
        ret.stdout
        == """\
Fetching fight data for report xtj2mVgQXFp4n9RT...
Fetching fight data for report xtj2mVgQXFp4n9RT... Done.
Extracting player names...
Extracting player names... Done.
Fetching healing events from WCL...
[>                                                                     ]    0%         0 /  3500005
[======>                                                               ]    9%    309870 /  3500005
[======================>                                               ]   33%   1148517 /  3500005
[=================================>                                    ]   47%   1658934 /  3500005
[==============================================>                       ]   66%   2314662 /  3500005
[========================================================>             ]   81%   2828287 /  3500005
[===================================================================>  ]   97%   3394592 /  3500005
[======================================================================]  100%   3500005 /  3500005

     id  Spell name                     #H    No OH   Any OH  Half OH  Full OH    % OHd
   6063  Heal (Rank 3)                  70    40.0%    60.0%    25.7%    10.0%    33.0%
  10917  Flash Heal (Rank 7)            16    87.5%    12.5%     6.2%     6.2%     7.0%
  10963  Greater Heal (Rank 2)          58    31.0%    69.0%    41.4%    10.3%    38.0%
   2061  Flash Heal (Rank 1)            45    62.2%    37.8%    28.9%     6.7%    25.3%
   2053  Lesser Heal (Rank 3)            1   100.0%     0.0%     0.0%     0.0%     0.0%
  10965  Greater Heal (Rank 4)          13    30.8%    69.2%    38.5%    15.4%    46.8%
   9474  Flash Heal (Rank 4)             2   100.0%     0.0%     0.0%     0.0%     0.0%
  10901  Power Word: Shield (Rank 10)   24   100.0%     0.0%     0.0%     0.0%     0.0%
  15701  Night Dragon's Breath           1     0.0%   100.0%   100.0%   100.0%   100.0%
  10929  Renew (Rank 9)                 28    53.6%    46.4%    35.7%    32.1%    39.2%
  27805  Holy Nova (Rank 6)              2    50.0%    50.0%     0.0%     0.0%     1.0%
    596  Prayer of Healing (Rank 1)      6    50.0%    50.0%    33.3%    16.7%    35.0%
  10961  Prayer of Healing (Rank 4)      6    50.0%    50.0%    50.0%    33.3%    45.6%
  -------------------------------------------------------------------------------------
         Total Spell                   272    51.8%    48.2%    28.3%    11.8%    33.7%

"""
    )


overheal_crit_output = """\

Crits:
  Flash Heal (Rank 1)           :   3 /  18 crits (16.7%); (17.5% OH), Crit H:  268 ( 111 +  157 oh)  (58.7% oh), 1% crit gives +1.1 healing eq to  +2.4 h ( +2.6 at 0% crit).
  Flash Heal (Rank 4)           :   0 /   5 crits ( 0.0%); ( 0.1% OH)
  Flash Heal (Rank 7)           :   2 /  15 crits (13.3%); (25.1% OH), Crit H:  606 ( 307 +  299 oh)  (49.4% oh), 1% crit gives +3.1 healing eq to  +6.7 h ( +7.1 at 0% crit).
  Heal (Rank 2)                 :   2 /   5 crits (40.0%); (38.8% OH), Crit H:  540 ( 150 +  390 oh)  (72.3% oh), 1% crit gives +1.5 healing eq to  +1.5 h ( +1.7 at 0% crit).
  Heal (Rank 3)                 :   1 /   8 crits (12.5%); (21.8% OH), Crit H:  622 ( 350 +  272 oh)  (43.7% oh), 1% crit gives +3.5 healing eq to  +3.8 h ( +4.1 at 0% crit).
  Lesser Heal (Rank 3)          :   0 /   1 crits ( 0.0%); ( 0.0% OH)

  Overall / Average             :   8 /  52 crits (15.4%); (22.5% OH), Crit H:  465 ( 199 +  265 oh)  (57.1% oh), 1% crit gives +2.0 healing eq to  +3.1 h ( +3.4 at 0% crit).

"""


def test_overheal_crit(script_runner):
    ret = script_runner.run(python, "overheal_crit.py", log_file, character, "-e", "1")
    assert ret.success
    assert ret.stderr == ""

    assert ret.stdout == overheal_crit_output


def test_overheal_crit_input(script_runner):
    import io

    ret = script_runner.run(python, "overheal_crit.py", log_file, character, stdin=io.StringIO("1"))
    assert ret.success
    assert ret.stderr == ""

    assert (
        ret.stdout
        == """\
Found the following encounters:

   0)  Whole log
   1)  Onyxia

Encounter to analyse: """
        + overheal_crit_output
    )


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


def test_overheal_summary(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "overheal_summary.py", log_file, character, "--path", path, "-e", "0")

    assert ret.success
    assert ret.stderr == ""
    assert ret.stdout == ""

    _, _, filenames = next(os.walk(tmpdir))

    assert 1 == len(filenames)

    assert f"{character}_summary.png" in filenames


def test_overheal_plot(script_runner, tmpdir):
    path = tmpdir.strpath
    ret = script_runner.run(python, "overheal_plot.py", log_file, character, "--path", path, "-e", "0")

    assert ret.success
    assert ret.stderr == ""

    assert ret.stdout == """\
Saving fig for Saintis, 10917, None
Saving fig for Saintis, 2055, None
Saving fig for Saintis, 2061, None
Saving fig for Saintis, 9474, None
Saving fig for Saintis, 6063, None
Saving fig for Saintis, 2053, None
Saving fig for Saintis, 10929, None
"""
    _, _, filenames = next(os.walk(tmpdir))

    expected_ids = (10917, 2055, 2061, 9474, 6063, 2053, 10929)

    assert len(filenames) == 2 * len(expected_ids), print(filenames)

    expected_files = (f"{character}_overheal_{i}.png" for i in expected_ids)
    for f in expected_files:
        assert f in filenames

    expected_files = (f"{character}_heal_{i}.png" for i in expected_ids)
    for f in expected_files:
        assert f in filenames
