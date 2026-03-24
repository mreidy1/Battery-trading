import pandas as pd

from optimisation.bess_dispatch_model import (
    build_dispatch_model,
    solve_dispatch_model,
    extract_dispatch_results,
)


def run_rolling_horizon(price_series, params, initial_soc, horizon):
    """
    Run a rolling-horizon battery dispatch simulation.

    At each timestep:
    - optimise over the next 'horizon' intervals
    - execute only the first interval
    - update SOC
    - move forward one timestep
    """

    current_soc = initial_soc
    history = []

    n_steps = len(price_series)

    for t in range(n_steps):
        window_prices = price_series[t : t + horizon]

        # Need at least 2 steps because the SOC balance is written as soc[t+1]
        if len(window_prices) < 2:
            break

        model, _, throughput_cost = build_dispatch_model(
            price_series=window_prices,
            params=params,
            initial_soc=current_soc,
        )

        model = solve_dispatch_model(model)
        results = extract_dispatch_results(model, params, throughput_cost)
        dispatch = results["dispatch"]

        first_step = dispatch.iloc[0]

        actual_price = price_series[t]
        charge_mw = first_step["charge_mw"]
        discharge_mw = first_step["discharge_mw"]
        net_mw = discharge_mw - charge_mw

        energy_revenue_gbp = net_mw * actual_price * params["dt"]
        degradation_cost_gbp = (
            (charge_mw + discharge_mw) * params["dt"] * params["degr_cost"]
        )
        realised_profit_gbp = energy_revenue_gbp - degradation_cost_gbp

        next_soc = dispatch.iloc[1]["soc_mwh"]
        current_soc = next_soc

        """ print(
            f"t={t}, current_soc={current_soc:.2f}, price={actual_price:.2f}, "
            f"charge={charge_mw:.2f}, discharge={discharge_mw:.2f}, next_soc={next_soc:.2f}"
        ) """

        history.append(
            {
                "t": t,
                "soc_mwh_start": current_soc,
                "price": actual_price,
                "charge_mw": charge_mw,
                "discharge_mw": discharge_mw,
                "net_mw": net_mw,
                "energy_revenue_gbp": energy_revenue_gbp,
                "degradation_cost_gbp": degradation_cost_gbp,
                "realised_profit_gbp": realised_profit_gbp,
                "soc_mwh_end": next_soc,
            }
        )

        current_soc = next_soc

    return pd.DataFrame(history)