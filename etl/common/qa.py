def is_outlier_delta(prev: float, curr: float, threshold: float = 25.0) -> bool:
    return abs(curr - prev) > threshold

