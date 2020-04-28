# Overheal
Overheal analysis of WoW Classic combatlogs.

The two scripts look at the same data and process it similarly.

`overheal_table.py` outputs a list of spells used, and overheal frequency.

`overheal_plot.py` shows how the total healing and overhealing would change if the heal power was reduced.

# Usage
Requires `python3`, `numpy`, and `matplotlib`.

You will have to create a `figs` directory for the script to save the figures into.

Run either scripts with:
```
overheal_plot.py [player_name] [log_file]
```

Run `overheal_plot.py -h` for more options.
