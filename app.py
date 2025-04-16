import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Gersh Agent Revenue", layout="wide")

# Connect to your database
conn = sqlite3.connect("bookings_final.db")

# Trim agent names for dropdown to avoid whitespace bugs
agents = pd.read_sql("""
    SELECT DISTINCT TRIM(AgentName) AS AgentName
    FROM bookings_final
    ORDER BY AgentName
""", conn)

agent_selected = st.sidebar.selectbox("Select Agent", agents["AgentName"])
agent_selected_clean = agent_selected.strip()

# Filter full data for selected agent
query = f"""
    SELECT YearAndQuarter, Year, SUM(GrossCommission) AS Revenue
    FROM bookings_final
    WHERE TRIM(AgentName) = ? AND Year IN ({','.join(['?']*len(years))})
    GROUP BY YearAndQuarter, Year
    ORDER BY Year, YearAndQuarter
"""
agent_data = pd.read_sql(query, conn, params=(agent_selected_clean, *years))

# Format summary table
years = st.sidebar.multiselect("Select Year(s)", sorted(agent_data["Year"].unique(), reverse=True), default=2024)

# Filter data by year
year_data = agent_data[agent_data["Year"] == year]

# Add total annual revenue row
total = year_data["Revenue"].sum()
summary = year_data.copy()
summary.loc[len(summary.index)] = ["Total", year, total]

# Show table + bar chart
st.title(f"📊 Revenue Summary for {agent_selected}")
st.subheader(f"Quarterly + Annual Commission - {year}")
st.dataframe(summary)

# Bar chart
st.bar_chart(summary.set_index("YearAndQuarter")["Revenue"])

# --- Drilldown: Select Quarter or Full Year ---
quarters = year_data["YearAndQuarter"].tolist()
options = ["All Year"] + quarters
selected_period = st.selectbox("Drilldown: Select Quarter or All Year", options)

if selected_period == "All Year":
    client_breakdown = pd.read_sql("""
        SELECT ClientName, SUM(GrossCommission) AS Revenue
        FROM bookings_final
        WHERE TRIM(AgentName) = ? AND Year = ?
        GROUP BY ClientName
        ORDER BY Revenue DESC
    """, conn, params=(agent_selected_clean, year))
else:
    client_breakdown = pd.read_sql("""
        SELECT ClientName, SUM(GrossCommission) AS Revenue
        FROM bookings_final
        WHERE TRIM(AgentName) = ? AND YearAndQuarter = ?
        GROUP BY ClientName
        ORDER BY Revenue DESC
    """, conn, params=(agent_selected_clean, selected_period))

st.subheader(f"💼 Client Breakdown – {selected_period}")
st.dataframe(client_breakdown)

conn.close()
