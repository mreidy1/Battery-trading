from optimisation.bess_dispatch_model import run_dispatch_model

def main():
    model_results = run_dispatch_model()

    dispatch = model_results["dispatch"]
    summary = model_results["summary"]

    print(dispatch.head())
    print(summary)

if __name__ == "__main__":
    main()