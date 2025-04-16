import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Gersh Agent Revenue", layout="wide")

# Connect to your database
conn = sqlite3.connect("bookings_final.db")

# --- Global Summary (All Agents) ---
st.title("📈 Firmwide Bookings Overview")

# Revenue by year
yearly_rev = pd.read_sql("""
    SELECT Year, SUM(GrossCommission) AS Revenue
    FROM bookings_final
    GROUP BY Year
    ORDER BY Year
""", conn)
st.subheader("📅 Revenue by Year")
st.dataframe(yearly_rev)
st.bar_chart(yearly_rev.set_index("Year"))

# Revenue by quarter
quarterly_rev = pd.read_sql("""
    SELECT YearAndQuarter, SUM(GrossCommission) AS Revenue
    FROM bookings_final
    GROUP BY YearAndQuarter
    ORDER BY YearAndQuarter
""", conn)
st.subheader("🗓️ Revenue by Quarter")
st.dataframe(quarterly_rev)
st.bar_chart(quarterly_rev.set_index("YearAndQuarter"))

# Get agent list (trimmed)
agents = pd.read_sql("""
    SELECT DISTINCT TRIM(AgentName) AS AgentName
    FROM bookings_final
    ORDER BY AgentName
""", conn)

agent_selected = st.sidebar.selectbox("Select Agent", agents["AgentName"])
agent_selected_clean = agent_selected.strip()

# Get distinct years (safe fallback in case no data loaded yet)
all_years = pd.read_sql("SELECT DISTINCT Year FROM bookings_final ORDER BY Year DESC", conn)["Year"].tolist()

# Select multiple years
years = st.sidebar.multiselect("Select Year(s)", all_years, default=[2024])

# Get revenue by quarter for selected agent + years
query = f"""
    SELECT YearAndQuarter, Year, SUM(GrossCommission) AS Revenue
    FROM bookings_final
    WHERE TRIM(AgentName) = ? AND Year IN ({','.join(['?'] * len(years))})
    GROUP BY YearAndQuarter, Year
    ORDER BY Year, YearAndQuarter
"""
agent_data = pd.read_sql(query, conn, params=(agent_selected_clean, *years))

# Summarize quarterly + yearly
summary = agent_data.copy()
summary.loc[len(summary)] = ["Total", "—", summary["Revenue"].sum()]

# Show results
st.title(f"📊 Revenue Summary for {agent_selected}")
st.subheader(f"Quarterly + Annual Commission: {', '.join(map(str, years))}")
st.dataframe(summary)

# Bar chart
st.bar_chart(summary[summary["YearAndQuarter"] != "Total"].set_index("YearAndQuarter")["Revenue"])

# Drilldown: Select quarter or full year
quarters = agent_data["YearAndQuarter"].tolist()
options = ["All Selected Year(s)"] + quarters
selected_period = st.selectbox("Drilldown: Select Quarter or All Year(s)", options)

if selected_period == "All Selected Year(s)":
    client_breakdown = pd.read_sql(f"""
        SELECT ClientName, SUM(GrossCommission) AS Revenue
        FROM bookings_final
        WHERE TRIM(AgentName) = ? AND Year IN ({','.join(['?'] * len(years))})
        GROUP BY ClientName
        ORDER BY Revenue DESC
    """, conn, params=(agent_selected_clean, *years))
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
