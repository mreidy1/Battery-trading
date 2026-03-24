from optimisation.bess_dispatch_model import run_dispatch_model
from src.plot_results import plot_rolling_results
from config.battery_config import BATTERY_PARAMS
from trading.rolling_horizon import run_rolling_horizon
import numpy as np

def main():
    T = 192  # 96 timesteps (15-min for 24h)
    period = 96

    prices = [
        round(50 + 30 * np.sin(2 * np.pi * t / period - np.pi/2) # daily RTM cycle
        + 8 * np.sin(2 * np.pi * t / 18),2) # intraday noise
        for t in range(T) 
        ]
    results = run_rolling_horizon(
        price_series=prices,
        params=BATTERY_PARAMS,
        initial_soc=5.0,
        horizon=24,
    )

    plot_rolling_results(results)
    

if __name__ == "__main__":
    main()