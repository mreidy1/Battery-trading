import matplotlib.pyplot as plt

def plot_price_series(df):
    """
    Plot price time series.
    """
    plt.figure()
    plt.plot(df["price"])
    plt.title("Price Series")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.show()


""" 
    # -----------------------------
    # Plots
    # -----------------------------
    plt.figure()
    plt.plot(results.index, results["price"])
    plt.title("Price (£/MWh)")
    plt.xlabel("Time step")
    plt.ylabel("£/MWh")
    plt.grid(True)

    plt.figure()
    plt.plot(results.index, results["soc_mwh"])
    plt.title("State of Charge (MWh)")
    plt.xlabel("Time step")
    plt.ylabel("MWh")
    plt.grid(True)

    plt.figure()
    plt.plot(results.index, results["net_mw"])
    plt.axhline(0)
    plt.title("Battery Dispatch (MW)")
    plt.xlabel("Time step")
    plt.ylabel("MW (+ discharge, − charge)")
    plt.grid(True)

    plt.figure()
    plt.plot(results.index, results["r_up"])
    plt.axhline(0)
    plt.title("Reserve UP (MW)")
    plt.xlabel("Time step")
    plt.ylabel("Reserve UP Power (MW)")
    plt.grid(True)

    plt.figure()
    plt.plot(results.index, results["r_down"])
    plt.axhline(0)
    plt.title("Reserve Down (MW)")
    plt.xlabel("Time step")
    plt.ylabel("Reserve Down Power (MW)")
    plt.grid(True)
 """