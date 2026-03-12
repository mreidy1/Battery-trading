from pyomo.environ import ConcreteModel
from pyomo.environ import Set
from pyomo.environ import Param
from pyomo.environ import Var, NonNegativeReals
from pyomo.environ import Constraint
from pyomo.environ import Objective, maximize
from pyomo.opt import SolverFactory
from pyomo.environ import value
import pandas as pd

def build_dispatch_model(price_series=None):
    m = ConcreteModel()

    if price_series is None:
        price_series = [30.0 if t < 48 else 80.0 for t in range(96)]

    T = range(len(price_series))
    m.T = Set(initialize=T, ordered=True)

    prices = {t: price_series[t] for t in m.T}
    m.price = Param(m.T, initialize=prices)          # £/MWh    - *Question 1* how would you do this if the data being feed in is off unknowen length e.g. livedata for trading
    
    response_up_price = {t: 5.0 for t in m.T}    # £/MW·h            - *Question 2* how would you add a tolerance range e.g. dynamic pricing, dont want the battery trading on the decline of a spike (is that legal???)
    response_down_price = {t: 2.0 for t in m.T}  # £/MW·h            - *Question 3* how would you add a tolerance range e.g. dynamic pricing, dont want the battery trading on the decline of a spike (is that legal???)
    m.response_up_price = Param(m.T, initialize=response_up_price)
    m.response_down_price = Param(m.T, initialize=response_down_price)  # - *Question 4* dont know how this would interact with above // probably would have to change the strucutre for live data (below as well)
    m.charge = Var(m.T, domain=NonNegativeReals)     # MW
    m.discharge = Var(m.T, domain=NonNegativeReals)  # MW
    m.soc = Var(m.T, domain=NonNegativeReals)        # MWh
    m.response_up = Var(m.T, domain=NonNegativeReals)       # MW
    m.response_down = Var(m.T, domain=NonNegativeReals)     # MW



    # battery constraints   - *Question 5* some of these would have to be dynamic e.g. efficiency and SoC decrease due to degredation - this is financial covered by degr_cost (could cause double counting in finacial calcs??)
    params = dict(
    Pmax = 50.0,            # MW
    soc_min = 5.0,          # MWh
    soc_max = 95.0,         # MWh
    soc_init = 50.0,        # battery starts at 50MWh charge
    eta_c = 0.95,           # (η) efficiency
    eta_d = 0.95,           # (η) efficiency
    dt = 0.25,              # hours per timestep (15 min)
    degr_cost = 8.0,        # £ per MWh throughput (tune later)
    cycles_per_day = 1.0,   # number of "full" cycles the battery can cycle through
    epsilon = 1e-3,         # small £3/MWh offset
    tau = 0.5,              # reserve duration (hours)
    )

    T_last = max(m.T)



    m.soc_terminal = Constraint(expr=m.soc[T_last] == params["soc_init"]) # forces the end SoC to be 50MWh (the start point)

    hours = len(list(m.T)) * params["dt"]
    days = hours / 24.0
    throughput_cap = 2 * (params["soc_max"] - params["soc_min"]) * params["cycles_per_day"] * days # 1 full cycle per day
    throughput_cost = params["degr_cost"] + params["epsilon"] # *Question 6* added degradition here should pyhiscal deg be done here or at the end? if at end why not calc cost there as well ref *Question 5* 

    #================================= Battery operation rules ===================================================

    # *Question 7* should degredation be a function "module" here? ref *Question 5*

    # rules to ensure the optimiser stays within the pysical limits of the battery
    def charge_cap_rule(m, t):
        return m.charge[t] + m.response_down[t] <= params["Pmax"] # battery cant change faster than 50MW               *Question 8* deg can effect actual output same for below   ref *Question 7*

    def discharge_cap_rule(m, t):
        return m.discharge[t] + m.response_up[t] <= params["Pmax"] # battery cant dischange faster than 50MW           ref *Question 7*

    def soc_bounds_rule(m, t):
        return (params["soc_min"], m.soc[t], params["soc_max"]) #  soc_min <= m.soc[t] <= soc_max, battery stays within the healthy range       ref *Question 7*

    def soc_balance_rule(m, t):
        if t == T_last:
            return Constraint.Skip  # reached the end, can't write soc[t+1] for the last t
        return m.soc[t + 1] == (
            m.soc[t] # current energy stored in battery
            + params["eta_c"] * m.charge[t] * params["dt"] # energy in (observed), efficiency * Power * time step           ref *Question 7*
            - (1.0 / params["eta_d"]) * m.discharge[t] * params["dt"]) # energy out (observed) , efficiency * Power * time step === to deliver X MWh to grid you must remove X/eta from battery SoC             ref *Question 7*

    def up_response_energy_rule (m,t): # ensure theres enough energy for the reserve for length of tau (Reserve + SoC_min)
        return m.soc[t] - params["soc_min"] >= (1.0 / params["eta_d"]) * m.response_up[t] * params["tau"]

    def down_response_energy_rule(m, t): # enough theres headroom below soc_max to absorb r_down for tau
        return params["soc_max"] - m.soc[t] >= params["eta_c"] * m.response_down[t] * params["tau"]

    # ================================== Finanical rules =========================================================

    # *Question 9* does throughput_cost give a dynamic cost? does it degredate finacnial inline with the metrics above? 
    # how much money the battery makes from discharging or costs from charging      
    def profit_rule(m): # ref *Question 2/3*
        revenue_arb = sum(m.price[t] * (m.discharge[t] - m.charge[t]) * params["dt"] for t in m.T) # revenue from arbitrage ref *Question 7*
        penalty_arb = sum(throughput_cost * (m.charge[t] + m.discharge[t]) * params["dt"] for t in m.T) # degradation cost from arbitrage ref *Question 7*
        revenue_response = sum(
    (
        m.response_up_price[t] * m.response_up[t]
        + m.response_down_price[t] * m.response_down[t]
    ) * params["dt"]
    for t in m.T
)
        #penalty_res = sum(throughput_cost * (m.charge[t] + m.discharge[t]) * params["dt"] for t in m.T) # degradation cost from ancillary ref *Question 7*
        revenue = revenue_arb + revenue_response
        penalty = penalty_arb # + penalty_res (need to track the amount of energy discharged through ancillary)
        return revenue - penalty


    # these will probably need to be changed based on above questions. dont fully understande the 'mechanics' of the solve yet to know how these get feedback in the objective funcution 


    m.charge_cap = Constraint(m.T, rule=charge_cap_rule)
    m.discharge_cap = Constraint(m.T, rule=discharge_cap_rule)
    m.soc_bounds = Constraint(m.T, rule=soc_bounds_rule)
    m.soc_balance = Constraint(m.T, rule=soc_balance_rule)
    m.soc_init = Constraint(expr=m.soc[0] == params["soc_init"])
    m.throughput_cap = Constraint(expr=sum((m.charge[t] + m.discharge[t]) * params["dt"] for t in m.T) <= throughput_cap)
    m.up_response_energy = Constraint(m.T, rule=up_response_energy_rule)
    m.down_response_energy = Constraint(m.T, rule=down_response_energy_rule)

    m.obj = Objective(rule=profit_rule, sense=maximize)

    return m, params, throughput_cost


