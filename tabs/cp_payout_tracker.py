# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.

import datetime
import time
import pandas as pd

CP_PAYOUT_TABLE = "cp_payout_tracker"

# ----------------- THEME -----------------
st.markdown("""
<style>
  :root{ --ink:#0f172a; --muted:#475569; --border:#e2e8f0; --soft:#f8fafc; --card:#ffffff; }
  .pane{border:1px solid var(--border); background:var(--card); border-radius:16px; padding:16px; margin:14px 0;
        box-shadow:0 8px 18px rgba(15,23,42,.06);}
  .title{font-weight:900; font-size:20px; color:var(--ink); margin-bottom:6px;}
  .sub{color:var(--muted); font-size:13px; margin-top:-4px; margin-bottom:12px;}

  .kpi{border:1px solid var(--border); background:var(--card); border-radius:14px; padding:12px 14px;
       box-shadow:0 6px 14px rgba(15,23,42,.06); height:100%;}
  .kpi h6{margin:0; font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em}
  .kpi p{margin:6px 0 0; font-size:22px; font-weight:900; color:var(--ink)}
  .kpi-row3{display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-bottom:12px;}
  .kpi-row2{display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px; margin-bottom:12px;}
  @media(max-width: 900px){ .kpi-row3{grid-template-columns:repeat(2, minmax(0,1fr));}
                           .kpi-row2{grid-template-columns:1fr;} }
  @media(max-width: 560px){ .kpi-row3{grid-template-columns:1fr;} }

  .rowhdr{font-weight:800; color:#0f172a; padding:6px 8px; background:#eef2ff;
          border:1px solid var(--border); border-radius:10px;}

  .stButton > button[kind="primary"]{
    background: linear-gradient(135deg,#6366f1 0%, #06b6d4 100%) !important;
    color:#ffffff !important; border: none !important; border-radius: 10px !important;
    padding: 10px 16px !important; font-weight: 800 !important;
    box-shadow: 0 6px 14px rgba(99,102,241,.35) !important;
  }
  .stButton > button[kind="primary"]:hover{ filter: brightness(1.05); }
  .stButton > button[kind="primary"]:disabled{
    background:#e5e7eb !important; color:#94a3b8 !important; box-shadow:none !important;
  }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="title">🧾 CP Payout Expenditure</div>'
    '<div class="sub">Add invoice-level payouts and track FOS vs Brokerage releases independently.</div>',
    unsafe_allow_html=True
)

# ============================================================
# SUPABASE GUARD
# ============================================================
if not supabase_connected:
    st.warning("📋 Please connect to Supabase to use CP Payout Expenditure.")
else:
    # ----------------- LOCAL HELPERS -----------------
    def _t6_clear_cache():
        st.session_state["t6_cache_bump"] = st.session_state.get("t6_cache_bump", 0) + 1
        try:
            _t6_read_cp_df.clear()
            _t6_read_bookings_df.clear()
        except Exception:
            try:
                st.cache_data.clear()
            except Exception:
                pass

    @st.cache_data(ttl=300, show_spinner=False)
    def _t6_read_cp_df(bump: int = 0) -> pd.DataFrame:
        delay = 0.5

        for _ in range(5):
            try:
                res = (
                    supabase
                    .table(CP_PAYOUT_TABLE)
                    .select("*")
                    .order("created_at", desc=False)
                    .execute()
                )

                data = res.data or []
                return pd.DataFrame(data)

            except Exception:
                time.sleep(delay)
                delay *= 2

        return pd.DataFrame()

    @st.cache_data(ttl=300, show_spinner=False)
    def _t6_read_bookings_df(bump: int = 0) -> pd.DataFrame:
        # Prefer your already-loaded Supabase booking dataframe
        if "booking_df" in globals() and isinstance(booking_df, pd.DataFrame):
            return booking_df.copy()

        if "sheet_df" in globals() and isinstance(sheet_df, pd.DataFrame):
            return sheet_df.copy()

        # Optional fallback: try Supabase bookings table
        try:
            res = (
                supabase
                .table("bookings")
                .select("*")
                .execute()
            )
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()

    def _iso_date(d):
        if isinstance(d, datetime.date):
            return d.isoformat()
        return None

    def _iso_ts_now():
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _display_date(v):
        if v is None:
            return ""
        s = str(v).strip()
        if not s or s.lower() in ("none", "nan", "nat"):
            return ""
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
        if pd.isna(dt):
            return s
        return dt.strftime("%d/%m/%Y")

    def _parse_any_date(val):
        if val is None:
            return pd.NaT
        s = str(val).strip()
        if not s or s.lower() in ("none", "nan", "nat"):
            return pd.NaT

        # Supabase date normally comes as YYYY-MM-DD
        dt = pd.to_datetime(s, errors="coerce", dayfirst=False)
        if pd.isna(dt):
            dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
        return dt

    def _avg_release_days(df_in, invoice_col, cheque_col):
        if df_in.empty or invoice_col not in df_in.columns or cheque_col not in df_in.columns:
            return None

        temp = df_in.copy()
        temp[invoice_col] = temp[invoice_col].apply(_parse_any_date)
        temp[cheque_col] = temp[cheque_col].apply(_parse_any_date)

        temp = temp.dropna(subset=[invoice_col, cheque_col]).copy()
        if temp.empty:
            return None

        day_diff = (temp[cheque_col] - temp[invoice_col]).dt.days
        day_diff = day_diff[day_diff >= 0]

        if day_diff.empty:
            return None

        return round(day_diff.mean(), 1)

    def _t6_truthy(series):
        return (
            series
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .isin(["TRUE", "YES", "1", "GIVEN", "DONE"])
        )

    def _num(s):
        try:
            return pd.to_numeric(s, errors="coerce").fillna(0.0)
        except Exception:
            return pd.Series(dtype=float)

    def fmt_money(v):
        try:
            return f"₹ {float(v):,.0f}"
        except Exception:
            return "₹ 0"

    def _find_col(df_in: pd.DataFrame, candidates: list[str]):
        if df_in.empty:
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

    def _t6_insert_row(row_dict: dict) -> bool:
        try:
            supabase.table(CP_PAYOUT_TABLE).insert(row_dict).execute()
            _t6_clear_cache()
            return True
        except Exception as e:
            st.error(f"❌ Supabase insert failed: {e}")
            return False

    def _t6_mark_given(kind: str, wing: str, flat_no: str, given_dt: datetime.date, cheque_no: str, cheque_dt: datetime.date):
        try:
            # First find matching rows so we can tell if anything exists
            match_res = (
                supabase
                .table(CP_PAYOUT_TABLE)
                .select("id")
                .eq("wing", str(wing).strip())
                .eq("flat_number", str(flat_no).strip())
                .execute()
            )

            ids = [r.get("id") for r in (match_res.data or []) if r.get("id") is not None]

            if not ids:
                return False, "No matching rows."

            if kind == "FOS":
                update_payload = {
                    "fos_given": "TRUE",
                    "fos_given_date": _iso_date(given_dt),
                    "fos_cheque_no": str(cheque_no).strip(),
                    "fos_cheque_date": _iso_date(cheque_dt),
                }
            else:
                update_payload = {
                    "brokerage_given": "TRUE",
                    "brokerage_given_date": _iso_date(given_dt),
                    "brokerage_cheque_no": str(cheque_no).strip(),
                    "brokerage_cheque_date": _iso_date(cheque_dt),
                }

            (
                supabase
                .table(CP_PAYOUT_TABLE)
                .update(update_payload)
                .in_("id", ids)
                .execute()
            )

            _t6_clear_cache()
            return True, None

        except Exception as e:
            return False, str(e)

    # ----------------- LOAD -----------------
    bump = st.session_state.get("t6_cache_bump", 0)
    cp_payout_df = _t6_read_cp_df(bump=bump)
    bookings_df = _t6_read_bookings_df(bump=bump)

    # Ensure expected columns exist locally
    cp_cols = [
        "id",
        "created_at",
        "invoice_date",
        "invoice_number",
        "firm_cp_name",
        "wing",
        "flat_number",
        "flat",
        "fos_amount",
        "brokerage_amount",
        "recorded_at",
        "cp_name_fos",
        "firm_name_brokerage",
        "fos_given",
        "fos_given_date",
        "fos_cheque_no",
        "fos_cheque_date",
        "brokerage_given",
        "brokerage_given_date",
        "brokerage_cheque_no",
        "brokerage_cheque_date",
    ]

    for c in cp_cols:
        if c not in cp_payout_df.columns:
            cp_payout_df[c] = ""

    # ----------------- KPIs -----------------
    fos_amt = _num(cp_payout_df["fos_amount"]) if not cp_payout_df.empty else pd.Series(dtype=float)
    bro_amt = _num(cp_payout_df["brokerage_amount"]) if not cp_payout_df.empty else pd.Series(dtype=float)

    fos_mask = (fos_amt > 0) if len(fos_amt) else pd.Series(dtype=bool)
    bro_mask = (bro_amt > 0) if len(bro_amt) else pd.Series(dtype=bool)

    fos_given_bool = (
        _t6_truthy(cp_payout_df["fos_given"])
        if not cp_payout_df.empty
        else pd.Series(False, index=[])
    )

    bro_given_bool = (
        _t6_truthy(cp_payout_df["brokerage_given"])
        if not cp_payout_df.empty
        else pd.Series(False, index=[])
    )

    fos_count = int(fos_mask.sum()) if len(fos_mask) else 0
    bro_count = int(bro_mask.sum()) if len(bro_mask) else 0

    fos_given_count = int((fos_mask & fos_given_bool).sum()) if not cp_payout_df.empty else 0
    fos_pending_count = int((fos_mask & ~fos_given_bool).sum()) if not cp_payout_df.empty else 0

    bro_given_count = int((bro_mask & bro_given_bool).sum()) if not cp_payout_df.empty else 0
    bro_pending_count = int((bro_mask & ~bro_given_bool).sum()) if not cp_payout_df.empty else 0

    if not cp_payout_df.empty:
        status_df = (
            cp_payout_df
            .assign(**{
                "fos_given_bool": fos_given_bool.astype(bool),
                "brokerage_given_bool": bro_given_bool.astype(bool),
            })
            .groupby(["wing", "flat_number"], as_index=False)
            .agg({
                "fos_given_bool": "max",
                "brokerage_given_bool": "max",
            })
        )

        fos_given_flat_count = int(status_df["fos_given_bool"].sum())
        bro_given_flat_count = int(status_df["brokerage_given_bool"].sum())
    else:
        status_df = pd.DataFrame(columns=["wing", "flat_number", "fos_given_bool", "brokerage_given_bool"])
        fos_given_flat_count = 0
        bro_given_flat_count = 0

    cp_bookings_count = 0

    if isinstance(bookings_df, pd.DataFrame) and not bookings_df.empty:
        lead_col = _find_col(bookings_df, ["lead_type", "Lead Type", "leadtype"])

        if lead_col:
            cp_bookings_count = int(
                bookings_df[lead_col]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
                .eq("CP")
                .sum()
            )

    total_fos_pending_from_cp = max(cp_bookings_count - fos_given_flat_count, 0)
    total_bro_pending_from_cp = max(cp_bookings_count - bro_given_flat_count, 0)

    fos_amount_till_date = fos_amt.sum() if len(fos_amt) else 0
    bro_amount_till_date = bro_amt.sum() if len(bro_amt) else 0

    avg_fos_release_days = _avg_release_days(
        cp_payout_df,
        "invoice_date",
        "fos_cheque_date"
    )

    avg_bro_release_days = _avg_release_days(
        cp_payout_df,
        "invoice_date",
        "brokerage_cheque_date"
    )

    st.markdown('<div class="pane">', unsafe_allow_html=True)
    st.subheader("📌 Summary (Till Date)")
    st.markdown(f"""
      <div class="kpi-row3">
        <div class="kpi"><h6>FOS — Total Count</h6><p>{fos_count}</p></div>
        <div class="kpi"><h6>FOS — Given</h6><p>{fos_given_count}</p></div>
        <div class="kpi"><h6>FOS — Pending</h6><p>{fos_pending_count}</p></div>
      </div>
      <div class="kpi-row3">
        <div class="kpi"><h6>Brokerage — Total Count</h6><p>{bro_count}</p></div>
        <div class="kpi"><h6>Brokerage — Given</h6><p>{bro_given_count}</p></div>
        <div class="kpi"><h6>Brokerage — Pending</h6><p>{bro_pending_count}</p></div>
      </div>
      <div class="kpi-row3">
        <div class="kpi"><h6>Total CP Bookings</h6><p>{cp_bookings_count:,}</p></div>
        <div class="kpi"><h6>Total FOS Given (Count)</h6><p>{fos_given_flat_count}</p></div>
        <div class="kpi"><h6>Total FOS Pending (Count)</h6><p>{total_fos_pending_from_cp}</p></div>
      </div>
      <div class="kpi-row3">
        <div class="kpi"><h6>Total CP Bookings</h6><p>{cp_bookings_count:,}</p></div>
        <div class="kpi"><h6>Total Brokerage Given (Count)</h6><p>{bro_given_flat_count}</p></div>
        <div class="kpi"><h6>Total Brokerage Pending (Count)</h6><p>{total_bro_pending_from_cp}</p></div>
      </div>
      <div class="kpi-row2">
        <div class="kpi"><h6>FOS Amount Till Date</h6><p>{fmt_money(fos_amount_till_date)}</p></div>
        <div class="kpi"><h6>Brokerage Amount Till Date</h6><p>{fmt_money(bro_amount_till_date)}</p></div>
      </div>
      <div class="kpi-row2">
        <div class="kpi"><h6>Average Days to Release FOS Payment</h6><p>{avg_fos_release_days if avg_fos_release_days is not None else "—"}</p></div>
        <div class="kpi"><h6>Average Days to Release Brokerage Payment</h6><p>{avg_bro_release_days if avg_bro_release_days is not None else "—"}</p></div>
      </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------- VERTICAL FORM -----------------
    st.markdown('<div class="pane">', unsafe_allow_html=True)
    st.subheader("➕ Add CP Payout")

    wings = ["E", "F"]

    if isinstance(bookings_df, pd.DataFrame) and not bookings_df.empty:
        wing_col = _find_col(bookings_df, ["wing", "Wing"])

        if wing_col:
            try:
                wings = sorted([
                    str(w).strip()
                    for w in bookings_df[wing_col].dropna().unique().tolist()
                    if str(w).strip()
                ]) or wings
            except Exception:
                pass

    with st.form("t6_form_add", clear_on_submit=False):
        date_inv = st.date_input("Date of Invoice", format="DD/MM/YYYY", key="t6_date")
        invoice = st.text_input("Invoice Number", key="t6_invoice")
        cp_name = st.text_input("Channel Partner Name (for FOS)", key="t6_cpname")
        firm_name = st.text_input("Firm Name (for Brokerage)", key="t6_firmname")
        wing = st.selectbox("Wing", wings, key="t6_wing")
        flat_no = st.text_input("Flat Number", placeholder="e.g., 699", key="t6_flat")
        fos_amt_v = st.number_input("FOS (₹)", min_value=0.0, step=100.0, format="%.2f", key="t6_fos_amt")
        bro_amt_v = st.number_input("Brokerage (₹)", min_value=0.0, step=100.0, format="%.2f", key="t6_bro_amt")
        add_btn = st.form_submit_button("Add CP Payout")

    if add_btn:
        if invoice and wing and flat_no and (fos_amt_v > 0 or bro_amt_v > 0):
            flat_label = f"{wing} {str(flat_no).strip()}"

            row = {
                "invoice_date": _iso_date(date_inv),
                "invoice_number": invoice.strip(),
                "firm_cp_name": f"CP: {cp_name or '-'} | Firm: {firm_name or '-'}",
                "wing": str(wing).strip(),
                "flat_number": str(flat_no).strip(),
                "flat": flat_label,
                "fos_amount": float(fos_amt_v) if fos_amt_v else 0,
                "brokerage_amount": float(bro_amt_v) if bro_amt_v else 0,
                "recorded_at": _iso_ts_now(),
                "cp_name_fos": cp_name or "",
                "firm_name_brokerage": firm_name or "",
                "fos_given": "",
                "fos_given_date": None,
                "fos_cheque_no": "",
                "fos_cheque_date": None,
                "brokerage_given": "",
                "brokerage_given_date": None,
                "brokerage_cheque_no": "",
                "brokerage_cheque_date": None,
            }

            if _t6_insert_row(row):
                st.success("✅ Entry added.")
                st.rerun()
        else:
            st.error("Fill required fields. At least one of FOS/Brokerage must be > 0.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------- TRACKER -----------------
    st.subheader("📋 Tracker")

    if cp_payout_df.empty:
        st.info("No CP payout records yet. Add entries above to populate the tracker.")
    else:
        tracker_df = cp_payout_df.copy()

        tracker_df["wing"] = tracker_df["wing"].fillna("").astype(str).str.strip()
        tracker_df["flat_number"] = tracker_df["flat_number"].fillna("").astype(str).str.strip()
        tracker_df["flat"] = tracker_df["flat"].fillna("").astype(str).str.strip()

        tracker_df["fos_given_bool"] = (
            tracker_df["fos_given"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .isin(["TRUE", "YES", "1", "GIVEN", "DONE"])
        )

        tracker_df["brokerage_given_bool"] = (
            tracker_df["brokerage_given"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .isin(["TRUE", "YES", "1", "GIVEN", "DONE"])
        )

        base = (
            tracker_df
            .groupby(["wing", "flat_number"], as_index=False)
            .agg({
                "flat": lambda s: next((x for x in s if str(x).strip()), ""),
                "fos_given_bool": "max",
                "brokerage_given_bool": "max",
            })
            .rename(columns={
                "fos_given_bool": "FOS Given",
                "brokerage_given_bool": "Brokerage Given",
            })
            .sort_values(by=["wing", "flat_number"])
            .reset_index(drop=True)
        )

        base["flat"] = base.apply(
            lambda r: str(r["flat"]).strip()
            if str(r["flat"]).strip()
            else f"{str(r['wing']).strip()} {str(r['flat_number']).strip()}",
            axis=1
        )

        pending_base = base[(~base["FOS Given"]) | (~base["Brokerage Given"])].reset_index(drop=True)

        if pending_base.empty:
            st.success("✅ All FOS and Brokerage entries are already marked as Given.")
        else:
            h1, h2, h3 = st.columns([2, 1, 1])

            with h1:
                st.markdown('<div class="rowhdr">Flat Number</div>', unsafe_allow_html=True)

            with h2:
                st.markdown('<div class="rowhdr">FOS — Given</div>', unsafe_allow_html=True)

            with h3:
                st.markdown('<div class="rowhdr">Brokerage — Given</div>', unsafe_allow_html=True)

            for i, r in pending_base.iterrows():
                flat_label = r["flat"]
                w = str(r["wing"]).strip()
                f = str(r["flat_number"]).strip()
                fos_default = bool(r["FOS Given"])
                bro_default = bool(r["Brokerage Given"])

                c1, c2, c3 = st.columns([2, 1, 1])

                with c1:
                    st.write(flat_label)

                with c2:
                    fos_ck = st.checkbox("Given", value=fos_default, key=f"t6_fos_{i}")

                with c3:
                    bro_ck = st.checkbox("Given", value=bro_default, key=f"t6_bro_{i}")

                if fos_ck and not fos_default:
                    st.session_state["t6_dialog_ctx"] = {
                        "type": "FOS",
                        "wing": w,
                        "flat": f,
                        "label": flat_label
                    }

                if bro_ck and not bro_default:
                    st.session_state["t6_dialog_ctx"] = {
                        "type": "Brokerage",
                        "wing": w,
                        "flat": f,
                        "label": flat_label
                    }

    # ----------------- Cheque popup -----------------
    def _t6_save(kind, wing, flat_no, chq_no, chq_dt):
        today = datetime.date.today()

        ok, err = _t6_mark_given(
            kind=kind,
            wing=wing,
            flat_no=flat_no,
            given_dt=today,
            cheque_no=chq_no,
            cheque_dt=chq_dt
        )

        if ok:
            st.success(f"✅ Marked {kind} as Given.")
            st.session_state["t6_dialog_ctx"] = None
            st.rerun()
        else:
            st.error(f"❌ Update failed: {err}")

    if "t6_dialog_ctx" in st.session_state and st.session_state["t6_dialog_ctx"]:
        ctx = st.session_state["t6_dialog_ctx"]

        def dialog_body():
            st.write(f"**Flat:** {ctx['label']}  |  **Type:** {ctx['type']}")

            chq = st.text_input("Cheque Number", key="t6_chq")
            dt = st.date_input("Cheque Date", format="DD/MM/YYYY", key="t6_chq_dt")

            b1, b2 = st.columns(2)

            with b1:
                if st.button("Save", key="t6_save"):
                    if chq:
                        _t6_save(ctx["type"], ctx["wing"], ctx["flat"], chq, dt)
                    else:
                        st.error("Enter Cheque Number.")

            with b2:
                if st.button("Cancel", key="t6_cancel"):
                    st.session_state["t6_dialog_ctx"] = None
                    st.rerun()

        if hasattr(st, "dialog"):
            @st.dialog("Enter Cheque Details")
            def _dlg():
                dialog_body()

            _dlg()

        elif hasattr(st, "experimental_dialog"):
            @st.experimental_dialog("Enter Cheque Details")
            def _dlg():
                dialog_body()

            _dlg()

        else:
            with st.expander("Enter Cheque Details", expanded=True):
                dialog_body()

    # ----------------- Optional full table preview -----------------
    with st.expander("View CP payout raw records"):
        if cp_payout_df.empty:
            st.info("No records.")
        else:
            preview_cols = [
                "invoice_date",
                "invoice_number",
                "firm_cp_name",
                "wing",
                "flat_number",
                "flat",
                "fos_amount",
                "brokerage_amount",
                "cp_name_fos",
                "firm_name_brokerage",
                "fos_given",
                "fos_given_date",
                "fos_cheque_no",
                "fos_cheque_date",
                "brokerage_given",
                "brokerage_given_date",
                "brokerage_cheque_no",
                "brokerage_cheque_date",
            ]

            show_cols = [c for c in preview_cols if c in cp_payout_df.columns]
            show_df = cp_payout_df[show_cols].copy()

            for dc in ["invoice_date", "fos_given_date", "fos_cheque_date", "brokerage_given_date", "brokerage_cheque_date"]:
                if dc in show_df.columns:
                    show_df[dc] = show_df[dc].apply(_display_date)

            st.dataframe(show_df, use_container_width=True, hide_index=True)
