Build a Streamlit tab named "Geographic Risk Intelligence" for an existing executive dashboard. The goal is to answer: "Where is the highest risk located, and how can we cluster aging infrastructure for efficient replacement?"
Data Source: Load dashboard_master_data.csv into a dataframe named df. Use EXACTLY these columns: Hostname, State, PhysicalAddressCounty, Latitude, Longitude, Risk_Level, Total_Replacement_Cost, Site_Code.
Tab Layout Requirements:
1. Header & Filters:
Title: "Geographic Lifecycle Risk Mapping"
Caption: "Identify risk hotspots and cluster aging infrastructure for optimized field deployments."
Add a multi-select filter for State to let the user zoom in on specific regions.
2. Interactive 3D Risk Map (The "WOW" Factor):
Use st.pydeck_chart to create a stunning 3D map.
Filter out any rows with missing Latitude/Longitude.
Create a ScatterplotLayer for precise device locations. Color the dots based on Risk_Level (Critical = Red, High = Orange, Medium = Blue, Low = Green).
Create a HexagonLayer or ColumnLayer that aggregates Total_Replacement_Cost so high-cost risk areas appear as tall 3D towers on the map.
3. Geographic Risk Summary Charts (Two Columns): Create a two-column layout using st.columns(2) using Plotly:
Left Column: A horizontal bar chart showing the count of high-risk devices (Filter for Critical + High) grouped by State.
Right Column: A horizontal bar chart showing the count of high-risk devices grouped by PhysicalAddressCounty (Top 15 only).
4. Risk Clustering Insight Table:
Group the dataframe by Site_Code and State.
Calculate the total count of devices where Risk_Level is 'Critical (Past EoL)' or 'High (Near EoL)'.
Sum the Total_Replacement_Cost for those high-risk devices.
Display this using st.dataframe, sorted descending by the total replacement cost. Format the cost as currency. This shows leadership exactly which physical buildings to send technicians to first.
Design Requirements:
Maintain the strict color mapping for Risk_Level across all charts.
Ensure the PyDeck map has a dark, modern tooltip.
