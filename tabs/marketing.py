# =============== TAB 7 — Marketing (Supabase: Add + Dashboard + Tables) ===============
if selected_main_section == "Marketing":
    import datetime
    import pandas as pd
    import altair as alt

    MARKETING_TABLE = "marketing_expenditure"

    st.header("📊 Marketing")

    if not supabase_connected:
        st.warning("📋 Please connect to Supabase to use this feature.")
        st.stop()

    # Purpose dropdown options
    purpose_options = [
        "Hoarding", "Channel Partner", "FOS", "WiFi Bill", "Light Bill", "Digital Marketing",
        "Print Advertisement", "Radio Advertisement", "Event Sponsorship", "Brochure Printing", "Kaman",
        "Sales Office & Sample Flat", "Offers", "Referral", "Site Maintenance", "Office Rent",
        "Mobile Internet and Recharge", "Transportation", "Miscellaneous", "Refreshment", "Electrical Appliances",
        "Stage", "Brochures", "Housekeeping", "CP Meet", "Launch Event", "Model", "IVR", "Stationary",
        "Offers", "Sales Office & Sample Flat", "Garden Maintenance"
    ]

    add_tab, dashboard_tab, tables_tab = st.tabs(
        ["🧾 Add Expenditure", "📈 Marketing Dashboard", "📋 Tables & Filters"]
    )

    # ---------------------- Shared caching helpers ----------------------
    if "t7_cache_buster" not in st.session_state:
        st.session_state["t7_cache_buster"] = 0

    def _t7_clear_cache():
        st.session_state["t7_cache_buster"] = st.session_state.get("t7_cache_buster", 0) + 1
        try:
            _load_marketing_df.clear()
            _load_booking_df.clear()
        except Exception:
            try:
                st.cache_data.clear()
            except Exception:
                pass

    def _norm_series(s: pd.Series) -> pd.Series:
        return s.fillna("").astype(str).str.upper().str.strip()

    def _find_col(df_in: pd.DataFrame, candidates: list[str]):
        if df_in is None or df_in.empty:
            return None

        norm_map = {
            str(c).strip().lower().replace(" ", "_").replace("-", "_"): c
            for c in df_in.columns
        }

        for cand in candidates:
            key = str(cand).strip().lower().replace(" ", "_").replace("-", "_")
            if key in norm_map:
                return norm_map[key]

        return None

    @st.cache_data(ttl=180, show_spinner=False)
    def _load_marketing_df(cache_buster: int) -> pd.DataFrame:
        try:
            res = (
                supabase
                .table(MARKETING_TABLE)
                .select("*")
                .order("expense_date", desc=False)
                .execute()
            )
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()

    @st.cache_data(ttl=180, show_spinner=False)
    def _load_booking_df(cache_buster: int) -> pd.DataFrame:
        # Prefer already-loaded app dataframe
        if "booking_df" in globals() and isinstance(booking_df, pd.DataFrame):
            return booking_df.copy()

        if "sheet_df" in globals() and isinstance(sheet_df, pd.DataFrame):
            return sheet_df.copy()

        if "df" in globals() and isinstance(df, pd.DataFrame):
            return df.copy()

        # Optional fallback if your bookings Supabase table is named "bookings"
        try:
            res = supabase.table("bookings").select("*").execute()
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()

    def _prepare_marketing(df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Standard output columns:
          - Amount
          - Purpose
          - Date
          - Month
          - Vendor
          - Remark
          - MonthKey
          - MonthLabel
        """
        if df_raw is None or df_raw.empty:
            return pd.DataFrame(columns=[
                "Amount", "Purpose", "Date", "Month", "Vendor", "Remark", "MonthKey", "MonthLabel"
            ])

        dfm = df_raw.copy()

        # Supabase snake_case -> display columns
        rename_map = {
            "amount": "Amount",
            "purpose": "Purpose",
            "expense_date": "Date",
            "month": "Month",
            "vendor": "Vendor",
            "remark": "Remark",
        }

        dfm = dfm.rename(columns={k: v for k, v in rename_map.items() if k in dfm.columns})

        for c in ["Amount", "Purpose", "Date", "Month", "Vendor", "Remark"]:
            if c not in dfm.columns:
                dfm[c] = ""

        dfm["Amount"] = pd.to_numeric(dfm["Amount"], errors="coerce")
        dfm = dfm.dropna(subset=["Amount"]).copy()

        # Date can be Supabase YYYY-MM-DD or old DD/MM/YYYY
        dfm["Date"] = pd.to_datetime(dfm["Date"], errors="coerce", dayfirst=False)

        # If parse failed, retry dayfirst
        bad_date_mask = dfm["Date"].isna()
        if bad_date_mask.any():
            dfm.loc[bad_date_mask, "Date"] = pd.to_datetime(
                dfm.loc[bad_date_mask, "Date"],
                errors="coerce",
                dayfirst=True
            )

        if dfm["Date"].notna().any():
            dfm["MonthKey"] = _norm_series(dfm["Date"].dt.strftime("%B %y"))
        else:
            dfm["MonthKey"] = _norm_series(dfm["Month"])

        dfm["MonthLabel"] = dfm["MonthKey"].str.title()

        dfm["Purpose"] = dfm["Purpose"].fillna("").astype(str).str.strip()
        dfm["Vendor"] = dfm["Vendor"].fillna("").astype(str).str.strip()
        dfm["Remark"] = dfm["Remark"].fillna("").astype(str).str.strip()

        return dfm

    def _ordered_month_keys(df_in: pd.DataFrame) -> list[str]:
        if df_in is None or df_in.empty or "MonthKey" not in df_in.columns:
            return []

        if "Date" in df_in.columns and df_in["Date"].notna().any():
            tmp = df_in.dropna(subset=["Date"]).copy()
            tmp["MonthPeriod"] = tmp["Date"].dt.to_period("M")
            periods = sorted(tmp["MonthPeriod"].unique())
            return [pd.to_datetime(str(p)).strftime("%B %y").upper() for p in periods]

        try:
            dt = pd.to_datetime(df_in["MonthKey"].str.title(), format="%B %y", errors="coerce")
            out = (
                pd.DataFrame({"k": df_in["MonthKey"], "dt": dt})
                .dropna(subset=["dt"])
                .drop_duplicates(subset=["k"])
                .sort_values("dt")["k"]
                .tolist()
            )
            if out:
                return out
        except Exception:
            pass

        return sorted(df_in["MonthKey"].dropna().unique().tolist())

    def _insert_marketing_row(amount, purpose, expense_date, month, vendor, remark):
        payload = {
            "amount": float(amount),
            "purpose": str(purpose).strip(),
            "expense_date": expense_date.isoformat() if isinstance(expense_date, datetime.date) else None,
            "month": str(month).strip().upper(),
            "vendor": str(vendor).strip(),
            "remark": str(remark or "").strip(),
        }

        supabase.table(MARKETING_TABLE).insert(payload).execute()
        _t7_clear_cache()

    def _format_date_for_display(v):
        if pd.isna(v):
            return ""
        try:
            return pd.to_datetime(v).strftime("%d/%m/%Y")
        except Exception:
            return str(v)

    # ====================== Sub-tab 1: Add Expenditure ======================
    with add_tab:
        st.subheader("➕ Add New Marketing Expenditure")

        with st.form("t7mkt_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                expense_amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    key="t7mkt_amount"
                )

                expense_purpose = st.selectbox(
                    "Purpose",
                    purpose_options,
                    key="t7mkt_purpose",
                    index=purpose_options.index("Digital Marketing") if "Digital Marketing" in purpose_options else 0
                )

                expense_vendor = st.text_input(
                    "Vendor",
                    key="t7mkt_vendor"
                )

            with col2:
                expense_date = st.date_input(
                    "Date",
                    format="DD/MM/YYYY",
                    key="t7mkt_date"
                )

                expense_month_val = expense_date.strftime("%B %y").upper()

                st.text_input(
                    "Month (auto)",
                    value=expense_month_val,
                    disabled=True,
                    key="t7mkt_month"
                )

                expense_remark = st.text_area(
                    "Remark",
                    key="t7mkt_remark",
                    placeholder="Optional remark / notes"
                )

            submitted = st.form_submit_button("💾 Add Expenditure", use_container_width=True)

        if submitted:
            if expense_amount > 0 and expense_purpose and expense_vendor:
                try:
                    _insert_marketing_row(
                        amount=expense_amount,
                        purpose=expense_purpose,
                        expense_date=expense_date,
                        month=expense_month_val,
                        vendor=expense_vendor,
                        remark=expense_remark,
                    )
                    st.toast("✅ Marketing expenditure added!", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.toast(f"❌ Error adding expenditure: {e}", icon="❌")
            else:
                st.toast("⚠️ Please fill Amount, Purpose and Vendor.", icon="⚠️")

    # ====================== Sub-tab 2: Marketing Dashboard ======================
    with dashboard_tab:
        st.markdown("""
        <style>
          :root{
            --bg:#ffffff; --ink:#0f172a; --muted:#475569; --border:#e2e8f0;
            --soft:#f8fafc; --soft-blue:#eff6ff; --soft-green:#ecfdf5; --soft-amber:#fff7ed;
          }
          .md-sub{font-weight:800; font-size:18px; color:var(--ink); margin:8px 0 10px;}
          .kpi{background:var(--bg); border:1px solid var(--border); border-radius:14px; padding:16px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,.06);}
          .kpi h4{margin:0 0 6px; font-size:13px; color:var(--muted); font-weight:700; text-transform:uppercase; letter-spacing:.04em;}
          .kpi p{margin:0; font-size:22px; font-weight:900; color:var(--ink);}
          .kpi.blue  {background:var(--soft-blue);}
          .kpi.green {background:var(--soft-green);}
          .kpi.amber {background:var(--soft-amber);}
          .kpi.gray  {background:#f8fafc;}
        </style>
        """, unsafe_allow_html=True)

        try:
            marketing_df_dash = _prepare_marketing(_load_marketing_df(st.session_state["t7_cache_buster"]))
            booking_df_dash = _load_booking_df(st.session_state["t7_cache_buster"])
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()

        if marketing_df_dash.empty:
            st.info("📋 No marketing expenditure data available. Add some expenditures in the 'Add Expenditure' sub-tab first.")
            st.stop()

        ordered_keys = _ordered_month_keys(marketing_df_dash)
        ordered_months_display = [k.title() for k in ordered_keys]
        display_to_key = {k.title(): k for k in ordered_keys}

        # ---------- KEY METRICS ----------
        total_expense = float(marketing_df_dash["Amount"].sum())

        total_bookings = len(booking_df_dash) if booking_df_dash is not None and not booking_df_dash.empty else 0
        cost_per_booking = (total_expense / total_bookings) if total_bookings > 0 else 0.0

        agreement_col = _find_col(booking_df_dash, ["Agreement Cost", "agreement_cost"])
        if agreement_col:
            total_agreement_value = float(
                pd.to_numeric(booking_df_dash[agreement_col], errors="coerce").fillna(0).sum()
            )
        else:
            total_agreement_value = 0.0

        agreement_spend_percent = (
            total_expense / total_agreement_value * 100
            if total_agreement_value > 0 else 0.0
        )

        RECURRING_PURPOSES = [
            "Hoarding",
            "Digital Marketing",
            "Print Advertisement",
            "Radio Advertisement",
            "Event Sponsorship",
            "Kaman",
            "Refreshment",
            "Housekeeping",
            "Garden Maintenance",
            "Channel Partner",
            "FOS",
            "Referral"
        ]

        _purpose_norm = marketing_df_dash["Purpose"].astype(str).str.strip().str.casefold()
        _recurring_norm = {p.strip().casefold() for p in RECURRING_PURPOSES}

        recurring_expense = float(
            marketing_df_dash.loc[_purpose_norm.isin(_recurring_norm), "Amount"].sum()
        )

        recurring_cost_per_booking = (
            recurring_expense / total_bookings
            if total_bookings > 0 else 0.0
        )

        recurring_spend_percent = (
            recurring_expense / total_agreement_value * 100
            if total_agreement_value > 0 else 0.0
        )

        carpet_col = _find_col(booking_df_dash, ["Carpet Area", "carpet_area"])
        if carpet_col:
            total_carpet_area = float(
                pd.to_numeric(booking_df_dash[carpet_col], errors="coerce").fillna(0).sum()
            )
        else:
            total_carpet_area = 0.0

        AREA_MULTIPLIER = 1.38

        expenditure_per_sqft = (
            total_expense / total_carpet_area * AREA_MULTIPLIER
            if total_carpet_area > 0 else 0.0
        )

        recurring_expenditure_per_sqft = (
            recurring_expense / total_carpet_area * AREA_MULTIPLIER
            if total_carpet_area > 0 else 0.0
        )

        ms = marketing_df_dash.groupby("MonthKey", dropna=True)["Amount"].sum()

        today = pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)
        this_label = today.strftime("%B %y").upper()
        last_label = (today.to_period("M") - 1).to_timestamp().strftime("%B %y").upper()

        this_month_spend = float(ms.get(this_label, 0.0))
        last_month_spend = float(ms.get(last_label, 0.0))

        mom_change_pct = (
            (this_month_spend - last_month_spend) / last_month_spend * 100
            if last_month_spend > 0 else None
        )

        this_txn = int((marketing_df_dash["MonthKey"] == this_label).sum())
        avg_monthly_spend = float(ms.mean()) if not ms.empty else 0.0

        st.markdown("<div class='md-sub'>📌 Key Metrics</div>", unsafe_allow_html=True)

        r1 = st.columns(1)
        with r1[0]:
            st.markdown(
                f"<div class='kpi blue'><h4>Total Spend</h4><p>₹ {total_expense:,.2f}</p></div>",
                unsafe_allow_html=True
            )

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.markdown(
                f"<div class='kpi amber'><h4>Cost per Booking</h4><p>₹ {cost_per_booking:,.0f}</p></div>",
                unsafe_allow_html=True
            )
        with r2c2:
            st.markdown(
                f"<div class='kpi green'><h4>% of Agreement Value</h4><p>{agreement_spend_percent:.2f}%</p></div>",
                unsafe_allow_html=True
            )

        r3c1, r3c2, r3c3 = st.columns(3)
        with r3c1:
            st.markdown(
                f"<div class='kpi gray'><h4>Average Monthly Spend</h4><p>₹ {avg_monthly_spend:,.2f}</p></div>",
                unsafe_allow_html=True
            )
        with r3c2:
            st.markdown(
                f"<div class='kpi blue'><h4>This Month Spend</h4><p>₹ {this_month_spend:,.2f}</p></div>",
                unsafe_allow_html=True
            )
        with r3c3:
            st.markdown(
                f"<div class='kpi gray'><h4>Last Month Spend</h4><p>₹ {last_month_spend:,.2f}</p></div>",
                unsafe_allow_html=True
            )

        r4c1, r4c2 = st.columns(2)
        with r4c1:
            mom_text = "—" if mom_change_pct is None else f"{mom_change_pct:+.1f}%"
            st.markdown(
                f"<div class='kpi green'><h4>MoM Change</h4><p>{mom_text}</p></div>",
                unsafe_allow_html=True
            )
        with r4c2:
            st.markdown(
                f"<div class='kpi amber'><h4>Transactions (This Month)</h4><p>{this_txn}</p></div>",
                unsafe_allow_html=True
            )

        r5c1, r5c2, r5c3 = st.columns(3)
        with r5c1:
            st.markdown(
                f"<div class='kpi blue'><h4>Expenditure (Recurring Expense)</h4><p>₹ {recurring_expense:,.2f}</p></div>",
                unsafe_allow_html=True
            )
        with r5c2:
            st.markdown(
                f"<div class='kpi amber'><h4>Cost/Booking (Recurring Expense)</h4><p>₹ {recurring_cost_per_booking:,.0f}</p></div>",
                unsafe_allow_html=True
            )
        with r5c3:
            st.markdown(
                f"<div class='kpi green'><h4>% of Agreement Value (Recurring Expense)</h4><p>{recurring_spend_percent:.2f}%</p></div>",
                unsafe_allow_html=True
            )

        r6c1, r6c2 = st.columns(2)
        with r6c1:
            st.markdown(
                f"<div class='kpi gray'><h4>Expenditure / Sq ft</h4><p>₹ {expenditure_per_sqft:,.2f}</p></div>",
                unsafe_allow_html=True
            )
        with r6c2:
            st.markdown(
                f"<div class='kpi blue'><h4>Recurring Expenditure / Sq ft</h4><p>₹ {recurring_expenditure_per_sqft:,.2f}</p></div>",
                unsafe_allow_html=True
            )

        # ---------- Monthly Trend ----------
        st.markdown("<div class='md-sub'>📈 Monthly Marketing Expenditure Trend</div>", unsafe_allow_html=True)

        monthly_expenditure = (
            marketing_df_dash.groupby("MonthKey", dropna=True)["Amount"]
            .sum()
            .reindex(ordered_keys, fill_value=0)
        )

        if len(monthly_expenditure) > 0:
            monthly_chart_data = pd.DataFrame({
                "Month": [k.title() for k in monthly_expenditure.index],
                "Amount": monthly_expenditure.values
            })

            line = alt.Chart(monthly_chart_data).mark_line(point=True).encode(
                x=alt.X("Month:N", sort=ordered_months_display, title="Month"),
                y=alt.Y("Amount:Q", title="Total Amount (₹)"),
                tooltip=[
                    alt.Tooltip("Month:N"),
                    alt.Tooltip("Amount:Q", format=",.0f")
                ]
            ).properties(height=360)

            labels = alt.Chart(monthly_chart_data).mark_text(
                align="center",
                baseline="bottom",
                dy=-10,
                fontSize=11,
                fontWeight="bold"
            ).encode(
                x=alt.X("Month:N", sort=ordered_months_display),
                y="Amount:Q",
                text=alt.Text("Amount:Q", format=",.0f")
            )

            st.altair_chart(line + labels, use_container_width=True)
        else:
            st.info("No data for monthly trend.")

        st.divider()

        # ---------- Vendor-wise Expenditure ----------
        st.markdown("<div class='md-sub'>🏢 Vendor-wise Marketing Expenditure</div>", unsafe_allow_html=True)

        if ordered_months_display:
            selected_month_vendor = st.selectbox(
                "Select Month for Vendor Analysis",
                ordered_months_display,
                key="t7_vendor_month"
            )

            sel_key = display_to_key.get(
                selected_month_vendor,
                selected_month_vendor.upper().strip()
            )

            vendor_df = marketing_df_dash[marketing_df_dash["MonthKey"] == sel_key]

            if not vendor_df.empty and "Vendor" in vendor_df.columns:
                vendor_exp = vendor_df.groupby("Vendor", dropna=True)["Amount"].sum().sort_values()
                vendor_chart_data = pd.DataFrame({
                    "Vendor": vendor_exp.index,
                    "Amount": vendor_exp.values
                })

                bars = alt.Chart(vendor_chart_data).mark_bar().encode(
                    x=alt.X("Amount:Q", title="Amount (₹)"),
                    y=alt.Y("Vendor:N", sort="-x", title="Vendor"),
                    tooltip=[
                        alt.Tooltip("Vendor:N"),
                        alt.Tooltip("Amount:Q", format=",.0f")
                    ]
                ).properties(height=max(220, len(vendor_exp) * 28))

                txt = alt.Chart(vendor_chart_data).mark_text(
                    align="left",
                    baseline="middle",
                    dx=5,
                    fontSize=10,
                    fontWeight="bold"
                ).encode(
                    x="Amount:Q",
                    y=alt.Y("Vendor:N", sort="-x"),
                    text=alt.Text("Amount:Q", format=",.0f")
                )

                st.altair_chart(bars + txt, use_container_width=True)
            else:
                st.info("No vendor data to show for the selected month.")

        st.divider()

        # ---------- Purpose-wise Expenditure ----------
        st.markdown("<div class='md-sub'>🎯 Purpose-wise Marketing Expenditure</div>", unsafe_allow_html=True)

        if ordered_months_display:
            selected_month_purpose = st.selectbox(
                "Select Month for Purpose Analysis",
                ordered_months_display,
                key="t7_purpose_month"
            )

            sel_key = display_to_key.get(
                selected_month_purpose,
                selected_month_purpose.upper().strip()
            )

            purpose_df = marketing_df_dash[marketing_df_dash["MonthKey"] == sel_key]

            if not purpose_df.empty and "Purpose" in purpose_df.columns:
                purpose_exp = purpose_df.groupby("Purpose", dropna=True)["Amount"].sum().sort_values(ascending=False)
                purpose_chart_data = pd.DataFrame({
                    "Purpose": purpose_exp.index,
                    "Amount": purpose_exp.values
                })

                bars_p = alt.Chart(purpose_chart_data).mark_bar().encode(
                    x=alt.X("Amount:Q", title="Amount (₹)"),
                    y=alt.Y("Purpose:N", sort="-x", title="Purpose"),
                    tooltip=[
                        alt.Tooltip("Purpose:N"),
                        alt.Tooltip("Amount:Q", format=",.0f")
                    ]
                ).properties(height=max(220, len(purpose_exp) * 28))

                txt_p = alt.Chart(purpose_chart_data).mark_text(
                    align="left",
                    baseline="middle",
                    dx=5,
                    fontSize=10,
                    fontWeight="bold"
                ).encode(
                    x="Amount:Q",
                    y=alt.Y("Purpose:N", sort="-x"),
                    text=alt.Text("Amount:Q", format=",.0f")
                )

                st.altair_chart(bars_p + txt_p, use_container_width=True)
            else:
                st.info("No purpose data to show for the selected month.")

    # ====================== Sub-tab 3: Tables & Filters ======================
    with tables_tab:
        st.subheader("📋 Explore Expenses — Vendor-wise & Purpose-wise")

        try:
            df_tbl_raw = _load_marketing_df(st.session_state["t7_cache_buster"])
            df_tbl = _prepare_marketing(df_tbl_raw)
        except Exception as e:
            st.error(f"Error loading marketing data: {e}")
            st.stop()

        if df_tbl.empty:
            st.info("No marketing expenditure data found. Add some in the 'Add Expenditure' tab.")
            st.stop()

        keys_chrono = _ordered_month_keys(df_tbl)
        keys_desc = (
            list(reversed(keys_chrono))
            if keys_chrono
            else sorted(df_tbl["MonthKey"].dropna().unique().tolist(), reverse=True)
        )

        months_display_desc = [k.title() for k in keys_desc]
        disp_to_key_desc = {k.title(): k for k in keys_desc}
        months_with_all = ["All"] + months_display_desc

        # ---------- Vendor-wise table ----------
        st.markdown("### 🏢 Vendor-wise")

        col_v1, col_v2 = st.columns([1, 2])

        with col_v1:
            v_month_disp = st.selectbox("Month", months_with_all, key="vw_month")

        base_v = df_tbl.copy()

        if v_month_disp != "All":
            k = disp_to_key_desc.get(v_month_disp, v_month_disp.upper().strip())
            base_v = base_v[base_v["MonthKey"] == k]

        vendors_options = sorted(
            base_v.get("Vendor", pd.Series(dtype=str))
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        with col_v2:
            v_vendors = st.multiselect("Vendor", vendors_options, key="vw_vendor")

        vw = base_v.copy()

        if v_vendors:
            vw = vw[vw["Vendor"].astype(str).isin([str(x) for x in v_vendors])]

        if vw.empty:
            st.info("No records for the selected Month/Vendor.")
        else:
            vend_group = (
                vw.dropna(subset=["Vendor"])
                .groupby("Vendor", as_index=False)
                .agg(
                    Total=("Amount", "sum"),
                    Transactions=("Amount", "count"),
                    Avg_per_Txn=("Amount", "mean")
                )
                .sort_values("Total", ascending=False)
            )

            vend_colconf = {
                "Total": st.column_config.NumberColumn("Total (₹)", format="₹ %.2f"),
                "Transactions": st.column_config.NumberColumn("Transactions", format="%d"),
                "Avg_per_Txn": st.column_config.NumberColumn("Avg / Txn (₹)", format="₹ %.2f"),
            }

            st.dataframe(
                vend_group,
                use_container_width=True,
                hide_index=True,
                column_config=vend_colconf
            )

            csv_vend = vend_group.to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download Vendor-wise CSV",
                data=csv_vend,
                file_name="marketing_vendorwise.csv",
                mime="text/csv",
                key="vw_dl",
                use_container_width=True
            )

        st.divider()

        # ---------- Purpose-wise table ----------
        st.markdown("### 🎯 Purpose-wise")

        col_p1, col_p2 = st.columns([1, 2])

        with col_p1:
            p_month_disp = st.selectbox("Month", months_with_all, key="pw_month")

        base_p = df_tbl.copy()

        if p_month_disp != "All":
            k = disp_to_key_desc.get(p_month_disp, p_month_disp.upper().strip())
            base_p = base_p[base_p["MonthKey"] == k]

        purposes_options = sorted(
            base_p.get("Purpose", pd.Series(dtype=str))
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        with col_p2:
            p_purposes = st.multiselect("Purpose", purposes_options, key="pw_purpose")

        pw = base_p.copy()

        if p_purposes:
            pw = pw[pw["Purpose"].astype(str).isin([str(x) for x in p_purposes])]

        if pw.empty:
            st.info("No records for the selected Month/Purpose.")
        else:
            purp_group = (
                pw.dropna(subset=["Purpose"])
                .groupby("Purpose", as_index=False)
                .agg(
                    Total=("Amount", "sum"),
                    Transactions=("Amount", "count"),
                    Avg_per_Txn=("Amount", "mean")
                )
                .sort_values("Total", ascending=False)
            )

            purp_colconf = {
                "Total": st.column_config.NumberColumn("Total (₹)", format="₹ %.2f"),
                "Transactions": st.column_config.NumberColumn("Transactions", format="%d"),
                "Avg_per_Txn": st.column_config.NumberColumn("Avg / Txn (₹)", format="₹ %.2f"),
            }

            st.dataframe(
                purp_group,
                use_container_width=True,
                hide_index=True,
                column_config=purp_colconf
            )

            csv_purp = purp_group.to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download Purpose-wise CSV",
                data=csv_purp,
                file_name="marketing_purposewise.csv",
                mime="text/csv",
                key="pw_dl",
                use_container_width=True
            )

        st.divider()

        # ---------- Detailed records table ----------
        st.markdown("### 🧾 Detailed Marketing Records")

        detail_df = df_tbl.copy()

        dcol1, dcol2, dcol3 = st.columns(3)

        with dcol1:
            d_month = st.selectbox("Detailed Table Month", months_with_all, key="t7_detail_month")

        with dcol2:
            d_vendor_options = sorted(detail_df["Vendor"].dropna().astype(str).unique().tolist())
            d_vendors = st.multiselect("Detailed Table Vendor", d_vendor_options, key="t7_detail_vendor")

        with dcol3:
            d_purpose_options = sorted(detail_df["Purpose"].dropna().astype(str).unique().tolist())
            d_purposes = st.multiselect("Detailed Table Purpose", d_purpose_options, key="t7_detail_purpose")

        if d_month != "All":
            dk = disp_to_key_desc.get(d_month, d_month.upper().strip())
            detail_df = detail_df[detail_df["MonthKey"] == dk]

        if d_vendors:
            detail_df = detail_df[detail_df["Vendor"].astype(str).isin([str(x) for x in d_vendors])]

        if d_purposes:
            detail_df = detail_df[detail_df["Purpose"].astype(str).isin([str(x) for x in d_purposes])]

        if detail_df.empty:
            st.info("No detailed records for selected filters.")
        else:
            detail_show = detail_df[["Date", "MonthLabel", "Purpose", "Vendor", "Amount", "Remark"]].copy()
            detail_show["Date"] = detail_show["Date"].apply(_format_date_for_display)
            detail_show = detail_show.rename(columns={"MonthLabel": "Month"})

            detail_colconf = {
                "Amount": st.column_config.NumberColumn("Amount (₹)", format="₹ %.2f"),
            }

            st.dataframe(
                detail_show,
                use_container_width=True,
                hide_index=True,
                column_config=detail_colconf
            )

            csv_detail = detail_show.to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download Detailed Records CSV",
                data=csv_detail,
                file_name="marketing_detailed_records.csv",
                mime="text/csv",
                key="t7_detail_dl",
                use_container_width=True
            )
