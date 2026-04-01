import numpy as np
from src.plot_results import plot_rolling_results
from config.battery_config import BATTERY_PARAMS
from trading.rolling_horizon import run_rolling_horizon
from forecasting.price_forecast import make_smoothed_forecast, make_flat_forecast
from analytics import compute_performance_metrics


def print_metrics(title, metrics):
    print(f"\n{title}")
    print("-" * len(title))
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"{k}: {v:.2f}")
        else:
            print(f"{k}: {v}")


def main():
    T = 192
    period = 96

    prices = [
        round(
            50
            + 30 * np.sin(2 * np.pi * t / period - np.pi / 2)
            + 8 * np.sin(2 * np.pi * t / 18),
            2,
        )
        for t in range(T)
    ]

    results_perfect = run_rolling_horizon(
        price_series=prices,
        params=BATTERY_PARAMS,
        initial_soc=5.0,
        horizon=24,
        forecast_fn=None,
    )

    results_smoothed = run_rolling_horizon(
        price_series=prices,
        params=BATTERY_PARAMS,
        initial_soc=5.0,
        horizon=24,
        forecast_fn=make_smoothed_forecast,
        forecast_kwargs={"smoothing_weight": 0.7},
    )

    results_flat = run_rolling_horizon(
        price_series=prices,
        params=BATTERY_PARAMS,
        initial_soc=5.0,
        horizon=24,
        forecast_fn=make_flat_forecast,
        forecast_kwargs={"flat_price": 50.0},
    )

    metrics_perfect = compute_performance_metrics(results_perfect, BATTERY_PARAMS)
    metrics_smoothed = compute_performance_metrics(results_smoothed, BATTERY_PARAMS)
    metrics_flat = compute_performance_metrics(results_flat, BATTERY_PARAMS)

    print_metrics("Perfect Foresight Metrics", metrics_perfect)
    print_metrics("Smoothed Forecast Metrics", metrics_smoothed)
    print_metrics("Flat Forecast Metrics", metrics_flat)

    plot_rolling_results(results_perfect)
    plot_rolling_results(results_smoothed)
    plot_rolling_results(results_flat)


if __name__ == "__main__":
    main()