def solve_dispatch_model(model):
    solver = SolverFactory("highs")
    solver.solve(model)
    return model


def extract_dispatch_results(model, params, throughput_cost):
    results = pd.DataFrame(
        index=list(model.T),
        data={
            "price": [value(model.price[t]) for t in model.T],
            "charge_mw": [value(model.charge[t]) for t in model.T],
            "discharge_mw": [value(model.discharge[t]) for t in model.T],
            "soc_mwh": [value(model.soc[t]) for t in model.T],
            "response_up": [value(model.response_up[t]) for t in model.T],
            "response_down": [value(model.response_down[t]) for t in model.T],
            "response_up_price": [value(model.response_up_price[t]) for t in model.T],
            "response_down_price": [value(model.response_down_price[t]) for t in model.T],
        },
    )

    results["net_mw"] = results["discharge_mw"] - results["charge_mw"]
    results["throughput_mwh"] = (results["charge_mw"] + results["discharge_mw"]) * params["dt"]
    results["energy_gbp"] = (results["price"] * (results["discharge_mw"] - results["charge_mw"]) * params["dt"])
    results["response_gbp"] = (
    (
        results["response_up_price"] * results["response_up"]
        + results["response_down_price"] * results["response_down"]
    ) * params["dt"]
)
    results["penalty_gbp"] = throughput_cost * results["throughput_mwh"]
    results["gross_gbp"] = results["energy_gbp"] + results["response_gbp"]
    results["net_gbp"] = results["gross_gbp"] - results["penalty_gbp"]

    summary = {
        "objective_gbp": value(model.obj),
        "gross_energy_margin_gbp": results["gross_gbp"].sum(),
        "energy_revenue_gbp": results["energy_gbp"].sum(),
        "response_revenue_gbp": results["response_gbp"].sum(),
        "degradation_cost_gbp": results["penalty_gbp"].sum(),
        "net_objective_gbp": results["net_gbp"].sum(),
    }

    return {
        "dispatch": results,
        "summary": summary,
    }

def run_dispatch_model(price_series=None):
    
    model, params, throughput_cost = build_dispatch_model(price_series)

    model = solve_dispatch_model(model)

    results = extract_dispatch_results(model, params, throughput_cost)

    return results