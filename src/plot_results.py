import matplotlib.pyplot as plt

def plot_rolling_results(results_df):
    t = results_df["t"]

    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Battery Dispatch Results", fontsize=14)

    # --- Price (with forecast) ---
    axs[0, 0].plot(t, results_df["price"], label="Actual")
    if "forecast_price" in results_df.columns:
        axs[0, 0].plot(t, results_df["forecast_price"], linestyle="--", label="Forecast")
    #if "forecast_error" in results_df.columns:
        #axs[0, 0].plot(t,results_df["forecast_error"],linestyle=":",alpha=0.5,label="Forecast Error")
    axs[0, 0].set_title("Price (£/MWh): Actual vs Forecast")
    axs[0, 0].set_xlabel("Time step")
    axs[0, 0].set_ylabel("£/MWh")
    axs[0, 0].legend()
    axs[0, 0].grid(True)

    # --- SOC ---
    axs[0, 1].plot(t, results_df["soc_mwh_start"], label="SOC (start)")
    axs[0, 1].plot(t, results_df["soc_mwh_end"], linestyle="--", label="SOC (end)")
    axs[0, 1].set_title("State of Charge (MWh)")
    axs[0, 1].set_xlabel("Time step")
    axs[0, 1].set_ylabel("MWh")
    axs[0, 1].legend()
    axs[0, 1].grid(True)

    # --- Dispatch ---
    net_mw = results_df["discharge_mw"] - results_df["charge_mw"]
    axs[1, 0].plot(t, net_mw)
    axs[1, 0].axhline(0)
    axs[1, 0].set_title("Battery Dispatch (MW)")
    axs[1, 0].set_xlabel("Time step")
    axs[1, 0].set_ylabel("MW (+ discharge, - charge)")
    axs[1, 0].grid(True)

    # --- Profit ---
    axs[1, 1].plot(t, results_df["realised_profit_gbp"].cumsum())
    axs[1, 1].set_title("Cumulative Profit (£)")
    axs[1, 1].set_xlabel("Time step")
    axs[1, 1].set_ylabel("£")
    axs[1, 1].grid(True)

    plt.tight_layout()
    plt.show()
    plt.close()