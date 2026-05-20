_run_app_file("app_parts/construction_progress_core.py")

st.header("Construction Progress Dashboard")
_inject_css()

supabase_client = globals().get("supabase", None) or globals().get("supabase_client", None)

if supabase_client is None:
    st.warning("Supabase client is not initialized.")
else:
    floor_df, flat_df = _load_data(supabase_client)
    floor_col_map = _column_lookup(floor_df, RCC_CHECKPOINTS)
    flat_col_map = _column_lookup(flat_df, FLAT_CHECKPOINTS)
    wings = _wing_options(floor_df, flat_df)

    if not wings:
        st.warning("No construction progress data found.")
    else:
        dash_tabs = st.tabs(["All Wings"] + [f"{w} Wing" for w in wings])

        with dash_tabs[0]:
            _render_dashboard_panel(floor_df, flat_df, floor_col_map, flat_col_map, None)

        for tab_obj, wing in zip(dash_tabs[1:], wings):
            with tab_obj:
                _render_dashboard_panel(floor_df, flat_df, floor_col_map, flat_col_map, wing)
