# Battery trading

## Overview

This repository contains a battery energy storage system (BESS) trading model developed to explore optimisation-based dispatch strategies in wholesale electricity markets.

The project focuses on building a simplified trading framework for a utility-scale battery, combining electricity price signals with operational constraints to determine optimal charge, discharge, and reserve participation decisions.

The model is implemented using Python and Pyomo and solves a linear optimisation problem to maximise battery revenue subject to power limits, state-of-charge constraints, and degradation costs.

## Learning Objectives

This project is part of an ongoing effort to build practical experience in electricity market modelling and optimisation. Key areas of focus include:

• Learning linear programming and optimisation techniques for energy systems

• Implementing dispatch optimisation using Pyomo

• Modelling battery operational constraints such as power limits, state-of-charge dynamics, and cycling limits

• Exploring the interaction between energy arbitrage and ancillary service markets

• Developing a structured codebase for energy trading simulations

The longer-term objective is to extend the model toward a simplified trading architecture, including price forecasting, rolling optimisation, and market participation strategies.

## Model Architecture

The optimisation model determines the battery dispatch schedule that maximises total revenue across energy and reserve markets.

The model includes:

• Energy arbitrage based on wholesale electricity prices
• Reserve capacity provision (frequency response / balancing services)
• Battery state-of-charge dynamics
• Power and energy capacity constraints
• Degradation costs associated with battery throughput

The optimisation problem is formulated as a linear program and solved using the HiGHS solver through Pyomo.

## Model Workflow

The model follows a structured workflow:

1.Input electricity price data

2.Construct optimisation model

3.Solve the dispatch problem

4.Extract operational and financial results

5.Visualise battery operation and revenue streams

Future versions of the model will incorporate price forecasting and rolling optimisation to better replicate real trading environments.

## Repository Structure

battery_trading
│

run_model.py – main script used to run the optimisation

optimisation/ – battery dispatch optimisation model

plotting/ – visualisation of dispatch and revenue results

data/ – price input data (future development)

## Future Development

Planned extensions include:

• Integration of real electricity market price data

• Price forecasting models for trading decisions

• Rolling horizon optimisation

• Additional market services such as balancing and frequency response

• Performance metrics for evaluating trading strategies
