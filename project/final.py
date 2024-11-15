import os
import numpy as np
import pandas as pd
from tkinter import Tk, filedialog
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, CustomJS, Div
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

# Function to fit model and display results with error handling
def fit_model(x_data, y_data, y_error):
    try:
        popt, _ = curve_fit(nonlinear_model, x_data, y_data, sigma=y_error, absolute_sigma=True)
        return popt  # Return the optimal parameters
    except Exception as e:
        # In case of error, print the error and return dummy parameters
        print(f"Error during fitting: {e}")
        return [1, 1, 1]  # Return dummy parameters (c1, c2, b)

# Pre-calculate fitted curves for all possible slices with error handling
def precompute_fitted_curves(x_data, y_data, y_error):
    fitted_curves = {}
    for start in range(len(x_data)):
        for end in range(start + 1, len(x_data) + 1):
            x_sliced = x_data[start:end]
            y_sliced = y_data[start:end]
            y_error_sliced = y_error[start:end]
            popt = fit_model(x_sliced, y_sliced, y_error_sliced)
            if popt != [1, 1, 1]:  # Check if fitting was successful
                y_fit = nonlinear_model(x_sliced, *popt)
            else:
                # If fitting failed, generate dummy data (e.g., flat line at the average y-value)
                y_fit = np.full_like(y_sliced, np.mean(y_sliced))
            fitted_curves[(start, end)] = (x_sliced, y_sliced, y_fit)  # Store both raw and fitted data
    return fitted_curves

# Main program
x_data, y_data, y_error = load_data()

if x_data is not None and y_data is not None and y_error is not None:
    print("Starting curve fitting process...")

    # Pre-compute fitted curves for all combinations of start and end
    fitted_curves = precompute_fitted_curves(x_data, y_data, y_error)

    # Prepare data for Bokeh plot
    source = ColumnDataSource(data=dict(x=x_data, y=y_data))  # Raw data (no fitted curve initially)

    # Create plot
    plot = figure(title="Data", x_axis_label='1/Temp', y_axis_label='Intensity Ratio')
    plot.circle('x', 'y', source=source, size=5, color="navy", alpha=0.5, legend_label="Data")

    # Create sliders for start and end
    start_slider = Slider(start=0, end=len(x_data) - 1, value=0, step=1, title="Start Index")
    end_slider = Slider(start=1, end=len(x_data), value=len(x_data), step=1, title="End Index")

    # JavaScript callback to update data on slider change
    callback = CustomJS(args=dict(source=source, start_slider=start_slider, end_slider=end_slider,
                                  param_div=param_div, fitted_curves=fitted_curves),
                        code="""
        const start = start_slider.value;
        const end = end_slider.value;

        // Fetch the precomputed fitted data for the current slice
        const fitData = fitted_curves[`${start},${end}`];
        const x_sliced = fitData[0];
        const y_sliced = fitData[1];
        const y_fit = fitData[2];

        // Update data source with sliced data and fitted curve
        source.data = { x: x_sliced, y: y_sliced, y_fit: y_fit };
        source.change.emit();

        // Optionally update the parameter display (if needed)
        param_div.text = "<b>Parameters (popt):</b> " + fitData[0].toString();
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
