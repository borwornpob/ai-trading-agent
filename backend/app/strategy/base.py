"""
Base Strategy — abstract class for all trading strategies.
"""

from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def min_bars_required(self) -> int:
        ...

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicators and signals on the DataFrame.
        Must add a 'signal' column: 1=BUY, -1=SELL, 0=HOLD.
        """
        ...

    @abstractmethod
    def get_params(self) -> dict:
        ...
