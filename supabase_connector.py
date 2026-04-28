import pandas as pd
import streamlit as st
from supabase import create_client

_SUPABASE_CLIENT = None


TABLES = {
    "bookings": "bookings",
    "marketing": "marketing_expenditure",
    "holds": "holds",
    "cp_payout": "cp_payout_tracker",
    "daily_visits": "daily_visits",
    "cashflow_slab_master": "cashflow_slab_master",
}


def set_supabase_client(client):
    global _SUPABASE_CLIENT
    _SUPABASE_CLIENT = client


def _get_client():
    global _SUPABASE_CLIENT

    if _SUPABASE_CLIENT is not None:
        return _SUPABASE_CLIENT

    url = st.secrets["SUPABASE_URL"]
    anon_key = st.secrets["SUPABASE_ANON_KEY"]
    _SUPABASE_CLIENT = create_client(url, anon_key)
    return _SUPABASE_CLIENT


def _select_all(table_name: str, order_col: str = "id") -> list[dict]:
    sb = _get_client()

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


def _df(table_name: str) -> pd.DataFrame:
    try:
        return pd.DataFrame(_select_all(table_name))
    except Exception:
        return pd.DataFrame()


def load_all_data():
    return {
        "sheet_df": _df(TABLES["bookings"]),
        "marketing_df": _df(TABLES["marketing"]),
        "hold_df": _df(TABLES["holds"]),
        "cp_payout_df": _df(TABLES["cp_payout"]),
        "daily_visits_df": _df(TABLES["daily_visits"]),
        "cashflow_slab_master_df": _df(TABLES["cashflow_slab_master"]),
    }


def insert_row(table_name: str, row_dict: dict):
    sb = _get_client()
    return sb.table(table_name).insert(row_dict).execute()


def update_row(table_name: str, row_id, row_dict: dict, id_col: str = "id"):
    sb = _get_client()
    return sb.table(table_name).update(row_dict).eq(id_col, row_id).execute()


def delete_row(table_name: str, row_id, id_col: str = "id"):
    sb = _get_client()
    return sb.table(table_name).delete().eq(id_col, row_id).execute()


def refresh_all_data():
    try:
        st.cache_data.clear()
    except Exception:
        pass

    return load_all_data()
