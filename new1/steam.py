import os

import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
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

# Streamlit layout
st.title('Data and Fitted Curve')

# Load data
x_data, y_data, y_error = load_data()

if x_data is not None:
    start = st.slider('Start Index', 0, len(x_data)-1, 0)
    end = st.slider('End Index', start+1, len(x_data), len(x_data))

    # Slice data
    x_sliced = x_data[start:end]
    y_sliced = y_data[start:end]
    y_error_sliced = y_error[start:end]

    # Fit the model
    popt = fit_model(x_sliced, y_sliced, y_error_sliced)

    # Plot with Plotly
    y_fit = nonlinear_model(x_sliced, *popt)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_sliced, y=y_sliced, mode='markers', name='Data', marker=dict(color='navy')))
    fig.add_trace(go.Scatter(x=x_sliced, y=y_fit, mode='lines', name='Fitted Curve', line=dict(color='firebrick')))
    fig.update_layout(title="Data and Fitted Curve", xaxis_title="1/Temp", yaxis_title="Intensity Ratio")

    st.plotly_chart(fig)

    # Display optimal parameters
    st.write(f"Optimal parameters (popt): {popt}")
else:
    st.write("No data available.")
