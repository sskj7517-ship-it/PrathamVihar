# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.

# ---------- Shared UI CSS (Schedule + Referral Invoice) ----------
st.markdown("""
<style>
  :root{
    --grad: linear-gradient(135deg,#4f46e5 0%,#7c3aed 100%);
    --soft:#f1f5f9; --soft-green:#eef7ec; --soft-blue:#eff6ff;
    --border:#e2e8f0; --text:#0f172a; --muted:#475569;
  }
  .rg-wrap{border:1px solid var(--border); border-radius:14px; padding:16px; background:white; margin:10px 0 16px;}
  .rg-badge{display:inline-flex;align-items:center;gap:8px;padding:6px 12px;border-radius:999px;font-weight:700;font-size:12px;background:var(--soft-blue);color:#1d4ed8;border:1px solid #bfdbfe;margin:6px 0 10px;}
  .rg-badge.green{background:var(--soft-green);color:#166534;border-color:#bbf7d0}
  .rg-card{border:1px solid var(--border);border-radius:12px;background:var(--soft);padding:14px 16px;margin-bottom:10px;box-shadow:0 6px 14px rgba(15,23,42,.06);}
  .rg-card.info{background:var(--soft-blue); border-color:#c7ddff}
  .rg-card.ok{background:var(--soft-green); border-color:#c7eed0}
  .rg-label{font-size:12px;color:var(--muted);margin-bottom:6px}
  .rg-value{font-size:18px;font-weight:800;color:var(--text)}
  .rg-kicker{font-size:12px;color:var(--muted);margin-left:6px}
  .rg-download{display:inline-block;margin-top:10px;padding:8px 12px;border-radius:10px;background:var(--grad);color:#fff !important;text-decoration:none}
  .schedule-table {
      border-collapse: collapse;
      width: 100%;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 10px rgba(0,0,0,.08);
      margin: 15px 0;
  }
  .schedule-table th {
      background: #2563eb;
      color: white;
      text-align: left;
      padding: 10px;
      font-size: 14px;
  }
  .schedule-table td {
      padding: 10px;
      font-size: 13px;
      border-bottom: 1px solid #e2e8f0;
  }
  .schedule-table tr:nth-child(even) {background: #f8fafc;}
  .schedule-table tr:last-child td {
      font-weight: 700;
      background: #f1f5f9;
  }
  .pill-ok{
    display:inline-block;padding:2px 10px;border-radius:999px;
    font-weight:800;font-size:12px;background:#dcfce7;color:#166534;border:1px solid #bbf7d0;
  }
  .pill-pend{
    display:inline-block;padding:2px 10px;border-radius:999px;
    font-weight:800;font-size:12px;background:#ffedd5;color:#9a3412;border:1px solid #fed7aa;
  }
  .mono {white-space: nowrap;}
</style>
""", unsafe_allow_html=True)

schedule_tab, referral_invoice_tab, agreement_schedule_tab = st.tabs([
    "Schedule",
    "Referral Invoice",
    "Agreement Schedule"
])

