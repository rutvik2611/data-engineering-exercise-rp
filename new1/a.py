import numpy as np
import pandas as pd
from tkinter import Tk, filedialog
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider, CustomJS
from bokeh.plotting import figure, show
from scipy.optimize import curve_fit


# Define the model function
def model_func(x, c1, c2, b):
    return (-c1 * ((1 / x) - 366.15) / (c2 + (1 / x) - 366.15)) + b


# Load data from a file
def load_data():
    Tk().withdraw()
    file_path = filedialog.askopenfilename(title="Select data file")
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
    popt, _ = curve_fit(model_func, x, y, sigma=y_error, absolute_sigma=True)
    return popt


# Load the data
x_data, y_data, y_error = load_data()
if x_data is None:
    raise Exception("No data loaded")

# Initial fit on full data
initial_params = fit_model(x_data, y_data, y_error)
y_fit = model_func(x_data, *initial_params)

# Create ColumnDataSource for the original data and fitted curve
data_source = ColumnDataSource(data=dict(x=x_data, y=y_data, yerr=y_error))
fit_source = ColumnDataSource(data=dict(x=x_data, y=y_fit))

# Plot setup
plot = figure(title="Fitted Model", x_axis_label="1/Temp (1/Kelvin)", y_axis_label="Intensity Ratio")
plot.circle('x', 'y', source=data_source, size=5, color="blue", alpha=0.6)
plot.line('x', 'y', source=fit_source, line_width=2, color="red", legend_label="Fitted Curve")

# Slider for selecting fitting range
slider_1 = Slider(start=0, end=len(x_data) - 1, value=0, step=1, title="Start Index")
slider_2 = Slider(start=0, end=len(x_data) - 1, value=len(x_data) - 1, step=1, title="End Index")

# JavaScript callback to update fit with new slider range
callback = CustomJS(args=dict(data=data_source, fit_source=fit_source, slider_1=slider_1, slider_2=slider_2), code="""
    function model_func(x, c1, c2, b) {
        return (-c1 * ((1 / x) - 366.15) / (c2 + (1 / x) - 366.15)) + b;
    }

    // Enhanced gradient descent with momentum
    function fit_model(x_vals, y_vals) {
        let c1 = 0.10176, c2 = 90.0, b = 0.135;
        const learning_rate = 1e-4;
        const max_iter = 5000;
        const tolerance = 1e-6;
        const momentum = 0.9;

        let velocity = [0, 0, 0];

        for (let iter = 0; iter < max_iter; iter++) {
            let gradients = [0, 0, 0];
            let error = 0;

            for (let i = 0; i < x_vals.length; i++) {
                let x = x_vals[i];
                let y = y_vals[i];
                let y_pred = model_func(x, c1, c2, b);
                let residual = y - y_pred;

                gradients[0] += -2 * residual * ((1 / x) - 366.15) / (c2 + ((1 / x) - 366.15))**2;
                gradients[1] += -2 * residual * c1 * ((1 / x) - 366.15) / ((c2 + ((1 / x) - 366.15))**2);
                gradients[2] += -2 * residual;

                error += residual**2;
            }

            if (error < tolerance) break;

            // Update parameters with momentum
            for (let j = 0; j < gradients.length; j++) {
                velocity[j] = momentum * velocity[j] + learning_rate * gradients[j];
                if (j === 0) c1 -= velocity[j];
                else if (j === 1) c2 -= velocity[j];
                else b -= velocity[j];
            }
        }

        return [c1, c2, b];
    }

    const start_idx = slider_1.value;
    const end_idx = slider_2.value;
    const x_vals = data.data['x'].slice(start_idx, end_idx + 1);
    const y_vals = data.data['y'].slice(start_idx, end_idx + 1);

    // Calculate new parameters with selected range
    const [c1, c2, b] = fit_model(x_vals, y_vals);

    // Update fit_source with new fitted values
    fit_source.data['x'] = x_vals;
    fit_source.data['y'] = x_vals.map(x => model_func(x, c1, c2, b));
    fit_source.change.emit();
""");

# Attach the callback to the sliders
slider_1.js_on_change('value', callback)
slider_2.js_on_change('value', callback)

# Layout and show
layout = column(plot, slider_1, slider_2)
show(layout)
