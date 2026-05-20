# ------------------------------------------------------------
# TAB 2: Combined Tools - Supabase Compatible
# ------------------------------------------------------------
if selected_main_section == "Calculators":
    import math
    import re
    import base64
    import numpy as np
    import pandas as pd
    import streamlit as st
    from fpdf import FPDF

    # ============================================================
    # Supabase-compatible booking dataframe prep
    # ============================================================
    def _tab2_safe_text(v):
        if pd.isna(v):
            return ""
        return str(v).strip()

    def _tab2_to_num(x):
        if pd.isna(x):
            return np.nan
        s = (
            str(x)
            .replace("₹", "")
            .replace("Rs", "")
            .replace("rs", "")
            .replace("INR", "")
            .replace("inr", "")
            .replace(",", "")
            .strip()
        )
        try:
            return float(s)
        except Exception:
            return np.nan

    def _tab2_prepare_bookings_df():
        if "booking_df" in globals() and isinstance(booking_df, pd.DataFrame):
            out = booking_df.copy()
        elif "sheet_df" in globals() and isinstance(sheet_df, pd.DataFrame):
            out = sheet_df.copy()
        elif "df" in globals() and isinstance(df, pd.DataFrame):
            out = df.copy()
        else:
            out = pd.DataFrame()

        rename_map = {
            "booking_date": "Date",
            "customer_name": "Customer Name",
            "wing": "Wing",
            "floor": "Floor",
            "flat_number": "Flat Number",
            "type": "Type",
            "final_price": "Final Price",
            "rate": "Rate",
            "agreement_cost": "Agreement Cost",
            "lead_type": "Lead Type",
            "sales_executive": "Sales Executive",
            "month": "Month",
            "civil_changes": "Civil Changes",
            "offer_1": "Offer 1",
            "offer_2": "Offer 2",
            "offer_1_rewarded": "Offer 1 Rewarded",
            "offer_2_rewarded": "Offer 2 Rewarded",
            "referral_given": "Referral Given",
            "stamp_duty": "Stamp Duty",
            "agreement_done": "Agreement Done",
            "incentive": "Incentive",
            "rcc": "RCC",
            "possession_handover": "POSSESSION HANDOVER",
            "insider_banker": "Insider Banker",
            "outsider_banker": "Outsider Banker",
            "carpet_area": "Carpet Area",
            "booking_amount": "Booking Amount",
            "agreement": "Agreement",
            "plinth": "Plinth",
            "third_floor": "Third Floor",
            "seventh_floor": "Seventh Floor",
            "tenth_floor": "Tenth Floor",
            "thirteenth_floor": "Thirteenth Floor",
            "flooring": "Flooring",
            "plastering": "Plastering",
            "plumbing": "Plumbing",
            "electrical": "Electrical",
            "sanitary_lift": "Sanitary Lift",
            "possession": "Possession",
            "first_visit_date": "First Visit Date",
            "conversion_period_days": "Conversion Period (days)",
            "parking_number": "Parking Number",
            "merged_units": "Merged Units",
            "location": "Location",
            "visit_count": "Visit Count",
            "received_amount": "Received Amount",
            "stamp_duty_percent": "Stamp Duty Percent",
        }

        for old_col, new_col in rename_map.items():
            if old_col in out.columns and new_col not in out.columns:
                out[new_col] = out[old_col]

        required_cols = [
            "Date",
            "Customer Name",
            "Wing",
            "Floor",
            "Flat Number",
            "Type",
            "Final Price",
            "Rate",
            "Agreement Cost",
            "Lead Type",
            "Sales Executive",
            "Month",
            "Stamp Duty",
            "Agreement Done",
            "Incentive",
            "Carpet Area",
            "Conversion Period (days)",
        ]

        for col in required_cols:
            if col not in out.columns:
                out[col] = ""

        if "id" not in out.columns:
            out["id"] = None

        out["Date"] = pd.to_datetime(out["Date"], errors="coerce", dayfirst=True)

        if out["Month"].astype(str).str.strip().eq("").all():
            out["Month"] = out["Date"].dt.strftime("%B %y")

        out["MonthYear"] = out["Month"].astype(str).str.strip()

        if "Quarter" not in out.columns:
            if "get_custom_quarter_label" in globals():
                out["Quarter"] = out["Date"].apply(
                    lambda d: get_custom_quarter_label(d) if pd.notna(d) else ""
                )
            else:
                def _fallback_quarter_label(d):
                    if pd.isna(d):
                        return ""
                    year = d.year
                    if d.month in [4, 5, 6]:
                        return f"April-June {year}"
                    elif d.month in [7, 8, 9]:
                        return f"July-September {year}"
                    elif d.month in [10, 11, 12]:
                        return f"October-December {year}"
                    else:
                        return f"January-March {year}"

                out["Quarter"] = out["Date"].apply(_fallback_quarter_label)

        text_cols = [
            "Customer Name",
            "Wing",
            "Flat Number",
            "Type",
            "Lead Type",
            "Sales Executive",
            "Month",
            "MonthYear",
            "Quarter",
            "Stamp Duty",
            "Agreement Done",
            "Incentive",
        ]

        for col in text_cols:
            if col in out.columns:
                out[col] = out[col].apply(_tab2_safe_text)

        out["Agreement Cost"] = pd.to_numeric(
            out["Agreement Cost"].apply(_tab2_to_num),
            errors="coerce"
        ).fillna(0)

        out["Carpet Area"] = pd.to_numeric(
            out["Carpet Area"].apply(_tab2_to_num),
            errors="coerce"
        ).fillna(0)

        out["Rate"] = pd.to_numeric(
            out["Rate"].apply(_tab2_to_num),
            errors="coerce"
        )

        out["Floor"] = out["Floor"].apply(_tab2_safe_text)

        return out

    df_tab2 = _tab2_prepare_bookings_df()

    # ============================
    # Combined Tools in Sub-Tabs
    # ============================
    ST_RATE, ST_REVERSE, ST_CP, ST_INCENTIVE, ST_INCENTIVE_STATUS = st.tabs([
        "Rate Calculator",
        "Reverse Rate Calculator",
        "CP Payout Calculator",
        "Incentive Calculator",
        "Incentive Status"
    ])

    # ------------------------------------------------------------------
    # SUBTAB 1 — RATE CALCULATOR
    # ------------------------------------------------------------------
    with ST_RATE:
        st.markdown("""
        <style>
          :root{
            --ink:#0f172a; --muted:#475569; --border:#e2e8f0; --bg:#ffffff;
            --soft:#f8fafc; --card:#ffffff;
            --green:#ecfdf5; --amber:#fff7ed; --red:#fef2f2;
          }
          .tool-wrap{border:1px solid var(--border); background:var(--card); border-radius:16px; padding:18px; margin:18px 0;
                     box-shadow:0 8px 18px rgba(15,23,42,.06);}
          .tool-title{font-weight:900;font-size:22px;color:var(--ink);margin-bottom:4px;}
          .subtext{color:var(--muted);font-size:13px;margin-top:-4px;margin-bottom:10px;}
          .result-card{border:1px dashed var(--border); background:var(--soft); border-radius:12px; padding:12px 14px; margin-top:12px}
          .result-row{display:flex; justify-content:space-between; gap:10px; padding:8px 0; border-bottom:1px solid #edf2f7}
          .result-row:last-child{border-bottom:none}
          .label{font-weight:700;color:var(--muted);font-size:13px}
          .value{font-weight:900;color:var(--ink);font-size:18px}
          .note{border:1px solid var(--border); border-left-width:6px; border-radius:10px; padding:10px 12px; margin-top:12px;}
          .note.good{background:var(--green); border-left-color:#10b981}
          .note.ok{background:var(--amber); border-left-color:#f59e0b}
          .note.bad{background:var(--red); border-left-color:#ef4444}
          .section-divider{height:1px;background:#e2e8f0;margin:28px 0}
        </style>
        """, unsafe_allow_html=True)

        ALL_CARPETS = [480.94, 482.12, 655.10, 665.65, 666.29]

        st.markdown(
            '<div class="tool-wrap"><div class="tool-title">🧮 Rate Calculator</div>'
            '<div class="subtext">Computes per-sqft rates with & without Channel Partner deduction.</div>',
            unsafe_allow_html=True
        )

        with st.form("rate_calc_form", clear_on_submit=False):
            rc_col1, rc_col2 = st.columns(2)

            with rc_col1:
                cost_lakhs = st.number_input(
                    "Enter Cost (in Lakhs)",
                    min_value=0.0,
                    step=0.1,
                    key="rc_cost_lakhs"
                )

            with rc_col2:
                carpet_area = st.selectbox(
                    "Select Carpet Area",
                    options=ALL_CARPETS,
                    key="rc_carpet_area"
                )

            cp_percentage = st.number_input(
                "Channel Partner %",
                min_value=0.0,
                step=0.1,
                key="rc_cp_percentage"
            )

            rc_submit = st.form_submit_button("Calculate Rate")

        if rc_submit and (cost_lakhs is not None) and (cp_percentage is not None) and (carpet_area is not None):
            saleable_area = round(carpet_area * 1.38, 2)
            adjusted_cost = (cost_lakhs * 100000) - 30000

            gst_divisor = 1.0

            if 662 <= saleable_area <= 667:
                gst_divisor = 1.08
            elif 903 <= saleable_area <= 920:
                gst_divisor = 1.12

            pre_cp_value = adjusted_cost / gst_divisor
            rate_excl_cp = round(pre_cp_value / saleable_area)

            after_cp_deduction = ((pre_cp_value - 400000) * (1 - cp_percentage / 100)) + 400000
            rate_incl_cp = round(after_cp_deduction / saleable_area)

            if rate_excl_cp >= 6000:
                remark = ("BECH DO AACHA RATE HAI", "good")
            elif 5800 <= rate_excl_cp <= 5999:
                remark = ("AACHA RATE HAI LEKIN THODA UPAR CLOSE KARNE KA TRY KARO", "ok")
            else:
                remark = ("ISPE KIYA AUR INCENTIVE GAYA", "bad")

            st.markdown(f"""
            <div class="result-card">
              <div class="result-row"><div class="label">Saleable Area</div><div class="value">{saleable_area:,} sq.ft</div></div>
              <div class="result-row"><div class="label">Per Sqft Rate (Excl. CP)</div><div class="value">₹ {rate_excl_cp:,}</div></div>
              <div class="result-row"><div class="label">Per Sqft Rate (Incl. CP)</div><div class="value">₹ {rate_incl_cp:,}</div></div>
            </div>
            <div class="note {remark[1]}">💡 {remark[0]}</div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # SUBTAB 2 — REVERSE RATE CALCULATOR
    # ------------------------------------------------------------------
    with ST_REVERSE:
        st.markdown("""
        <style>
          :root{
            --ink:#0f172a; --muted:#475569; --border:#e2e8f0; --bg:#ffffff;
            --soft:#f8fafc; --card:#ffffff;
          }
          .tool-wrap{border:1px solid var(--border); background:var(--card); border-radius:16px; padding:18px; margin:18px 0;
                     box-shadow:0 8px 18px rgba(15,23,42,.06);}
          .tool-title{font-weight:900;font-size:22px;color:var(--ink);margin-bottom:4px;}
          .subtext{color:var(--muted);font-size:13px;margin-top:-4px;margin-bottom:10px;}
          .result-card{border:1px dashed var(--border); background:var(--soft); border-radius:12px; padding:12px 14px; margin-top:12px}
          .result-row{display:flex; justify-content:space-between; gap:10px; padding:8px 0; border-bottom:1px solid #edf2f7}
          .result-row:last-child{border-bottom:none}
          .label{font-weight:700;color:var(--muted);font-size:13px}
          .value{font-weight:900;color:var(--ink);font-size:18px}
          .section-divider{height:1px;background:#e2e8f0;margin:28px 0}
        </style>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div class="tool-wrap"><div class="tool-title">🔄 Reverse Rate Calculator</div>'
            '<div class="subtext">Back-calculates total package from a given PSF rate.</div>',
            unsafe_allow_html=True
        )

        with st.form("reverse_rate_form", clear_on_submit=False):
            psf_rate = st.number_input(
                "Enter Per Square Feet Rate",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                key="rev_psf_rate"
            )

            rev_submit = st.form_submit_button("Calculate Total Cost")

        if rev_submit and psf_rate > 0:
            for carpet in [480.94, 482.12, 655.1, 665.65, 666.29, 678, 689, 790, 545, 756]:
                saleable_area = carpet * 1.38
                base_cost = saleable_area * psf_rate

                stamp_duty = base_cost * 0.07
                gst_rate = 0.01 if carpet in [480.94, 482.12] else 0.05
                gst = base_cost * gst_rate
                registration = 30000
                total_cost = base_cost + stamp_duty + gst + registration

                st.markdown(f"""
                <div class="result-card">
                  <div class="result-row"><div class="label">Carpet Area</div><div class="value">{carpet} sq.ft</div></div>
                  <div class="result-row"><div class="label">Total Flat Cost</div><div class="value">₹{total_cost:,.2f}</div></div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # SUBTAB 3 — CP PAYOUT CALCULATOR
    # ------------------------------------------------------------------
    with ST_CP:
        st.markdown("""
        <style>
          :root{
            --ink:#0f172a; --muted:#475569; --border:#e2e8f0; --bg:#ffffff;
            --soft:#f8fafc; --card:#ffffff;
          }
          .tool-wrap{border:1px solid var(--border); background:var(--card); border-radius:16px; padding:18px; margin:18px 0;
                     box-shadow:0 8px 18px rgba(15,23,42,.06);}
          .tool-title{font-weight:900;font-size:22px;color:var(--ink);margin-bottom:4px;}
          .subtext{color:var(--muted);font-size:13px;margin-top:-4px;margin-bottom:10px;}
          .result-card{border:1px dashed var(--border); background:var(--soft); border-radius:12px; padding:12px 14px; margin-top:12px}
          .result-row{display:flex; justify-content:space-between; gap:10px; padding:8px 0; border-bottom:1px solid #edf2f7}
          .result-row:last-child{border-bottom:none}
          .label{font-weight:700;color:var(--muted);font-size:13px}
          .value{font-weight:900;color:var(--ink);font-size:18px}
        </style>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div class="tool-wrap"><div class="tool-title">💰 CP Payout Calculator</div>'
            '<div class="subtext">Computes CP payout on final cost after adjustments.</div>',
            unsafe_allow_html=True
        )

        with st.form("cp_payout_form", clear_on_submit=False):
            final_cost_lakhs = st.number_input(
                "Enter Final Cost (in lakhs)",
                min_value=0.0,
                step=0.1,
                key="cp_final_cost"
            )

            cp_percent = st.number_input(
                "Enter Channel Partner %",
                min_value=0.0,
                step=0.1,
                key="cp_percent"
            )

            cp_submit = st.form_submit_button("Calculate CP Payout")

        if cp_submit and (final_cost_lakhs > 0) and (cp_percent > 0):
            final_cost = final_cost_lakhs * 100000
            cost = final_cost - 30000
            cost /= 1.07

            if final_cost_lakhs < 50:
                cost /= 1.01
            else:
                cost /= 1.05

            basic_cost = cost - 400000
            cp_payout = basic_cost * (cp_percent / 100)

            st.markdown(f"""
            <div class="result-card">
              <div class="result-row"><div class="label">Basic Cost</div><div class="value">₹{int(basic_cost):,}</div></div>
              <div class="result-row"><div class="label">Channel Partner Payout</div><div class="value">₹{int(cp_payout):,}</div></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # SUBTAB 4 — INCENTIVE CALCULATOR
    # ------------------------------------------------------------------
    with ST_INCENTIVE:
        st.header("💸 Incentive Calculator")

        st.markdown("""
        <style>
          :root{
            --muted:#475569; --border:#e2e8f0; --soft:#f8fafc; --soft-blue:#eff6ff; --soft-amber:#fff7ed; --soft-green:#ecfdf5;
          }
          .kpi{
            border:1px solid var(--border);
            background:#fff;
            border-radius:14px;
            padding:12px 14px;
            margin:4px 8px 10px 8px;
          }
          .kpi.blue{background:var(--soft-blue)}
          .kpi.amb{background:var(--soft-amber)}
          .kpi.green{background:var(--soft-green)}
          .kpi h6{margin:0; font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em}
          .kpi p{margin:6px 0 0; font-size:20px; font-weight:900;}
          .bar{height:6px; width:100%; background:#e5e7eb; border-radius:999px; overflow:hidden; margin-top:8px}
          .bar>span{display:block; height:100%; background:#4f46e5}
          .summary-card{border:1px solid var(--border); background:#fff; border-radius:16px; overflow:hidden; margin-top:8px;}
          .smart-table{width:100%; border-collapse:separate; border-spacing:0; font-size:14px;}
          .smart-table thead th{
            background:linear-gradient(135deg,#06b6d4 0%,#6366f1 100%);
            color:#fff; text-transform:uppercase; letter-spacing:.04em; font-weight:800; padding:10px 12px; border:0;
          }
          .smart-table td{padding:10px 12px; border-bottom:1px solid var(--border); color:#0f172a;}
          .smart-table tr:last-child td{border-bottom:0;}
          .ta-l{text-align:left;} .ta-c{text-align:center;} .ta-r{text-align:right;}
          .chips{display:flex; flex-wrap:wrap; gap:6px;}
          .chip{display:inline-block; padding:4px 8px; border-radius:999px; background:#eef2ff; border:1px solid var(--border); font-weight:700}
          .row-alt:nth-child(odd) td{background:var(--soft);}
          @media(max-width: 640px){
             .smart-table td:nth-child(3), .smart-table th:nth-child(3){display:none;}
          }
        </style>
        """, unsafe_allow_html=True)

        if df_tab2.empty:
            st.warning("No booking data available for Incentive Calculator.")
        else:
            calc_df = df_tab2.copy()
            calc_df["Lead"] = calc_df["Lead Type"].astype(str).str.strip().str.title()

            def _fiscal_q_sort(q):
                q = str(q)
                m = re.search(r"(\d{4})", q)
                year = int(m.group(1)) if m else 9999

                if "April-June" in q:
                    order = 1
                elif "July-September" in q:
                    order = 2
                elif "October-December" in q:
                    order = 3
                elif "January-March" in q:
                    order = 4
                else:
                    order = 9

                return (year, order, q)

            quarter_options = sorted(
                [
                    q for q in calc_df["Quarter"].dropna().unique().tolist()
                    if str(q).strip()
                ],
                key=_fiscal_q_sort
            )

            default_exec_names = ["Harshal S", "Tejas P", "Sagar B", "Alok R", "Ashutosh S", "Komal K", "Sailee D", "Dhanashree W"]

            exec_from_data = sorted([
                x for x in calc_df["Sales Executive"].dropna().astype(str).str.strip().unique().tolist()
                if x and x.upper() not in ("NAN", "NONE", "NULL")
            ])

            exec_names = []
            for name in default_exec_names + exec_from_data:
                if name not in exec_names:
                    exec_names.append(name)

            if not quarter_options:
                st.warning("No quarters found in data.")
            elif not exec_names:
                st.warning("No Sales Executive names found in data.")
            else:
                default_quarter = st.session_state.get("ic_selected_quarter_val", quarter_options[0])
                default_exec = st.session_state.get("ic_selected_exec_val", exec_names[0])

                try:
                    default_q_index = quarter_options.index(default_quarter)
                except Exception:
                    default_q_index = 0

                try:
                    default_e_index = exec_names.index(default_exec)
                except Exception:
                    default_e_index = 0

                with st.form("incentive_filter"):
                    selected_quarter = st.selectbox(
                        "Select Quarter",
                        quarter_options,
                        index=default_q_index
                    )

                    selected_exec = st.selectbox(
                        "Select Sales Executive",
                        exec_names,
                        index=default_e_index
                    )

                    submitted = st.form_submit_button("Show Incentive")

                if submitted:
                    st.session_state["ic_selected_quarter_val"] = selected_quarter
                    st.session_state["ic_selected_exec_val"] = selected_exec

                active_quarter = st.session_state.get("ic_selected_quarter_val")
                active_exec = st.session_state.get("ic_selected_exec_val")

                if active_quarter is None or active_exec is None:
                    st.info("Please select Quarter and Sales Executive, then click **Show Incentive**.")
                else:
                    exec_df = calc_df[
                        (calc_df["Quarter"] == active_quarter)
                        & (calc_df["Sales Executive"] == active_exec)
                    ].copy()

                    if exec_df.empty:
                        st.info("No bookings found for selected Quarter and Sales Executive.")
                    else:
                        def _avg_rate_for_mask(sub_df):
                            if sub_df.empty or ("Agreement Cost" not in sub_df.columns) or ("Carpet Area" not in sub_df.columns):
                                return np.nan

                            ac_sum = pd.to_numeric(sub_df["Agreement Cost"], errors="coerce").sum(min_count=1)
                            ca_sum = pd.to_numeric(sub_df["Carpet Area"], errors="coerce").sum(min_count=1)
                            denom = (ca_sum * 1.38) if pd.notna(ca_sum) else np.nan

                            return (ac_sum / denom) if (pd.notna(ac_sum) and pd.notna(denom) and denom > 0) else np.nan

                        def _fmt_flat_number(v):
                            s = "" if pd.isna(v) else (v if isinstance(v, str) else str(v))
                            s = s.strip()

                            if s.endswith(".0"):
                                s = s[:-2]

                            return s

                        def _pct_label(p):
                            return f"{int(p * 100)}%"

                        def old_global_payout_percent_from_rate(r):
                            if pd.isna(r):
                                return 0.0
                            if r >= 5800:
                                return 1.0
                            elif 5700 <= r < 5800:
                                return 0.7
                            elif 5600 <= r < 5700:
                                return 0.4
                            return 0.0

                        def ef_wing_payout_percent_from_rate(r):
                            if pd.isna(r):
                                return 0.0
                            if r >= 5950:
                                return 1.0
                            elif 5900 <= r < 5950:
                                return 0.7
                            elif 5850 <= r < 5900:
                                return 0.4
                            return 0.0

                        def c_wing_payout_percent_from_rate(r):
                            if pd.isna(r):
                                return 0.0
                            if r >= 6325:
                                return 1.0
                            elif 6300 <= r < 6325:
                                return 0.7
                            elif 6275 <= r < 6300:
                                return 0.4
                            return 0.0

                        def podium_payout_percent_from_rate(r):
                            if pd.isna(r):
                                return 0.0
                            if r >= 5800:
                                return 1.0
                            elif 5700 <= r < 5800:
                                return 0.7
                            return 0.0

                        floor_norm = exec_df["Floor"].astype(str).str.strip().str.lower()

                        podium_mask = (
                            floor_norm.eq("1")
                            | floor_norm.eq("1.0")
                            | floor_norm.str.contains(r"\b1st\b|\bfirst\b|podium|garden", case=False, na=False)
                        )

                        exec_df["PodiumFlag"] = podium_mask

                        agreement_cost_sum = pd.to_numeric(exec_df["Agreement Cost"], errors="coerce").sum(min_count=1)
                        carpet_area_sum = pd.to_numeric(exec_df["Carpet Area"], errors="coerce").sum(min_count=1)
                        denom = (carpet_area_sum * 1.38) if pd.notna(carpet_area_sum) else np.nan
                        avg_rate = (agreement_cost_sum / denom) if (pd.notna(agreement_cost_sum) and pd.notna(denom) and denom > 0) else np.nan

                        unit_count = len(exec_df)

                        exec_df["WingNorm"] = exec_df["Wing"].astype(str).str.strip().str.upper()

                        mask_non_podium = ~exec_df["PodiumFlag"]
                        mask_E = exec_df["WingNorm"].eq("E") & mask_non_podium
                        mask_F = exec_df["WingNorm"].eq("F") & mask_non_podium
                        mask_C = exec_df["WingNorm"].eq("C") & mask_non_podium
                        mask_EF = mask_E | mask_F
                        mask_EFC = mask_EF | mask_C
                        mask_POD = exec_df["PodiumFlag"]

                        e_units = int(mask_E.sum())
                        f_units = int(mask_F.sum())
                        c_units = int(mask_C.sum())
                        ef_units = e_units + f_units
                        pod_units = int(mask_POD.sum())
                        efc_units_no_podium = ef_units + c_units

                        avg_rate_EF = _avg_rate_for_mask(exec_df[mask_EF]) if ef_units > 0 else np.nan
                        avg_rate_C = _avg_rate_for_mask(exec_df[mask_C]) if c_units > 0 else np.nan
                        avg_rate_E = _avg_rate_for_mask(exec_df[mask_E]) if e_units > 0 else np.nan
                        avg_rate_F = _avg_rate_for_mask(exec_df[mask_F]) if f_units > 0 else np.nan
                        avg_rate_POD = _avg_rate_for_mask(exec_df[mask_POD]) if pod_units > 0 else np.nan

                        if unit_count >= 18:
                            direct_rate = 6000
                            cp_like_rate = 6000
                        else:
                            direct_rate = 5000
                            cp_like_rate = 5000

                        def per_unit_rate(lead):
                            lead = str(lead).strip().title()

                            if lead == "Direct":
                                return direct_rate

                            if lead in {"Cp", "CP", "Referral", "Digital", "Hoarding"}:
                                return cp_like_rate

                            return 0

                        exec_df["Per Unit Rate Applied"] = exec_df["Lead"].map(per_unit_rate)

                        def wing_payout(row):
                            if row["PodiumFlag"]:
                                return podium_payout_percent_from_rate(avg_rate_POD)

                            w = str(row["WingNorm"]).strip().upper()

                            if w in {"E", "F"}:
                                return ef_wing_payout_percent_from_rate(avg_rate_EF)

                            if w == "C":
                                return c_wing_payout_percent_from_rate(avg_rate_C)

                            return old_global_payout_percent_from_rate(avg_rate)

                        exec_df["Payout % Applied"] = exec_df.apply(wing_payout, axis=1)
                        pod_pct = podium_payout_percent_from_rate(avg_rate_POD)

                        exec_df["Per Unit Incentive"] = exec_df["Per Unit Rate Applied"] * exec_df["Payout % Applied"]
                        base_incentive_all = float(exec_df["Per Unit Incentive"].sum())

                        left = exec_df["Wing"].astype(str).str.strip()
                        right = exec_df["Flat Number"].apply(_fmt_flat_number)

                        exec_df["Flat ID"] = (left + " " + right).astype(str).str.strip()
                        exec_df["Flat ID"] = exec_df["Flat ID"].replace({"nan": "", "None": ""}, regex=True).str.strip()

                        exec_df["Is Given"] = exec_df["Incentive"].astype(str).str.contains("given", case=False, na=False)

                        exec_df["Agreement Done Flag"] = (
                            exec_df["Agreement Done"]
                            .astype(str)
                            .str.strip()
                            .str.lower()
                            .eq("done")
                        )

                        applicable_mask = exec_df["Agreement Done Flag"]
                        applicable_df = exec_df[applicable_mask].copy()
                        applicable_count = len(applicable_df)

                        applicable_flats = [
                            f for f in applicable_df["Flat ID"].fillna("").tolist()
                            if f
                        ]

                        applicable_incentive_base = float(applicable_df["Per Unit Incentive"].sum())

                        top_seller_amount_screen = unit_count * 1000 if unit_count >= 20 else 0

                        q_df = calc_df[calc_df["Quarter"] == active_quarter].copy()
                        team_units_screen = len(q_df)

                        elig_counts_screen = q_df.groupby("Sales Executive").size() if not q_df.empty else pd.Series(dtype=int)
                        elig_names_screen = elig_counts_screen[elig_counts_screen >= 12].index.tolist()

                        team_bonus_amount_screen = 0

                        if team_units_screen >= 60 and len(elig_names_screen) > 0 and active_exec in elig_names_screen:
                            team_bonus_amount_screen = 50000 / len(elig_names_screen)

                        cond_ef_screen = (ef_units == 0) or (pd.notna(avg_rate_EF) and avg_rate_EF >= 6000)
                        cond_c_screen = (c_units == 0) or (pd.notna(avg_rate_C) and avg_rate_C >= 6000)

                        high_rate_amount_screen = 100000 if (efc_units_no_podium >= 18 and cond_ef_screen and cond_c_screen) else 0

                        bonus_total_screen = int(round(top_seller_amount_screen + team_bonus_amount_screen + high_rate_amount_screen))

                        sd_norm = exec_df["Stamp Duty"].astype(str).str.strip().str.lower()
                        stamp_duty_mask = sd_norm.str.contains("receiv") | sd_norm.isin(["yes", "y", "received", "recieved", "done"])

                        stamp_duty_count = int(stamp_duty_mask.sum())
                        stamp_duty_incentive = float(exec_df.loc[stamp_duty_mask, "Per Unit Incentive"].sum())

                        applicable_ratio_pct = 0 if unit_count == 0 else int((applicable_count / unit_count) * 100)

                        ef_pct = ef_wing_payout_percent_from_rate(avg_rate_EF)
                        c_pct = c_wing_payout_percent_from_rate(avg_rate_C)
                        pod_pct = podium_payout_percent_from_rate(avg_rate_POD)

                        ef_label = _pct_label(ef_pct)
                        c_label = _pct_label(c_pct)
                        pod_label = _pct_label(pod_pct)

                        ef_bar = max(0, min(int(ef_pct * 100), 100))
                        c_bar = max(0, min(int(c_pct * 100), 100))
                        pod_bar = max(0, min(int(pod_pct * 100), 100))

                        # ---------------- KPI CARDS ----------------
                        r1c1, r1c2, r1c3 = st.columns(3)

                        with r1c1:
                            st.markdown(f"""
                            <div class="kpi"><h6>E+F Total Bookings</h6>
                              <p>{ef_units}</p>
                              <div class="bar"><span style="width:{min(ef_units, 20) / 20 * 100}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        with r1c2:
                            st.markdown(f"""
                            <div class="kpi blue"><h6>E+F Avg PSF</h6>
                              <p>₹ {0 if pd.isna(avg_rate_EF) else round(avg_rate_EF, 2):,}</p>
                              <div class="bar"><span style="width:{min(max(((0 if pd.isna(avg_rate_EF) else avg_rate_EF) - 5400) / 8, 0), 100)}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        with r1c3:
                            st.markdown(f"""
                            <div class="kpi amb"><h6>E+F Payout Slab</h6>
                              <p>{ef_label}</p>
                              <div class="bar"><span style="width:{ef_bar}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        r2c1, r2c2, r2c3 = st.columns(3)

                        with r2c1:
                            st.markdown(f"""
                            <div class="kpi"><h6>C Total Bookings</h6>
                              <p>{c_units}</p>
                              <div class="bar"><span style="width:{min(c_units, 20) / 20 * 100}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        with r2c2:
                            st.markdown(f"""
                            <div class="kpi blue"><h6>C Avg PSF</h6>
                              <p>₹ {0 if pd.isna(avg_rate_C) else round(avg_rate_C, 2):,}</p>
                              <div class="bar"><span style="width:{min(max(((0 if pd.isna(avg_rate_C) else avg_rate_C) - 5400) / 8, 0), 100)}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        with r2c3:
                            st.markdown(f"""
                            <div class="kpi amb"><h6>C Payout Slab</h6>
                              <p>{c_label}</p>
                              <div class="bar"><span style="width:{c_bar}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        r3c1, r3c2, r3c3 = st.columns(3)

                        with r3c1:
                            st.markdown(f"""
                            <div class="kpi"><h6>Podium Units Total Bookings</h6>
                              <p>{pod_units}</p>
                              <div class="bar"><span style="width:{min(pod_units, 20) / 20 * 100}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        with r3c2:
                            st.markdown(f"""
                            <div class="kpi blue"><h6>Podium Units Avg PSF</h6>
                              <p>₹ {0 if pd.isna(avg_rate_POD) else round(avg_rate_POD, 2):,}</p>
                              <div class="bar"><span style="width:{min(max(((0 if pd.isna(avg_rate_POD) else avg_rate_POD) - 5400) / 8, 0), 100)}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        with r3c3:
                            st.markdown(f"""
                            <div class="kpi amb"><h6>Podium Units Payout Slab</h6>
                              <p>{pod_label}</p>
                              <div class="bar"><span style="width:{pod_bar}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        r4c1, r4c2, r4c3 = st.columns(3)

                        with r4c1:
                            st.markdown(f"""
                            <div class="kpi green"><h6>Total Incentive (All)</h6>
                              <p>₹ {int(base_incentive_all + bonus_total_screen):,}</p>
                            </div>""", unsafe_allow_html=True)

                        with r4c2:
                            st.markdown(f"""
                            <div class="kpi"><h6>Applicable Flats / Total</h6>
                              <p>{applicable_count}/{unit_count}</p>
                              <div class="bar"><span style="width:{applicable_ratio_pct}%"></span></div>
                            </div>""", unsafe_allow_html=True)

                        with r4c3:
                            st.markdown(f"""
                            <div class="kpi"><h6>Applicable Incentive (Base)</h6>
                              <p>₹ {int(applicable_incentive_base):,}</p>
                            </div>""", unsafe_allow_html=True)

                        r5c1, r5c2, r5c3 = st.columns(3)

                        with r5c1:
                            st.markdown(f"""
                            <div class="kpi"><h6>Overall Total Booking Count</h6>
                              <p>{unit_count}</p>
                            </div>""", unsafe_allow_html=True)

                        with r5c2:
                            st.markdown(f"""
                            <div class="kpi"><h6>Stamp Duty Received Flats</h6>
                              <p>{stamp_duty_count}</p>
                            </div>""", unsafe_allow_html=True)

                        with r5c3:
                            st.markdown(f"""
                            <div class="kpi green"><h6>Incentive (Base) on Stamp Duty Received</h6>
                              <p>₹ {int(round(stamp_duty_incentive)):,}</p>
                            </div>""", unsafe_allow_html=True)

                        # ---------------- SUMMARY TABLE ----------------
                        def _fmt_rate(r):
                            return "—" if pd.isna(r) else f"₹{round(r, 2):,}"

                        flats_E = [f for f in exec_df.loc[mask_E, "Flat ID"].fillna("").tolist() if f]
                        flats_F = [f for f in exec_df.loc[mask_F, "Flat ID"].fillna("").tolist() if f]
                        flats_C = [f for f in exec_df.loc[mask_C, "Flat ID"].fillna("").tolist() if f]
                        flats_POD = [f for f in exec_df.loc[mask_POD, "Flat ID"].fillna("").tolist() if f]

                        mask_other = ~(mask_EFC | mask_POD)
                        other_units = int(mask_other.sum())
                        flats_other = [f for f in exec_df.loc[mask_other, "Flat ID"].fillna("").tolist() if f]

                        base_incentive_E = int(exec_df.loc[mask_E, "Per Unit Incentive"].sum())
                        base_incentive_F = int(exec_df.loc[mask_F, "Per Unit Incentive"].sum())
                        base_incentive_C = int(exec_df.loc[mask_C, "Per Unit Incentive"].sum())
                        base_incentive_POD = int(exec_df.loc[mask_POD, "Per Unit Incentive"].sum())
                        base_incentive_other = int(exec_df.loc[mask_other, "Per Unit Incentive"].sum())

                        released_amount_base_all = int(exec_df.loc[exec_df["Is Given"], "Per Unit Incentive"].sum())

                        summary_rows = [
                            ("Total Flats (Bookings)", "—", "—", unit_count),
                            ("Applicable Flats (Agreement Done)", "—", "—", f"{applicable_count}"),
                            ("Applicable Flats — Flat Numbers", "—", "—", applicable_flats),

                            ("E Wing (non-Podium)", _fmt_rate(avg_rate_E), f"{int((exec_df.loc[mask_E, 'Payout % Applied'].mean() if mask_E.any() else 0) * 100)}%", flats_E),
                            ("F Wing (non-Podium)", _fmt_rate(avg_rate_F), f"{int((exec_df.loc[mask_F, 'Payout % Applied'].mean() if mask_F.any() else 0) * 100)}%", flats_F),
                            ("C Wing (non-Podium)", _fmt_rate(avg_rate_C), f"{int((exec_df.loc[mask_C, 'Payout % Applied'].mean() if mask_C.any() else 0) * 100)}%", flats_C),
                            ("Podium Units", _fmt_rate(avg_rate_POD), f"{int((pod_pct if not pd.isna(pod_pct) else 0) * 100)}%", flats_POD),
                        ]

                        if other_units > 0:
                            summary_rows.append(("Other Wings", "—", "—", flats_other))

                        summary_rows.extend([
                            ("Base Incentive — E Wing", "—", "—", f"₹{base_incentive_E:,}"),
                            ("Base Incentive — F Wing", "—", "—", f"₹{base_incentive_F:,}"),
                            ("Base Incentive — C Wing", "—", "—", f"₹{base_incentive_C:,}"),
                            ("Base Incentive — Podium Units", "—", "—", f"₹{base_incentive_POD:,}"),
                            ("Base Incentive — Other Wings", "—", "—", f"₹{base_incentive_other:,}"),
                            ("Base Incentive (All Wings)", "—", "—", f"₹{int(base_incentive_all):,}"),

                            ("— Bonuses (Bookings basis) —", "—", "—", "—"),
                            ("Top Seller Bonus", "—", "—", f"₹{int(round(top_seller_amount_screen)):,}"),
                            ("Team Achievement Bonus (your share)", "—", "—", f"₹{int(round(team_bonus_amount_screen)):,}"),
                            ("High Rate Bonus", "—", "—", f"₹{int(round(high_rate_amount_screen)):,}"),
                            ("Bonus Total (Bookings)", "—", "—", f"₹{int(round(bonus_total_screen)):,}"),

                            ("Already Given (Base)", "—", "—", f"₹{released_amount_base_all:,}"),
                            ("Total Incentive Payout (All)", "—", "—", f"₹{int(round(base_incentive_all + bonus_total_screen)):,}"),

                            ("— Stamp Duty Snapshot —", "—", "—", "—"),
                            ("Overall Total Booking Count", "—", "—", unit_count),
                            ("Stamp Duty Received Flats", "—", "—", stamp_duty_count),
                            ("Incentive on Stamp Duty (Base only)", "—", "—", f"₹{int(round(stamp_duty_incentive)):,}"),
                        ])

                        def _amt_cell(amt):
                            if isinstance(amt, list):
                                chips = "".join(f'<span class="chip">{f}</span>' for f in amt) or "—"
                                return f'<div class="chips">{chips}</div>'

                            return str(amt)

                        table_rows_html = []

                        for cat, col2, col3, amt in summary_rows:
                            table_rows_html.append(
                                f'<tr class="row-alt">'
                                f'<td class="ta-l">{cat}</td>'
                                f'<td class="ta-c">{col2}</td>'
                                f'<td class="ta-c">{col3}</td>'
                                f'<td class="ta-r">{_amt_cell(amt)}</td>'
                                f'</tr>'
                            )

                        st.markdown(
                            f"""
                            <div class="summary-card">
                              <table class="smart-table">
                                <thead><tr>
                                  <th>Category</th><th>Avg Rate</th><th>Payout %</th><th>Flats / Amount</th>
                                </tr></thead>
                                <tbody>{''.join(table_rows_html)}</tbody>
                              </table>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # ======================= PDF — Invoice Style =======================
                        is_given_mask = exec_df["Is Given"].astype(bool)

                        given_flats_list = [
                            f for f in exec_df.loc[applicable_mask & is_given_mask, "Flat ID"].fillna("").tolist()
                            if f
                        ]

                        balance_flats_list = [
                            f for f in exec_df.loc[applicable_mask & (~is_given_mask), "Flat ID"].fillna("").tolist()
                            if f
                        ]

                        total_app_amt = float(exec_df.loc[applicable_mask, "Per Unit Incentive"].sum())
                        given_app_amt = float(exec_df.loc[applicable_mask & is_given_mask, "Per Unit Incentive"].sum())
                        balance_app_amt = float(exec_df.loc[applicable_mask & (~is_given_mask), "Per Unit Incentive"].sum())

                        def _avg(col, mask):
                            if col not in exec_df.columns:
                                return 0.0

                            s = exec_df.loc[mask, col]

                            if s.empty:
                                return 0.0

                            return float(np.nanmean(pd.to_numeric(s, errors="coerce")))

                        avg_payout_total = _avg("Payout % Applied", applicable_mask)
                        avg_amt_per_flat = _avg("Per Unit Incentive", applicable_mask)
                        avg_payout_given = _avg("Payout % Applied", applicable_mask & is_given_mask)
                        avg_amt_per_given = _avg("Per Unit Incentive", applicable_mask & is_given_mask)
                        avg_payout_balance = _avg("Payout % Applied", applicable_mask & (~is_given_mask))
                        avg_amt_per_balance = _avg("Per Unit Incentive", applicable_mask & (~is_given_mask))

                        count_all = int(len(exec_df))
                        count_non_app = int((~applicable_mask).sum())
                        count_app = int(applicable_mask.sum())
                        count_given = int((applicable_mask & is_given_mask).sum())
                        count_balance = int((applicable_mask & (~is_given_mask)).sum())

                        app_mask_non_pod = applicable_mask & (~exec_df["PodiumFlag"])

                        e_app_units = int((exec_df["WingNorm"].eq("E") & app_mask_non_pod).sum())
                        f_app_units = int((exec_df["WingNorm"].eq("F") & app_mask_non_pod).sum())
                        c_app_units = int((exec_df["WingNorm"].eq("C") & app_mask_non_pod).sum())
                        efc_app_units = e_app_units + f_app_units + c_app_units

                        def _avg_rate_app(mask_bool):
                            sub = exec_df[mask_bool]

                            if sub.empty or ("Agreement Cost" not in sub.columns) or ("Carpet Area" not in sub.columns):
                                return np.nan

                            ac_sum = pd.to_numeric(sub["Agreement Cost"], errors="coerce").sum(min_count=1)
                            ca_sum = pd.to_numeric(sub["Carpet Area"], errors="coerce").sum(min_count=1)
                            denom = (ca_sum * 1.38) if pd.notna(ca_sum) else np.nan

                            return (ac_sum / denom) if (pd.notna(ac_sum) and pd.notna(denom) and denom > 0) else np.nan

                        avg_rate_EF_app = _avg_rate_app(exec_df["WingNorm"].isin(["E", "F"]) & app_mask_non_pod)
                        avg_rate_C_app = _avg_rate_app(exec_df["WingNorm"].eq("C") & app_mask_non_pod)

                        top_seller_amount_pdf = count_app * 1000 if count_app >= 20 else 0

                        q_df_app = calc_df[calc_df["Quarter"] == active_quarter].copy()
                        q_df_app["AgDone"] = q_df_app["Agreement Done"].astype(str).str.strip().str.lower().eq("done")

                        team_units_app = int(q_df_app["AgDone"].sum())

                        elig_counts_app = (
                            q_df_app[q_df_app["AgDone"]].groupby("Sales Executive").size()
                            if not q_df_app[q_df_app["AgDone"]].empty
                            else pd.Series(dtype=int)
                        )

                        elig_names_app = elig_counts_app[elig_counts_app >= 0].index.tolist()

                        team_bonus_amount_pdf = 0

                        if team_units_app >= 60 and len(elig_names_app) > 0 and active_exec in elig_names_app:
                            team_bonus_amount_pdf = 50000 / len(elig_names_app)

                        cond_ef_pdf = (e_app_units + f_app_units == 0) or (pd.notna(avg_rate_EF_app) and avg_rate_EF_app >= 6000)
                        cond_c_pdf = (c_app_units == 0) or (pd.notna(avg_rate_C_app) and avg_rate_C_app >= 6000)

                        high_rate_amount_pdf = 100000 if (efc_app_units >= 18 and cond_ef_pdf and cond_c_pdf) else 0

                        bonus_total_pdf = int(round(top_seller_amount_pdf + team_bonus_amount_pdf + high_rate_amount_pdf))

                        balance_amount_with_bonus_pdf = balance_app_amt + bonus_total_pdf

                        bonus_tags = []

                        if top_seller_amount_pdf > 0:
                            bonus_tags.append("Top Seller Bonus")

                        if team_bonus_amount_pdf > 0:
                            bonus_tags.append("Team Bonus")

                        if high_rate_amount_pdf > 0:
                            bonus_tags.append("High Rate Bonus")

                        if bonus_tags:
                            balance_flats_list = balance_flats_list + bonus_tags

                        def ascii_only(s: str) -> str:
                            return (
                                str(s)
                                .replace("₹", "Rs ")
                                .replace("—", "-")
                                .replace("–", "-")
                                .replace("→", "->")
                            )

                        def fmt_money(v):
                            try:
                                return f"Rs {int(round(float(v))):,}"
                            except Exception:
                                return "Rs 0"

                        def fmt_pct(p):
                            try:
                                return f"{int(round(float(p) * 100))}%"
                            except Exception:
                                return "0%"

                        pdf = FPDF(orientation="P", unit="mm", format="A4")
                        pdf.set_margins(10, 10, 10)
                        pdf.set_auto_page_break(auto=True, margin=12)
                        pdf.add_page()

                        page_w = pdf.w - pdf.l_margin - pdf.r_margin
                        page_h = pdf.h
                        b_margin = getattr(pdf, "b_margin", 12)

                        def ensure_space(h):
                            if pdf.get_y() + h > (page_h - b_margin):
                                pdf.add_page()

                        def section_title(txt, size=12, top=2, bottom=1):
                            ensure_space(10)
                            pdf.ln(top)
                            pdf.set_font("Arial", "B", size)
                            pdf.cell(0, 8, ascii_only(txt), ln=True, align="C")
                            pdf.ln(bottom)

                        def wrap_by_spaces(text, inner_w, font=("Arial", "", 9)):
                            pdf.set_font(font[0], font[1], font[2])
                            s = ascii_only(str(text)) or "-"
                            words = s.split()
                            lines = []
                            cur = ""

                            for w in words:
                                probe = (cur + " " + w) if cur else w

                                if pdf.get_string_width(probe) <= inner_w:
                                    cur = probe
                                else:
                                    if cur:
                                        lines.append(cur)
                                    cur = w

                            if cur:
                                lines.append(cur)

                            return lines

                        def wrap_by_commas(text, inner_w, font=("Arial", "", 9)):
                            pdf.set_font(font[0], font[1], font[2])
                            s = ascii_only(str(text)) or "-"
                            tokens = [t.strip() for t in s.split(",") if t.strip()]

                            if not tokens:
                                return ["-"]

                            lines = []
                            cur = ""

                            for tok in tokens:
                                piece = (cur + ", " + tok) if cur else tok

                                if pdf.get_string_width(piece) <= inner_w:
                                    cur = piece
                                else:
                                    if cur:
                                        lines.append(cur)
                                    cur = tok

                            if cur:
                                lines.append(cur)

                            return lines

                        def table_header(headers, widths, size=10):
                            ensure_space(9)
                            pdf.set_font("Arial", "B", size)

                            for h, w in zip(headers, widths):
                                pdf.cell(w, 7.2, ascii_only(h), border=1, align="C")

                            pdf.ln()

                        def table_row_exact(values, widths, aligns, size=9, lh=5.8, hpad=1.8, vpad=2.0, comma_cols=None):
                            comma_cols = set(comma_cols or {})
                            pdf.set_font("Arial", "", size)

                            inner_ws = [w - 2 * hpad for w in widths]

                            wrapped = []

                            for idx, (v, iw) in enumerate(zip(values, inner_ws)):
                                if idx in comma_cols:
                                    wrapped.append(wrap_by_commas(v, iw, ("Arial", "", size)))
                                else:
                                    wrapped.append(wrap_by_spaces(v, iw, ("Arial", "", size)))

                            n_lines_max = max(len(x) for x in wrapped) if wrapped else 1
                            row_h = n_lines_max * lh + 2 * vpad

                            ensure_space(row_h + 1.0)

                            x0, y0 = pdf.get_x(), pdf.get_y()
                            cx = x0

                            for w in widths:
                                pdf.rect(cx, y0, w, row_h)
                                cx += w

                            cx = x0

                            for cell_lines, w, iw, alg in zip(wrapped, widths, inner_ws, aligns):
                                ix = cx + hpad
                                iy = y0 + vpad

                                for line_idx, line in enumerate(cell_lines):
                                    pdf.set_xy(ix, iy + line_idx * lh)
                                    pdf.cell(iw, lh, ascii_only(line), border=0, ln=0, align=alg)

                                cx += w

                            pdf.set_xy(pdf.l_margin, y0 + row_h + 0.6)

                        pdf.set_font("Arial", "B", 13)
                        pdf.cell(0, 9, ascii_only(f"Incentive Invoice - {active_exec} ({active_quarter})"), ln=True, align="C")
                        pdf.ln(2)

                        all_flats = [f for f in exec_df["Flat ID"].fillna("").tolist() if f]
                        non_app_flats = [f for f in exec_df.loc[~applicable_mask, "Flat ID"].fillna("").tolist() if f]
                        app_flats = [f for f in exec_df.loc[applicable_mask, "Flat ID"].fillna("").tolist() if f]

                        ov_w_cat = page_w * 0.28
                        ov_w_count = page_w * 0.12
                        ov_w_vals = page_w * 0.60

                        ov_widths = [ov_w_cat, ov_w_count, ov_w_vals]
                        ov_aligns = ["L", "C", "L"]

                        table_header(["Category", "Count", "Flat Numbers"], ov_widths)

                        table_row_exact(
                            ["TOTAL FLATS", count_all, ", ".join(all_flats) if all_flats else "-"],
                            ov_widths,
                            ov_aligns,
                            size=9,
                            comma_cols=[2]
                        )

                        table_row_exact(
                            ["AGREEMENT NOT DONE (NON-APPLICABLE)", count_non_app, ", ".join(non_app_flats) if non_app_flats else "-"],
                            ov_widths,
                            ov_aligns,
                            size=9,
                            comma_cols=[2]
                        )

                        table_row_exact(
                            ["AGREEMENT DONE (APPLICABLE)", count_app, ", ".join(app_flats) if app_flats else "-"],
                            ov_widths,
                            ov_aligns,
                            size=9,
                            comma_cols=[2]
                        )

                        section_title("Incentive Summary")

                        sum_w_cat = page_w * 0.32
                        sum_w_cnt = page_w * 0.12
                        sum_w_pct = page_w * 0.16
                        sum_w_each = page_w * 0.18
                        sum_w_amt = page_w * 0.22

                        sum_widths = [sum_w_cat, sum_w_cnt, sum_w_pct, sum_w_each, sum_w_amt]
                        sum_aligns = ["L", "C", "C", "R", "R"]

                        table_header(
                            ["Category", "Flat Count", "Payout % (Avg)", "Amount / Flat (Avg)", "Total Amount"],
                            sum_widths
                        )

                        table_row_exact(
                            ["TOTAL INCENTIVE (Applicable Base)", count_app, fmt_pct(avg_payout_total), fmt_money(avg_amt_per_flat), fmt_money(total_app_amt)],
                            sum_widths,
                            sum_aligns,
                            size=10
                        )

                        table_row_exact(
                            ["INCENTIVE GIVEN", count_given, fmt_pct(avg_payout_given), fmt_money(avg_amt_per_given), fmt_money(given_app_amt)],
                            sum_widths,
                            sum_aligns,
                            size=10
                        )

                        table_row_exact(
                            ["INCENTIVE BALANCE", count_balance, fmt_pct(avg_payout_balance), fmt_money(avg_amt_per_balance), fmt_money(balance_app_amt)],
                            sum_widths,
                            sum_aligns,
                            size=10
                        )

                        table_row_exact(
                            ["TOP SELLER BONUS (Applicable units)", "-", "-", "-", fmt_money(top_seller_amount_pdf)],
                            sum_widths,
                            sum_aligns,
                            size=10
                        )

                        table_row_exact(
                            ["TEAM BONUS (your share; Applicable basis)", "-", "-", "-", fmt_money(team_bonus_amount_pdf)],
                            sum_widths,
                            sum_aligns,
                            size=10
                        )

                        table_row_exact(
                            ["HIGH RATE BONUS (Applicable basis)", "-", "-", "-", fmt_money(high_rate_amount_pdf)],
                            sum_widths,
                            sum_aligns,
                            size=10
                        )

                        table_row_exact(
                            ["BONUS TOTAL", "-", "-", "-", fmt_money(bonus_total_pdf)],
                            sum_widths,
                            sum_aligns,
                            size=10
                        )

                        section_title("Applicable Flats - Grouped Ledger")

                        led_w_status = page_w * 0.20
                        led_w_count = page_w * 0.12
                        led_w_flats = page_w * 0.46
                        led_w_amt = page_w * 0.22

                        led_widths = [led_w_status, led_w_count, led_w_flats, led_w_amt]
                        led_aligns = ["C", "C", "L", "R"]

                        table_header(["Remark", "Flats", "Flat Numbers / Notes", "Amount"], led_widths)

                        table_row_exact(
                            ["Given", str(count_given), ", ".join(given_flats_list) if given_flats_list else "-", fmt_money(given_app_amt)],
                            led_widths,
                            led_aligns,
                            size=9,
                            comma_cols=[2]
                        )

                        table_row_exact(
                            ["Balance Amount", str(count_balance), ", ".join(balance_flats_list) if balance_flats_list else "-", fmt_money(balance_amount_with_bonus_pdf)],
                            led_widths,
                            led_aligns,
                            size=9,
                            comma_cols=[2]
                        )

                        orig_apb_state = getattr(pdf, "_auto_page_break", True)
                        orig_bmargin = getattr(pdf, "b_margin", 12)
                        pdf.set_auto_page_break(auto=False)

                        sig_h = 24
                        y_bottom = pdf.h - (orig_bmargin if hasattr(pdf, "b_margin") else 10)
                        y_sig = y_bottom - sig_h
                        y_sig = max(y_sig, pdf.get_y() + 4)

                        gap = 30
                        block_w = (page_w - gap) / 2
                        x_left = pdf.l_margin
                        x_right = pdf.l_margin + block_w + gap

                        pdf.set_xy(x_left, y_sig)
                        pdf.line(x_left, y_sig, x_left + block_w, y_sig)
                        pdf.line(x_right, y_sig, x_right + block_w, y_sig)

                        pdf.set_xy(x_left, y_sig + 4)
                        pdf.set_font("Arial", size=10)
                        pdf.cell(block_w, 7, ascii_only("Developer Signature"), ln=False, align="L")

                        pdf.set_xy(x_right, y_sig + 4)
                        pdf.set_font("Arial", size=10)
                        pdf.cell(block_w, 7, ascii_only(f"{active_exec} Signature"), ln=False, align="R")

                        pdf.set_xy(pdf.l_margin, y_sig + sig_h)
                        pdf.set_auto_page_break(auto=orig_apb_state, margin=orig_bmargin)

                        pdf_output = pdf.output(dest="S")

                        if isinstance(pdf_output, str):
                            pdf_bytes = pdf_output.encode("latin1", "ignore")
                        else:
                            pdf_bytes = bytes(pdf_output)

                        b64 = base64.b64encode(pdf_bytes).decode()

                        st.markdown(
                            f"""
                            <a href="data:application/octet-stream;base64,{b64}" download="incentive_invoice.pdf"
                               style="display:inline-block;margin-top:10px;padding:10px 14px;border-radius:10px;
                               background:linear-gradient(135deg,#06b6d4 0%,#6366f1 100%);color:#fff;text-decoration:none;
                               font-weight:800">⬇️ Download Incentive Invoice (PDF)</a>
                            """,
                            unsafe_allow_html=True
                        )
    with ST_INCENTIVE_STATUS:
        st.header("📊 Incentive Status")
    
        import re
        import numpy as np
        import pandas as _pd
    
        # ============================================================
        # Supabase-compatible dataframe prep
        # Works with:
        # - df_tab2 if created in Tab 2
        # - booking_df / sheet_df from your Supabase load
        # - old Google Sheet style column names
        # - new Supabase snake_case column names
        # ============================================================
        def _prepare_incentive_status_df():
            if "df_tab2" in globals() and isinstance(df_tab2, _pd.DataFrame):
                out = df_tab2.copy()
            elif "booking_df" in globals() and isinstance(booking_df, _pd.DataFrame):
                out = booking_df.copy()
            elif "sheet_df" in globals() and isinstance(sheet_df, _pd.DataFrame):
                out = sheet_df.copy()
            elif "df" in globals() and isinstance(df, _pd.DataFrame):
                out = df.copy()
            else:
                out = _pd.DataFrame()
    
            rename_map = {
                "booking_date": "Date",
                "customer_name": "Customer Name",
                "wing": "Wing",
                "floor": "Floor",
                "flat_number": "Flat Number",
                "type": "Type",
                "final_price": "Final Price",
                "rate": "Rate",
                "agreement_cost": "Agreement Cost",
                "lead_type": "Lead Type",
                "sales_executive": "Sales Executive",
                "month": "Month",
                "civil_changes": "Civil Changes",
                "offer_1": "Offer 1",
                "offer_2": "Offer 2",
                "offer_1_rewarded": "Offer 1 Rewarded",
                "offer_2_rewarded": "Offer 2 Rewarded",
                "referral_given": "Referral Given",
                "stamp_duty": "Stamp Duty",
                "agreement_done": "Agreement Done",
                "incentive": "Incentive",
                "rcc": "RCC",
                "possession_handover": "POSSESSION HANDOVER",
                "insider_banker": "Insider Banker",
                "outsider_banker": "Outsider Banker",
                "carpet_area": "Carpet Area",
                "booking_amount": "Booking Amount",
                "agreement": "Agreement",
                "plinth": "Plinth",
                "third_floor": "Third Floor",
                "seventh_floor": "Seventh Floor",
                "tenth_floor": "Tenth Floor",
                "thirteenth_floor": "Thirteenth Floor",
                "flooring": "Flooring",
                "plastering": "Plastering",
                "plumbing": "Plumbing",
                "electrical": "Electrical",
                "sanitary_lift": "Sanitary Lift",
                "possession": "Possession",
                "first_visit_date": "First Visit Date",
                "conversion_period_days": "Conversion Period (days)",
                "parking_number": "Parking Number",
                "merged_units": "Merged Units",
                "location": "Location",
                "visit_count": "Visit Count",
                "received_amount": "Received Amount",
                "stamp_duty_percent": "Stamp Duty Percent",
            }
    
            for old_col, new_col in rename_map.items():
                if old_col in out.columns and new_col not in out.columns:
                    out[new_col] = out[old_col]
    
            required_cols = [
                "Date",
                "Quarter",
                "Sales Executive",
                "Lead Type",
                "Wing",
                "Floor",
                "Flat Number",
                "Agreement Done",
                "Stamp Duty",
                "Incentive",
                "RCC",
                "POSSESSION HANDOVER",
                "Agreement Cost",
                "Carpet Area",
            ]
    
            for col in required_cols:
                if col not in out.columns:
                    out[col] = ""
    
            # Date parse
            out["Date"] = _pd.to_datetime(out["Date"], errors="coerce", dayfirst=True)
    
            # Month fallback
            if "Month" not in out.columns:
                out["Month"] = ""
    
            out["Month"] = out["Month"].fillna("").astype(str).str.strip()
    
            if out["Month"].eq("").all():
                out["Month"] = out["Date"].dt.strftime("%B %y")
    
            # Quarter derive because Supabase bookings table does not store Quarter
            def _custom_quarter_from_date(d):
                if _pd.isna(d):
                    return ""
                try:
                    d = _pd.to_datetime(d)
                except Exception:
                    return ""
    
                year = d.year
    
                if d.month in [4, 5, 6]:
                    return f"April-June {year}"
                elif d.month in [7, 8, 9]:
                    return f"July-September {year}"
                elif d.month in [10, 11, 12]:
                    return f"October-December {year}"
                else:
                    return f"January-March {year}"
    
            def _date_from_month_label(m):
                s = str(m or "").strip()
                if not s:
                    return _pd.NaT
    
                s = s.replace("-", " ").replace("_", " ")
                s = " ".join(s.split())
    
                for fmt in ("%B %y", "%b %y", "%B %Y", "%b %Y"):
                    try:
                        return _pd.to_datetime(s.title(), format=fmt)
                    except Exception:
                        pass
    
                return _pd.to_datetime(s, errors="coerce", dayfirst=True)
    
            q_blank = out["Quarter"].fillna("").astype(str).str.strip().eq("")
    
            if q_blank.any():
                out.loc[q_blank, "Quarter"] = out.loc[q_blank, "Date"].apply(_custom_quarter_from_date)
    
            q_blank = out["Quarter"].fillna("").astype(str).str.strip().eq("")
    
            if q_blank.any():
                month_dt = out.loc[q_blank, "Month"].apply(_date_from_month_label)
                out.loc[q_blank, "Quarter"] = month_dt.apply(_custom_quarter_from_date)
    
            # Text cleanup
            text_cols = [
                "Quarter",
                "Sales Executive",
                "Lead Type",
                "Wing",
                "Floor",
                "Flat Number",
                "Agreement Done",
                "Stamp Duty",
                "Incentive",
                "RCC",
                "POSSESSION HANDOVER",
            ]
    
            for col in text_cols:
                out[col] = out[col].fillna("").astype(str).str.strip()
    
            # Numeric cleanup
            def _clean_num(x):
                if _pd.isna(x):
                    return np.nan
    
                s = (
                    str(x)
                    .replace("₹", "")
                    .replace("Rs", "")
                    .replace("rs", "")
                    .replace("INR", "")
                    .replace("inr", "")
                    .replace(",", "")
                    .strip()
                )
    
                try:
                    return float(s)
                except Exception:
                    return np.nan
    
            out["Agreement Cost"] = _pd.to_numeric(out["Agreement Cost"].apply(_clean_num), errors="coerce").fillna(0)
            out["Carpet Area"] = _pd.to_numeric(out["Carpet Area"].apply(_clean_num), errors="coerce").fillna(0)
    
            return out
    
        data = _prepare_incentive_status_df()
    
        if data.empty:
            st.warning("No booking data available for Incentive Status.")
        else:
            # ================= Quarter helpers =================
            MONTHS = {
                "jan": 1, "january": 1,
                "feb": 2, "february": 2,
                "mar": 3, "march": 3,
                "apr": 4, "april": 4,
                "may": 5,
                "jun": 6, "june": 6,
                "jul": 7, "july": 7,
                "aug": 8, "august": 8,
                "sep": 9, "sept": 9, "september": 9,
                "oct": 10, "october": 10,
                "nov": 11, "november": 11,
                "dec": 12, "december": 12,
            }
    
            def _parse_yq(qtxt):
                s = str(qtxt).strip().lower()
    
                # Handles "Q1 2025", "q2-2026", etc.
                m = re.search(r"\bq\s*(\d)\b.*?(\d{4})", s)
                if m:
                    return (int(m.group(2)), int(m.group(1)))
    
                # Handles "April-June 2025", "July-September 2025", etc.
                my = re.search(r"(\d{4})", s)
                if my:
                    y = int(my.group(1))
    
                    m1 = re.search(
                        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
                        r"january|february|march|april|june|july|august|september|october|november|december)",
                        s
                    )
    
                    if m1:
                        mnum = MONTHS[m1.group(1)]
                        q = (mnum - 1) // 3 + 1
                        return (y, q)
    
                return (9999, 9)
    
            def _quarter_sort_key(qtxt):
                y, q = _parse_yq(qtxt)
                return (y, q, str(qtxt))
    
            def _canonical_quarter(qtxt):
                y, q = _parse_yq(qtxt)
                return f"{y}-Q{q}"
    
            quarters = sorted(
                [
                    q for q in data["Quarter"].dropna().unique().tolist()
                    if str(q).strip() and str(q).strip().lower() not in ["nan", "none", "null"]
                ],
                key=_quarter_sort_key
            )
    
            if not quarters:
                st.warning("No valid Quarter values found. Check booking_date/month values.")
            else:
                # ============ Quarter-specific rules ============
                # IMPORTANT:
                # Apr-Jun 2025 -> calendar 2025-Q2
                # Jul-Sep 2025 -> calendar 2025-Q3
                # Oct-Dec 2025 -> calendar 2025-Q4
                # Jan-Mar 2026 -> calendar 2026-Q1
                QUARTER_RULES = {
                    "2025-Q2": {
                        "mode": "FIXED_PER_EXEC",
                        "fixed_rates": {
                            "Harshal S": 5000,
                            "Tejas P": 3500,
                            "Alok R": 4000,
                        },
                    },
    
                    "2025-Q3": {
                        "mode": "GLOBAL",
                        "global_t": {
                            "t100": 5800,
                            "t70": 5700,
                            "t40": 5600,
                        },
                    },
    
                    "2025-Q4": {
                        "mode": "WING_WISE",
                        "ef_t": {
                            "t100": 5950,
                            "t70": 5900,
                            "t40": 5850,
                        },
                        "c_t": {
                            "t100": 6325,
                            "t70": 6300,
                            "t40": 6275,
                        },
                    },
    
                    "2026-Q1": {
                        "mode": "WING_WISE",
                        "ef_t": {
                            "t100": 6000,
                            "t70": 5950,
                            "t40": 5900,
                        },
                        "c_t": {
                            "t100": 6325,
                            "t70": 6300,
                            "t40": 6275,
                        },
                    },
                }
    
                DEFAULT_RULE_KEY = "2026-Q1"
    
                # From Apr-Jun 2026 onwards -> staged payout policy applies
                CUTOFF_YEAR, CUTOFF_Q = 2026, 2
    
                def use_three_term_for(qtxt):
                    y, q = _parse_yq(qtxt)
                    return (y, q) >= (CUTOFF_YEAR, CUTOFF_Q)
    
                # ============ Normalize base data ============
                data = data.copy()
    
                data["Quarter"] = data["Quarter"].astype(str).str.strip()
                data["Sales Executive"] = data["Sales Executive"].fillna("").astype(str).str.strip()
    
                if "Lead Type" in data.columns:
                    data["Lead"] = data["Lead Type"].fillna("").astype(str).str.strip().str.title()
                else:
                    data["Lead"] = ""
    
                # Exclude Advait M
                executives = sorted(
                    [
                        str(e).strip()
                        for e in data["Sales Executive"].dropna().unique().tolist()
                        if str(e).strip()
                        and str(e).strip().upper() not in ["NAN", "NONE", "NULL"]
                        and str(e).strip() != "Advait M"
                    ]
                )
    
                if not executives:
                    st.warning("No Sales Executive values found.")
                else:
                    # Wing + Podium detection
                    data["WingNorm"] = data["Wing"].fillna("").astype(str).str.strip().str.upper()
    
                    floor_norm = data["Floor"].fillna("").astype(str).str.strip().str.lower()
    
                    data["PodiumFlag"] = (
                        floor_norm.eq("1")
                        | floor_norm.eq("1.0")
                        | floor_norm.str.contains(r"\b1st\b|\bfirst\b|podium|garden", case=False, na=False)
                    )
    
                    # Stage flags
                    data["Agreement Done Flag"] = (
                        data["Agreement Done"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.lower()
                        .eq("done")
                    )
    
                    rcc_s = data["RCC"].fillna("").astype(str).str.strip().str.lower()
                    data["RCC Flag"] = rcc_s.str.contains("complet", na=False)
    
                    pos_s = data["POSSESSION HANDOVER"].fillna("").astype(str).str.strip().str.lower()
                    data["Possession Flag"] = pos_s.str.contains("handover", na=False)
    
                    data["Is Given"] = data["Incentive"].fillna("").astype(str).str.contains(
                        "given",
                        case=False,
                        na=False
                    )
    
                    # Stamp Duty
                    def stamp_duty_mask(df_local):
                        if "Stamp Duty" not in df_local.columns:
                            return _pd.Series(False, index=df_local.index)
    
                        s = df_local["Stamp Duty"].fillna("").astype(str).str.strip().str.lower()
    
                        return (
                            s.str.contains("receiv", na=False)
                            | s.isin(["yes", "y", "received", "recieved", "done"])
                        )
    
                    # Numeric helpers
                    def _to_num(x):
                        if _pd.isna(x):
                            return np.nan
    
                        s = (
                            str(x)
                            .replace("₹", "")
                            .replace("Rs", "")
                            .replace("rs", "")
                            .replace("INR", "")
                            .replace("inr", "")
                            .replace(",", "")
                            .strip()
                        )
    
                        try:
                            return float(s)
                        except Exception:
                            return np.nan
    
                    def avg_rate_subset(df_local):
                        # Avg PSF = Sum Agreement Cost / Sum Carpet Area * 1.38
                        if df_local.empty or ("Agreement Cost" not in df_local.columns) or ("Carpet Area" not in df_local.columns):
                            return np.nan
    
                        ac_sum = df_local["Agreement Cost"].apply(_to_num).sum(min_count=1)
                        ca_sum = df_local["Carpet Area"].apply(_to_num).sum(min_count=1)
                        denom = (ca_sum * 1.38) if _pd.notna(ca_sum) else np.nan
    
                        return (ac_sum / denom) if (_pd.notna(ac_sum) and _pd.notna(denom) and denom > 0) else np.nan
    
                    # Base per-unit rate rule except FIXED_PER_EXEC quarter
                    def per_unit_rate_from_count(qdf_len: int):
                        # Same as Incentive Calculator: >=18 bookings => 6000 else 5000
                        return (6000, 6000) if qdf_len >= 18 else (5000, 5000)
    
                    def unit_rate_map(lead, dr, cr):
                        lead = str(lead).strip().title()
    
                        if lead == "Direct":
                            return dr
    
                        if lead in {"Cp", "CP", "Referral", "Digital", "Hoarding"}:
                            return cr
    
                        return 0
    
                    # ============ Quarter-aware payout engine ============
                    def get_rule_for_quarter(qtxt):
                        key = _canonical_quarter(qtxt)
                        return QUARTER_RULES.get(key, QUARTER_RULES[DEFAULT_RULE_KEY])
    
                    def _pct_from_thresholds(rate_value, tdict):
                        if _pd.notna(rate_value) and rate_value >= tdict["t100"]:
                            return 1.0
    
                        if _pd.notna(rate_value) and tdict["t70"] <= rate_value < tdict["t100"]:
                            return 0.7
    
                        if _pd.notna(rate_value) and tdict["t40"] <= rate_value < tdict["t70"]:
                            return 0.4
    
                        return 0.0
    
                    def apply_payouts_for_exec_quarter(q_df, q, exec_name):
                        q_df = q_df.copy()
    
                        # Masks
                        mask_np = ~q_df["PodiumFlag"]     # non-podium
                        mask_p = q_df["PodiumFlag"]       # podium
    
                        mE = q_df["WingNorm"].eq("E") & mask_np
                        mF = q_df["WingNorm"].eq("F") & mask_np
                        mC = q_df["WingNorm"].eq("C") & mask_np
                        mEF = mE | mF
    
                        rule = get_rule_for_quarter(q)
    
                        # ---------- Mode 1: FIXED PER EXEC ----------
                        if rule["mode"] == "FIXED_PER_EXEC":
                            fixed = rule.get("fixed_rates", {})
                            flat_rate = float(fixed.get(exec_name, 0))
    
                            q_df["Per Unit Rate Applied"] = flat_rate
                            q_df["Payout % Applied"] = 1.0
    
                            # Do not apply podium override in fixed scheme
                            q_df["Per Unit Incentive"] = q_df["Per Unit Rate Applied"] * q_df["Payout % Applied"]
    
                            return q_df
    
                        # ---------- Mode 2/3: PSF slabs ----------
                        dr, cr = per_unit_rate_from_count(len(q_df))
    
                        q_df["Per Unit Rate Applied"] = q_df["Lead"].map(lambda L: unit_rate_map(L, dr, cr))
    
                        # Averages
                        avg_all_np = avg_rate_subset(q_df[mask_np])
                        avgEF = avg_rate_subset(q_df[mEF]) if mEF.any() else np.nan
                        avgC = avg_rate_subset(q_df[mC]) if mC.any() else np.nan
    
                        GLOBAL_FALLBACK = {
                            "t100": 5800,
                            "t70": 5700,
                            "t40": 5600,
                        }
    
                        if rule["mode"] == "GLOBAL":
                            t = rule["global_t"]
                            base_pct = _pct_from_thresholds(avg_all_np, t)
                            q_df["Payout % Applied"] = base_pct
    
                        elif rule["mode"] == "WING_WISE":
                            tef = rule["ef_t"]
                            tc = rule["c_t"]
    
                            def wing_pct_row(row):
                                if row["PodiumFlag"]:
                                    return 0.0
    
                                w = row["WingNorm"]
    
                                if w in {"E", "F"}:
                                    return _pct_from_thresholds(avgEF, tef)
    
                                if w == "C":
                                    return _pct_from_thresholds(avgC, tc)
    
                                return _pct_from_thresholds(avg_all_np, GLOBAL_FALLBACK)
    
                            q_df["Payout % Applied"] = q_df.apply(wing_pct_row, axis=1)
    
                        else:
                            q_df["Payout % Applied"] = _pct_from_thresholds(avg_all_np, GLOBAL_FALLBACK)
    
                        # ---------- Podium override ----------
                        # Keeping your existing logic:
                        # >= 5800 => 100%
                        # 5700 to <5800 => 70%
                        # else 0%
                        if mask_p.any():
                            avg_pod = avg_rate_subset(q_df[mask_p])
    
                            if _pd.isna(avg_pod):
                                pod_pct = 0.0
                            elif avg_pod >= 5800:
                                pod_pct = 1.0
                            elif 5700 <= avg_pod < 5800:
                                pod_pct = 0.7
                            else:
                                pod_pct = 0.0
    
                            q_df.loc[mask_p, "Payout % Applied"] = pod_pct
    
                        # Final per-flat incentive
                        q_df["Per Unit Incentive"] = q_df["Per Unit Rate Applied"] * q_df["Payout % Applied"]
    
                        return q_df
    
                    # Split from 2026-Q2:
                    # RCC = 1000, POS = 1000, AG = remainder
                    # Bonuses never split
                    def split_fixed_1000(amount):
                        A = 0.0 if _pd.isna(amount) else float(amount)
    
                        if A <= 0:
                            return (0.0, 0.0, 0.0)
    
                        rcc = min(1000.0, A)
                        rem = A - rcc
                        pos = min(1000.0, rem)
                        ag = max(A - rcc - pos, 0.0)
    
                        return (ag, rcc, pos)
    
                    # Bonuses on Applicable basis
                    def bonuses_applicable(q_df_all, q, exec_name):
                        q_app = q_df_all[q_df_all["Agreement Done Flag"]].copy()
                        q_app_np = q_app[~q_app["PodiumFlag"]]
    
                        e_cnt = int((q_app_np["WingNorm"] == "E").sum())
                        f_cnt = int((q_app_np["WingNorm"] == "F").sum())
                        c_cnt = int((q_app_np["WingNorm"] == "C").sum())
    
                        efc_cnt = e_cnt + f_cnt + c_cnt
    
                        avgEF = avg_rate_subset(q_app_np[q_app_np["WingNorm"].isin(["E", "F"])])
                        avgC = avg_rate_subset(q_app_np[q_app_np["WingNorm"] == "C"])
    
                        # Top seller: 20+ applicable units => 1000 per unit
                        top_seller = (len(q_app) * 1000) if len(q_app) >= 20 else 0
    
                        # Team bonus:
                        # if team applicable units in quarter >= 60,
                        # share 50000 among eligible execs
                        all_q = data[data["Quarter"] == q].copy()
    
                        all_q["Agreement Done Flag"] = all_q["Agreement Done"].astype(str).str.strip().str.lower().eq("done")
    
                        team_units_app = int(all_q["Agreement Done Flag"].sum())
    
                        elig_counts = (
                            all_q[all_q["Agreement Done Flag"]].groupby("Sales Executive").size()
                            if not all_q[all_q["Agreement Done Flag"]].empty
                            else _pd.Series(dtype=int)
                        )
    
                        elig_names = elig_counts[elig_counts >= 1].index.tolist()
    
                        team_share = (
                            50000 / len(elig_names)
                            if (
                                team_units_app >= 60
                                and len(elig_names) > 0
                                and exec_name in elig_names
                            )
                            else 0
                        )
    
                        # High rate bonus:
                        # 18+ applicable non-podium E/F/C,
                        # EF avg >= 6000,
                        # C avg >= 6000
                        high_rate = 100000 if (
                            efc_cnt >= 18
                            and ((e_cnt + f_cnt == 0) or (_pd.notna(avgEF) and avgEF >= 6000))
                            and ((c_cnt == 0) or (_pd.notna(avgC) and avgC >= 6000))
                        ) else 0
    
                        return int(round(top_seller + team_share + high_rate))
    
                    def fmt_inr(x):
                        try:
                            return f"₹ {int(round(float(x))):,}"
                        except Exception:
                            return "₹ 0"
    
                    def _to_int_series(col):
                        return _pd.to_numeric(
                            col.astype(str)
                            .str.replace("₹", "", regex=False)
                            .str.replace(",", "", regex=False)
                            .str.strip(),
                            errors="coerce"
                        ).fillna(0).astype(int)
    
                    # ================= Build per-executive sections =================
                    overall_rows = []
                    overall_paid_rows = []
    
                    for exec_name in executives:
                        st.subheader(f"👤 {exec_name}")
    
                        # -------- Agreement Done basis --------
                        rows_ag = []
    
                        for q in quarters:
                            q_df = data[
                                (data["Quarter"] == q)
                                & (data["Sales Executive"] == exec_name)
                            ].copy()
    
                            if q_df.empty:
                                rows_ag.append({
                                    "Quarter": q,
                                    "AG": "₹ 0",
                                    "RCC": "₹ 0",
                                    "POS": "₹ 0",
                                    "AG Paid": "₹ 0",
                                    "RCC Paid": "₹ 0",
                                    "POS Paid": "₹ 0",
                                    "Total Paid": "₹ 0",
                                    "Bonus": "₹ 0",
                                    "Balance": "₹ 0",
                                })
                                continue
    
                            q_df = apply_payouts_for_exec_quarter(q_df, q, exec_name)
    
                            ag_mask = q_df["Agreement Done Flag"]
                            rcc_mask = ag_mask & q_df["RCC Flag"]
                            pos_mask = ag_mask & q_df["Possession Flag"]
    
                            base_series = (q_df["Per Unit Incentive"] * ag_mask).fillna(0.0).astype(float)
    
                            # Term-wise due
                            if use_three_term_for(q):
                                splits = base_series.apply(split_fixed_1000)
    
                                t1 = splits.apply(lambda t: t[0])
                                t2 = splits.apply(lambda t: t[1])
                                t3 = splits.apply(lambda t: t[2])
    
                                ag_due = float(t1.loc[ag_mask].sum())
                                rcc_due = float(t2.loc[rcc_mask].sum())
                                pos_due = float(t3.loc[pos_mask].sum())
                            else:
                                ag_due = float(base_series.sum())
                                rcc_due = 0.0
                                pos_due = 0.0
    
                            # Paid logic
                            if not use_three_term_for(q):
                                ag_paid = float(q_df.loc[ag_mask & q_df["Is Given"], "Per Unit Incentive"].sum())
                                rcc_paid = 0.0
                                pos_paid = 0.0
                            else:
                                splits_all = q_df["Per Unit Incentive"].fillna(0.0).astype(float).apply(split_fixed_1000)
    
                                ag_share = splits_all.apply(lambda t: t[0])
                                rcc_share = splits_all.apply(lambda t: t[1])
                                pos_share = splits_all.apply(lambda t: t[2])
    
                                ag_paid = float(ag_share.loc[ag_mask & q_df["Is Given"]].sum())
                                rcc_paid = float(rcc_share.loc[rcc_mask].sum())
                                pos_paid = float(pos_share.loc[pos_mask].sum())
    
                            total_paid = ag_paid + rcc_paid + pos_paid
    
                            bonus_amt = bonuses_applicable(q_df, q, exec_name)
    
                            bal_base = max((ag_due + rcc_due + pos_due) - total_paid, 0.0)
                            balance = int(round(bal_base + bonus_amt))
    
                            rows_ag.append({
                                "Quarter": q,
                                "AG": fmt_inr(ag_due),
                                "RCC": fmt_inr(rcc_due),
                                "POS": fmt_inr(pos_due),
                                "AG Paid": fmt_inr(ag_paid),
                                "RCC Paid": fmt_inr(rcc_paid),
                                "POS Paid": fmt_inr(pos_paid),
                                "Total Paid": fmt_inr(total_paid),
                                "Bonus": fmt_inr(bonus_amt),
                                "Balance": fmt_inr(balance),
                            })
    
                        df_ag = _pd.DataFrame(
                            rows_ag,
                            columns=[
                                "Quarter",
                                "AG",
                                "RCC",
                                "POS",
                                "AG Paid",
                                "RCC Paid",
                                "POS Paid",
                                "Total Paid",
                                "Bonus",
                                "Balance",
                            ]
                        )
    
                        df_ag["__key"] = df_ag["Quarter"].map(_quarter_sort_key)
                        df_ag = df_ag.sort_values("__key").drop(columns="__key").reset_index(drop=True)
    
                        st.markdown("**Status by Quarter (Agreement Done basis)**")
                        st.dataframe(df_ag, use_container_width=True, hide_index=True)
    
                        # -------- Stamp Duty basis --------
                        rows_sd = []
    
                        for q in quarters:
                            q_df = data[
                                (data["Quarter"] == q)
                                & (data["Sales Executive"] == exec_name)
                            ].copy()
    
                            if q_df.empty:
                                rows_sd.append({
                                    "Quarter": q,
                                    "AG": "₹ 0",
                                    "RCC": "₹ 0",
                                    "POS": "₹ 0",
                                    "AG Paid": "₹ 0",
                                    "RCC Paid": "₹ 0",
                                    "POS Paid": "₹ 0",
                                    "Total Paid": "₹ 0",
                                    "Bonus": "₹ 0",
                                    "Balance": "₹ 0",
                                })
                                continue
    
                            q_df = apply_payouts_for_exec_quarter(q_df, q, exec_name)
    
                            sd_mask = stamp_duty_mask(q_df)
                            rcc_mask = sd_mask & q_df["RCC Flag"]
                            pos_mask = sd_mask & q_df["Possession Flag"]
    
                            base_series = (q_df["Per Unit Incentive"] * sd_mask).fillna(0.0).astype(float)
    
                            if use_three_term_for(q):
                                splits = base_series.apply(split_fixed_1000)
    
                                t1 = splits.apply(lambda t: t[0])
                                t2 = splits.apply(lambda t: t[1])
                                t3 = splits.apply(lambda t: t[2])
    
                                ag_due = float(t1.loc[sd_mask].sum())
                                rcc_due = float(t2.loc[rcc_mask].sum())
                                pos_due = float(t3.loc[pos_mask].sum())
                            else:
                                ag_due = float(base_series.sum())
                                rcc_due = 0.0
                                pos_due = 0.0
    
                            if not use_three_term_for(q):
                                ag_paid = float(q_df.loc[sd_mask & q_df["Is Given"], "Per Unit Incentive"].sum())
                                rcc_paid = 0.0
                                pos_paid = 0.0
                            else:
                                splits_all = q_df["Per Unit Incentive"].fillna(0.0).astype(float).apply(split_fixed_1000)
    
                                ag_share = splits_all.apply(lambda t: t[0])
                                rcc_share = splits_all.apply(lambda t: t[1])
                                pos_share = splits_all.apply(lambda t: t[2])
    
                                ag_paid = float(ag_share.loc[sd_mask & q_df["Is Given"]].sum())
                                rcc_paid = float(rcc_share.loc[rcc_mask].sum())
                                pos_paid = float(pos_share.loc[pos_mask].sum())
    
                            # Bonuses on Stamp Duty subset
                            q_sd = q_df[sd_mask].copy()
                            q_sd_np = q_sd[~q_sd["PodiumFlag"]]
    
                            e_cnt = int((q_sd_np["WingNorm"] == "E").sum())
                            f_cnt = int((q_sd_np["WingNorm"] == "F").sum())
                            c_cnt = int((q_sd_np["WingNorm"] == "C").sum())
    
                            efc_cnt = e_cnt + f_cnt + c_cnt
    
                            avgEF_sd = avg_rate_subset(q_sd_np[q_sd_np["WingNorm"].isin(["E", "F"])])
                            avgC_sd = avg_rate_subset(q_sd_np[q_sd_np["WingNorm"] == "C"])
    
                            top_seller_sd = (len(q_sd) * 1000) if len(q_sd) >= 20 else 0
    
                            all_q_sd = data[stamp_duty_mask(data) & (data["Quarter"] == q)]
    
                            elig_counts_sd = (
                                all_q_sd.groupby("Sales Executive").size()
                                if not all_q_sd.empty
                                else _pd.Series(dtype=int)
                            )
    
                            elig_names_sd = elig_counts_sd[elig_counts_sd >= 12].index.tolist()
    
                            team_sd = (
                                50000 / len(elig_names_sd)
                                if (
                                    len(all_q_sd) >= 60
                                    and len(elig_names_sd) > 0
                                    and exec_name in elig_names_sd
                                )
                                else 0
                            )
    
                            high_rate_sd = 100000 if (
                                efc_cnt >= 18
                                and ((e_cnt + f_cnt == 0) or (_pd.notna(avgEF_sd) and avgEF_sd >= 6000))
                                and ((c_cnt == 0) or (_pd.notna(avgC_sd) and avgC_sd >= 6000))
                            ) else 0
    
                            bonus_sd = int(round(top_seller_sd + team_sd + high_rate_sd))
    
                            total_paid = ag_paid + rcc_paid + pos_paid
    
                            bal_base = max((ag_due + rcc_due + pos_due) - total_paid, 0.0)
                            balance = int(round(bal_base + bonus_sd))
    
                            rows_sd.append({
                                "Quarter": q,
                                "AG": fmt_inr(ag_due),
                                "RCC": fmt_inr(rcc_due),
                                "POS": fmt_inr(pos_due),
                                "AG Paid": fmt_inr(ag_paid),
                                "RCC Paid": fmt_inr(rcc_paid),
                                "POS Paid": fmt_inr(pos_paid),
                                "Total Paid": fmt_inr(total_paid),
                                "Bonus": fmt_inr(bonus_sd),
                                "Balance": fmt_inr(balance),
                            })
    
                        df_sd = _pd.DataFrame(
                            rows_sd,
                            columns=[
                                "Quarter",
                                "AG",
                                "RCC",
                                "POS",
                                "AG Paid",
                                "RCC Paid",
                                "POS Paid",
                                "Total Paid",
                                "Bonus",
                                "Balance",
                            ]
                        )
    
                        df_sd["__key"] = df_sd["Quarter"].map(_quarter_sort_key)
                        df_sd = df_sd.sort_values("__key").drop(columns="__key").reset_index(drop=True)
    
                        st.markdown("**Status by Quarter (Stamp Duty Received basis)**")
                        st.dataframe(df_sd, use_container_width=True, hide_index=True)
    
                        # Collect for overall tables - Agreement basis
                        overall_rows.append({
                            "Sales Executive": exec_name,
                            "Amount": int(_to_int_series(df_ag["Balance"]).sum()),
                        })
    
                        overall_paid_rows.append({
                            "Sales Executive": exec_name,
                            "Amount": int(_to_int_series(df_ag["Total Paid"]).sum()),
                        })
    
                        st.markdown("---")
    
                    # ===== Overall Totals - Agreement basis =====
                    df_overall = _pd.DataFrame(overall_rows, columns=["Sales Executive", "Amount"])
                    total_sum_bal = int(df_overall["Amount"].sum()) if not df_overall.empty else 0
    
                    df_overall = _pd.concat(
                        [
                            df_overall,
                            _pd.DataFrame([{
                                "Sales Executive": "TOTAL",
                                "Amount": total_sum_bal,
                            }])
                        ],
                        ignore_index=True
                    )
    
                    df_overall["Amount"] = df_overall["Amount"].apply(fmt_inr)
    
                    st.markdown("**Overall Total Balance (Agreement basis)**")
                    st.dataframe(df_overall, use_container_width=True, hide_index=True)
    
                    df_paid = _pd.DataFrame(overall_paid_rows, columns=["Sales Executive", "Amount"])
                    total_sum_paid = int(df_paid["Amount"].sum()) if not df_paid.empty else 0
    
                    df_paid = _pd.concat(
                        [
                            df_paid,
                            _pd.DataFrame([{
                                "Sales Executive": "TOTAL",
                                "Amount": total_sum_paid,
                            }])
                        ],
                        ignore_index=True
                    )
    
                    df_paid["Amount"] = df_paid["Amount"].apply(fmt_inr)
    
                    st.markdown("**Overall Total Paid to Date (Agreement basis)**")
                    st.dataframe(df_paid, use_container_width=True, hide_index=True)
