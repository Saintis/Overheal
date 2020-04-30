# Overheal
Overheal analysis of WoW Classic combatlogs.

The two scripts look at the same data and process it similarly.

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

## Plot of single spell

To get a plot of just one spell use the `--spell_id` option

E.g. (for Heal Rank 2)
```
python3 overheal_plot.py Saintis WoWCombatLog.txt --spell_id 2055
```

Running `overheal_table.py` will list the spell id of each spell found.
