"""
Minimal BESS optimisation platform (Pyomo)
- Energy arbitrage LP
- Optional degradation cost + throughput cap
- Synthetic price generator so you can start immediately

Install:
  pip install pyomo highspy pandas numpy matplotlib
"""
"""
bess_platform/
  README.md
  requirements.txt
  config.yaml
  data/
    prices.csv
  src/
    battery.py
    markets.py
    optimiser.py
    run.py
    reporting.py

"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pyomo.environ import (
    ConcreteModel, Set, Param, Var, NonNegativeReals, Constraint, Objective, maximize, value
)
from pyomo.opt import SolverFactory


# -----------------------------
# Asset layer
# -----------------------------
@dataclass(frozen=True)
class Battery:
    power_mw: float
    energy_mwh: float
    eta_charge: float = 0.95
    eta_discharge: float = 0.95
    soc_min_frac: float = 0.05
    soc_max_frac: float = 0.95
    soc_init_frac: float = 0.50

    # Economics / operational constraints (optional)
    degr_cost_per_mwh: float = 0.0  # £ per MWh throughput (charge + discharge energy)
    throughput_cap_mwh: Optional[float] = None  # total throughput over horizon (MWh), optional

    def validate(self) -> None:
        assert self.power_mw > 0
        assert self.energy_mwh > 0
        assert 0 < self.eta_charge <= 1
        assert 0 < self.eta_discharge <= 1
        assert 0 <= self.soc_min_frac < self.soc_max_frac <= 1
        assert self.soc_min_frac <= self.soc_init_frac <= self.soc_max_frac
        if self.throughput_cap_mwh is not None:
            assert self.throughput_cap_mwh > 0


# -----------------------------
# Data layer
# -----------------------------
def make_synthetic_prices(
    start: str = "2026-01-01",
    periods: int = 96,
    freq: str = "15min",
    base: float = 70.0,
    daily_amp: float = 35.0,
    noise_std: float = 8.0,
    spike_prob: float = 0.02,
    spike_mult: float = 3.0,
    seed: int = 7,
) -> pd.Series:
    """
    Synthetic price series (£/MWh) with daily shape + noise + occasional spikes.
    periods=96 at 15min => 1 day. Use e.g. periods=96*7 for a week.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start=start, periods=periods, freq=freq)

    # daily sinusoid (two harmonics for more realistic shape)
    t = np.arange(periods)
    day = 96 if freq.lower().startswith("15") else max(24, periods)
    shape = (
        np.sin(2 * math.pi * t / day - 1.2)
        + 0.35 * np.sin(4 * math.pi * t / day + 0.6)
    )

    prices = base + daily_amp * shape + rng.normal(0, noise_std, size=periods)

    # occasional spikes
    spikes = rng.random(periods) < spike_prob
    prices[spikes] *= spike_mult

    # floor to avoid absurd negatives in synthetic land
    prices = np.maximum(prices, -50.0)

    return pd.Series(prices, index=idx, name="price_gbp_per_mwh")


