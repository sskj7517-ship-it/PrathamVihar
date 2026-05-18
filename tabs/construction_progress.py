# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.

from construction_progress_tab import render_construction_progress_tab

supabase_client = globals().get("supabase", None) or globals().get("supabase_client", None)

if supabase_client is None:
    st.warning("Supabase client is not initialized.")
    st.stop()

render_construction_progress_tab(supabase_client)
