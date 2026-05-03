import pandas as pd


TABLES = {
    "sheet_df": "bookings",
    "marketing_df": "marketing_expenditure",
    "hold_df": "holds",
    "cp_payout_df": "cp_payout_tracker",
    "daily_visits_df": "daily_visits",
    "cashflow_slab_master_df": "cashflow_slab_master",
    "sales_targets_df": "sales_targets",
}


def fetch_table(supabase, table_name: str, order_col: str = "id") -> pd.DataFrame:
    rows = []
    page_size = 1000
    start = 0

    while True:
        query = supabase.table(table_name).select("*")

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

    df = pd.DataFrame(rows)

    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]

    return df


def load_all_data(supabase) -> dict:
    data = {}

    for key, table_name in TABLES.items():
        try:
            data[key] = fetch_table(supabase, table_name)
        except Exception:
            data[key] = pd.DataFrame()

    return data


def insert_row(supabase, table_name: str, row: dict):
    return supabase.table(table_name).insert(row).execute()


def update_row(supabase, table_name: str, row_id, updates: dict):
    return supabase.table(table_name).update(updates).eq("id", row_id).execute()


def delete_row(supabase, table_name: str, row_id):
    return supabase.table(table_name).delete().eq("id", row_id).execute()
