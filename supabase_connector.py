import streamlit as st
import pandas as pd
from supabase import create_client


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

_supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def set_supabase_client(client):
    global _supabase_client
    _supabase_client = client


def get_supabase():
    return _supabase_client


def _select_all(table_name: str, order_col: str = "id") -> list[dict]:
    sb = get_supabase()

    rows = []
    page_size = 1000
    start = 0

    while True:
        query = sb.table(table_name).select("*")

        if order_col:
            try:
                query = query.order(order_col)
            except Exception:
                pass

        res = query.range(start, start + page_size - 1).execute()
        batch = getattr(res, "data", None) or []

        rows.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    return rows


def load_all_data():
    bookings = pd.DataFrame(_select_all("bookings"))
    marketing = pd.DataFrame(_select_all("marketing_expenditure"))
    holds = pd.DataFrame(_select_all("holds"))
    cp_payout = pd.DataFrame(_select_all("cp_payout_tracker"))
    daily_visits = pd.DataFrame(_select_all("daily_visits"))
    cashflow_slab_master = pd.DataFrame(_select_all("cashflow_slab_master"))

    return {
        "sheet_df": bookings,
        "marketing_df": marketing,
        "hold_df": holds,
        "cp_payout_df": cp_payout,
        "daily_visits_df": daily_visits,
        "cashflow_slab_master_df": cashflow_slab_master,
    }


def insert_row(table_name: str, row: dict):
    sb = get_supabase()
    return sb.table(table_name).insert(row).execute()


def update_row(table_name: str, row_id, updates: dict):
    sb = get_supabase()
    return sb.table(table_name).update(updates).eq("id", row_id).execute()


def delete_row(table_name: str, row_id):
    sb = get_supabase()
    return sb.table(table_name).delete().eq("id", row_id).execute()
