if selected_main_section == "Sales Target":
    import re
    import datetime
    import pandas as pd
    import altair as alt
    import streamlit as st

    st.header("🎯 Sales Executive Monthly Booking Targets")
    st.caption("Submit this month’s booking targets once. After submission, the month is locked.")

    # ============================================================
    # SUPABASE CONNECTION
    # ============================================================
    supabase_client = globals().get("supabase", None) or globals().get("supabase_client", None)

    if supabase_client is None:
        st.error("Supabase client is not initialized. Please check your Supabase connection block.")
        st.stop()

    SALES_TARGET_TABLE = "sales_targets"
    BOOKINGS_TABLE = "bookings"

    SALES_EXECUTIVES = [
        {"name": "Tejas P", "col": "tejas_p"},
        {"name": "Ashutosh S", "col": "ashutosh_s"},
        {"name": "Komal K", "col": "komal_k"},
        {"name": "Sailee D", "col": "sailee_d"},
        {"name": "Harshal S", "col": "harshal_s"},
        {"name": "Alok R", "col": "alok_r"},
        {"name": "Sagar B", "col": "sagar_b"},
        {"name": "Advait M", "col": "advait_m"},
        {"name": "Dhanashree W", "col": "dhanashree_w"},
    ]

    # ============================================================
    # HELPERS
    # ============================================================
    def _safe_str(x):
        if x is None:
            return ""
        try:
            if pd.isna(x):
                return ""
        except Exception:
            pass
        s = str(x).strip()
        if s.endswith(".0"):
            s = s[:-2]
        return s

    def _norm_col(x):
        return re.sub(r"[^a-z0-9]+", "", str(x or "").lower())

    def _col(df: pd.DataFrame, *names):
        if df is None or df.empty:
            return None

        cmap = {_norm_col(c): c for c in df.columns}

        for name in names:
            key = _norm_col(name)
            if key in cmap:
                return cmap[key]

        return None

    def _to_num(x):
        try:
            if x is None or pd.isna(x):
                return 0.0

            s = str(x).replace("₹", "").replace("Rs.", "").replace("Rs", "").replace(",", "").strip()

            if s == "":
                return 0.0

            return float(s)

        except Exception:
            return 0.0

    def _pct(num, den):
        den = _to_num(den)
        num = _to_num(num)

        if den <= 0:
            return 0.0

        return (num / den) * 100.0

    def _fmt_pct(x):
        try:
            return f"{float(x):.1f}%"
        except Exception:
            return "0.0%"

    def _parse_date_series(series):
        return pd.to_datetime(series, errors="coerce", dayfirst=True)

    def _style_table(df):
        return (
            df.style
            .set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#2563eb"),
                        ("color", "white"),
                        ("font-weight", "900"),
                        ("text-align", "center"),
                    ],
                },
                {
                    "selector": "td",
                    "props": [
                        ("text-align", "center"),
                        ("font-weight", "700"),
                    ],
                },
            ])
        )

    @st.cache_data(ttl=180, show_spinner=False)
    def _sb_select_all(table_name: str, order_col: str | None = None) -> list[dict]:
        rows = []
        page_size = 1000
        start = 0

        while True:
            query = supabase_client.table(table_name).select("*")

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

    def _load_table(table_name: str, order_col: str | None = None) -> pd.DataFrame:
        try:
            rows = _sb_select_all(table_name, order_col)
            return pd.DataFrame(rows)
        except Exception as e:
            st.warning(f"Could not load `{table_name}`: {e}")
            return pd.DataFrame()

    def _insert_sales_target(row: dict):
        return supabase_client.table(SALES_TARGET_TABLE).insert(row).execute()

    # ============================================================
    # CURRENT MONTH
    # ============================================================
    today = datetime.date.today()
    current_month_label = today.strftime("%B %y").upper()

    # Example: APRIL 25
    # This is stored in sales_targets.month

    # ============================================================
    # CSS
    # ============================================================
    st.markdown(
        """
        <style>
        .target-section-card {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            border-radius: 18px;
            padding: 18px 20px;
            text-align: center;
            font-size: 24px;
            font-weight: 900;
            margin: 22px 0 16px 0;
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.25);
        }

        .target-kpi {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 14px;
            text-align: center;
            min-height: 105px;
            box-shadow: 0 8px 18px rgba(15,23,42,.06);
            margin-bottom: 12px;
        }

        .target-kpi h4 {
            margin: 0;
            font-size: 12px;
            color: #475569;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: .04em;
        }

        .target-kpi p {
            margin: 8px 0 0;
            font-size: 28px;
            color: #0f172a;
            font-weight: 900;
        }

        .target-kpi span {
            display: block;
            margin-top: 6px;
            font-size: 12px;
            color: #64748b;
            font-weight: 700;
        }

        .target-blue { background: #eff6ff; }
        .target-green { background: #ecfdf5; }
        .target-amber { background: #fff7ed; }
        .target-red { background: #fef2f2; }
        </style>
        """,
        unsafe_allow_html=True
    )

    def section_card(title):
        st.markdown(
            f"<div class='target-section-card'>{title}</div>",
            unsafe_allow_html=True
        )

    def kpi_card(title, value, sub="", tone="target-blue"):
        st.markdown(
            f"""
            <div class="target-kpi {tone}">
              <h4>{title}</h4>
              <p>{value}</p>
              <span>{sub}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ============================================================
    # LOAD DATA
    # ============================================================
    if st.button("🔄 Refresh Target Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    targets_df = _load_table(SALES_TARGET_TABLE)
    bookings_df = _load_table(BOOKINGS_TABLE)

    # ============================================================
    # BOOKING ACHIEVED DATA — USE DATE COLUMN ONLY
    # ============================================================
    b_date_col = _col(bookings_df, "booking_date", "date", "Date")
    b_sales_exec_col = _col(bookings_df, "sales_executive", "Sales Executive")

    if not bookings_df.empty:
        bookings_work = bookings_df.copy()

        if b_date_col:
            bookings_work["_BookingDate"] = _parse_date_series(bookings_work[b_date_col])
            bookings_work["_Month"] = bookings_work["_BookingDate"].dt.strftime("%B %y").str.upper()
        else:
            bookings_work["_BookingDate"] = pd.NaT
            bookings_work["_Month"] = ""

        if b_sales_exec_col:
            bookings_work["_SalesExecutive"] = bookings_work[b_sales_exec_col].fillna("").astype(str).str.strip()
        else:
            bookings_work["_SalesExecutive"] = ""

        bookings_work = bookings_work[
            bookings_work["_BookingDate"].notna() &
            bookings_work["_SalesExecutive"].ne("")
        ].copy()

    else:
        bookings_work = pd.DataFrame()

    # Current month achieved bookings
    if not bookings_work.empty:
        current_month_bookings = bookings_work[
            bookings_work["_Month"] == current_month_label
        ].copy()

        achieved_df = (
            current_month_bookings
            .groupby("_SalesExecutive", as_index=False)
            .size()
            .rename(columns={
                "_SalesExecutive": "Sales Executive",
                "size": "Achieved",
            })
        )
    else:
        achieved_df = pd.DataFrame(columns=["Sales Executive", "Achieved"])

    # ============================================================
    # CURRENT MONTH TARGET ROW
    # ============================================================
    if not targets_df.empty and "month" in targets_df.columns:
        targets_work = targets_df.copy()
        targets_work["month"] = targets_work["month"].fillna("").astype(str).str.strip().str.upper()

        current_target_rows = targets_work[
            targets_work["month"] == current_month_label
        ].copy()
    else:
        targets_work = pd.DataFrame()
        current_target_rows = pd.DataFrame()

    month_is_locked = not current_target_rows.empty

    # ============================================================
    # TARGET SUMMARY
    # ============================================================
    target_row = {}

    if month_is_locked:
        target_row = current_target_rows.iloc[0].to_dict()

    total_target = 0

    if target_row:
        for ex in SALES_EXECUTIVES:
            total_target += int(_to_num(target_row.get(ex["col"], 0)))

    total_achieved = int(achieved_df["Achieved"].sum()) if not achieved_df.empty else 0
    total_pending = max(total_target - total_achieved, 0)
    achievement_pct = _pct(total_achieved, total_target)

    # ============================================================
    # KPI CARDS
    # ============================================================
    section_card(f"🎯 {current_month_label} Target Summary")

    k1, k2, k3 = st.columns(3)

    with k1:
        kpi_card("Month", current_month_label, "Current target month", "target-blue")

    with k2:
        kpi_card("Target", f"{total_target:,}", "Total booking target", "target-amber")

    with k3:
        kpi_card("Achieved", f"{total_achieved:,}", f"Pending: {total_pending:,} | {_fmt_pct(achievement_pct)}", "target-green")

    # ============================================================
    # TARGET ENTRY FORM
    # ============================================================
    section_card("📝 Monthly Target Entry")

    if month_is_locked:
        st.info("This month’s target is already submitted and locked.")

        locked_rows = []

        for ex in SALES_EXECUTIVES:
            locked_rows.append({
                "Sales Executive": ex["name"],
                "Target": int(_to_num(target_row.get(ex["col"], 0))),
            })

        locked_display = pd.DataFrame(locked_rows)

        st.dataframe(
            _style_table(locked_display),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning("Enter target booking count for every Sales Executive. Once submitted, this month will be locked.")

        with st.form("sales_exec_monthly_targets_form", clear_on_submit=False):
            target_values = {}

            for ex in SALES_EXECUTIVES:
                c1, c2 = st.columns([2, 1])

                with c1:
                    st.markdown(f"**{ex['name']}**")

                with c2:
                    target_values[ex["col"]] = st.number_input(
                        "Target",
                        min_value=0,
                        step=1,
                        value=0,
                        key=f"target_{ex['col']}",
                        label_visibility="collapsed"
                    )

            submit_targets = st.form_submit_button(
                "🔒 Submit Monthly Targets",
                use_container_width=True
            )

        if submit_targets:
            row_to_insert = {
                "month": current_month_label,
            }

            for ex in SALES_EXECUTIVES:
                row_to_insert[ex["col"]] = int(target_values.get(ex["col"], 0) or 0)

            try:
                _insert_sales_target(row_to_insert)
                st.cache_data.clear()
                st.success("✅ Monthly targets submitted and locked successfully.")
                st.rerun()

            except Exception as e:
                st.error(f"Could not save targets. Target for this month may already exist. Error: {e}")

    # ============================================================
    # TARGET VS ACHIEVED TABLE
    # ============================================================
    section_card("📊 Target vs Achieved")

    rows = []

    for ex in SALES_EXECUTIVES:
        target_val = int(_to_num(target_row.get(ex["col"], 0))) if target_row else 0

        achieved_match = achieved_df[
            achieved_df["Sales Executive"].astype(str).str.strip().str.casefold() == ex["name"].casefold()
        ]

        achieved_val = int(achieved_match["Achieved"].sum()) if not achieved_match.empty else 0

        rows.append({
            "Sales Executive": ex["name"],
            "Target": target_val,
            "Achieved": achieved_val,
            "Pending": max(target_val - achieved_val, 0),
            "Achievement %": _fmt_pct(_pct(achieved_val, target_val)),
        })

    performance_df = pd.DataFrame(rows)

    st.dataframe(
        _style_table(performance_df),
        use_container_width=True,
        hide_index=True
    )

    # ============================================================
    # GRAPH — TARGET VS ACHIEVED
    # ============================================================
    if not performance_df.empty:
        chart_df = performance_df[["Sales Executive", "Target", "Achieved"]].copy()

        chart_long = chart_df.melt(
            id_vars="Sales Executive",
            var_name="Metric",
            value_name="Bookings"
        )

        bar = alt.Chart(chart_long).mark_bar().encode(
            x=alt.X("Sales Executive:N", title="Sales Executive"),
            xOffset=alt.XOffset("Metric:N"),
            y=alt.Y("Bookings:Q", title="Bookings"),
            color=alt.Color(
                "Metric:N",
                scale=alt.Scale(range=["#2563eb", "#10b981"])
            ),
            tooltip=[
                "Sales Executive:N",
                "Metric:N",
                alt.Tooltip("Bookings:Q", format=",")
            ]
        ).properties(
            height=360,
            title="Current Month — Target vs Achieved"
        )

        labels = alt.Chart(chart_long).mark_text(
            dy=-8,
            fontSize=12,
            fontWeight="bold"
        ).encode(
            x=alt.X("Sales Executive:N"),
            xOffset=alt.XOffset("Metric:N"),
            y=alt.Y("Bookings:Q"),
            text=alt.Text("Bookings:Q", format=","),
            color=alt.value("#0f172a")
        )

        st.altair_chart(bar + labels, use_container_width=True)
