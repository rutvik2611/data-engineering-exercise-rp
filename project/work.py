import os
import numpy as np
import pandas as pd
from tkinter import Tk, filedialog
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, RangeSlider, Div
from bokeh.plotting import figure, show
from scipy.optimize import curve_fit
from bokeh.io import curdoc

# Global variable to display parameters
param_div = Div(text="")  # Initialize with an empty string

# Function to load data from a file
def load_data():
    default_file = "New S1 50nm.txt"

    if os.path.exists(default_file):
        file_path = default_file
        print(f"Loading default file: {file_path}")
    else:
        Tk().withdraw()  # Hide the main Tkinter window
        file_path = filedialog.askopenfilename(title="Select data file",
                                               filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"),
                                                          ("All files", "*.*")])
        if not file_path:
            print("No file selected.")
            return None, None, None

    data = pd.read_table(file_path, delim_whitespace=True, header=None)
    print("Data loaded from file:\n", data)

    x_data = data.iloc[:, 0].values  # First column (1/Temp)
    y_data = data.iloc[:, 1].values  # Second column (intensity ratio)
    y_error = data.iloc[:, 2].values  # Third column (error in intensity ratio)

    return x_data, y_data, y_error

# Define a non-linear model (e.g., quadratic)
def nonlinear_model(x, c1, c2, b):
    return (-c1 * ((1 / x) - 366.15) / (c2 + (1 / x) - 366.15)) + b

# Function to fit model and update parameters
def fit_model(x_data, y_data, y_error):
    global param_div  # Refer to the global param_div so we can modify it

    # Fit the data using the nonlinear_model function
    popt, pcov = curve_fit(nonlinear_model, x_data, y_data, sigma=y_error, absolute_sigma=True)

    # Display the optimal parameters and covariance in the console
    print("Optimal parameters (popt):", popt)
    print("Covariance of parameters (pcov):", pcov)

    # Update the param_div text to display in the Bokeh interface
    param_div.text = f"<b>Optimal parameters (popt):</b> {popt}<br><b>Covariance of parameters (pcov):</b> {pcov}"

    return popt

if __name__ == "__main__":
    # Load the data
    x_data, y_data, y_error = load_data()

    if x_data is not None and y_data is not None and y_error is not None:
        print("Starting curve fitting process...")

        # Prepare initial data
        source = ColumnDataSource(data=dict(x=x_data, y=y_data, y_fit=y_data))
        plot = figure(title="Data and Fitted Curve", x_axis_label='1/Temp', y_axis_label='Intensity Ratio')
        plot.circle('x', 'y', source=source, size=5, color="navy", alpha=0.5, legend_label="Data")
        plot.line('x', 'y_fit', source=source, line_width=2, color="firebrick", legend_label="Fitted Curve")

        # Range slider for x_data
        x_min = min(x_data)
        x_max = max(x_data)
        range_slider = RangeSlider(start=x_min, end=x_max, value=(x_min, x_max), step=(x_max - x_min) / 100,
                                   title="Select x_data Range")

        # Callback to update the plot based on the slider range
        def update_plot(attr, old, new):
            range_start, range_end = range_slider.value
            mask = (x_data >= range_start) & (x_data <= range_end)
            filtered_x = x_data[mask]
            filtered_y = y_data[mask]
            filtered_y_error = y_error[mask]

            if len(filtered_x) > 3:  # Ensure enough data points for fitting
                popt = fit_model(filtered_x, filtered_y, filtered_y_error)
                fitted_curve = nonlinear_model(filtered_x, *popt)

                # Update the data source
                source.data = dict(x=filtered_x, y=filtered_y, y_fit=fitted_curve)
            else:
                param_div.text = "<b>Not enough data points in the selected range to fit a curve.</b>"

        # Attach the callback to the range slider
        range_slider.on_change("value", update_plot)

        # Layout with param_div, range_slider, and plot
        layout = column(param_div, range_slider, plot)
        curdoc().add_root(layout)

        # Show the plot in a browser (for standalone script use)
        show(layout)
    else:
        print("Data loading failed. Exiting program.")
