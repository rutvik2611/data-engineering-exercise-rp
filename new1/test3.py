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

    data = pd.read_table(file_path, delim_whitespace=True, header=None)
    x_data = data.iloc[:, 0].values
    y_data = data.iloc[:, 1].values
    y_error = data.iloc[:, 2].values
    return x_data, y_data, y_error

# Nonlinear model for fitting
def nonlinear_model(x, c1, c2, b):
    return (-c1 * ((1 / x) - 366.15) / (c2 + (1 / x) - 366.15)) + b

# Fit model function
def fit_model(x_data, y_data, y_error):
    popt, pcov = curve_fit(nonlinear_model, x_data, y_data, sigma=y_error, absolute_sigma=True)
    return popt

# Initialize Dash app
app = dash.Dash(__name__)

# Layout with sliders
app.layout = html.Div([
    html.H1("Data and Fitted Curve"),
    dcc.Graph(id='graph'),
    dcc.Slider(
        id='start-slider',
        min=0,
        max=50,  # Max value should be the length of your data
        step=1,
        value=0,
        marks={i: str(i) for i in range(0, 51, 10)},
    ),
    dcc.Slider(
        id='end-slider',
        min=1,
        max=51,  # Max value should be the length of your data + 1
        step=1,
        value=50,
        marks={i: str(i) for i in range(1, 51, 10)},
    ),
    html.Div(id='param-div')
])

# Callback to update graph and parameters
@app.callback(
    [Output('graph', 'figure'),
     Output('param-div', 'children')],
    [Input('start-slider', 'value'),
     Input('end-slider', 'value')]
)
def update_graph(start, end):
    # Load data and fit model
    x_data, y_data, y_error = load_data()
    if x_data is None:
        return {}, "No data available."

    # Slice data based on slider input
    x_sliced = x_data[start:end]
    y_sliced = y_data[start:end]
    y_error_sliced = y_error[start:end]

    # Fit model
    popt = fit_model(x_sliced, y_sliced, y_error_sliced)

    # Prepare figure with plotly
    y_fit = nonlinear_model(x_sliced, *popt)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_sliced, y=y_sliced, mode='markers', name='Data', marker=dict(color='navy')))
    fig.add_trace(go.Scatter(x=x_sliced, y=y_fit, mode='lines', name='Fitted Curve', line=dict(color='firebrick')))
    fig.update_layout(title="Data and Fitted Curve", xaxis_title="1/Temp", yaxis_title="Intensity Ratio")

    # Display parameters
    param_text = f"Optimal parameters (popt): {popt}"
    return fig, param_text

if __name__ == '__main__':
    app.run_server(debug=True)

# Comments:
# 1. Dash allows you to zoom into a subset of the data using start and end sliders.
#    The sliders are linked to the callback function, which dynamically updates the data shown in the plot.
#    At any given point, the plot will display both the selected data and the corresponding fitted curve for that subset of the data.
#    This ensures the fitting process reflects only the data visible in the current view, making it more accurate for zoomed-in sections.
#    The sliders show the start and end indices of the data subset being visualized, allowing for precise control over the data range.

# 2. The fit model and its parameters are recalculated and displayed dynamically as the sliders are adjusted.
#    The callback function handles the slicing of the data and updates the fit model based on the sliced data.
#    As the user adjusts the sliders, the fitting model is recalculated to match the new data range, ensuring the fitted curve reflects the current data subset.

# 3. The slider values are connected to a Python callback that slices the data and refits the curve for that specific data range.
#    The curve fitting process runs entirely in Python, allowing for more flexibility and integration with your model.
#    The Python environment manages both the data processing and the fitting, providing a seamless user experience.

# 4. As the slider values are adjusted, the fitting function is triggered, and the updated fit curve is drawn with the new parameters.
#    Dash automatically handles the updating of the plot, so the user sees the results of the recalculated fitted curve as they adjust the sliders.
#    This interaction is efficient, ensuring the plot is responsive without significant overhead.
