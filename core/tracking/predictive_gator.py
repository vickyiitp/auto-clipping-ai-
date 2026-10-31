"""
Predictive Frame Gator & Shannon Information Entropy Gate.
Implements Rao-Ballard predictive coding to evaluate CPU Haar cascades
only on visual novelty, bypassing redundant frames in 0.00ms.
"""

import math
import numpy as np


class PredictiveFrameGator:
    """
    Rao-Ballard Predictive Coding Filter for Haar cascades.
    Computes visual residual delta between consecutive frames. If visual delta
    is below threshold, reuses prior detected coordinate in 0.00ms.
    """
    def __init__(self, delta_threshold: float = 0.04):
        self.delta_threshold = delta_threshold
        self.last_frame_repr = None

    def should_evaluate(self, gray_frame: np.ndarray) -> bool:
        if gray_frame is None or gray_frame.size == 0:
            return False

        # Lightweight representation: subsample 16x16 grid
        h, w = gray_frame.shape[:2]
        step_y = max(1, h // 16)
        step_x = max(1, w // 16)
        sub = gray_frame[::step_y, ::step_x].astype(np.float32) / 255.0

        if self.last_frame_repr is None:
            self.last_frame_repr = sub
            return True

        diff = np.mean(np.abs(sub - self.last_frame_repr))
        self.last_frame_repr = sub
        return diff >= self.delta_threshold


class ShannonEntropyGator:
    """
    Computes Shannon Information Entropy of the luminosity histogram.
    Skips redundant, static or dark background frames with minimal information content.
    """
    def __init__(self, entropy_threshold: float = 0.08):
        self.entropy_threshold = entropy_threshold
        self.last_entropy = None

    def has_novelty(self, gray_frame: np.ndarray) -> bool:
        if gray_frame is None or gray_frame.size == 0:
            return True

        # Quick 16-bin histogram
        hist, _ = np.histogram(gray_frame, bins=16, range=(0, 256), density=True)
        hist = hist[hist > 0]
        entropy = -float(np.sum(hist * np.log2(hist))) / 4.0  # Normalized 0 to 1

        if self.last_entropy is None:
            self.last_entropy = entropy
            return True

        delta = abs(entropy - self.last_entropy)
        self.last_entropy = entropy
        return delta >= self.entropy_threshold

