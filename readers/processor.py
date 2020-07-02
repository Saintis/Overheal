"""
Class for processing data.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
from abc import ABC, abstractmethod


class Encounter:
    """Class containing encounter data."""

    def __init__(self, boss, start, end):
        self.boss = boss
        self.start = start
        self.end = end

    def __str__(self):
        return self.boss

    def short_name(self):
        name_parts = self.boss.split()

        if name_parts[0] == "The":
            return name_parts[1]

        return name_parts[0]


class AbstractProcessor(ABC):
    """Helper class for processing data from raw logs or WCL"""

    def __init__(self, source, character_name=None):
        """
        :param source: the data source
        :param character_name: Character name to filter for.
        """
        self.source = source
        self.character_name = character_name

        self.all_events = []
        self.heals = []
        self.periodic_heals = []
        self.damage = []

        self.resurrections = []
        self.deaths = []

        self._encounters = None

    @property
    def encounters(self):
        if self._encounters is None:
            self._encounters = self.get_encounters()

        return self._encounters

    @abstractmethod
    def get_encounters(self):
        """Get all encounters in the source."""
        pass

    @abstractmethod
    def get_deaths(self):
        """Get all deaths during the encounter."""
        pass

    @abstractmethod
    def process(self):
        """Process data from the source."""
        pass

    def select_encounter(self):
        encounters = self.encounters

        print("Found the following encounters:")
        print("")

        print(f"  {0:2d})  Whole log")

        for i, e in enumerate(encounters):
            print(f"  {i+1:2d})  {e.boss}")

        print("")

        while True:
            i_enc = input("Encounter to analyse: ")
            try:
                i_enc = int(i_enc)

                if 0 <= i_enc <= len(encounters):
                    break
            except ValueError:
                print(f"Please enter an integer between {0} and {len(encounters)}")

        if i_enc == 0:
            return None

        return encounters[i_enc - 1]
