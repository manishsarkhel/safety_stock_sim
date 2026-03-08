import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm

# --- Page Configuration ---
st.set_page_config(page_title="Safety Stock Simulator", layout="wide")

st.title("📦 Inventory & Safety Stock Simulator")
st.markdown("""
This simulation demonstrates how **Safety Stock** acts as a buffer against demand variability. 
Adjust the sliders to see how higher variability or longer lead times require larger safety buffers to prevent stockouts.
""")

# --- Sidebar Inputs ---
st.sidebar.header("Configuration")

# 1. Demand Settings
st.sidebar.subheader("Demand Parameters")
avg_daily_demand = st.sidebar.number_input("Average Daily Demand (units)", value=50, min_value=10)
std_dev_demand = st.sidebar.slider("Demand Volatility (Std Dev)", min_value=1, max_value=30, value=10, 
                                   help="How much demand fluctuates day-to-day.")

# 2. Supply Settings
st.sidebar.subheader("Supply Parameters")
lead_time = st.sidebar.slider("Lead Time (Days)", min_value=1, max_value=30, value=5, 
                              help="Days between placing an order and receiving it.")
order_quantity = st.sidebar.number_input("Reorder Quantity (units)", value=500, min_value=100)

# 3. Service Level Target
st.sidebar.subheader("Risk Appetite")
service_level = st.sidebar.slider("Target Service Level (%)", min_value=80.0, max_value=99.9, value=95.0, step=0.1)

# --- Calculations ---
# Calculate Z-score based on service level (e.g., 95% -> 1.645)
z_score = norm.ppf(service_level / 100)

# Calculate Safety Stock Formula: Z * StdDev * Sqrt(LeadTime)
# Note: We scale volatility by sqrt(Lead Time) because variance adds up over time.
safety_stock = z_score * std_dev_demand * np.sqrt(lead_time)

# Calculate Reorder Point (ROP): (Avg Demand * Lead Time) + Safety Stock
reorder_point = (avg_daily_demand * lead_time) + safety_stock

# --- Simulation Logic ---
days_to_simulate = 365
inventory = reorder_point + order_quantity # Start full
pending_orders = [] # List of tuples: (arrival_day, quantity)
history = []

np.random.seed(42) # For reproducibility within the session

for day in range(days_to_simulate):
    # 1. Receive stock if order arrives today
    new_stock = 0
    # Process arriving orders
    pending_orders = [o for o in pending_orders if o[0] > day] + [o for o in pending_orders if o[0] == day] # filter/keep
    
    # Check for arrivals
    for i in range(len(pending_orders) - 1, -1, -1):
        arrival_day, qty = pending_orders[i]
        if arrival_day == day:
            inventory += qty
            new_stock += qty
            pending_orders.pop(i)

    # 2. Generate random daily demand
    # Ensure demand doesn't drop below 0
    daily_demand = max(0, np.random.normal(avg_daily_demand, std_dev_demand))
    
    # 3. Fulfill demand
    inventory -= daily_demand
    
    # 4. Check Reorder Point
    # Only order if we are below ROP and don't have an order on the way
    if inventory <= reorder_point and not pending_orders:
        arrival_day = day + lead_time
        pending_orders.append((arrival_day, order_quantity))
        
    history.append({
        "Day": day,
        "Inventory": inventory,
        "Demand": daily_demand,
        "Stockout": inventory < 0
    })

df = pd.DataFrame(history)

# --- Visualizing Results ---

# 1. Key Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Calculated Safety Stock", f"{int(safety_stock)} units")
col2.metric("Reorder Point (ROP)", f"{int(reorder_point)} units")
col3.metric("Stockouts Occurred", f"{df['Stockout'].sum()} days")
realized_service_level = 100 * (1 - (df['Stockout'].sum() / days_to_simulate))
col4.metric("Realized Service Level", f"{realized_service_level:.1f}%")

# 2. Plotting the Inventory Levels
fig = go.Figure()

# Inventory Line
fig.add_trace(go.Scatter(x=df['Day'], y=df['Inventory'], mode='lines', name='Inventory Level', line=dict(color='#1f77b4')))

# Safety Stock Line
fig.add_trace(go.Scatter(x=df['Day'], y=[safety_stock]*len(df), mode='lines', name='Safety Stock Level', 
                         line=dict(color='orange', dash='dash')))

# Zero Line (Stockout Threshold)
fig.add_trace(go.Scatter(x=df['Day'], y=[0]*len(df), mode='lines', name='Zero Inventory', 
                         line=dict(color='red', width=2)))

# Highlight Stockouts
stockout_days = df[df['Stockout']]
fig.add_trace(go.Scatter(x=stockout_days['Day'], y=stockout_days['Inventory'], mode='markers', name='Stockout Event',
                         marker=dict(color='red', size=8, symbol='x')))

fig.update_layout(title="Daily Inventory Simulation (1 Year)", xaxis_title="Day", yaxis_title="Units in Stock", height=500)

st.plotly_chart(fig, use_container_width=True)

# --- Educational Expander ---
with st.expander("📚 How to interpret this graph"):
    st.write("""
    1. **The Blue Line (Inventory):** Shows your stock going down as customers buy items, and shooting up when a new order arrives.
    2. **The Orange Dashed Line (Safety Stock):** This is your buffer. Ideally, the blue line should "bounce" off the orange line right before a new order arrives.
    3. **The Red Line (Zero):** If the blue line crosses below this, you have run out of stock (Stockout).
    4. **The Sawtooth Pattern:** Notice how variability makes the "teeth" uneven. Sometimes demand is high during the lead time, eating into your safety stock.
    """)
