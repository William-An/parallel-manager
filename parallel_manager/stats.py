from __future__ import annotations
from collections import Counter


class Statistics(Counter):
    def __iadd__(self, other: Statistics) -> Statistics:
        return self.__add__(other)

    def __add__(self, other: Statistics) -> Statistics:
        """Override default add method to keep zero values

        Args:
            other (Counter): other stats

        Raises:
            NotImplementedError

        Returns:
            Counter
        """
        if not isinstance(other, Statistics):
            raise NotImplementedError
        result = Statistics()

        for name, val in self.items():
            result[name] = val + other[name]

        for name, val in other.items():
            if name not in self:
                result[name] = val

        return result
