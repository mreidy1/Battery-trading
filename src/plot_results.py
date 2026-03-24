import matplotlib.pyplot as plt

def plot_rolling_results(results_df):

    t = results_df["t"]

    # Price
    plt.figure()
    plt.plot(t, results_df["price"])
    plt.title("Price (£/MWh)")
    plt.xlabel("Time step")
    plt.ylabel("£/MWh")
    plt.grid(True)

    # SOC
    plt.figure()
    plt.plot(t, results_df["soc_mwh_start"], label="SOC (start)")
    plt.plot(t, results_df["soc_mwh_end"], linestyle="--", label="SOC (end)")
    plt.title("State of Charge (MWh)")
    plt.xlabel("Time step")
    plt.ylabel("MWh")
    plt.legend()
    plt.grid(True)

    # Dispatch
    plt.figure()
    net_mw = results_df["discharge_mw"] - results_df["charge_mw"]
    plt.plot(t, net_mw)
    plt.axhline(0)
    plt.title("Battery Dispatch (MW)")
    plt.xlabel("Time step")
    plt.ylabel("MW (+ discharge, - charge)")
    plt.grid(True)

    # Profit
    plt.figure()
    plt.plot(t, results_df["realised_profit_gbp"].cumsum())
    plt.title("Cumulative Profit (£)")
    plt.xlabel("Time step")
    plt.ylabel("£")
    plt.grid(True)

    plt.show()