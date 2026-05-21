_run_app_file("app_parts/construction_progress_core.py")

st.header("Construction Progress Charts")
_inject_css()

supabase_client = globals().get("supabase", None) or globals().get("supabase_client", None)

if supabase_client is None:
    st.warning("Supabase client is not initialized.")
else:
    floor_df, flat_df = _load_data(supabase_client)
    floor_col_map = _column_lookup(floor_df, RCC_CHECKPOINTS)
    flat_col_map = _column_lookup(flat_df, FLAT_CHECKPOINTS)
    wings = _wing_options(floor_df, flat_df)

    floor_tab, rcc_delay_tab, flat_tab, consumption_tab = st.tabs([
        "Floor-wise Progress",
        "RCC Delay Tracking",
        "Flat-wise Progress",
        "Consumption",
    ])

    with floor_tab:
        _render_floorwise(floor_df, flat_df, floor_col_map, flat_col_map, wings)

    with rcc_delay_tab:
        _render_rcc_delay_tracking(supabase_client, floor_df, floor_col_map, wings)

    with flat_tab:
        _render_flatwise(flat_df, flat_col_map, wings)

    with consumption_tab:
        _render_consumption_tab(flat_df, wings)
