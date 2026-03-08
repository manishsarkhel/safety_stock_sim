import streamlit as st
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Safety Stock Derivation Visualizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Title and Intro ---
st.title("🧮 Visual Derivation: The Safety Stock Formula")
st.markdown("""
This interactive tool visualizes the mathematical derivation of Safety Stock step-by-step using **generic retail data**. 
It demonstrates how we translate a business metric (Forecast Error) into a statistical buffer (Safety Stock) using the Normal Distribution.

**The Formula:**
$$Safety\ Stock \\approx z \\times 1.25 \\times MAPE \\times R \\times \\sqrt{L}$$
""")

# --- Sidebar Inputs (Generic Data) ---
st.sidebar.header("1. Scenario Inputs")

# Using generic defaults (not case specific)
# Default: 100 units/week is a standard round number for easy visualization
R = st.sidebar.number_input(
    "Average Weekly Demand (R)", 
    value=100.0, 
    step=10.0,
    help="The average number of units sold per week."
)

# Default: 4 weeks (1 month) is a standard supply chain lead time
L = st.sidebar.number_input(
    "Lead Time in Weeks (L)", 
    value=4.0, 
    step=1.0,
    help="The time between placing an order and receiving it."
)

# Default: 20% error is a common benchmark for stable retail items
MAPE = st.sidebar.slider(
    "Forecast Error (MAPE)", 
    min_value=0.0, 
    max_value=1.0, 
    value=0.20, 
    step=0.01,
    help="Mean Absolute Percentage Error (e.g., 0.20 = 20% error)"
)

# Default: 90% is a standard starting service level
CSL = st.sidebar.slider(
    "Target Service Level (%)", 
    min_value=50.0, 
    max_value=99.9, 
    value=90.0, 
    step=0.1,
    help="The probability of NOT running out of stock during the lead time."
)

# --- Step-by-Step Derivation Logic ---

# Step 1: Mean Absolute Deviation (MAD)
# Logic: Convert percentage error into actual units per week.
MAD = R * MAPE 

# Step 2: Standard Deviation (1 Week)
# Logic: Approximation for Normal Distribution: Sigma ≈ 1.25 * MAD
# This converts the "average error" into "standard deviation".
sigma_1 = 1.25 * MAD

# Step 3: Standard Deviation (Lead Time)
# Logic: Variances add linearly over time. Standard Deviation scales by sqrt(L).
sigma_L = sigma_1 * np.sqrt(L)

# Step 4: Z-Score
# Logic: The number of standard deviations needed to cover the Service Level % area under the curve.
z_score = stats.norm.ppf(CSL / 100)

# Step 5: Final Safety Stock
safety_stock = z_score * sigma_L

# Metrics for the Graph
demand_during_lead_time = R * L
reorder_point = demand_during_lead_time + safety_stock

# --- Layout: The Mathematical Pipeline ---
st.divider()
st.header("1. The Mathematical Pipeline")
st.markdown("See how the inputs flow through the statistical transformation:")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.info("**Step 1: Unit Error**")
    st.latex(r"MAD = R \times MAPE")
    st.latex(f"{R:.0f} \\times {MAPE:.2f} = {MAD:.1f}")
    st.caption("Avg error (units/week)")

with c2:
    st.info("**Step 2: To Sigma**")
    st.latex(r"\sigma_1 \approx 1.25 \times MAD")
    st.latex(f"1.25 \\times {MAD:.1f} = {sigma_1:.1f}")
    st.caption("Std Dev per week")

with c3:
    st.info("**Step 3: Time Scaling**")
    st.latex(r"\sigma_L = \sigma_1 \times \sqrt{L}")
    st.latex(f"{sigma_1:.1f} \\times \\sqrt{{{L:.0f}}} = {sigma_L:.1f}")
    st.caption("Std Dev over Lead Time")

with c4:
    st.info("**Step 4: Risk Factor**")
    st.latex(r"Z_{" + str(CSL) + r"\%} = " + f"{z_score:.2f}")
    st.caption(f"Z-score for {CSL}%")

with c5:
    st.success("**Step 5: Result**")
    st.latex(r"SS = Z \times \sigma_L")
    st.latex(f"{z_score:.2f} \\times {sigma_L:.1f} = \\mathbf{{{int(safety_stock)}}}")
    st.caption("Final Safety Stock (Units)")

# --- Visualization: The Normal Distribution ---
st.divider()
st.header("2. Visualizing the 'Why'")
st.markdown("This bell curve represents the **probability of demand** while you are waiting for the order to arrive.")

# Generate Distribution Data for Plotting
# We plot 4 standard deviations out to capture the full tail
x_min = demand_during_lead_time - 4*sigma_L
x_max = demand_during_lead_time + 4*sigma_L
x = np.linspace(x_min, x_max, 1000)
y = stats.norm.pdf(x, demand_during_lead_time, sigma_L)

# Create Plotly Graph
fig = go.Figure()

# 1. The Full Bell Curve (Background)
fig.add_trace(go.Scatter(
    x=x, y=y, 
    mode='lines', 
    name='Demand Distribution', 
    line=dict(color='gray'), 
    fill='tozeroy',
    fillcolor='rgba(200, 200, 200, 0.2)'
))

# 2. The "Safe" Area (Green) - Matches Service Level
# This is the area from the left tail up to the Reorder Point
x_safe = np.linspace(x_min, reorder_point, 1000)
y_safe = stats.norm.pdf(x_safe, demand_during_lead_time, sigma_L)

fig.add_trace(go.Scatter(
    x=x_safe, y=y_safe, 
    mode='lines', 
    fill='tozeroy', 
    name=f'Service Level ({CSL}%)', 
    line=dict(width=0), 
    fillcolor='rgba(46, 204, 113, 0.5)' # Green
))

# 3. The "Risk" Area (Red) - Matches Stockout Probability
# This is the area from the Reorder Point to the right tail
x_risk = np.linspace(reorder_point, x_max, 1000)
y_risk = stats.norm.pdf(x_risk, demand_during_lead_time, sigma_L)

fig.add_trace(go.Scatter(
    x=x_risk, y=y_risk, 
    mode='lines', 
    fill='tozeroy', 
    name=f'Stockout Risk ({100-CSL:.1f}%)', 
    line=dict(width=0), 
    fillcolor='rgba(231, 76, 60, 0.6)' # Red
))

# 4. Vertical Line: Average Demand
fig.add_vline(
    x=demand_during_lead_time, 
    line_width=2, 
    line_dash="dash", 
    line_color="black", 
    annotation_text="Expected Demand", 
    annotation_position="top left"
)

# 5. Vertical Line: Reorder Point
fig.add_vline(
    x=reorder_point, 
    line_width=3, 
    line_color="blue", 
    annotation_text=f"Reorder Point\n(Avg + {int(safety_stock)} SS)", 
    annotation_position="top right"
)

# Layout Polish
fig.update_layout(
    title=f"Demand Distribution over {int(L)} Weeks Lead Time",
    xaxis_title="Total Units Demanded",
    yaxis_title="Probability Density",
    height=500,
    showlegend=True,
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- Explanation Text ---
st.info(f"""
### Interpretation:
* **Expected Demand:** During the {int(L)}-week lead time, you expect to sell **{int(demand_during_lead_time)} units** ({int(R)} × {int(L)}).
* **The Buffer:** However, demand varies. To protect against surges, you hold **{int(safety_stock)} extra units**.
* **The Result:** You place your reorder when stock hits **{int(reorder_point)} units**. This ensures that in **{CSL}%** of cases (Green Area), you will have enough stock until the new order arrives.
""")
