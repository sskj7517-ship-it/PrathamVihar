_run_app_file("app_parts/construction_progress_core.py")

LABOUR_TABLE = "construction_labour_counts"
CONCRETE_TABLE = "construction_concrete_consumption"
CONSTRUCTION_WINGS = ["A", "B", "C", "D", "E", "F", "G"]
LABOUR_ENTRY_COUNT = 5
CONCRETE_ENTRY_COUNT = 5
CONCRETE_GRADE_OPTIONS = ["", "M5", "M7.5", "M10", "M15", "M20", "M25", "M30", "M35", "M40", "M45", "M50", "Other"]


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
        report_date = st.date_input("Date", value=_dt.date.today(), format="DD/MM/YYYY", key="cp_labour_report_date")
        st.caption("Punch up to 5 vendor entries together. Rows with no vendor/count will be skipped.")

        labour_entries = []
        for idx in range(1, LABOUR_ENTRY_COUNT + 1):
            st.markdown(f"#### Vendor Entry {idx}")

            top_cols = st.columns([2.2, 1, 1, 1, 1, 1, 1, 1])
            with top_cols[0]:
                contractor_name = st.text_input("Vendor / Contractor", key=f"cp_labour_{idx}_contractor")
            with top_cols[1]:
                wing = st.selectbox("Wing", [""] + CONSTRUCTION_WINGS, key=f"cp_labour_{idx}_wing")
            with top_cols[2]:
                carpenter = st.number_input("Carpenter", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_carpenter")
            with top_cols[3]:
                fitter = st.number_input("Fitter", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_fitter")
            with top_cols[4]:
                mason = st.number_input("Mason", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_mason")
            with top_cols[5]:
                skilled = st.number_input("Skilled", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_skilled")
            with top_cols[6]:
                unskilled = st.number_input("Unskilled", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_unskilled")
            with top_cols[7]:
                others = st.number_input("Others", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_others")

            staff_cols = st.columns(4)
            with staff_cols[0]:
                project_manager = st.number_input("Project Manager", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_pm")
            with staff_cols[1]:
                senior_engineer = st.number_input("Senior Engineer", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_senior")
            with staff_cols[2]:
                junior_engineer = st.number_input("Junior Engineer", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_junior")
            with staff_cols[3]:
                supervisor = st.number_input("Supervisor", min_value=0, step=1, value=0, key=f"cp_labour_{idx}_supervisor")

            labour_entries.append({
                "idx": idx,
                "contractor_name": (contractor_name or "").strip(),
                "wing": wing,
                "carpenter": int(carpenter),
                "fitter": int(fitter),
                "mason": int(mason),
                "skilled": int(skilled),
                "unskilled": int(unskilled),
                "others": int(others),
                "project_manager": int(project_manager),
                "senior_engineer": int(senior_engineer),
                "junior_engineer": int(junior_engineer),
                "supervisor": int(supervisor),
            })

        submitted = st.form_submit_button("Save Labour / Staff Count", type="primary", use_container_width=True)

    if submitted:
        payloads = []
        errors = []

        labour_cols = ["carpenter", "fitter", "mason", "skilled", "unskilled", "others"]
        staff_cols = ["project_manager", "senior_engineer", "junior_engineer", "supervisor"]

        for row in labour_entries:
            row_total = sum(row[col] for col in labour_cols + staff_cols)
            if row_total <= 0 and not row["contractor_name"]:
                continue

            if not row["contractor_name"]:
                errors.append(f"Vendor Entry {row['idx']}: Vendor / Contractor is required.")

            if not row["wing"]:
                errors.append(f"Vendor Entry {row['idx']}: Wing is required.")

            if row_total <= 0:
                errors.append(f"Vendor Entry {row['idx']}: Enter at least one labour or staff count.")

            if row["contractor_name"] and row["wing"] and row_total > 0:
                payloads.append({
                    "report_date": report_date.isoformat(),
                    "wing": row["wing"],
                    "contractor_name": row["contractor_name"],
                    "carpenter": row["carpenter"],
                    "fitter": row["fitter"],
                    "mason": row["mason"],
                    "skilled": row["skilled"],
                    "unskilled": row["unskilled"],
                    "others": row["others"],
                    "project_manager": row["project_manager"],
                    "senior_engineer": row["senior_engineer"],
                    "junior_engineer": row["junior_engineer"],
                    "supervisor": row["supervisor"],
                })

        if errors:
            for err in errors:
                st.error(err)
        elif not payloads:
            st.error("Enter at least one vendor row before saving.")
        else:
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
        report_date = st.date_input("Date", value=_dt.date.today(), format="DD/MM/YYYY", key="cp_concrete_report_date")
        st.caption("Punch up to 5 concrete entries together. Each row is one wing + one work + one grade + one quantity.")

        concrete_entries = []
        for idx in range(1, CONCRETE_ENTRY_COUNT + 1):
            st.markdown(f"#### Concrete Entry {idx}")
            cols = st.columns([1, 1.5, 2, 1.2, 1.2, 1.2])

            with cols[0]:
                wing = st.selectbox("Wing", [""] + CONSTRUCTION_WINGS, key=f"cp_concrete_{idx}_wing")
            with cols[1]:
                existing_work = st.selectbox(
                    "Existing Work",
                    [""] + work_options,
                    key=f"cp_concrete_{idx}_existing_work",
                )
            with cols[2]:
                new_work = st.text_input(
                    "Work / New Work",
                    key=f"cp_concrete_{idx}_work",
                    help="Type a new work name, or leave blank to use selected existing work.",
                )
            with cols[3]:
                concrete_grade = st.selectbox("Grade", CONCRETE_GRADE_OPTIONS, key=f"cp_concrete_{idx}_grade")
            with cols[4]:
                custom_grade = st.text_input("Other Grade", key=f"cp_concrete_{idx}_custom_grade")
            with cols[5]:
                quantity_m3 = st.number_input(
                    "Quantity (M3)",
                    min_value=0.0,
                    step=0.25,
                    value=0.0,
                    key=f"cp_concrete_{idx}_quantity",
                )

            concrete_entries.append({
                "idx": idx,
                "wing": wing,
                "existing_work": existing_work,
                "new_work": (new_work or "").strip(),
                "concrete_grade": (custom_grade or "").strip() if concrete_grade == "Other" else concrete_grade,
                "quantity_m3": float(quantity_m3 or 0),
            })

        submitted = st.form_submit_button("Save Concrete Consumption", type="primary", use_container_width=True)

    if submitted:
        payloads = []
        errors = []

        for row in concrete_entries:
            work = (row["new_work"] or row["existing_work"] or "").strip()
            has_any_input = bool(row["wing"] or work or row["concrete_grade"] or row["quantity_m3"] > 0)

            if not has_any_input:
                continue

            if not row["wing"]:
                errors.append(f"Concrete Entry {row['idx']}: Wing is required.")

            if not work:
                errors.append(f"Concrete Entry {row['idx']}: Work is required.")

            if not row["concrete_grade"]:
                errors.append(f"Concrete Entry {row['idx']}: Concrete grade is required.")

            if row["quantity_m3"] <= 0:
                errors.append(f"Concrete Entry {row['idx']}: Quantity must be greater than 0.")

            if row["wing"] and work and row["concrete_grade"] and row["quantity_m3"] > 0:
                payloads.append({
                    "report_date": report_date.isoformat(),
                    "wing": row["wing"],
                    "work": work,
                    "concrete_grade": row["concrete_grade"],
                    "concrete_quantity_m3": row["quantity_m3"],
                })

        if errors:
            for err in errors:
                st.error(err)
        elif not payloads:
            st.error("Enter at least one concrete row before saving.")
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
