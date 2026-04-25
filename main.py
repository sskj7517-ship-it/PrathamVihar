import streamlit as st
import pandas as pd

from supabase_connector import load_all_data, insert_row, update_row, delete_row

st.set_page_config(
    page_title="Rate Guard - PRATHAM VIHAR",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Rate Guard - Pratham Vihar")
st.subheader("Supabase Connection Test")

try:
    data = load_all_data()

    sheet_df = data["sheet_df"]
    marketing_df = data["marketing_df"]
    hold_df = data["hold_df"]
    cp_payout_df = data["cp_payout_df"]
    daily_visits_df = data["daily_visits_df"]
    cashflow_slab_master_df = data["cashflow_slab_master_df"]

    supabase_connected = True
    sheets_connected = True

    st.success("✅ Supabase connected successfully!")

    st.write("### Tables Loaded")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Bookings", len(sheet_df))
        st.metric("Marketing Expenditure", len(marketing_df))

    with col2:
        st.metric("Holds", len(hold_df))
        st.metric("CP Payout Tracker", len(cp_payout_df))

    with col3:
        st.metric("Daily Visits", len(daily_visits_df))
        st.metric("Cashflow Slab Master", len(cashflow_slab_master_df))

    st.divider()

    st.write("### Bookings Preview")
    st.dataframe(sheet_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ Error loading app: {e}")
