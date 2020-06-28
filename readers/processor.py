"""
Class for processing data.

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

    @abstractmethod
    def process(self):
        """Process data from the source."""
        pass
