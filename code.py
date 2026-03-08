import streamlit as st
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go

# --- Configuration ---
st.set_page_config(page_title="Safety Stock Derivation Visualizer", layout="wide")

st.title("🧮 Visual Derivation: The Safety Stock Formula")
st.markdown("""
This tool visualizes the mathematical derivation of Safety Stock step-by-step.
It connects the **Normal Distribution** (Bell Curve) to the formula used in business:
$$Safety\ Stock \\approx z \\times 1.25 \\times MAPE \\times R \\times \\sqrt{L}$$
""")

# --- Sidebar Inputs ---
st.sidebar.header("1. Input Variables")
R = st.sidebar.number_input("Average Weekly Demand (R)", value=59.0, step=1.0)
L = st.sidebar.number_input("Lead Time in Weeks (L)", value=16.0, step=1.0)
MAPE = st.sidebar.slider("Forecast Error (MAPE)", 0.0, 1.0, 0.40, step=0.01)
CSL = st.sidebar.slider("Target Service Level (%)", 50.0, 99.9, 95.0, step=0.1)

# --- Step-by-Step Derivation Logic ---

# Step 1: Mean Absolute Deviation (MAD)
# Logic: MAPE is just error percentage. MAD is the actual unit error per week.
MAD = R * MAPE 

# Step 2: Standard Deviation (1 Week)
# Logic: approx conversion for normal distribution: Sigma approx 1.25 * MAD
sigma_1 = 1.25 * MAD

# Step 3: Standard Deviation (Lead Time)
# Logic: Variances add linearly. Std Dev scales by sqrt(L).
sigma_L = sigma_1 * np.sqrt(L)

# Step 4: Z-Score
# Logic: The number of standard deviations needed to cover the Service Level % area.
z_score = stats.norm.ppf(CSL / 100)

# Step 5: Final Safety Stock
safety_stock = z_score * sigma_L

# Reorder Point (for visualization)
demand_during_lead_time = R * L
reorder_point = demand_during_lead_time + safety_stock

# --- Layout: The Derivation Pipeline ---
st.header("1. The Mathematical Pipeline")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.info("**Step 1: Raw Error**")
    st.latex(f"MAD = R \\times MAPE")
    st.latex(f"{R} \\times {MAPE:.2f} = {MAD:.1f}")
    st.caption("Average error in units per week.")

with c2:
    st.info("**Step 2: To Sigma**")
    st.latex(f"\\sigma_1 \\approx 1.25 \\times MAD")
    st.latex(f"1.25 \\times {MAD:.1f} = {sigma_1:.1f}")
    st.caption("Convert MAD to Std Dev (Normal Dist property).")

with c3:
    st.info("**Step 3: Scale Time**")
    st.latex(f"\\sigma_L = \\sigma_1 \\times \\sqrt{{L}}")
    st.latex(f"{sigma_1:.1f} \\times {np.sqrt(L):.1f} = {sigma_L:.1f}")
    st.caption("Errors accumulate over lead time (Random Walk).")

with c4:
    st.info("**Step 4: Risk (Z)**")
    st.latex(f"Z_{{{CSL}\\%}} = {z_score:.2f}")
    st.caption(f"Standard deviations needed to cover {CSL}% of the curve.")

with c5:
    st.success("**Step 5: Result**")
    st.latex(f"SS = Z \\times \\sigma_L")
    st.latex(f"{z_score:.2f} \\times {sigma_L:.1f} = \\mathbf{{{int(safety_stock)}}}")
    st.caption("Final Safety Stock Units.")

st.divider()

# --- Visualization: The Normal Distribution ---
st.header("2. Visualizing the 'Why'")

# Generate Distribution Data
x = np.linspace(demand_during_lead_time - 4*sigma_L, demand_during_lead_time + 4*sigma_L, 1000)
y = stats.norm.pdf(x, demand_during_lead_time, sigma_L)

# Create Plot
fig = go.Figure()

# 1. The Full Bell Curve
fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Demand Probability', line=dict(color='gray'), fill='tozeroy'))

# 2. The "Service Level" Area (Green)
# This represents the scenarios where we have enough stock.
x_safe = np.linspace(demand_during_lead_time - 4*sigma_L, reorder_point, 1000)
y_safe = stats.norm.pdf(x_safe, demand_during_lead_time, sigma_L)
fig.add_trace(go.Scatter(x=x_safe, y=y_safe, mode='lines', fill='tozeroy', name=f'Service Level ({CSL}%)', line=dict(width=0), fillcolor='rgba(0, 200, 0, 0.3)'))

# 3. The "Stockout" Area (Red)
x_risk = np.linspace(reorder_point, demand_during_lead_time + 4*sigma_L, 1000)
y_risk = stats.norm.pdf(x_risk, demand_during_lead_time, sigma_L)
fig.add_trace(go.Scatter(x=x_risk, y=y_risk, mode='lines', fill='tozeroy', name=f'Stockout Risk ({100-CSL:.1f}%)', line=dict(width=0), fillcolor='rgba(200, 0, 0, 0.5)'))

# 4. Vertical Line: Expected Demand (Mean)
fig.add_vline(x=demand_during_lead_time, line_width=2, line_dash="dash", line_color="black", annotation_text="Avg Demand")

# 5. Vertical Line: Reorder Point
fig.add_vline(x=reorder_point, line_width=3, line_color="blue", annotation_text=f"Reorder Point\n(Avg + {int(safety_stock)} SS)")

# Layout Polish
fig.update_layout(
    title="Probability Distribution of Demand During Lead Time",
    xaxis_title="Total Units Demanded during Lead Time",
    yaxis_title="Probability Density",
    height=500,
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

# --- Explanation Text ---
st.markdown(f"""
### How to Read This Graph
1.  **The Center (Dotted Line):** This is your **Average Demand during Lead Time** ({int(demand_during_lead_time)} units). If you only ordered this amount, you would stock out 50% of the time (whenever demand is above average).
2.  **The Blue Line (Reorder Point):** We shift this line to the right to create a buffer. The distance between the Center and the Blue Line is your **Safety Stock** ({int(safety_stock)} units).
3.  **The Green Area:** By adding that safety stock, we cover **{CSL}%** of all possible demand scenarios (the area under the curve).
4.  **The Red Area:** This represents the statistical probability ({100-CSL:.1f}%) that demand will be so unusually high that it exceeds even your safety buffer.
""")
