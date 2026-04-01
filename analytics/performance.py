def compute_performance_metrics(results_df, params):
    """
    Compute core performance metrics from a rolling-horizon run.

    Inputs:
        results_df: DataFrame returned by run_rolling_horizon
        params: battery config dict

    Returns:
        dict of metrics
    """

    # --- Core profit ---
    total_profit = results_df["realised_profit_gbp"].sum()

    # --- Throughput (MWh) ---
    throughput_mwh = (
        (results_df["charge_mw"].abs() + results_df["discharge_mw"].abs())
        * params["dt"]
    ).sum()

    # --- Capacity and cycles ---
    capacity = params["soc_max"] - params["soc_min"]
    approx_cycles = throughput_mwh / (2 * capacity)

    # --- Forecast metrics (if available) ---
    if "forecast_error" in results_df.columns:
        avg_forecast_error = results_df["forecast_error"].mean()
        mean_abs_error = results_df["forecast_error"].abs().mean()
    else:
        avg_forecast_error = None
        mean_abs_error = None

    return {
        "total_profit_gbp": total_profit,
        "throughput_mwh": throughput_mwh,
        "approx_cycles": approx_cycles,
        "avg_forecast_error": avg_forecast_error,
        "mean_abs_error": mean_abs_error,
        "total_profit_per_cycle": total_profit / approx_cycles
    }