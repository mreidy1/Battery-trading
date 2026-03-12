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