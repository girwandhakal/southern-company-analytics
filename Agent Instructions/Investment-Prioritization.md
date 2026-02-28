Build a Streamlit tab named "Investment Prioritization" for an existing executive dashboard. The goal is to answer: "Where should leadership prioritize investment first?"
Data Source: Load dashboard_master_data.csv into a dataframe named df. Use EXACTLY these columns: Hostname, State, Site_Code, Risk_Level, Total_Replacement_Cost, Risk_Score, Is_Decom. CRITICAL: Immediately filter the dataframe to only include rows where Is_Decom == False and Risk_Score > 0. We do not invest in dead sites.
Tab Layout Requirements:
1. Header:
Title: "Investment Prioritization & Risk Reduction"
Caption: "Data-driven replacement roadmap based on risk severity, support status, and cost."
2. The Budget Impact Simulator (Killer Feature):
Create an st.slider called "Select 2026 CapEx Budget". Set the min value to 0, max value to 5,000,000, step to 50,000, and default to 1,000,000. Format it as currency.
Sort the filtered dataframe by Risk_Score descending.
Create a cumulative sum column of Total_Replacement_Cost.
Calculate how many devices can be fully replaced with the selected budget.
Display a massive st.success or st.metric box saying: "With a budget of [Slider Value], you can fully replace the top [Calculated Number] highest-risk devices, completely clearing [X]% of critical technical debt."
3. Priority Ranking Table:
Below the simulator, display an st.dataframe showing the top 100 devices that fit within that selected budget.
Display columns: Hostname, State, Site_Code, Risk_Level, Risk_Score, Total_Replacement_Cost.
Apply conditional formatting to the dataframe to highlight the Risk_Score column (e.g., using pandas background gradients).
4. Site-Level Action Plan:
Create a Plotly bar chart showing the Top 10 Site_Codes with the highest sum of Risk_Score.
Title: "Top 10 Sites Requiring Immediate Intervention".
This tells the project managers exactly which buildings to target first.
Design Requirements:
Clean executive layout emphasizing decision support.
The simulator MUST recalculate instantly when the slider is moved.

