_run_app_file("app_parts/construction_progress_core.py")
_run_app_file("tabs/inventory_status.py")

LABOUR_TABLE = "construction_labour_counts"
CONCRETE_TABLE = "construction_concrete_consumption"


def _dpr_norm_col(name: str) -> str:
    return "".join(ch for ch in str(name or "").lower() if ch.isalnum())


def _dpr_col(df: pd.DataFrame, *names):
    if df is None or df.empty:
        return None
    lookup = {_dpr_norm_col(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(_dpr_norm_col(name))
        if hit:
            return hit
    return None


def _dpr_to_num(value):
    try:
        if pd.isna(value):
            return 0.0
        return float(str(value).replace(",", "").replace("₹", "").replace("Rs", "").strip())
    except Exception:
        return 0.0


def _dpr_date_series(series):
    def parse_one(v):
        if pd.isna(v) or str(v).strip() == "":
            return pd.NaT
        s = str(v).strip()
        if re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", s):
            return pd.to_datetime(s, errors="coerce")
        return pd.to_datetime(s, errors="coerce", dayfirst=True)

    return series.apply(parse_one)


def _dpr_fetch_table(supabase_client, table_name: str) -> pd.DataFrame:
    try:
        response = supabase_client.table(table_name).select("*").execute()
        return pd.DataFrame(response.data or [])
    except Exception as exc:
        st.warning(f"Could not load `{table_name}`. Please run the latest SQL migration. Details: {exc}")
        return pd.DataFrame()


def _dpr_fmt_money(value):
    return f"₹ {int(round(float(value or 0))):,}"


def _dpr_fmt_num(value):
    return f"{float(value or 0):,.2f}".rstrip("0").rstrip(".")


def _dpr_status_done(series):
    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["done", "completed", "yes", "true", "1", "received", "recieved", "given"])
    )


def _dpr_sales_section(bookings_df: pd.DataFrame, target_date: _dt.date):
    st.markdown("## Sales")

    if bookings_df is None or bookings_df.empty:
        st.warning("No booking data available.")
        return pd.DataFrame()

    df = bookings_df.copy()
    date_col = _dpr_col(df, "booking_date", "Date", "Booking Date")
    wing_col = _dpr_col(df, "wing", "Wing")
    flat_col = _dpr_col(df, "flat_number", "Flat Number")
    type_col = _dpr_col(df, "type", "Type")
    exec_col = _dpr_col(df, "sales_executive", "Sales Executive")
    stamp_col = _dpr_col(df, "stamp_duty", "Stamp Duty")
    agreement_col = _dpr_col(df, "agreement_done", "Agreement Done")

    if not date_col:
        st.warning("Booking date column not found.")
        return pd.DataFrame()

    df["_date"] = _dpr_date_series(df[date_col])
    today_df = df[df["_date"].dt.date == target_date].copy()

    total_bookings = len(today_df)
    stamp_received = int(_dpr_status_done(today_df[stamp_col]).sum()) if stamp_col and not today_df.empty else 0
    agreement_done = int(_dpr_status_done(today_df[agreement_col]).sum()) if agreement_col and not today_df.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Bookings", total_bookings)
    c2.metric("Stamp Duty Received", stamp_received)
    c3.metric("Agreement Done", agreement_done)

    if "booking_df" in globals() and "hold_df" in globals():
        try:
            inventory_df = _build_inventory_status_df(booking_df, hold_df)
            inv = inventory_df[inventory_df["Base Category"].eq("OUR")].copy()
            inv_rows = []
            for wing, wing_df in inv.groupby("Wing"):
                total_units = int(len(wing_df))
                sold_units = int(wing_df["Internal Status"].isin(["BOOKED_PENDING", "STAMP_DUTY_RECEIVED", "AGREEMENT_LINEUP", "AGREEMENT_DONE"]).sum())
                balance_units = max(total_units - sold_units, 0)
                inv_rows.append({
                    "Wing": wing,
                    "Our Inventory": total_units,
                    "Sold": sold_units,
                    "Balance": balance_units,
                })
            st.markdown("### Wing-wise Inventory")
            st.dataframe(pd.DataFrame(inv_rows), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"Could not build inventory summary: {exc}")

    st.markdown("### Bookings Done Today")
    if today_df.empty:
        st.info("No bookings done on selected date.")
    else:
        show_cols = [c for c in [exec_col, wing_col, flat_col, type_col] if c]
        show = today_df[show_cols].copy()
        show.columns = ["Sales Executive" if c == exec_col else "Wing" if c == wing_col else "Flat Number" if c == flat_col else "Type" for c in show.columns]
        st.dataframe(show, use_container_width=True, hide_index=True)

    return today_df


