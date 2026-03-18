from optimisation.bess_dispatch_model import run_dispatch_model
from src.plot_results import plot_all_results
from config.battery_config import BATTERY_PARAMS

def main():
    prices = [30.0 if t < 48 else 80.0 for t in range(96)]

    model_results = run_dispatch_model(
        price_series=prices,
        params=BATTERY_PARAMS,
        initial_soc=50.0)

    dispatch = model_results["dispatch"]
    summary = model_results["summary"]

    print(dispatch.head())
    print("\nSummary:")
    for key, value in summary.items():
        print(f"{key}: {value:.2f}")

    plot_all_results(dispatch)

if __name__ == "__main__":
    main()