from supabase_connector import load_all_data, insert_row, update_row, delete_row

data = load_all_data()

sheet_df = data["sheet_df"]
marketing_df = data["marketing_df"]
hold_df = data["hold_df"]
cp_payout_df = data["cp_payout_df"]
daily_visits_df = data["daily_visits_df"]
cashflow_slab_master_df = data["cashflow_slab_master_df"]

supabase_connected = True
sheets_connected = True
