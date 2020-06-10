# Overheal
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Saintis](https://circleci.com/gh/Saintis/Overheal.svg?style=shield)](https://app.circleci.com/pipelines/github/Saintis/Overheal)

Overheal analysis of WoW Classic combatlogs.

There are now quite a few scripts that do slightly differnt things, below are some that might be of interest.

`overheal_table.py` outputs a list of spells used, and overheal frequency.

`overheal_plot.py` shows how the total healing and overhealing would change if the heal power was reduced.

`overheal_crit.py` shows how much extra healing 1% of crit gives you. Also relates it to an equivalent amount of +healing.

`overheal_probability.py` generates plots of the probability of each spell to overheal as your +heal would change.

# Usage
Requires `python3`. Also requires the following python packages: `numpy`, `requests`, and `matplotlib` (best installed with `pip`).

Run either scripts with:
```
python3 overheal_plot.py [data source] [player name]
```
e.g.
```
python3 overheal_plot.py WoWCombatLog.txt Saintis
```

(if `python3` gives an error you can try `python`, otherwise look up how to run a python script on your machine)

Run `python3 overheal_plot.py -h` for more options.

Figures from the script will be saved in a `figs` directory.

## Reading data from Warcraft Logs

Some scripts can use data from a Warcraft Logs report instead of a raw combat log file.

To get this working you need to get your api key from the WCL website. Make sure you have an account and look for it at the bottom of your profile page, [here](https://classic.warcraftlogs.com/profile). Save that api key to a text file called `apikey.txt` in the same folder you downloaded the scripts to and it should work.

If you want to read from WCL, just pass in the full link to the combat report. For example
```
python3 overheal_crit.py https://classic.warcraftlogs.com/reports/1KQrVMkXaYB29L7H Saintis
```

All `overheal_` scripts should accept a warcraft log link. The `analyse_` scripts require the WoWCombatLog.txt file produced by the client.

## Data for a single spell

To get data of just one spell use the `--spell_id` option

E.g. (for Heal Rank 2, id `2055`)
```
python3 overheal_plot.py Saintis WoWCombatLog.txt --spell_id 2055
```

Running `overheal_table.py` will list the spell id of each spell found.
