import matplotlib.pyplot as plt

def plot_price(dispatch_df):
    plt.figure()
    plt.plot(dispatch_df.index, dispatch_df["price"])
    plt.title("Price (£/MWh)")
    plt.xlabel("Time step")
    plt.ylabel("£/MWh")
    plt.grid(True)


def plot_soc(dispatch_df):
    plt.figure()
    plt.plot(dispatch_df.index, dispatch_df["soc_mwh"])
    plt.title("State of Charge (MWh)")
    plt.xlabel("Time step")
    plt.ylabel("MWh")
    plt.grid(True)


def plot_dispatch(dispatch_df):
    plt.figure()
    plt.plot(dispatch_df.index, dispatch_df["net_mw"])
    plt.axhline(0)
    plt.title("Battery Dispatch (MW)")
    plt.xlabel("Time step")
    plt.ylabel("MW (+ discharge, - charge)")
    plt.grid(True)


def plot_reserve_up(dispatch_df):
    plt.figure()
    plt.plot(dispatch_df.index, dispatch_df["response_up"])
    plt.axhline(0)
    plt.title("Reserve UP (MW)")
    plt.xlabel("Time step")
    plt.ylabel("Reserve UP Power (MW)")
    plt.grid(True)


def plot_reserve_down(dispatch_df):
    plt.figure()
    plt.plot(dispatch_df.index, dispatch_df["response_down"])
    plt.axhline(0)
    plt.title("Reserve Down (MW)")
    plt.xlabel("Time step")
    plt.ylabel("Reserve Down Power (MW)")
    plt.grid(True)


def plot_all_results(dispatch_df):
    plot_price(dispatch_df)
    plot_soc(dispatch_df)
    plot_dispatch(dispatch_df)
    plot_reserve_up(dispatch_df)
    plot_reserve_down(dispatch_df)
    plt.show()