import numpy as np


def make_perfect_forecast(actual_window):
    return [round(p, 2) for p in actual_window]

def make_flat_forecast(actual_window, flat_price=50.0):
    return [flat_price for _ in actual_window]

def make_smoothed_forecast(actual_window, smoothing_weight=0.7):
    actual_array = np.array(actual_window, dtype=float)
    window_mean = actual_array.mean()

    forecast_array = (
        smoothing_weight * actual_array
        + (1 - smoothing_weight) * window_mean
    )

    return [round(p, 2) for p in forecast_array]


def make_noisy_forecast(actual_window, sigma=3.0, seed=None):
    rng = np.random.default_rng(seed)
    actual_array = np.array(actual_window, dtype=float)

    forecast_array = actual_array + rng.normal(0, sigma, size=len(actual_array))

    return [round(p, 2) for p in forecast_array]