"""
Custom argument parser, for simplifying setting up scripts with command line options.

By: Filip Gokstorp (Saintis), 2020
"""
import argparse


class OverhealParser(argparse.ArgumentParser):
    """Default setup for an arg parser for Overheal scripts."""

    def __init__(
        self,
        *,
        need_character=False,
        accept_character=False,
        accept_spell_id=False,
        accept_spell_power=False,
        accept_encounter=False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.add_argument(
            "source",
            help="Data source, either path to the .txt log file to analyse, link to a Warcraftlog report or the WCL "
            "report code.",
        )

        if need_character:
            self.add_argument("character_name", help="Character name to perform analysis for.")
        elif accept_character:
            self.add_argument("character_name", nargs="?", help="Character name to limit analysis to.")

        if accept_spell_id:
            self.add_argument("--spell_id", help="Spell id to filter events for.")

        if accept_spell_power:
            self.add_argument(
                "-p",
                "--spell_power",
                type=int,
                help="Character spell power. If None, only look at spell power change relative to current amount",
                default=0,
            )

        if accept_encounter:
            self.add_argument(
                "-e",
                "--encounter",
                type=int,
                help="The encounter index to pick directly. Bypasses the encounter selection menu. Pass a 0 for all "
                "encounters.",
            )
