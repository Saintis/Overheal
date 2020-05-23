# Overheal
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Overheal analysis of WoW Classic combatlogs.

Two scripts look at the same data and process it similarly.

`overheal_table.py` outputs a list of spells used, and overheal frequency.

`overheal_plot.py` shows how the total healing and overhealing would change if the heal power was reduced.

# Usage
Requires `python3`, `numpy`, and `matplotlib`.

Run either scripts with:
```
python3 overheal_plot.py [player_name] [log_file]
```
e.g.
```
python3 overheal_plot.py Saintis WoWCombatLog.txt
```

(if `python3` gives an error you can try `python`, otherwise look up how to run a python script on your machine)

Run `python3 overheal_plot.py -h` for more options.

Figures from the script will be saved in a `figs` directory.

## Reading data from Warcraft Logs

Some scripts can use data from a Warcraft Logs report instead of a raw combat log file.

To get this working you need to get your api key from the WCL website. Make sure you have an account and look for it at the bottom of your profile page, [here](https://classic.warcraftlogs.com/profile). Save that api key to a text file called `apikey.txt` in the same folder you downloaded the scripts to and it should work.

You tell the script to read in a WCL with the option `-r`. For example
```
python3 overheal_crit.py [player_name] -r [report code]
```
You can find your `[report code]` in the WCL url after `report/`.

## Data for a single spell

To get data of just one spell use the `--spell_id` option

E.g. (for Heal Rank 2, id `2055`)
```
python3 overheal_plot.py Saintis WoWCombatLog.txt --spell_id 2055
```

Running `overheal_table.py` will list the spell id of each spell found.
