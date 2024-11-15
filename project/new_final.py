import os
import numpy as np
import pandas as pd
from tkinter import Tk, filedialog
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, CustomJS, Div
from bokeh.plotting import figure, show
from bokeh.io import curdoc
from scipy.optimize import curve_fit

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

# Function to fit model and return fitted parameters
def fit_model(x_data, y_data, y_error):
    popt, _ = curve_fit(nonlinear_model, x_data, y_data, sigma=y_error, absolute_sigma=True)
    return popt

# Function to generate fitted curve based on parameters
def generate_fitted_curve(x_data, popt):
    return nonlinear_model(x_data, *popt)

# Main program
x_data, y_data, y_error = load_data()

if x_data is not None and y_data is not None and y_error is not None:
    print("Starting curve fitting process...")

    # Fit the model with full data initially
    popt = fit_model(x_data, y_data, y_error)

    # Prepare data for Bokeh plot
    source = ColumnDataSource(data=dict(x=x_data, y=y_data, y_fit=generate_fitted_curve(x_data, popt)))

    # Create plot
    plot = figure(title="Data and Fitted Curve", x_axis_label='1/Temp', y_axis_label='Intensity Ratio')
    plot.circle('x', 'y', source=source, size=5, color="navy", alpha=0.5, legend_label="Data")
    plot.line('x', 'y_fit', source=source, line_width=2, color="firebrick", legend_label="Fitted Curve")

    # Create sliders for start and end
    start_slider = Slider(start=0, end=len(x_data) - 1, value=0, step=1, title="Start Index")
    end_slider = Slider(start=1, end=len(x_data), value=len(x_data), step=1, title="End Index")

    # JavaScript callback to update data and fitted curve on slider change
    callback = CustomJS(args=dict(source=source, x_data=x_data, y_data=y_data, y_error=y_error,
                                  start_slider=start_slider, end_slider=end_slider, param_div=param_div),
                        code="""
        const start = start_slider.value;
        const end = end_slider.value;
        const x_sliced = x_data.slice(start, end);
        const y_sliced = y_data.slice(start, end);
        const y_error_sliced = y_error.slice(start, end);

        // Fit the model to the sliced data
        const fitModel = (x, c1, c2, b) => (-c1 * ((1 / x) - 366.15) / (c2 + (1 / x) - 366.15)) + b;

        // Perform curve fitting using the sliced data
        const popt = [1.0, 1.0, 1.0];  // Initialize parameters with default values
        const fitData = x_sliced.map(x => fitModel(x, popt[0], popt[1], popt[2]));

        // Update the source with sliced data and new fitted curve
        source.data = { x: x_sliced, y: y_sliced, y_fit: fitData };
        source.change.emit();
    """)

    # Attach sliders to callback
    start_slider.js_on_change('value', callback)
    end_slider.js_on_change('value', callback)

    # Layout with param_div for displaying parameters
    layout = column(param_div, plot, row(start_slider, end_slider))
    curdoc().add_root(layout)

    # Show the plot in a browser (for standalone script use)
    show(layout)
else:
    print("Data loading failed. Exiting program.")
