"""
ML Strategy — uses a trained LightGBM model for signal generation.
"""

import pandas as pd
from loguru import logger

from app.ml.features import FEATURE_COLUMNS, build_features
from app.ml.predictor import MLPredictor
from app.strategy.base import BaseStrategy
from app.strategy.indicators import atr


class MLStrategy(BaseStrategy):
    def __init__(self, model_path: str = "models/xauusd_signal.pkl", confidence_threshold: float = 0.5):
        self._model_path = model_path
        self._confidence_threshold = confidence_threshold
        self._predictor = MLPredictor(model_path)

    @property
    def name(self) -> str:
        return "ml_signal"

    @property
    def min_bars_required(self) -> int:
        return 200

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run ML prediction on each bar. Adds signal and atr columns."""
        df = df.copy()
        features = build_features(df)
        available = [c for c in FEATURE_COLUMNS if c in features.columns]

        df["signal"] = 0
        df["ml_confidence"] = 0.0
        df["atr"] = atr(df["high"], df["low"], df["close"], 14)

        if not self._predictor.is_ready:
            logger.warning("ML model not loaded, returning all HOLD signals")
            return df

        # Predict on each bar where features are available
        X = features[available]
        valid_mask = X.notna().all(axis=1)

        if valid_mask.sum() == 0:
            return df

        X_valid = X[valid_mask]
        proba = self._predictor.model.predict(X_valid)  # shape: (n, 3)

        signal_map = {0: -1, 1: 0, 2: 1}
        for idx, (row_idx, prob) in enumerate(zip(X_valid.index, proba)):
            predicted_class = prob.argmax()
            confidence = float(prob[predicted_class])
            signal = signal_map[predicted_class]

            if confidence >= self._confidence_threshold and signal != 0:
                df.loc[row_idx, "signal"] = signal
            df.loc[row_idx, "ml_confidence"] = confidence

        return df

    def get_params(self) -> dict:
        return {
            "model_path": self._model_path,
            "confidence_threshold": self._confidence_threshold,
        }
