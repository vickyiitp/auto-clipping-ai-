"""
Kalman Crop Tracker Module.
NASA Apollo-grade 1D recursive Kalman State Filter.
Eliminates camera micro-tremors and smooths face tracking transitions without memory leaks.
"""

from typing import Optional


class KalmanCropTracker:
    """
    1D Apollo Kalman filter for 9:16 vertical auto-reframe crop center smoothing.
    Recursively filters camera micro-tremors with zero memory footprint while
    instantly snapping across sharp shot cuts when innovation residual exceeds threshold.
    """
    def __init__(self, process_noise: float = 2.0, measurement_noise: float = 10.0, cut_threshold: float = 280.0):
        self.q = process_noise
        self.r = measurement_noise
        self.cut_threshold = cut_threshold
        self.x = None       # State estimate
        self.p = 1.0        # Estimation error covariance

    def update(self, measurement: Optional[float]) -> Optional[float]:
        if measurement is None:
            return self.x

        if self.x is None:
            self.x = float(measurement)
            self.p = self.r
            return self.x

        # Scene cut detection: if sudden displacement > cut_threshold, reset filter instantly
        if abs(measurement - self.x) > self.cut_threshold:
            self.x = float(measurement)
            self.p = self.r
            return self.x

        # Time update (Prediction)
        x_pred = self.x
        p_pred = self.p + self.q

        # Measurement update (Correction)
        residual = measurement - x_pred
        k_gain = p_pred / (p_pred + self.r)
        self.x = x_pred + k_gain * residual
        self.p = (1.0 - k_gain) * p_pred

        return self.x

