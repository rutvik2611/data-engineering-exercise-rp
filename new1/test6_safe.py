import os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# Load data function
def load_data():
    default_file = "New S1 50nm.txt"
    if os.path.exists(default_file):
        file_path = default_file
        print(f"Loading default file: {file_path}")
    else:
        print("No file selected.")
        return None, None, None

    # Read data from the text file
    data = pd.read_table(file_path, sep='\s+', header=None)
    x_data = data.iloc[:, 0].values  # Independent variable (x)
    y_data = data.iloc[:, 1].values  # Dependent variable (y)
    y_error = data.iloc[:, 2].values  # Error for y
    return x_data, y_data, y_error

# Nonlinear model for fitting (to match your example)
def nonlinear_model(x, c1, c2, b):
    return (-c1 * ((1 / x) - 366.15) / (c2 + (1 / x) - 366.15)) + b

# Fit model function using curve_fit from SciPy (Levenberg-Marquardt)
def fit_model(x_data, y_data, y_error):
    # Perform the curve fitting using Levenberg-Marquardt (default in curve_fit)
    popt, pcov = curve_fit(nonlinear_model, x_data, y_data, sigma=y_error, absolute_sigma=True)
    return popt, pcov  # Return optimal parameters and their covariance matrix

# Initialize Dash app
app = dash.Dash(__name__)

# Layout with a single slider
app.layout = html.Div([
    html.H1("Data and Fitted Curve"),
    dcc.Graph(id='graph'),
    dcc.RangeSlider(
        id='range-slider',
        min=0,
        max=100,  # Placeholder; will be dynamically set
        step=1,
        value=[0, 50],  # Initial value
        marks={0: '0'},  # Placeholder; will be dynamically set
    ),
    html.Div(id='range-info'),
    html.Div(id='param-div'),
    html.Div(id='current-params', style={'marginTop': '20px'})  # To display current values of c1, c2, and b
])

# Callback to update graph and parameters
@app.callback(
    [Output('graph', 'figure'),
     Output('param-div', 'children'),
     Output('range-slider', 'min'),
     Output('range-slider', 'max'),
     Output('range-slider', 'marks'),
     Output('range-info', 'children'),
     Output('current-params', 'children')],  # Add output for current parameter values
    [Input('range-slider', 'value')]
)
def update_graph(selected_range):
    # Load data and fit model
    x_data, y_data, y_error = load_data()
    if x_data is None:
        return {}, "No data available.", 0, 0, {}, "No data available.", "No data available."

    # Update slider range dynamically
    n_data_points = len(x_data)
    slider_marks = {i: str(i) for i in range(0, n_data_points, max(1, n_data_points // 10))}

    # Slice data based on selected range
    start, end = selected_range
    x_sliced = x_data[start:end]
    y_sliced = y_data[start:end]
    y_error_sliced = y_error[start:end]

    # Fit model
    popt, pcov = fit_model(x_sliced, y_sliced, y_error_sliced)

    # Prepare figure with plotly
    y_fit = nonlinear_model(x_sliced, *popt)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='markers', name='Full Data', marker=dict(color='lightgray')))
    fig.add_trace(go.Scatter(x=x_sliced, y=y_sliced, mode='markers', name='Selected Data', marker=dict(color='navy')))
    fig.add_trace(go.Scatter(x=x_sliced, y=y_fit, mode='lines', name='Fitted Curve', line=dict(color='firebrick')))
    fig.update_layout(title="Data and Fitted Curve", xaxis_title="1/Temp", yaxis_title="Intensity Ratio")

    # Display parameters and range info
    param_text = f"Optimal parameters (popt): {popt}, Covariance: {pcov}"
    range_info = f"Full Range: (0, {n_data_points - 1}), Selected Range: ({start}, {end})"

    # Show current values of c1, c2, and b
    c1, c2, b = popt  # Extract values of c1, c2, and b
    param_display = f"Current Parameter Values: c1 = {c1:.4f}, c2 = {c2:.4f}, b = {b:.4f}"

    return fig, param_text, 0, n_data_points - 1, slider_marks, range_info, param_display

if __name__ == '__main__':
    app.run_server(debug=True)
