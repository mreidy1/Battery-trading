from optimisation.bess_dispatch_model import run_dispatch_model
from src.plot_results import plot_all_results


def main():
    model_results = run_dispatch_model()

    dispatch = model_results["dispatch"]
    summary = model_results["summary"]

    print(dispatch.head())
    print("\nSummary:")
    for key, value in summary.items():
        print(f"{key}: {value:.2f}")

    plot_all_results(dispatch)

if __name__ == "__main__":
    main()