# =========================================================
# SUBTAB 1: SCHEDULE
# =========================================================
with schedule_tab:
    st.header("📦 Total Package & 📅 Schedule")

    if "tab4_schedule_generated" not in st.session_state:
        st.session_state.tab4_schedule_generated = False
    if "tab4_final_cost" not in st.session_state:
        st.session_state.tab4_final_cost = 0
    if "tab4_schedule_sd_rate" not in st.session_state:
        st.session_state.tab4_schedule_sd_rate = 7

    with st.form("tab4_schedule_form"):
        c1, c2 = st.columns([2, 1])

        with c1:
            st.number_input(
                "Enter Total Cost (₹)",
                min_value=0,
                step=1000,
                value=int(st.session_state.tab4_final_cost or 0),
                key="tab4_final_cost",
                help="Enter the total package value inclusive of agreement, stamp duty, GST, registration and legal fees."
            )

        with c2:
            st.selectbox(
                "Stamp Duty % for Schedule",
                [6, 7],
                index=1 if st.session_state.tab4_schedule_sd_rate == 7 else 0,
                key="tab4_schedule_sd_rate"
            )

        gen = st.form_submit_button("Generate")

    if gen:
        st.session_state.tab4_schedule_generated = True

    if not st.session_state.tab4_schedule_generated:
        st.info("Enter Total Cost and Stamp Duty %, then click **Generate**.")
    else:
        final_cost = st.session_state.tab4_final_cost
        schedule_sd_rate = st.session_state.tab4_schedule_sd_rate

        legal_fee = 12000
        reg_fee = 30000

        agreement_cost = None
        stamp6 = stamp7 = None
        gst_rate = None
        gst_amt = None
        total6 = total7 = None
        total6_lakhs = total7_lakhs = None

        if final_cost and final_cost > 0:
            cost_less_legal = final_cost - reg_fee
            agreement_cost = cost_less_legal / (1.08 if final_cost <= 4_890_000 else 1.12)
            agreement_cost = math.ceil(agreement_cost / 100) * 100

            stamp6 = math.ceil((0.06 * agreement_cost) / 100) * 100
            stamp7 = math.ceil((0.07 * agreement_cost) / 100) * 100

            gst_rate = 0.01 if agreement_cost <= 4_500_000 else 0.05
            gst_amt = round(agreement_cost * gst_rate)

            total6 = agreement_cost + stamp6 + gst_amt + reg_fee
            total7 = agreement_cost + stamp7 + gst_amt + reg_fee
            total6_lakhs = round(total6 / 100000, 2)
            total7_lakhs = round(total7 / 100000, 2)

            st.markdown('<div class="rg-badge green">🔎 Preview</div>', unsafe_allow_html=True)
            st.markdown('<div class="rg-wrap">', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="rg-card ok">
                  <div class="rg-label">Agreement Cost (Auto)</div>
                  <div class="rg-value">₹ {agreement_cost:,}<span class="rg-kicker">(rounded to next ₹100)</span></div>
                </div>
                <div class="rg-card">
                  <div class="rg-label">GST on Agreement (Auto)</div>
                  <div class="rg-value">₹ {gst_amt:,}<span class="rg-kicker">Rate: {int(gst_rate * 100)}%</span></div>
                </div>
                <div class="rg-card">
                  <div class="rg-label">Stamp Duty @ 6% (Auto)</div>
                  <div class="rg-value">₹ {stamp6:,}</div>
                </div>
                <div class="rg-card info">
                  <div class="rg-label">Registration Fees (Auto)</div>
                  <div class="rg-value">₹ {reg_fee:,}</div>
                </div>
                <div class="rg-card">
                  <div class="rg-label">Total Package @ 6% (Auto)</div>
                  <div class="rg-value">₹ {total6:,}<span class="rg-kicker">≈ {total6_lakhs} Lakhs</span></div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="rg-card ok">
                  <div class="rg-label">Agreement Cost (Auto)</div>
                  <div class="rg-value">₹ {agreement_cost:,}<span class="rg-kicker">(rounded to next ₹100)</span></div>
                </div>
                <div class="rg-card">
                  <div class="rg-label">GST on Agreement (Auto)</div>
                  <div class="rg-value">₹ {gst_amt:,}<span class="rg-kicker">Rate: {int(gst_rate * 100)}%</span></div>
                </div>
                <div class="rg-card">
                  <div class="rg-label">Stamp Duty @ 7% (Auto)</div>
                  <div class="rg-value">₹ {stamp7:,}</div>
                </div>
                <div class="rg-card info">
                  <div class="rg-label">Registration Fees (Auto)</div>
                  <div class="rg-value">₹ {reg_fee:,}</div>
                </div>
                <div class="rg-card">
                  <div class="rg-label">Total Package @ 7% (Auto)</div>
                  <div class="rg-value">₹ {total7:,}<span class="rg-kicker">≈ {total7_lakhs} Lakhs</span></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🧾 Generate Schedule")

        if (final_cost and final_cost > 0) and (agreement_cost is not None):
            raw_schedule_stamp = (schedule_sd_rate / 100) * agreement_cost
            schedule_stamp_duty = math.ceil(raw_schedule_stamp / 100) * 100

            gst_rate = 0.01 if agreement_cost <= 4_500_000 else 0.05

            st.markdown('<div class="rg-wrap">', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="rg-card">
              <div class="rg-label">Schedule Summary</div>
              <div class="rg-value">Agreement: ₹ {agreement_cost:,}
                <span class="rg-kicker">• Stamp (@{schedule_sd_rate}%): ₹ {schedule_stamp_duty:,}
                • GST on stages: {int(gst_rate * 100)}%
                • Reg: ₹ {reg_fee:,}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            schedule_data = [
                ("ADVANCE PAYMENT TOWARDS FLAT BOOKING + SD + REG", 5),
                ("AFTER EXECUTION OF AGREEMENT WITHIN 30 DAYS", 10),
                ("ON COMPLETION OF THE PLINTH / 1ST FLOOR SLAB", 15),
                ("ON COMPLETION  OF THE THIRD FLOOR", 7.5),
                ("ON COMPLETION OF THE SEVENTH FLOOR", 7.5),
                ("ON COMPLETION OF THE TENTH FLOOR", 7.5),
                ("ON COMPLETION OF THE THIRTEEN FLOOR", 7.5),
                ("ON COMPLETION OF FLOORING WORK OF PARTICULAR FLAT / FLOOR.", 7.5),
                ("ON COMPLETION OF EXTERNAL PLASTERING / PRIMER OF BUILDING.", 7.5),
                ("ON COMMENCEMENT OF INTERNAL PLUMBING OF PARTICULAR FLAT.", 7.5),
                ("ON COMMENCEMENT ELECTRICAL WIRING / WINDOW/ DOOR OF PARTICULAR FLAT.", 7.5),
                ("ON COMMENCEMENT OF SANITARY OF PARTICULAR FLAT & LIFTS OF BUILDING & EXTERNAL PAINT.", 5),
                ("At the time of handover of POSSESSION OR on receipt of OCCUPATION / COMPLETION CERTIFICATE...", 5)
            ]

            schedule = []

            for desc, perc in schedule_data:
                base = agreement_cost * (perc / 100)
                gst_amt_line = base * gst_rate
                total_amt = base + gst_amt_line

                if "ADVANCE PAYMENT" in desc:
                    total_amt += schedule_stamp_duty + reg_fee

                schedule.append((desc, perc, round(base), round(gst_amt_line), round(total_amt)))

            schedule_df = pd.DataFrame(schedule, columns=["Description", "%", "Amount", "GST", "Total"])

            totals = {
                "Description": "Total",
                "%": "",
                "Amount": int(schedule_df["Amount"].sum()),
                "GST": int(schedule_df["GST"].sum()),
                "Total": int(schedule_df["Total"].sum()),
            }

            schedule_df = pd.concat([schedule_df, pd.DataFrame([totals])], ignore_index=True)

            html = '<table class="schedule-table">'
            html += "<tr>" + "".join([f"<th>{h}</th>" for h in ["#", "Description", "%", "Amount", "GST", "Total"]]) + "</tr>"

            for i, row in schedule_df.iterrows():
                is_total = row["Description"] == "Total"
                num = "" if is_total else str(i + 1)

                html += "<tr>"
                html += f"<td>{num}</td>"
                html += f"<td>{row['Description']}</td>"
                html += f"<td>{'' if is_total else row['%']}</td>"
                html += f"<td>₹ {int(row['Amount']):,}</td>"
                html += f"<td>₹ {int(row['GST']):,}</td>"
                html += f"<td>₹ {int(row['Total']):,}</td>"
                html += "</tr>"

            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=8)
            pdf.set_auto_page_break(auto=True, margin=15)

            pdf.cell(0, 10, txt=f"Payment Schedule (Stamp Duty {schedule_sd_rate}%)", ln=True, align="C")

            headers = ["#", "Description", "%", "Amount", "GST", "Total"]
            col_widths = [8, 90, 10, 25, 25, 25]

            pdf.set_fill_color(200, 220, 255)

            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, border=1, fill=True)

            pdf.ln()

            line_h = 5

            for idx, row in schedule_df.iterrows():
                desc = str(row["Description"])
                is_total = desc == "Total"

                x0 = pdf.get_x()
                y0 = pdf.get_y()

                pdf.set_xy(x0 + col_widths[0], y0)
                pdf.multi_cell(col_widths[1], line_h, desc, border=1)

                y1 = pdf.get_y()
                row_h = y1 - y0

                pdf.set_xy(x0, y0)
                pdf.cell(col_widths[0], row_h, "" if is_total else str(idx + 1), border=1, align="C")

                pct_val = "" if is_total else ("" if str(row["%"]) in ("", "nan", "None") else str(row["%"]))

                pdf.set_xy(x0 + col_widths[0] + col_widths[1], y0)
                pdf.cell(col_widths[2], row_h, pct_val, border=1, align="C")

                pdf.set_xy(x0 + col_widths[0] + col_widths[1] + col_widths[2], y0)
                pdf.cell(col_widths[3], row_h, f"Rs {int(row['Amount']):,}", border=1, align='R')

                pdf.set_xy(x0 + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], y0)
                pdf.cell(col_widths[4], row_h, f"Rs {int(row['GST']):,}", border=1, align='R')

                pdf.set_xy(
                    x0 + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4],
                    y0
                )
                pdf.cell(col_widths[5], row_h, f"Rs {int(row['Total']):,}", border=1, align='R')

                pdf.set_xy(x0, y0 + row_h)

            pdf.ln(4)
            pdf.cell(0, 8, f"Stamp Duty (@ {schedule_sd_rate}%): Rs {schedule_stamp_duty:,}", ln=True)
            pdf.cell(0, 8, f"Registration Fee: Rs {reg_fee:,}", ln=True)
            pdf.cell(0, 8, f"Agreement Cost: Rs {agreement_cost:,}", ln=True)
            pdf.cell(0, 8, f"GST Rate on stages: {int(gst_rate * 100)}%", ln=True)

            pdf_output = pdf.output(dest='S').encode('latin1', 'ignore')
            b64 = base64.b64encode(pdf_output).decode()

            st.markdown(
                f'<a class="rg-download" href="data:application/octet-stream;base64,{b64}" download="schedule.pdf">⬇️ Download PDF</a>',
                unsafe_allow_html=True
            )

            st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# SUBTAB 2: REFERRAL INVOICE / VOUCHER - FLEXIBLE SUPABASE VERSION