# -----------------------------
# Optimisation layer (energy arbitrage)
# -----------------------------
def optimise_bess_energy_arbitrage(
    prices: pd.Series,
    battery: Battery,
    dt_hours: float,
    solver_name: str = "highs",
    solver_options: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    LP formulation:
    vars: charge_mw[t], discharge_mw[t], soc_mwh[t]
    objective: sum price*(discharge-charge)*dt - degr_cost*throughput
    constraints: soc balance, bounds, power limits, optional throughput cap
    """
    battery.validate()
    assert prices.index.is_monotonic_increasing
    assert dt_hours > 0

    # Indexing
    T = list(range(len(prices)))
    price = prices.to_numpy(dtype=float)

    soc_min = battery.soc_min_frac * battery.energy_mwh
    soc_max = battery.soc_max_frac * battery.energy_mwh
    soc_init = battery.soc_init_frac * battery.energy_mwh

    m = ConcreteModel("bess_energy_arbitrage")

    m.T = Set(initialize=T, ordered=True)

    m.price = Param(m.T, initialize={t: float(price[t]) for t in T})

    # Decision vars
    m.charge = Var(m.T, domain=NonNegativeReals)     # MW
    m.discharge = Var(m.T, domain=NonNegativeReals)  # MW
    m.soc = Var(m.T, domain=NonNegativeReals)        # MWh (bounded via constraints)

    # Bounds via constraints (Pyomo Var bounds are fine too; constraints are explicit and auditable)
    def soc_bounds_rule(mdl, t):
        return (soc_min, mdl.soc[t], soc_max)
    m.soc_bounds = Constraint(m.T, rule=soc_bounds_rule)

    def power_charge_rule(mdl, t):
        return mdl.charge[t] <= battery.power_mw
    m.charge_cap = Constraint(m.T, rule=power_charge_rule)

    def power_discharge_rule(mdl, t):
        return mdl.discharge[t] <= battery.power_mw
    m.discharge_cap = Constraint(m.T, rule=power_discharge_rule)

    # SOC dynamics
    # soc[t+1] = soc[t] + eta_c * charge[t]*dt - (1/eta_d) * discharge[t]*dt
    def soc_balance_rule(mdl, t):
        if t == T[-1]:
            return Constraint.Skip
        return mdl.soc[t + 1] == (
            mdl.soc[t]
            + battery.eta_charge * mdl.charge[t] * dt_hours
            - (1.0 / battery.eta_discharge) * mdl.discharge[t] * dt_hours
        )
    m.soc_balance = Constraint(m.T, rule=soc_balance_rule)

    # Initial SOC
    m.soc_init = Constraint(expr=m.soc[T[0]] == soc_init)

    # Optional: end SOC = initial SOC (prevents "emptying to maximise last interval")
    m.soc_terminal = Constraint(expr=m.soc[T[-1]] == soc_init)

    # Optional throughput cap (over horizon): sum((charge+discharge)*dt) <= cap
    if battery.throughput_cap_mwh is not None:
        m.throughput_cap = Constraint(
            expr=sum((m.charge[t] + m.discharge[t]) * dt_hours for t in T) <= battery.throughput_cap_mwh
        )

    # Objective
    # revenue = price * (discharge - charge) * dt
    # degradation penalty = degr_cost_per_mwh * (charge + discharge) * dt
    def obj_rule(mdl):
        revenue = sum(mdl.price[t] * (mdl.discharge[t] - mdl.charge[t]) * dt_hours for t in T)
        degr = battery.degr_cost_per_mwh * sum((mdl.charge[t] + mdl.discharge[t]) * dt_hours for t in T)
        return revenue - degr

    m.obj = Objective(rule=obj_rule, sense=maximize)

    # Solve
    opt = SolverFactory(solver_name)
    if not opt.available(exception_flag=False):
        raise RuntimeError(
            f"Solver '{solver_name}' not available. Install a solver (recommended: highspy for HiGHS) "
            f"or change solver_name."
        )

    if solver_options:
        for k, v in solver_options.items():
            opt.options[k] = v

    res = opt.solve(m, tee=False)

    # Extract results
    out = pd.DataFrame(index=prices.index)
    out["price"] = prices.values
    out["charge_mw"] = [value(m.charge[t]) for t in T]
    out["discharge_mw"] = [value(m.discharge[t]) for t in T]
    out["soc_mwh"] = [value(m.soc[t]) for t in T]

    out["net_mw"] = out["discharge_mw"] - out["charge_mw"]
    out["throughput_mwh"] = (out["charge_mw"] + out["discharge_mw"]) * dt_hours
    out["revenue_gbp"] = out["price"] * out["net_mw"] * dt_hours
    out["degr_cost_gbp"] = battery.degr_cost_per_mwh * out["throughput_mwh"]
    out["profit_gbp"] = out["revenue_gbp"] - out["degr_cost_gbp"]

    summary = {
        "profit_gbp": float(out["profit_gbp"].sum()),
        "gross_revenue_gbp": float(out["revenue_gbp"].sum()),
        "degradation_cost_gbp": float(out["degr_cost_gbp"].sum()),
        "throughput_mwh": float(out["throughput_mwh"].sum()),
        "full_cycles_equiv": float(out["throughput_mwh"].sum() / (2.0 * battery.energy_mwh)),
    }

    print("\n=== SUMMARY ===")
    for k, v in summary.items():
        if "gbp" in k:
            print(f"{k:20s}: £{v:,.2f}")
        else:
            print(f"{k:20s}: {v:,.4f}")

    return out


# -----------------------------
# Run (start here)
# -----------------------------
if __name__ == "__main__":
    # 1 day of 15-min prices
    prices = make_synthetic_prices(periods=96, freq="15min")

    # Example battery: 50 MW / 100 MWh
    batt = Battery(
        power_mw=50,
        energy_mwh=100,
        eta_charge=0.95,
        eta_discharge=0.95,
        soc_min_frac=0.05,
        soc_max_frac=0.95,
        soc_init_frac=0.50,
        degr_cost_per_mwh=8.0,          # tweak this
        throughput_cap_mwh=None,        # or set e.g. 200 to cap ~1 cycle/day (2*E = 200)
    )

    out = optimise_bess_energy_arbitrage(
        prices=prices,
        battery=batt,
        dt_hours=0.25,
        solver_name="highs",
    )

    # Plots (simple + readable)
    fig1 = plt.figure()
    plt.plot(out.index, out["price"])
    plt.title("Price (£/MWh)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    fig2 = plt.figure()
    plt.plot(out.index, out["soc_mwh"])
    plt.title("State of Charge (MWh)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    fig3 = plt.figure()
    plt.plot(out.index, out["net_mw"])
    plt.title("Net Dispatch (MW) (+ discharge, - charge)")
    plt.xticks(rotation=45)
    plt.axhline(0)
    plt.tight_layout()

    plt.show()