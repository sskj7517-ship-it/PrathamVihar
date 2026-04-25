import streamlit as st
import pandas as pd
from supabase import create_client, Client


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_table(table_name: str) -> pd.DataFrame:
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error loading {table_name}: {e}")
        return pd.DataFrame()


def insert_row(table_name: str, row_data: dict):
    try:
        response = supabase.table(table_name).insert(row_data).execute()
        return response
    except Exception as e:
        st.error(f"Error inserting into {table_name}: {e}")
        return None


def update_row(table_name: str, row_id, update_data: dict):
    try:
        response = (
            supabase
            .table(table_name)
            .update(update_data)
            .eq("id", row_id)
            .execute()
        )
        return response
    except Exception as e:
        st.error(f"Error updating {table_name}: {e}")
        return None


def delete_row(table_name: str, row_id):
    try:
        response = (
            supabase
            .table(table_name)
            .delete()
            .eq("id", row_id)
            .execute()
        )
        return response
    except Exception as e:
        st.error(f"Error deleting from {table_name}: {e}")
        return None


def load_all_data():
    sheet_df = load_table("bookings")
    marketing_df = load_table("marketing_expenditure")
    hold_df = load_table("holds")
    cp_payout_df = load_table("cp_payout_tracker")
    daily_visits_df = load_table("daily_visits")
    cashflow_slab_master_df = load_table("cashflow_slab_master")

    return {
        "sheet_df": sheet_df,
        "marketing_df": marketing_df,
        "hold_df": hold_df,
        "cp_payout_df": cp_payout_df,
        "daily_visits_df": daily_visits_df,
        "cashflow_slab_master_df": cashflow_slab_master_df,
    }
