_run_app_file("app_parts/construction_progress_core.py")

LABOUR_TABLE = "construction_labour_counts"
CONCRETE_TABLE = "construction_concrete_consumption"


def _cp_insert_row(supabase_client, table_name: str, payload: dict):
    return supabase_client.table(table_name).insert(payload).execute()


def _cp_fetch_table(supabase_client, table_name: str, order_col: str = "report_date") -> pd.DataFrame:
    try:
        response = (
            supabase_client
            .table(table_name)
            .select("*")
            .order(order_col, desc=True)
            .limit(200)
            .execute()
        )
        return pd.DataFrame(response.data or [])
    except Exception as exc:
        st.warning(f"Could not load `{table_name}`. Please run the latest SQL migration. Details: {exc}")
        return pd.DataFrame()


def _render_labour_count_update(supabase_client):
    st.markdown("### Labour & Contractor Staff Count")

    with st.form("cp_labour_count_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            report_date = st.date_input("Date", value=_dt.date.today(), format="DD/MM/YYYY", key="cp_labour_report_date")
        with c2:
            wing = st.selectbox("Wing", ["A", "B", "C", "D", "E", "F", "G"], key="cp_labour_wing")
        with c3:
            contractor_name = st.text_input("Contractor Name", key="cp_labour_contractor")

        st.markdown("#### Wing-wise Labour Count")
        l1, l2, l3, l4, l5 = st.columns(5)
        with l1:
            carpenter = st.number_input("Carpenter", min_value=0, step=1, value=0, key="cp_labour_carpenter")
        with l2:
            fitter = st.number_input("Fitter", min_value=0, step=1, value=0, key="cp_labour_fitter")
        with l3:
            mason = st.number_input("Mason", min_value=0, step=1, value=0, key="cp_labour_mason")
        with l4:
            unskilled = st.number_input("Unskilled", min_value=0, step=1, value=0, key="cp_labour_unskilled")
        with l5:
            others = st.number_input("Others", min_value=0, step=1, value=0, key="cp_labour_others")

        st.markdown("#### Contractor Staff Count")
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            project_manager = st.number_input("Project Manager", min_value=0, step=1, value=0, key="cp_staff_pm")
        with s2:
            senior_engineer = st.number_input("Senior Engineer", min_value=0, step=1, value=0, key="cp_staff_senior")
        with s3:
            junior_engineer = st.number_input("Junior Engineer", min_value=0, step=1, value=0, key="cp_staff_junior")
        with s4:
            supervisor = st.number_input("Supervisor", min_value=0, step=1, value=0, key="cp_staff_supervisor")

        submitted = st.form_submit_button("Save Labour / Staff Count", type="primary", use_container_width=True)

    if submitted:
        contractor = (contractor_name or "").strip()
        if not contractor:
            st.error("Contractor Name is required.")
        else:
            payload = {
                "report_date": report_date.isoformat(),
                "wing": wing,
                "contractor_name": contractor,
                "carpenter": int(carpenter),
                "fitter": int(fitter),
                "mason": int(mason),
                "unskilled": int(unskilled),
                "others": int(others),
                "project_manager": int(project_manager),
                "senior_engineer": int(senior_engineer),
                "junior_engineer": int(junior_engineer),
                "supervisor": int(supervisor),
            }

            try:
                _cp_insert_row(supabase_client, LABOUR_TABLE, payload)
                st.cache_data.clear()
                st.success("Labour and staff count saved.")
            except Exception as exc:
                st.error(f"Could not save labour count. Please run the latest SQL migration. Details: {exc}")

    labour_df = _cp_fetch_table(supabase_client, LABOUR_TABLE)
    if not labour_df.empty:
        st.markdown("#### Latest Labour Entries")
        st.dataframe(labour_df, use_container_width=True, hide_index=True)


def _render_concrete_consumption_update(supabase_client):
    st.markdown("### Concrete Consumption")

    concrete_df = _cp_fetch_table(supabase_client, CONCRETE_TABLE)
    work_options = sorted([
        str(x).strip()
        for x in concrete_df.get("work", pd.Series(dtype=str)).dropna().unique().tolist()
        if str(x).strip()
    ]) if not concrete_df.empty else []

    with st.form("cp_concrete_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            report_date = st.date_input("Date", value=_dt.date.today(), format="DD/MM/YYYY", key="cp_concrete_report_date")
        with c2:
            wing = st.selectbox("Wing", ["A", "B", "C", "D", "E", "F", "G"], key="cp_concrete_wing")
        with c3:
            quantity_m3 = st.number_input("Concrete Quantity (M3)", min_value=0.0, step=0.25, value=0.0, key="cp_concrete_quantity")

        existing_work = st.selectbox(
            "Select Existing Work",
            [""] + work_options,
            key="cp_concrete_existing_work",
            help="Optional. Previously entered work names appear here.",
        )
        new_work = st.text_input(
            "Work",
            value=existing_work,
            key="cp_concrete_work",
            help="Type a new work name or use the selected existing work.",
        )

        submitted = st.form_submit_button("Save Concrete Consumption", type="primary", use_container_width=True)

    if submitted:
        work = (new_work or existing_work or "").strip()
        if not work:
            st.error("Work is required.")
        elif float(quantity_m3) <= 0:
            st.error("Concrete Quantity must be greater than 0.")
        else:
            payload = {
                "report_date": report_date.isoformat(),
                "wing": wing,
                "work": work,
                "concrete_quantity_m3": float(quantity_m3),
            }

            try:
                _cp_insert_row(supabase_client, CONCRETE_TABLE, payload)
                st.cache_data.clear()
                st.success("Concrete consumption saved.")
            except Exception as exc:
                st.error(f"Could not save concrete consumption. Please run the latest SQL migration. Details: {exc}")

    if not concrete_df.empty:
        st.markdown("#### Latest Concrete Entries")
        st.dataframe(concrete_df, use_container_width=True, hide_index=True)


st.header("Construction Progress Updates")
_inject_css()

supabase_client = globals().get("supabase", None) or globals().get("supabase_client", None)

if supabase_client is None:
    st.warning("Supabase client is not initialized.")
else:
    floor_df, flat_df = _load_data(supabase_client)
    floor_col_map = _column_lookup(floor_df, RCC_CHECKPOINTS)
    flat_col_map = _column_lookup(flat_df, FLAT_CHECKPOINTS)

    slab_tab, flat_tab, labour_tab, concrete_tab = st.tabs([
        "Update Slab / RCC",
        "Update Flat Work",
        "Labour Count",
        "Concrete Consumption",
    ])

    with slab_tab:
        _render_update_slab(supabase_client, floor_df, floor_col_map)

    with flat_tab:
        _render_update_flat(supabase_client, flat_df, flat_col_map)

    with labour_tab:
        _render_labour_count_update(supabase_client)

    with concrete_tab:
        _render_concrete_consumption_update(supabase_client)