def _dpr_cashflow_section(bookings_df: pd.DataFrame):
    st.markdown("## Cashflow")

    if bookings_df is None or bookings_df.empty:
        st.warning("No booking data available.")
        return

    df = bookings_df.copy()
    wing_col = _dpr_col(df, "wing", "Wing")
    agreement_col = _dpr_col(df, "agreement_cost", "Agreement Cost")
    received_col = _dpr_col(df, "received_amount", "Received Amount")
    carpet_col = _dpr_col(df, "carpet_area", "Carpet Area")

    if not agreement_col:
        st.warning("Agreement Cost column not found.")
        return

    df["_agreement"] = df[agreement_col].apply(_dpr_to_num)
    df["_received"] = df[received_col].apply(_dpr_to_num) if received_col else 0.0
    df["_due"] = (df["_agreement"] - df["_received"]).clip(lower=0)
    df["_carpet"] = df[carpet_col].apply(_dpr_to_num) if carpet_col else 0.0

    total_amount = float(df["_agreement"].sum())
    total_received = float(df["_received"].sum())
    total_due = float(df["_due"].sum())
    carpet_sold = float(df["_carpet"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Amount", _dpr_fmt_money(total_amount))
    c2.metric("Received", _dpr_fmt_money(total_received))
    c3.metric("Due", _dpr_fmt_money(total_due))
    c4.metric("Carpet Area Sold", f"{_dpr_fmt_num(carpet_sold)} sqft")

    if wing_col:
        wing_summary = (
            df.groupby(wing_col, as_index=False)
            .agg(
                **{
                    "Total Amount": ("_agreement", "sum"),
                    "Received": ("_received", "sum"),
                    "Due": ("_due", "sum"),
                    "Carpet Area Sold": ("_carpet", "sum"),
                }
            )
            .rename(columns={wing_col: "Wing"})
        )
        for col in ["Total Amount", "Received", "Due"]:
            wing_summary[col] = wing_summary[col].apply(_dpr_fmt_money)
        wing_summary["Carpet Area Sold"] = wing_summary["Carpet Area Sold"].apply(lambda x: f"{_dpr_fmt_num(x)} sqft")
        st.markdown("### Wing-wise Cashflow")
        st.dataframe(wing_summary, use_container_width=True, hide_index=True)


def _dpr_construction_work_done(floor_df, flat_df, floor_col_map, flat_col_map, target_date: _dt.date):
    rows = []

    if floor_df is not None and not floor_df.empty:
        for _, floor_row in floor_df.iterrows():
            completed = []
            for cp in _active_rcc_checkpoints(floor_row):
                col = floor_col_map.get(cp)
                if col:
                    d = _parse_date(floor_row.get(col))
                    if pd.notna(d) and d.date() == target_date:
                        completed.append(cp.label)
            if completed:
                rows.append({
                    "Wing": _wing_value(floor_row),
                    "Floor / Level": _level_label(floor_row),
                    "Main Work": "RCC Work",
                    "Work Done": ", ".join(completed),
                })

    if flat_df is not None and not flat_df.empty:
        for _, flat_row in flat_df.iterrows():
            done_by_heading = {}
            for cp in FLAT_CHECKPOINTS:
                col = flat_col_map.get(cp)
                if not col:
                    continue
                d = _parse_date(flat_row.get(col))
                if pd.notna(d) and d.date() == target_date:
                    done_by_heading.setdefault(cp.heading, []).append(f"{_flat_label(flat_row)}: {cp.label}")
            for heading, items in done_by_heading.items():
                rows.append({
                    "Wing": _wing_value(flat_row),
                    "Floor / Level": f"Floor {_floor_no(flat_row)}",
                    "Main Work": heading,
                    "Work Done": "; ".join(items),
                })

    return pd.DataFrame(rows)


def _dpr_construction_section(supabase_client, target_date: _dt.date):
    st.markdown("## Construction")

    labour_df = _dpr_fetch_table(supabase_client, LABOUR_TABLE)
    concrete_df = _dpr_fetch_table(supabase_client, CONCRETE_TABLE)

    if not labour_df.empty:
        labour_df["report_date"] = _dpr_date_series(labour_df["report_date"])
        labour_today = labour_df[labour_df["report_date"].dt.date == target_date].copy()
    else:
        labour_today = pd.DataFrame()

    if not labour_today.empty:
        staff_cols = ["project_manager", "senior_engineer", "junior_engineer", "supervisor"]
        labour_cols = ["carpenter", "fitter", "mason", "unskilled", "others"]

        st.markdown("### Contractor-wise Staff Count")
        staff = (
            labour_today.groupby("contractor_name", as_index=False)[staff_cols]
            .sum()
            .rename(columns={
                "contractor_name": "Contractor",
                "project_manager": "Project Manager",
                "senior_engineer": "Senior Engineer",
                "junior_engineer": "Junior Engineer",
                "supervisor": "Supervisor",
            })
        )
        st.dataframe(staff, use_container_width=True, hide_index=True)

        st.markdown("### Wing-wise Contractor-wise Labour Count")
        labour = (
            labour_today.groupby(["wing", "contractor_name"], as_index=False)[labour_cols]
            .sum()
            .rename(columns={
                "wing": "Wing",
                "contractor_name": "Contractor",
                "carpenter": "Carpenter",
                "fitter": "Fitter",
                "mason": "Mason",
                "unskilled": "Unskilled",
                "others": "Others",
            })
        )
        st.dataframe(labour, use_container_width=True, hide_index=True)
    else:
        st.info("No labour/staff entries found for selected date.")

    if not concrete_df.empty:
        concrete_df["report_date"] = _dpr_date_series(concrete_df["report_date"])
        concrete_today = concrete_df[concrete_df["report_date"].dt.date == target_date].copy()
    else:
        concrete_today = pd.DataFrame()

    st.markdown("### Concrete Consumption")
    if concrete_today.empty:
        st.info("No concrete consumption entries found for selected date.")
    else:
        concrete_summary = (
            concrete_today.groupby(["wing", "work"], as_index=False)["concrete_quantity_m3"]
            .sum()
            .rename(columns={
                "wing": "Wing",
                "work": "Work",
                "concrete_quantity_m3": "Concrete Quantity (M3)",
            })
        )
        st.dataframe(concrete_summary, use_container_width=True, hide_index=True)

    floor_df, flat_df = _load_data(supabase_client)
    floor_col_map = _column_lookup(floor_df, RCC_CHECKPOINTS)
    flat_col_map = _column_lookup(flat_df, FLAT_CHECKPOINTS)
    work_done_df = _dpr_construction_work_done(floor_df, flat_df, floor_col_map, flat_col_map, target_date)

    st.markdown("### Work Done Today")
    if work_done_df.empty:
        st.info("No construction checkpoints were marked done on selected date.")
    else:
        work_done_df = work_done_df.sort_values(["Wing", "Floor / Level", "Main Work"])
        st.dataframe(work_done_df, use_container_width=True, hide_index=True)


st.header("Daily Progress Report")

supabase_client = globals().get("supabase", None) or globals().get("supabase_client", None)

if supabase_client is None:
    st.warning("Supabase client is not initialized.")
else:
    report_date = st.date_input(
        "Report Date",
        value=_dt.date.today(),
        format="DD/MM/YYYY",
        key="daily_progress_report_date",
    )

    bookings_source = booking_df.copy() if "booking_df" in globals() and isinstance(booking_df, pd.DataFrame) else pd.DataFrame()

    _dpr_sales_section(bookings_source, report_date)
    _dpr_cashflow_section(bookings_source)
    _dpr_construction_section(supabase_client, report_date)
