_run_app_file("app_parts/construction_progress_core.py")

LABOUR_TABLE = "construction_labour_counts"
CONCRETE_TABLE = "construction_concrete_consumption"
CONSTRUCTION_WINGS = ["A", "B", "C", "D", "E", "F", "G"]


def _cp_insert_row(supabase_client, table_name: str, payload: dict):
    return supabase_client.table(table_name).insert(payload).execute()


def _cp_insert_rows(supabase_client, table_name: str, payloads: list[dict]):
    return supabase_client.table(table_name).insert(payloads).execute()


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
        c1, c2 = st.columns(2)
        with c1:
            report_date = st.date_input("Date", value=_dt.date.today(), format="DD/MM/YYYY", key="cp_labour_report_date")
        with c2:
            contractor_name = st.text_input("Contractor Name", key="cp_labour_contractor")

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

        st.markdown("#### Wing-wise Labour Count")
        st.caption("Fill only the wings where labour is present. Blank/zero wings will not be punched.")

        wing_inputs = {}
        h0, h1, h2, h3, h4, h5 = st.columns([0.75, 1, 1, 1, 1, 1])
        h0.markdown("**Wing**")
        h1.markdown("**Carpenter**")
        h2.markdown("**Fitter**")
        h3.markdown("**Mason**")
        h4.markdown("**Unskilled**")
        h5.markdown("**Others**")

        for wing in CONSTRUCTION_WINGS:
            w0, w1, w2, w3, w4, w5 = st.columns([0.75, 1, 1, 1, 1, 1])
            w0.markdown(f"**{wing} Wing**")
            with w1:
                carpenter = st.number_input("Carpenter", min_value=0, step=1, value=0, key=f"cp_labour_{wing}_carpenter", label_visibility="collapsed")
            with w2:
                fitter = st.number_input("Fitter", min_value=0, step=1, value=0, key=f"cp_labour_{wing}_fitter", label_visibility="collapsed")
            with w3:
                mason = st.number_input("Mason", min_value=0, step=1, value=0, key=f"cp_labour_{wing}_mason", label_visibility="collapsed")
            with w4:
                unskilled = st.number_input("Unskilled", min_value=0, step=1, value=0, key=f"cp_labour_{wing}_unskilled", label_visibility="collapsed")
            with w5:
                others = st.number_input("Others", min_value=0, step=1, value=0, key=f"cp_labour_{wing}_others", label_visibility="collapsed")

            wing_inputs[wing] = {
                "carpenter": int(carpenter),
                "fitter": int(fitter),
                "mason": int(mason),
                "unskilled": int(unskilled),
                "others": int(others),
            }

        submitted = st.form_submit_button("Save Labour / Staff Count", type="primary", use_container_width=True)

    if submitted:
        contractor = (contractor_name or "").strip()
        staff_payload = {
            "project_manager": int(project_manager),
            "senior_engineer": int(senior_engineer),
            "junior_engineer": int(junior_engineer),
            "supervisor": int(supervisor),
        }
        staff_total = sum(staff_payload.values())
        labour_rows = [
            (wing, vals)
            for wing, vals in wing_inputs.items()
            if sum(vals.values()) > 0
        ]

        if not contractor:
            st.error("Contractor Name is required.")
        elif not labour_rows and staff_total <= 0:
            st.error("Enter labour count for at least one wing or enter contractor staff count.")
        else:
            payloads = []

            if labour_rows:
                for idx, (wing, vals) in enumerate(labour_rows):
                    row_staff = staff_payload if idx == 0 else {
                        "project_manager": 0,
                        "senior_engineer": 0,
                        "junior_engineer": 0,
                        "supervisor": 0,
                    }

                    payloads.append({
                        "report_date": report_date.isoformat(),
                        "wing": wing,
                        "contractor_name": contractor,
                        **vals,
                        **row_staff,
                    })
            else:
                payloads.append({
                    "report_date": report_date.isoformat(),
                    "wing": "SITE",
                    "contractor_name": contractor,
                    "carpenter": 0,
                    "fitter": 0,
                    "mason": 0,
                    "unskilled": 0,
                    "others": 0,
                    **staff_payload,
                })

            try:
                _cp_insert_rows(supabase_client, LABOUR_TABLE, payloads)
                st.cache_data.clear()
                st.success(f"Saved {len(payloads)} labour/staff entr{'y' if len(payloads) == 1 else 'ies'}.")
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
        c1, c2 = st.columns(2)
        with c1:
            report_date = st.date_input("Date", value=_dt.date.today(), format="DD/MM/YYYY", key="cp_concrete_report_date")
        with c2:
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

        st.markdown("#### Wing-wise Concrete Quantity")
        st.caption("Fill only the wings where concrete was consumed. Zero wings will not be punched.")

        quantity_inputs = {}
        cols = st.columns(len(CONSTRUCTION_WINGS))
        for idx, wing in enumerate(CONSTRUCTION_WINGS):
            with cols[idx]:
                quantity_inputs[wing] = st.number_input(
                    f"{wing} Wing",
                    min_value=0.0,
                    step=0.25,
                    value=0.0,
                    key=f"cp_concrete_{wing}_quantity",
                )

        submitted = st.form_submit_button("Save Concrete Consumption", type="primary", use_container_width=True)

    if submitted:
        work = (new_work or existing_work or "").strip()
        payloads = [
            {
                "report_date": report_date.isoformat(),
                "wing": wing,
                "work": work,
                "concrete_quantity_m3": float(quantity),
            }
            for wing, quantity in quantity_inputs.items()
            if float(quantity or 0) > 0
        ]

        if not work:
            st.error("Work is required.")
        elif not payloads:
            st.error("Enter concrete quantity for at least one wing.")
        else:
            try:
                _cp_insert_rows(supabase_client, CONCRETE_TABLE, payloads)
                st.cache_data.clear()
                st.success(f"Saved {len(payloads)} concrete consumption entr{'y' if len(payloads) == 1 else 'ies'}.")
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