# No st.stop() version — other tabs will continue loading
# Works with both:
#   Supabase columns: customer_name, flat_number, booking_date, etc.
#   Old sheet columns: Customer Name, Flat Number, Date, etc.
# =========================================================

with referral_invoice_tab:

    def render_referral_invoice_tab():
        import re
        import io
        import base64
        import datetime
        import pandas as pd
        import streamlit as st
        from fpdf import FPDF

        st.header("🧾 Referral Incentive Voucher")

        # ---------------------------------------------------------
        # Basic CSS for cards/download button
        # ---------------------------------------------------------
        st.markdown(
            """
            <style>
            .rg-wrap{
                display:grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap:14px;
                margin: 14px 0 18px 0;
            }
            .rg-card{
                background:#ffffff;
                border:1px solid #e5e7eb;
                border-radius:16px;
                padding:16px;
                box-shadow:0 8px 20px rgba(15,23,42,.06);
            }
            .rg-card.ok{background:#ecfdf5;border-color:#bbf7d0;}
            .rg-card.info{background:#eff6ff;border-color:#bfdbfe;}
            .rg-label{
                font-size:12px;
                font-weight:800;
                color:#64748b;
                text-transform:uppercase;
                letter-spacing:.04em;
                margin-bottom:7px;
            }
            .rg-value{
                font-size:20px;
                font-weight:900;
                color:#0f172a;
                line-height:1.25;
            }
            .rg-kicker{
                display:block;
                font-size:12px;
                font-weight:700;
                color:#64748b;
                margin-top:6px;
            }
            .rg-download{
                display:inline-block;
                background:linear-gradient(135deg,#2563eb,#7c3aed);
                color:white !important;
                padding:13px 18px;
                border-radius:14px;
                font-weight:900;
                text-decoration:none !important;
                box-shadow:0 10px 24px rgba(37,99,235,.22);
                margin-top:10px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # ---------------------------------------------------------
        # Connection guard
        # ---------------------------------------------------------
        if not globals().get("supabase_connected", False):
            st.warning("📋 Please connect to Supabase to use this feature.")
            return

        # ---------------------------------------------------------
        # Pick booking dataframe safely
        # ---------------------------------------------------------
        df_ref_base = pd.DataFrame()

        for candidate_name in ["booking_df", "bookings_df", "sheet_df"]:
            candidate = globals().get(candidate_name, None)
            if isinstance(candidate, pd.DataFrame) and not candidate.empty:
                df_ref_base = candidate.copy()
                break

        if df_ref_base.empty:
            st.warning("No data available in Supabase bookings table.")
            return

        df_ref_base.columns = [str(c).strip() for c in df_ref_base.columns]

        # ---------------------------------------------------------
        # Flexible column helpers
        # ---------------------------------------------------------
        def _norm_col_name(x) -> str:
            return re.sub(r"[^a-z0-9]+", "", str(x or "").lower())

        def _find_col(df: pd.DataFrame, aliases: list[str]):
            if df is None or df.empty:
                return None

            cmap = {_norm_col_name(c): c for c in df.columns}

            for alias in aliases:
                key = _norm_col_name(alias)
                if key in cmap:
                    return cmap[key]

            return None

        def _safe_str(x) -> str:
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

        def _is_agreement_done(v) -> bool:
            s = _safe_str(v).lower()
            return (
                s in {"done", "completed", "complete", "yes", "true", "1"}
                or "done" in s
                or "complete" in s
            )

        def _is_referral_given(v) -> bool:
            s = _safe_str(v).lower()
            return s in {
                "given",
                "yes",
                "done",
                "paid",
                "received",
                "true",
                "1",
                "completed",
                "complete",
            }

        def _is_referral_lead(v) -> bool:
            s = _safe_str(v).lower()
            return "referral" in s or "reference" in s or s == "ref"

        # ---------------------------------------------------------
        # Map actual columns
        # ---------------------------------------------------------
        col_customer = _find_col(df_ref_base, [
            "customer_name", "customer name", "Customer Name",
            "name", "allottee_name", "allottee name"
        ])

        col_wing = _find_col(df_ref_base, [
            "wing", "Wing"
        ])

        col_flat = _find_col(df_ref_base, [
            "flat_number", "flat no", "flat number",
            "Flat Number", "Flat No", "unit", "unit_number"
        ])

        col_lead = _find_col(df_ref_base, [
            "lead_type", "lead type", "Lead Type",
            "source", "lead_source", "lead source"
        ])

        col_agreement_done = _find_col(df_ref_base, [
            "agreement_done", "agreement done", "Agreement Done",
            "agreement_status", "agreement status"
        ])

        col_referral_given = _find_col(df_ref_base, [
            "referral_given", "referral given", "Referral Given",
            "referral_status", "referral status"
        ])

        col_sales_exec = _find_col(df_ref_base, [
            "sales_executive", "sales executive", "Sales Executive",
            "executive", "handled_by", "handled by"
        ])

        col_booking_date = _find_col(df_ref_base, [
            "booking_date", "booking date", "Date", "date", "Booking Date"
        ])

        col_type = _find_col(df_ref_base, [
            "type", "Type", "unit_type", "unit type",
            "flat_type", "flat type", "configuration"
        ])

        col_pan = _find_col(df_ref_base, [
            "pan", "PAN", "pan_number", "pan number", "PAN Number"
        ])

        # Referral given can be optional. If missing, we assume not given.
        required_map = {
            "Customer Name": col_customer,
            "Wing": col_wing,
            "Flat Number": col_flat,
            "Lead Type": col_lead,
            "Agreement Done": col_agreement_done,
        }

        missing_required = [label for label, actual_col in required_map.items() if not actual_col]

        if missing_required:
            st.error(
                "Missing required booking columns: "
                + ", ".join(missing_required)
                + ". Please check your Supabase bookings table headers."
            )

            with st.expander("Show actual columns found in bookings dataframe", expanded=True):
                st.write(list(df_ref_base.columns))

            return

        # ---------------------------------------------------------
        # Normalize working dataframe
        # ---------------------------------------------------------
        df = df_ref_base.copy()

        df["_customer_name"] = df[col_customer].apply(_safe_str)
        df["_wing"] = df[col_wing].apply(_safe_str)
        df["_flat_number"] = df[col_flat].apply(_safe_str)
        df["_lead_type"] = df[col_lead].apply(_safe_str)
        df["_agreement_done"] = df[col_agreement_done].apply(_safe_str)

        if col_referral_given:
            df["_referral_given"] = df[col_referral_given].apply(_safe_str)
        else:
            df["_referral_given"] = ""

        if col_sales_exec:
            df["_sales_executive"] = df[col_sales_exec].apply(_safe_str)
        else:
            df["_sales_executive"] = ""

        if col_booking_date:
            df["_booking_date"] = df[col_booking_date].apply(_safe_str)
        else:
            df["_booking_date"] = ""

        if col_type:
            df["_type"] = df[col_type].apply(_safe_str)
        else:
            df["_type"] = ""

        if col_pan:
            df["_pan"] = df[col_pan].apply(_safe_str)
        else:
            df["_pan"] = ""

        # Remove blank customer rows
        df = df[df["_customer_name"].astype(str).str.strip().ne("")].copy()

        if df.empty:
            st.warning("No valid customer records found in bookings table.")
            return

        # ---------------------------------------------------------
        # Display helpers
        # ---------------------------------------------------------
        def flat_label(r):
            wing = _safe_str(r.get("_wing", ""))
            flat = _safe_str(r.get("_flat_number", ""))
            fl = f"{wing} {flat}".strip()
            return fl if fl else "NA"

        def label_row(i):
            r = df.loc[i]
            nm = _safe_str(r.get("_customer_name", ""))
            fl = flat_label(r)
            return f"{fl} - {nm}" if nm else fl

        def format_booking_date(v):
            s = _safe_str(v)
            if not s:
                return "NA"

            try:
                dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
                if pd.notna(dt):
                    return dt.strftime("%d/%m/%Y")
            except Exception:
                pass

            return s

        def get_unit_type_from_row(r):
            val = _safe_str(r.get("_type", ""))
            return val if val else "NA"

        # ---------------------------------------------------------
        # Pending referral vouchers
        # Rule:
        #   Lead Type contains referral/reference
        #   Agreement Done = done/completed/yes
        #   Referral Given is not given/paid/done
        # ---------------------------------------------------------
        lead_ok = df["_lead_type"].apply(_is_referral_lead)
        agree_ok = df["_agreement_done"].apply(_is_agreement_done)
        ref_not_given = ~df["_referral_given"].apply(_is_referral_given)

        for_df = df[lead_ok & agree_ok & ref_not_given].copy()

        if for_df.empty:
            st.info("✅ No pending referral vouchers.")
            return

        # ---------------------------------------------------------
        # Session state
        # ---------------------------------------------------------
        if "tab4_refinv_generated" not in st.session_state:
            st.session_state.tab4_refinv_generated = False

        if (
            "tab4_refinv_for_idx" not in st.session_state
            or st.session_state.tab4_refinv_for_idx not in for_df.index
        ):
            st.session_state.tab4_refinv_for_idx = for_df.index[0]

        if (
            "tab4_refinv_to_idx" not in st.session_state
            or st.session_state.tab4_refinv_to_idx not in df.index
        ):
            st.session_state.tab4_refinv_to_idx = df.index[0]

        if "tab4_refinv_to_pan" not in st.session_state:
            st.session_state.tab4_refinv_to_pan = ""

        # ---------------------------------------------------------
        # Form
        # ---------------------------------------------------------
        with st.form("tab4_refinv_form"):
            c1, c2 = st.columns(2)

            with c1:
                st.selectbox(
                    "For (Referred booking — Agreement Done & Referral not Given)",
                    options=list(for_df.index),
                    format_func=label_row,
                    key="tab4_refinv_for_idx"
                )

            with c2:
                st.selectbox(
                    "To (Referral amount will be given to)",
                    options=list(df.index),
                    format_func=label_row,
                    key="tab4_refinv_to_idx"
                )

            default_pan = ""
            try:
                to_idx_preview = st.session_state.get("tab4_refinv_to_idx")
                if to_idx_preview in df.index:
                    default_pan = _safe_str(df.loc[to_idx_preview].get("_pan", ""))
            except Exception:
                default_pan = ""

            if not st.session_state.get("tab4_refinv_to_pan") and default_pan:
                st.session_state["tab4_refinv_to_pan"] = default_pan

            st.text_input(
                "PAN Number (To Customer) — optional",
                key="tab4_refinv_to_pan",
                placeholder="Enter PAN e.g., ABCDE1234F"
            )

            g = st.form_submit_button("Generate Voucher", use_container_width=True)

        if g:
            st.session_state.tab4_refinv_generated = True

        if not st.session_state.tab4_refinv_generated:
            st.info("Select **For** and **To**, enter PAN if needed, then click **Generate Voucher**.")
            return

        # ---------------------------------------------------------
        # Voucher data
        # ---------------------------------------------------------
        for_idx = st.session_state.tab4_refinv_for_idx
        to_idx = st.session_state.tab4_refinv_to_idx

        for_row = df.loc[for_idx]
        to_row = df.loc[to_idx]

        for_name = _safe_str(for_row.get("_customer_name", ""))
        to_name = _safe_str(to_row.get("_customer_name", ""))

        for_flat = flat_label(for_row)
        to_flat = flat_label(to_row)

        for_unit_type = get_unit_type_from_row(for_row)
        sales_exec = _safe_str(for_row.get("_sales_executive", "")) or "NA"
        to_pan = _safe_str(st.session_state.tab4_refinv_to_pan) or _safe_str(to_row.get("_pan", "")) or "NA"

        to_booking_date = format_booking_date(to_row.get("_booking_date", ""))
        for_booking_date = format_booking_date(for_row.get("_booking_date", ""))

        gross_amount = 51000
        tds_rate = 0.02
        tds_amount = int(round(gross_amount * tds_rate))
        net_amount = gross_amount - tds_amount

        inv_date = datetime.datetime.now()
        date_str = inv_date.strftime("%d/%m/%Y")
        place_str = "132/2, DSK Vishwa Rd, DSK Vishwa, Dhayari, Pune, Khadewadi, Maharashtra 411041"

        # ---------------------------------------------------------
        # Number to words
        # ---------------------------------------------------------
        def num_to_words(n: int) -> str:
            ones = [
                "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                "Seventeen", "Eighteen", "Nineteen"
            ]
            tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

            def two_digits(x):
                if x < 20:
                    return ones[x]
                return tens[x // 10] + ("" if x % 10 == 0 else " " + ones[x % 10])

            def three_digits(x):
                h = x // 100
                r = x % 100

                if h and r:
                    return ones[h] + " Hundred " + two_digits(r)
                if h:
                    return ones[h] + " Hundred"

                return two_digits(r)

            if n == 0:
                return "Zero"

            parts = []

            if n >= 10000000:
                crores = n // 10000000
                parts.append(three_digits(crores) + " Crore")
                n %= 10000000

            if n >= 100000:
                lakhs = n // 100000
                parts.append(three_digits(lakhs) + " Lakh")
                n %= 100000

            if n >= 1000:
                th = n // 1000
                parts.append(three_digits(th) + " Thousand")
                n %= 1000

            if n > 0:
                parts.append(three_digits(n))

            return " ".join([p.strip() for p in parts if p.strip()])

        amount_words = f"Rupees {num_to_words(net_amount)} Only"

        # ---------------------------------------------------------
        # Preview cards
        # ---------------------------------------------------------
        st.markdown('<div class="rg-wrap">', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="rg-card ok">
              <div class="rg-label">Net Payable (After TDS)</div>
              <div class="rg-value">₹ {net_amount:,.0f}
                <span class="rg-kicker">Date: {date_str}</span>
              </div>
            </div>

            <div class="rg-card">
              <div class="rg-label">Gross / TDS</div>
              <div class="rg-value">₹ {gross_amount:,.0f}
                <span class="rg-kicker">TDS 2%: ₹ {tds_amount:,.0f}</span>
              </div>
            </div>

            <div class="rg-card">
              <div class="rg-label">To (Payable to)</div>
              <div class="rg-value">{to_name}
                <span class="rg-kicker">Flat: {to_flat} | PAN: {to_pan} | Booking: {to_booking_date}</span>
              </div>
            </div>

            <div class="rg-card info">
              <div class="rg-label">For (Referred booking)</div>
              <div class="rg-value">{for_name}
                <span class="rg-kicker">Flat: {for_flat} | Unit: {for_unit_type} | Booking: {for_booking_date}</span>
              </div>
            </div>

            <div class="rg-card">
              <div class="rg-label">Sales Executive</div>
              <div class="rg-value">{sales_exec}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # PDF helpers
        # ---------------------------------------------------------
        def pdf_safe(s):
            s = str(s or "")
            s = s.replace("₹", "Rs ").replace("—", "-").replace("•", "-").replace("→", "->")
            return s.encode("latin1", "ignore").decode("latin1")

        def _safe_filename(name: str) -> str:
            name = str(name or "").strip()
            bad = '\\/:*?"<>|'

            for ch in bad:
                name = name.replace(ch, "")

            name = " ".join(name.split())
            return name

        # ---------------------------------------------------------
        # Generate PDF
        # ---------------------------------------------------------
        pdf = FPDF("P", "mm", "A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=False, margin=10)

        LEFT = 10
        W = 190
        HALF = W / 2
        THIRD = W / 3
        FOOTER_BOTTOM = 287
        INSET = 1.2

        def double_rect(x, y, w, h, inset=INSET, outer=0.7, inner=0.25):
            pdf.set_line_width(outer)
            pdf.rect(x, y, w, h)
            pdf.set_line_width(inner)
            pdf.rect(x + inset, y + inset, w - 2 * inset, h - 2 * inset)
            pdf.set_line_width(0.25)

        def vline_trim(x, y, h, inset=INSET, eps=0.25):
            pdf.line(x, y + inset + eps, x, y + h - inset - eps)

        # Header
        pdf.set_fill_color(37, 99, 235)
        pdf.rect(0, 0, 210, 22, "F")
        pdf.set_text_color(255, 255, 255)

        pdf.set_xy(LEFT, 6)
        pdf.set_font("Arial", "B", 17)
        pdf.cell(W * 0.70, 7, pdf_safe("LJR CONSTRUCTIONS LLP"), ln=0, align="L")
        pdf.set_font("Arial", "B", 14)
        pdf.cell(W * 0.30, 7, pdf_safe("PRATHAM VIHAR"), ln=1, align="R")

        pdf.set_font("Arial", "", 12)
        pdf.set_xy(LEFT, 13)
        pdf.cell(0, 6, pdf_safe("Referral Voucher"), ln=1, align="L")
        pdf.set_text_color(0, 0, 0)

        y = 26
        pdf.set_fill_color(245, 247, 250)
        pdf.rect(LEFT, y, W, 12, "F")
        pdf.set_font("Arial", "B", 11)
        pdf.set_xy(LEFT + 2, y + 3)
        pdf.cell(0, 6, pdf_safe(f"Date: {date_str}"), ln=1)

        y = y + 16
        box_h = 50
        double_rect(LEFT, y, W, box_h)
        vline_trim(LEFT + HALF, y, box_h)

        # TO block
        pdf.set_font("Arial", "B", 11)
        pdf.set_xy(LEFT + 2, y + 3)
        pdf.cell(0, 5, pdf_safe("TO (Referral amount payable to)"), ln=1)
        pdf.set_font("Arial", "", 11)
        pdf.set_x(LEFT + 2)
        pdf.cell(0, 7, pdf_safe(f"Name: {to_name}"), ln=1)
        pdf.set_x(LEFT + 2)
        pdf.cell(0, 7, pdf_safe(f"Flat: {to_flat}"), ln=1)
        pdf.set_x(LEFT + 2)
        pdf.cell(0, 7, pdf_safe(f"Booking Date: {to_booking_date}"), ln=1)
        pdf.set_x(LEFT + 2)
        pdf.cell(0, 7, pdf_safe(f"PAN: {to_pan}"), ln=1)

        # FOR block
        rx = LEFT + HALF + 2
        pdf.set_font("Arial", "B", 11)
        pdf.set_xy(rx, y + 3)
        pdf.cell(0, 5, pdf_safe("FOR (Referred booking)"), ln=1)
        pdf.set_font("Arial", "", 11)
        pdf.set_x(rx)
        pdf.cell(0, 7, pdf_safe(f"Name: {for_name}"), ln=1)
        pdf.set_x(rx)
        pdf.cell(0, 7, pdf_safe(f"Flat: {for_flat}"), ln=1)
        pdf.set_x(rx)
        pdf.cell(0, 7, pdf_safe(f"Booking Date: {for_booking_date}"), ln=1)
        pdf.set_x(rx)
        pdf.cell(0, 7, pdf_safe(f"Unit Type: {for_unit_type}"), ln=1)

        # Particulars table
        y = y + box_h + 7
        col1 = 135
        col2 = W - col1
        header_h = 11
        pad = 2
        line_h = 6.5

        rows = [
            (
                f"Referral incentive (Gross) for booking of {for_name} (Flat {for_flat}) - {for_unit_type}.",
                f"{gross_amount:,.0f}",
                False,
                "R",
                16
            ),
            ("TDS 2%", f"- {tds_amount:,.0f}", False, "R", 16),
            ("Total Amount Payable", f"{net_amount:,.0f}", True, "R", 16),
            ("Amount in words", amount_words, False, "L", 18),
        ]

        def wrap_lines(text, max_w):
            text = pdf_safe(text).strip()

            if not text:
                return [""]

            words = text.split()
            lines = []
            cur = ""

            for w in words:
                test = (cur + " " + w).strip()

                if pdf.get_string_width(test) <= max_w:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w

            if cur:
                lines.append(cur)

            return lines

        pdf.set_font("Arial", "", 11)
        row_heights = []

        for lt, rt, bold, align, min_h in rows:
            ll = wrap_lines(lt, col1 - 2 * pad)
            rl = wrap_lines(rt, col2 - 2 * pad)
            n = max(len(ll), len(rl))
            row_h = max(min_h, n * line_h + 2 * pad)
            row_heights.append(row_h)

        total_h = header_h + sum(row_heights)

        pdf.set_line_width(0.7)
        pdf.rect(LEFT, y, W, total_h)
        pdf.set_line_width(0.25)

        pdf.set_fill_color(235, 242, 255)
        pdf.rect(LEFT, y, W, header_h, "F")
        pdf.line(LEFT + col1, y, LEFT + col1, y + total_h)
        pdf.line(LEFT, y + header_h, LEFT + W, y + header_h)

        pdf.set_font("Arial", "B", 12)
        pdf.set_xy(LEFT + 2, y + 3)
        pdf.cell(col1 - 4, 5, pdf_safe("Particulars"), 0, 0, "L")
        pdf.set_xy(LEFT + col1 + 2, y + 3)
        pdf.cell(col2 - 4, 5, pdf_safe("Amount (Rs.)"), 0, 0, "R")

        y_cur = y + header_h

        for i, rh in enumerate(row_heights):
            y_next = y_cur + rh

            if i < len(row_heights) - 1:
                pdf.line(LEFT, y_next, LEFT + W, y_next)

            y_cur = y_next

        y_cur = y + header_h

        for (lt, rt, bold, align, min_h), rh in zip(rows, row_heights):
            pdf.set_font("Arial", "B" if bold else "", 11)
            ll = wrap_lines(lt, col1 - 2 * pad)
            rl = wrap_lines(rt, col2 - 2 * pad)
            n = max(len(ll), len(rl))
            text_y = y_cur + pad

            for i in range(n):
                if i < len(ll):
                    pdf.set_xy(LEFT + pad, text_y + i * line_h)
                    pdf.cell(col1 - 2 * pad, line_h, ll[i], 0, 0, "L")

                if i < len(rl):
                    pdf.set_xy(LEFT + col1 + pad, text_y + i * line_h)
                    pdf.cell(col2 - 2 * pad, line_h, rl[i], 0, 0, align)

            y_cur += rh

        end_y = y + total_h

        # Footer layout
        note_h = 12
        sig_h = 64
        ack_h = 18
        field_h = 24
        gap = 4

        min_note_h = 10
        min_sig_h = 46
        min_ack_h = 14
        min_field_h = 20
        min_gap = 1

        min_top = end_y + 6

        def compute_positions(gap_, sig_h_, ack_h_, field_h_, note_h_):
            note_y_ = FOOTER_BOTTOM - note_h_
            sig_y_ = note_y_ - gap_ - sig_h_
            ack_y_ = sig_y_ - gap_ - ack_h_
            fld_y_ = ack_y_ - gap_ - field_h_
            return note_y_, sig_y_, ack_y_, fld_y_

        while True:
            note_y, sig_y, ack_y, field_y = compute_positions(gap, sig_h, ack_h, field_h, note_h)

            if field_y >= min_top:
                break

            if gap > min_gap:
                gap -= 1
            elif sig_h > min_sig_h:
                sig_h -= 2
            elif ack_h > min_ack_h:
                ack_h -= 2
            elif field_h > min_field_h:
                field_h -= 2
            elif note_h > min_note_h:
                note_h -= 1
            else:
                break

        # Cheque details
        y = field_y
        double_rect(LEFT, y, W, field_h)
        vline_trim(LEFT + THIRD, y, field_h)
        vline_trim(LEFT + 2 * THIRD, y, field_h)

        pdf.set_font("Arial", "B", 11)
        headings = ["Cheque No.", "Date of Cheque", "Bank Name"]

        for i, htxt in enumerate(headings):
            x0 = LEFT + i * THIRD
            pdf.set_xy(x0, y + 3)
            pdf.cell(THIRD, 6, pdf_safe(htxt), border=0, align="C")
            pdf.line(x0 + 10, y + 18, x0 + THIRD - 10, y + 18)

        # Acknowledgment
        y = ack_y
        double_rect(LEFT, y, W, ack_h)
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(LEFT + 2, y + 4)
        pdf.multi_cell(
            W - 4,
            5,
            pdf_safe("Acknowledgment: By signing below, the recipient acknowledges the receipt/entitlement of the above referral incentive amount."),
            border=0
        )

        # Signatures
        y = sig_y
        double_rect(LEFT, y, W, sig_h)
        vline_trim(LEFT + HALF, y, sig_h)

        # Customer signature
        pdf.set_xy(LEFT + 2, y + 4)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, pdf_safe("Customer Signature (To)"), ln=1)
        pdf.set_font("Arial", "", 10)
        pdf.set_x(LEFT + 2)
        pdf.cell(0, 6, pdf_safe(f"Name: {to_name}"), ln=1)
        pdf.set_x(LEFT + 2)
        pdf.cell(0, 6, pdf_safe(f"Date: {date_str}"), ln=1)
        pdf.set_x(LEFT + 2)
        pdf.multi_cell(HALF - 6, 5, pdf_safe(f"Place: {place_str}"), border=0)
        pdf.line(LEFT + 2, y + sig_h - 10, LEFT + HALF - 5, y + sig_h - 10)
        pdf.set_xy(LEFT + 2, y + sig_h - 9)
        pdf.cell(0, 5, pdf_safe("Signature"), ln=1)

        # Sales executive signature
        pdf.set_xy(LEFT + HALF + 2, y + 4)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, pdf_safe("Sales Executive Signature"), ln=1)
        pdf.set_font("Arial", "", 10)
        pdf.set_x(LEFT + HALF + 2)
        pdf.cell(0, 6, pdf_safe(f"Name: {sales_exec}"), ln=1)
        pdf.set_x(LEFT + HALF + 2)
        pdf.cell(0, 6, pdf_safe(f"Date: {date_str}"), ln=1)
        pdf.set_x(LEFT + HALF + 2)
        pdf.multi_cell(HALF - 6, 5, pdf_safe(f"Place: {place_str}"), border=0)
        pdf.line(LEFT + HALF + 2, y + sig_h - 10, LEFT + W - 2, y + sig_h - 10)
        pdf.set_xy(LEFT + HALF + 2, y + sig_h - 9)
        pdf.cell(0, 5, pdf_safe("Signature"), ln=1)

        # Note
        y = note_y
        double_rect(LEFT, y, W, note_h)
        pdf.set_font("Arial", "I", 9)
        pdf.set_xy(LEFT + 2, y + 3)
        pdf.multi_cell(
            W - 4,
            4,
            pdf_safe("Note: TDS @ 2% is applicable as per prevailing Income Tax rules. Net payable amount is after TDS deduction."),
            border=0
        )

        out = pdf.output(dest="S")
        pdf_bytes = bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin1", "ignore")
        b64 = base64.b64encode(pdf_bytes).decode()

        safe_to_name = _safe_filename(to_name)
        filename = f"Referral Voucher - {safe_to_name}.pdf" if safe_to_name else "Referral Voucher.pdf"

        st.markdown(
            f'<a class="rg-download" href="data:application/octet-stream;base64,{b64}" download="{filename}">⬇️ Download Referral Voucher (A4 PDF)</a>',
            unsafe_allow_html=True
        )

    render_referral_invoice_tab()
# =========================================================
# SUBTAB 3: AGREEMENT SCHEDULE
# =========================================================
with agreement_schedule_tab:
    st.subheader("🧾 Agreement Schedule (Based on Agreement Cost)")

    if "tab4_agree_form_generated" not in st.session_state:
        st.session_state.tab4_agree_form_generated = False
    if "tab4_agree_cost" not in st.session_state:
        st.session_state.tab4_agree_cost = 0
    if "tab4_agree_gst_choice" not in st.session_state:
        st.session_state.tab4_agree_gst_choice = "1%"
    if "tab4_agree_received" not in st.session_state:
        st.session_state.tab4_agree_received = 0

    with st.form("tab4_agreement_schedule_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.number_input("Agreement Cost (₹)", min_value=0, step=1000, key="tab4_agree_cost")

        with c2:
            st.selectbox("GST Slab", options=["1%", "5%"], key="tab4_agree_gst_choice")

        with c3:
            st.number_input("Received Amount (₹)", min_value=0, step=1000, key="tab4_agree_received")

        gen = st.form_submit_button("Generate Agreement Schedule")

    if gen:
        st.session_state.tab4_agree_form_generated = True

    if not st.session_state.tab4_agree_form_generated:
        st.info("Enter inputs and click **Generate Agreement Schedule**.")
    else:
        agreement_cost = float(st.session_state.tab4_agree_cost or 0)
        received_amt = float(st.session_state.tab4_agree_received or 0)

        gst_choice = st.session_state.tab4_agree_gst_choice
        gst_rate = 0.01 if gst_choice == "1%" else 0.05
        unit_type = "1 BHK" if gst_rate == 0.01 else "2 BHK"

        if agreement_cost <= 0:
            st.warning("Agreement Cost must be greater than 0.")
        else:
            schedule_1bhk = [
                ("ADVANCE PAYMENT TOWARDS FLAT BOOKING", 5),
                ("AFTER EXECUTION OF AGREEMENT WITHIN 30 DAYS", 10),
                ("ON COMPLETION OF THE PLINTH / 1ST FLOOR SLAB", 15),
                ("ON COMPLETION  OF THE THIRD FLOOR", 7.5),
                ("ON COMPLETION OF THE SEVENTH FLOOR", 7.5),
                ("ON COMPLETION OF THE TENTH FLOOR", 7.5),
                ("ON COMPLETION OF THE THIRTEEN FLOOR", 7.5),
                ("ON COMPLETION OF FLOORING WORK OF PARTICULAR FLAT / FLOOR.", 7.5),
                ("ON COMPLETION OF EXTERNAL PLASTERING / PRIMER OF BUILDING.", 7.5),
                ("ON COMMENCEMENT OF INTERNAL PLUMBING OF PARTICULAR FLAT.", 7.5),
                ("ON COMMENCEMENT ELECTRICAL WIRING / WINDOW/ DOOR OF PARTICULAR FLAT.", 7.5),
                ("ON COMMENCEMENT OF SANITARY OF PARTICULAR FLAT & LIFTS OF BUILDING & EXTERNAL PAINT.", 5),
                ("At the time of handover of POSSESSION OR on receipt of OCCUPATION / COMPLETION CERTIFICATE...", 5),
            ]

            schedule_2bhk = [
                ("ADVANCE PAYMENT TOWARDS FLAT BOOKING", 5),
                ("AFTER EXECUTION OF AGREEMENT WITHIN 30 DAYS", 9),
                ("TDS", 1),
                ("ON COMPLETION OF THE PLINTH / 1ST FLOOR SLAB", 15),
                ("ON COMPLETION  OF THE THIRD FLOOR", 7.5),
                ("ON COMPLETION OF THE SEVENTH FLOOR", 7.5),
                ("ON COMPLETION OF THE TENTH FLOOR", 7.5),
                ("ON COMPLETION OF THE THIRTEEN FLOOR", 7.5),
                ("ON COMPLETION OF FLOORING WORK OF PARTICULAR FLAT / FLOOR.", 7.5),
                ("ON COMPLETION OF EXTERNAL PLASTERING / PRIMER OF BUILDING.", 7.5),
                ("ON COMMENCEMENT OF INTERNAL PLUMBING OF PARTICULAR FLAT.", 7.5),
                ("ON COMMENCEMENT ELECTRICAL WIRING / WINDOW/ DOOR OF PARTICULAR FLAT.", 7.5),
                ("ON COMMENCEMENT OF SANITARY OF PARTICULAR FLAT & LIFTS OF BUILDING & EXTERNAL PAINT.", 5),
                ("At the time of handover of POSSESSION OR on receipt of OCCUPATION / COMPLETION CERTIFICATE...", 5),
            ]

            schedule_data = schedule_2bhk if unit_type == "2 BHK" else schedule_1bhk

            rows = []

            for desc, perc in schedule_data:
                req_base = int(round(agreement_cost * (perc / 100.0)))
                req_gst = int(round(req_base * gst_rate))
                req_total = req_base + req_gst

                rows.append({
                    "Description": desc,
                    "%": perc,
                    "Req_Amount": req_base,
                    "Req_GST": req_gst,
                    "Req_Total": req_total,
                })

            sched_df = pd.DataFrame(rows)

            def split_gross_into_base_gst(gross: float, rate: float) -> tuple[int, int]:
                if gross <= 0:
                    return (0, 0)

                gst_part = gross * (rate / (1.0 + rate))
                gst_i = int(round(gst_part))
                base_i = int(round(gross - gst_i))
                gross_i = int(round(gross))
                drift = gross_i - (base_i + gst_i)
                base_i += drift

                return base_i, gst_i

            received_remaining = float(received_amt)

            bal_base_list = []
            bal_gst_list = []
            bal_total_list = []
            paid_base_list = []
            paid_gst_list = []
            paid_total_list = []
            status_list = []

            for _, r in sched_df.iterrows():
                desc = str(r["Description"] or "").strip()
                req_base = float(r["Req_Amount"])
                req_gst = float(r["Req_GST"])
                req_total = float(r["Req_Total"])
                is_tds = desc.upper() == "TDS"

                if is_tds:
                    paid_base = 0.0
                    paid_gst = 0.0
                    paid_total = 0.0
                    bal_base = req_base
                    bal_gst = req_gst
                    bal_total = req_total
                else:
                    slab_paid_gross = min(received_remaining, req_total)
                    slab_paid_base, slab_paid_gst = split_gross_into_base_gst(slab_paid_gross, gst_rate)

                    paid_gst = min(req_gst, float(slab_paid_gst))
                    paid_base = min(req_base, float(slab_paid_base))

                    used = paid_base + paid_gst
                    target = float(int(round(slab_paid_gross)))
                    diff = target - used

                    if diff != 0:
                        if diff > 0:
                            add_base = min(req_base - paid_base, diff)
                            paid_base += add_base
                            diff -= add_base

                            add_gst = min(req_gst - paid_gst, diff)
                            paid_gst += add_gst
                        else:
                            take_base = min(paid_base, -diff)
                            paid_base -= take_base
                            diff += take_base

                            take_gst = min(paid_gst, -diff)
                            paid_gst -= take_gst

                    paid_total = paid_base + paid_gst
                    received_remaining = max(0.0, received_remaining - paid_total)

                    bal_base = max(0.0, req_base - paid_base)
                    bal_gst = max(0.0, req_gst - paid_gst)
                    bal_total = bal_base + bal_gst

                paid_base_list.append(int(round(paid_base)))
                paid_gst_list.append(int(round(paid_gst)))
                paid_total_list.append(int(round(paid_total)))

                bal_base_list.append(int(round(bal_base)))
                bal_gst_list.append(int(round(bal_gst)))
                bal_total_list.append(int(round(bal_total)))

                status_list.append("NIL" if bal_total <= 0 else "Pending")

            sched_df["Bal_Amount"] = bal_base_list
            sched_df["Bal_GST"] = bal_gst_list
            sched_df["Bal_Total"] = bal_total_list
            sched_df["Paid_Amount"] = paid_base_list
            sched_df["Paid_GST"] = paid_gst_list
            sched_df["Paid_Total"] = paid_total_list
            sched_df["Status"] = status_list

            st.markdown('<div class="rg-wrap">', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="rg-card ok">
              <div class="rg-label">Agreement Cost</div>
              <div class="rg-value">₹ {agreement_cost:,.0f}
                <span class="rg-kicker">• GST: {gst_choice} • Type: {unit_type}</span>
              </div>
            </div>
            <div class="rg-card">
              <div class="rg-label">Received Amount</div>
              <div class="rg-value">₹ {received_amt:,.0f}</div>
            </div>
            <div class="rg-card info">
              <div class="rg-label">Unallocated Received (if any)</div>
              <div class="rg-value">₹ {received_remaining:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            view_df = sched_df[["Description", "%", "Bal_Amount", "Status"]].copy()
            view_df.rename(columns={"Bal_Amount": "Amount"}, inplace=True)

            totals_row = {
                "Description": "Total",
                "%": "",
                "Amount": int(view_df["Amount"].sum()),
                "Status": ""
            }

            view_df = pd.concat([view_df, pd.DataFrame([totals_row])], ignore_index=True)

            def rupee(x):
                try:
                    return f"₹ {int(x):,}"
                except Exception:
                    return "—"

            def status_badge(s):
                if s == "NIL":
                    return "<span class='pill-ok'>NIL</span>"
                if s == "Pending":
                    return "<span class='pill-pend'>Pending</span>"
                return ""

            html = '<table class="schedule-table">'
            html += "<tr>" + "".join([
                "<th>#</th>",
                "<th>Description</th>",
                "<th class='mono'>%</th>",
                "<th class='mono'>Amount</th>",
                "<th>Status</th>",
            ]) + "</tr>"

            for i, row in view_df.iterrows():
                is_total = str(row["Description"]) == "Total"
                num = "" if is_total else str(i + 1)

                html += "<tr>"
                html += f"<td>{num}</td>"
                html += f"<td>{row['Description']}</td>"
                html += f"<td class='mono'>{'' if is_total else row['%']}</td>"
                html += f"<td class='mono'>{rupee(row['Amount'])}</td>"
                html += f"<td>{status_badge(str(row.get('Status', '')))}</td>"
                html += "</tr>"

            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)
