"""
Class for processing data.

By: Filip Gokstorp (Saintis-Dreadmist), 2020
"""
from abc import ABC, abstractmethod


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
