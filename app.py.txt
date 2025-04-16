import streamlit as st
import sqlite3
import pandas as pd

# Connect to your database
conn = sqlite3.connect("bookings_final.db")

# Agent dropdown
agents = pd.read_sql("SELECT DISTINCT AgentName FROM bookings_final ORDER BY AgentName", conn)
agent_selected = st.selectbox("Select Agent", agents["AgentName"])

# Year dropdown
years = pd.read_sql("SELECT DISTINCT Year FROM bookings_final ORDER BY Year", conn)
year_selected = st.selectbox("Select Year", years["Year"])

# Show revenue by quarter
quarterly = pd.read_sql("""
    SELECT YearAndQuarter, SUM(GrossCommission) AS Revenue
    FROM bookings_final
    WHERE AgentName = ? AND Year = ?
    GROUP BY YearAndQuarter
    ORDER BY YearAndQuarter
""", conn, params=(agent_selected, year_selected))

st.subheader("Quarterly Revenue")
st.bar_chart(quarterly.set_index("YearAndQuarter"))

# Show revenue by client
clients = pd.read_sql("""
    SELECT ClientName, SUM(GrossCommission) AS Revenue
    FROM bookings_final
    WHERE AgentName = ? AND Year = ?
    GROUP BY ClientName
    ORDER BY Revenue DESC
""", conn, params=(agent_selected, year_selected))

st.subheader("Client Breakdown")
st.dataframe(clients)

conn.close()
