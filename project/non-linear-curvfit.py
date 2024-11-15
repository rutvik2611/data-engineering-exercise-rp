# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 22:36:32 2024

@author: syada27
"""
import os

import numpy as np
import pandas as pd
from tkinter import Tk, filedialog
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider, CustomJS, Div
from bokeh.plotting import figure, show
from scipy.optimize import curve_fit
from bokeh.io import curdoc


# Define your model function
def model_func(x, c1, c2, b):
    return (-c1 * ((1 / x) - 366.15) / (c2 + (1 / x) - 366.15)) + b


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
    x_data = data.iloc[:, 0].values  # First column (1/Temp)
    y_data = data.iloc[:, 1].values  # Second column (intensity ratio)
    y_error = data.iloc[:, 2].values  # Third column (error in intensity ratio)

    return x_data, y_data, y_error

# Perform the curve fitting
def fit_model(x, y, y_error):
    popt, pcov = curve_fit(model_func, x, y, sigma=y_error, absolute_sigma=True)
    return popt, pcov



# Load the data
x_data, y_data, y_error = load_data()

# Create a Bokeh plot
plot = figure(title="Fitted Model", x_axis_label="1/Temp (1/Kelvin)", y_axis_label="Intensity Ratio",
              tools="pan,box_zoom,reset,wheel_zoom")


print(type(plot))
# <class 'bokeh.plotting._figure.figure'>
print(plot)




# Initially fit the model on the whole data
popt, pcov = fit_model(x_data, y_data, y_error)
print("Fitted parameters:", popt)
y_fit = model_func(x_data, *popt)

# Create ColumnDataSource for the original data and fitted curve
data = ColumnDataSource(data=dict(x=x_data, y=y_data, yerr=y_error))
bf_data = ColumnDataSource(data=dict(x=x_data, y=model_func(x_data, *popt)))  # Fitted data source
coords_1 = ColumnDataSource(data=dict(x=[0, 0], y=[min(y_data), max(y_data)]))  # Slider start indicator
coords_2 = ColumnDataSource(data=dict(x=[0, 0], y=[min(y_data), max(y_data)]))  # Slider end indicator
source_fit = ColumnDataSource(data=dict(x=x_data, y=y_fit))

# Plot the original data with error bars
plot.circle('x', 'y', size=5, color="blue", alpha=0.6, source=data)

# Plot the fitted curve (initially)
plot.line('x', 'y', source=source_fit, line_width=2, color="red", legend_label="Fitted Curve")

# Create sliders for selecting the fitting range
slider_1 = Slider(start=0, end=len(x_data) - 1, value=0, step=1, title="Start Index")
slider_2 = Slider(start=0, end=len(x_data) - 1, value=len(x_data) - 1, step=1, title="End Index")

callback_args = {
    'data': data,
    'bf_data': bf_data,
    'slider_1': slider_1,
    'slider_2': slider_2,
    'coords_1': coords_1,
    'coords_2': coords_2
}

callback = CustomJS(args=callback_args, code="""
    function model_func(x, c1, c2, b) {
        return (-c1 * ((1 / x) - 366.15) / (c2 + (1 / x) - 366.15)) + b;
    }

    function residuals(x_vals, y_vals, c1, c2, b) {
        let res = 0;
        for (let i = 0; i < x_vals.length; i++) {
            res += Math.pow(y_vals[i] - model_func(x_vals[i], c1, c2, b), 2);
        }
        return res;
    }

    function fitNonLinear(x_vals, y_vals, initial_c1, initial_c2, initial_b) {
        let c1 = initial_c1;
        let c2 = initial_c2;
        let b = initial_b;

        const learning_rate = 0.0001;
        const tolerance = 1e-6;
        const max_iter = 5000;

        let prev_res = Infinity;

        for (let iter = 0; iter < max_iter; iter++) {
            let current_res = residuals(x_vals, y_vals, c1, c2, b);
            if (Math.abs(prev_res - current_res) < tolerance) break;
            prev_res = current_res;

            let delta = 1e-5;
            let res_c1 = (residuals(x_vals, y_vals, c1 + delta, c2, b) - current_res) / delta;
            let res_c2 = (residuals(x_vals, y_vals, c1, c2 + delta, b) - current_res) / delta;
            let res_b = (residuals(x_vals, y_vals, c1, c2 , b + delta) - current_res) / delta;

            c1 -= learning_rate * res_c1;
            c2 -= learning_rate * res_c2;
            b -= learning_rate * res_b;
        }

        return [c1, c2, b];
    }

    function getInbetweens(data_source, slider_min, slider_max) {
        const start_index = slider_min.value;
        const end_index = slider_max.value;

        const output_x = [];
        const output_y = [];

        for (let i = start_index; i <= end_index; i++) {
            output_x.push(data_source.data['x'][i]);
            output_y.push(data_source.data['y'][i]);
        }

        return [output_x, output_y];
    }

    function updateFittedCurve(fit_source, x_vals, c1, c2, b) {
        fit_source.data['x'] = x_vals;
        fit_source.data['y'] = x_vals.map(x => model_func(x, c1, c2, b));
        fit_source.change.emit();
    }

    function updateCoords(slider, coords) {
        coords.data['x'] = [slider.value, slider.value];
        coords.change.emit();
    }

    updateCoords(slider_1, coords_1);
    updateCoords(slider_2, coords_2);

    const interval_data = getInbetweens(data, slider_1, slider_2);

    if (interval_data[0].length >= 2) {
        const initial_c1 = 10.0;
        const initial_c2 = 10.0;
        const initial_b = 10.0;

        // Perform the non-linear fit on the interval data
        const [c1, c2, b] = fitNonLinear(interval_data[0], interval_data[1], initial_c1, initial_c2, initial_b);

        // Update the fitted curve source with new parameters
        updateFittedCurve(source_fit, interval_data[0], c1, c2, b);
    }
""");
# Attach the callback to the sliders
slider_1.js_on_change('value', callback)
slider_2.js_on_change('value', callback)

# Layout the plot and sliders
layout = column(plot, slider_1, slider_2)

# Show the layout in the browser
show(layout)