import base64
import datetime as _dt
import re
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import pandas as pd
import streamlit as st
from fpdf import FPDF


_run_app_file("app_parts/construction_progress_core.py")
_run_app_file("tabs/inventory_status.py")

LABOUR_TABLE = "construction_labour_counts"
CONCRETE_TABLE = "construction_concrete_consumption"

DPR_ALL_SLABS = [
    "BOOKING AMOUNT",
    "AGREEMENT",
    "PLINTH",
    "3RD FLOOR",
    "7TH FLOOR",
    "10TH FLOOR",
    "13TH FLOOR",
    "FLOORING",
    "PLASTERING",
    "PLUMBING",
    "ELECTRICAL",
    "SANITARY & LIFT",
    "POSSESSION",
]

DPR_CONSTRUCTION_SLABS = DPR_ALL_SLABS[2:]


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

        return float(
            str(value)
            .replace(",", "")
            .replace("₹", "")
            .replace("Rs", "")
            .replace("INR", "")
            .strip()
        )
    except Exception:
        return 0.0


def _dpr_date_series(series):
    if series is None:
        return pd.Series(dtype="datetime64[ns]")

    def parse_one(v):
        if pd.isna(v) or str(v).strip() == "":
            return pd.NaT

        s = str(v).strip()

        # Supabase date columns arrive as YYYY-MM-DD. Keep this path strict so
        # 2026-03-05 is always shown as 05/03/2026, never 03/05/2026.
        if re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", s):
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return pd.Timestamp(_dt.datetime.strptime(s, fmt)).normalize()
                except Exception:
                    pass
            return pd.to_datetime(s, errors="coerce")

        return pd.to_datetime(s, errors="coerce", dayfirst=True)

    return series.apply(parse_one)


def _dpr_date_label(value):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "-"
    return parsed.strftime("%d/%m/%Y")


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
    if series is None:
        return pd.Series(dtype=bool)

    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["done", "completed", "yes", "true", "1", "received", "recieved", "given"])
    )


def _dpr_status_present_series(series):
    if series is None:
        return pd.Series(dtype=bool)

    false_values = {
        "",
        "pending",
        "not received",
        "not recieved",
        "not done",
        "not given",
        "no",
        "n",
        "false",
        "0",
        "na",
        "n/a",
        "nan",
        "nat",
        "none",
        "null",
        "-",
    }

    return ~series.fillna("").astype(str).str.strip().str.lower().isin(false_values)


def _dpr_status_count_until(df: pd.DataFrame, col: str | None, target_date: _dt.date) -> int:
    if df is None or df.empty or not col:
        return 0

    status_values = df[col]
    parsed_dates = _dpr_date_series(status_values)
    has_date = parsed_dates.notna()
    date_done = has_date & (parsed_dates.dt.date <= target_date)

    # Old text values are treated as completed for overall totals. The SQL
    # migration converts those old remarks to yesterday's date.
    old_text_done = (~has_date) & _dpr_status_present_series(status_values)

    return int((date_done | old_text_done).sum())


def _dpr_status_count_on_date(df: pd.DataFrame, col: str | None, target_date: _dt.date) -> int:
    if df is None or df.empty or not col:
        return 0

    parsed_dates = _dpr_date_series(df[col])
    return int((parsed_dates.notna() & (parsed_dates.dt.date == target_date)).sum())


def _dpr_status_present_value(value) -> bool:
    if pd.isna(value):
        return False

    s = str(value).strip().lower()
    return s not in {
        "",
        "pending",
        "not received",
        "not recieved",
        "not done",
        "not given",
        "no",
        "n",
        "false",
        "0",
        "na",
        "n/a",
        "nan",
        "nat",
        "none",
        "null",
        "-",
    }


def _dpr_norm_wing(value):
    s = str(value or "").strip().upper().replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    if not s:
        return ""
    s = re.sub(r"\s*WING\s*$", "", s).strip()
    s = re.sub(r"^WING\s*", "", s).strip()
    return f"{s} Wing"


def _dpr_gross_agreement_value(agreement_cost):
    agreement = _dpr_to_num(agreement_cost)
    gst_rate = 0.05 if agreement > 4499999 else 0.01
    gst_amt = round(agreement * gst_rate, 2)
    return round(agreement + gst_amt, 2)


def _dpr_head_amounts(agreement_cost):
    gross_value = _dpr_gross_agreement_value(agreement_cost)
    return {
        "BOOKING AMOUNT": round(gross_value * 5.0 / 100.0, 2),
        "AGREEMENT": round(gross_value * 10.0 / 100.0, 2),
        "PLINTH": round(gross_value * 15.0 / 100.0, 2),
        "3RD FLOOR": round(gross_value * 7.5 / 100.0, 2),
        "7TH FLOOR": round(gross_value * 7.5 / 100.0, 2),
        "10TH FLOOR": round(gross_value * 7.5 / 100.0, 2),
        "13TH FLOOR": round(gross_value * 7.5 / 100.0, 2),
        "FLOORING": round(gross_value * 7.5 / 100.0, 2),
        "PLASTERING": round(gross_value * 7.5 / 100.0, 2),
        "PLUMBING": round(gross_value * 7.5 / 100.0, 2),
        "ELECTRICAL": round(gross_value * 7.5 / 100.0, 2),
        "SANITARY & LIFT": round(gross_value * 5.0 / 100.0, 2),
        "POSSESSION": round(gross_value * 5.0 / 100.0, 2),
    }


def _dpr_current_stage_for_wing(wing, slab_master_df: pd.DataFrame) -> str:
    if slab_master_df is None or slab_master_df.empty:
        return DPR_CONSTRUCTION_SLABS[0]

    wing_col = _dpr_col(slab_master_df, "wing", "Wing")
    slab_col = _dpr_col(slab_master_df, "slab_name", "Slab Name")
    completed_col = _dpr_col(slab_master_df, "completed", "Completed")

    if not wing_col or not slab_col or not completed_col:
        return DPR_CONSTRUCTION_SLABS[0]

    target_wing = _dpr_norm_wing(wing).upper()
    df = slab_master_df.copy()
    df["_wing_norm"] = df[wing_col].apply(_dpr_norm_wing).astype(str).str.upper()
    df["_slab_norm"] = df[slab_col].fillna("").astype(str).str.strip().str.upper()
    df["_completed"] = (
        df[completed_col]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["completed", "done", "yes", "true", "1"])
    )

    completed = set(df.loc[df["_wing_norm"].eq(target_wing) & df["_completed"], "_slab_norm"].tolist())

    for slab in DPR_CONSTRUCTION_SLABS:
        if slab not in completed:
            return slab

    return DPR_CONSTRUCTION_SLABS[-1]


def _dpr_due_order_for_stage(row, stage: str, agreement_done_col: str | None) -> list[str]:
    order = ["BOOKING AMOUNT"]
    if agreement_done_col and _dpr_status_present_value(row.get(agreement_done_col)):
        order.append("AGREEMENT")
        if stage in DPR_CONSTRUCTION_SLABS:
            upto = DPR_CONSTRUCTION_SLABS.index(stage)
            order.extend(DPR_CONSTRUCTION_SLABS[:upto + 1])
    return order


def _dpr_page_css():
    st.markdown(
        """
        <style>
          .dpr-hero {
            border: 1px solid #dbe4ee;
            background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 52%, #f7f7ff 100%);
            border-radius: 18px;
            padding: 24px 22px 20px;
            text-align: center;
            margin: 8px 0 18px;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.07);
          }
          .dpr-hero h1 {
            margin: 0;
            color: #0f172a;
            font-size: 30px;
            font-weight: 900;
            letter-spacing: 0;
          }
          .dpr-hero p {
            margin: 8px 0 0;
            color: #475569;
            font-size: 15px;
            font-weight: 650;
          }
          .dpr-section {
            text-align: center;
            margin: 26px 0 14px;
          }
          .dpr-section h2 {
            margin: 0;
            font-size: 23px;
            font-weight: 900;
            color: #111827;
            letter-spacing: 0;
          }
          .dpr-section div {
            display: inline-block;
            width: 84px;
            height: 3px;
            border-radius: 999px;
            background: linear-gradient(90deg, #2563eb, #14b8a6);
            margin-top: 8px;
          }
          .dpr-kpi {
            min-height: 116px;
            border: 1px solid #dbe4ee;
            border-radius: 16px;
            background: #ffffff;
            padding: 14px 15px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            margin-bottom: 12px;
          }
          .dpr-kpi.blue { background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%); }
          .dpr-kpi.green { background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%); }
          .dpr-kpi.amber { background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%); }
          .dpr-kpi.slate { background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); }
          .dpr-kpi h6 {
            margin: 0;
            color: #64748b;
            font-size: 12px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: .04em;
          }
          .dpr-kpi p {
            margin: 8px 0 0;
            color: #0f172a;
            font-size: 26px;
            line-height: 1.12;
            font-weight: 950;
          }
          .dpr-kpi span {
            display: block;
            margin-top: 7px;
            color: #64748b;
            font-size: 12px;
            font-weight: 650;
          }
          .dpr-table-title {
            margin: 18px 0 8px;
            color: #1f2937;
            font-size: 16px;
            font-weight: 900;
          }
          .dpr-download-box {
            border: 1px solid #bfdbfe;
            background: #eff6ff;
            color: #1e3a8a;
            border-radius: 14px;
            padding: 12px 14px;
            font-weight: 750;
            margin: 8px 0 16px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _dpr_hero(report_date: _dt.date):
    st.markdown(
        f"""
        <div class="dpr-hero">
          <h1>Daily Progress Report</h1>
          <p>Pratham Vihar | Report Date: {_dpr_date_label(report_date)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _dpr_section_title(title: str):
    st.markdown(
        f"""
        <div class="dpr-section">
          <h2>{title}</h2>
          <div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _dpr_metric(label, value, note="", tone="slate"):
    return {
        "label": label,
        "value": value,
        "note": note,
        "tone": tone,
    }


def _dpr_render_kpis(items, columns=4):
    if not items:
        return

    cols = st.columns(columns)
    for idx, item in enumerate(items):
        with cols[idx % columns]:
            st.markdown(
                f"""
                <div class="dpr-kpi {item.get('tone', 'slate')}">
                  <h6>{item.get('label', '')}</h6>
                  <p>{item.get('value', '')}</p>
                  <span>{item.get('note', '')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _dpr_display_table(title: str, df: pd.DataFrame, empty_message: str, height=None):
    st.markdown(f'<div class="dpr-table-title">{title}</div>', unsafe_allow_html=True)

    if df is None or df.empty:
        st.info(empty_message)
        return

    kwargs = {"use_container_width": True, "hide_index": True}
    if height:
        kwargs["height"] = height

    st.dataframe(df, **kwargs)


def _dpr_bookings_until(df: pd.DataFrame, date_col: str | None, target_date: _dt.date):
    if df is None or df.empty or not date_col:
        return df.copy() if df is not None else pd.DataFrame()

    out = df.copy()
    out["_date"] = _dpr_date_series(out[date_col])
    mask = out["_date"].isna() | (out["_date"].dt.date <= target_date)
    return out[mask].copy()


def _dpr_build_inventory_table():
    if "booking_df" not in globals() or "hold_df" not in globals():
        return pd.DataFrame()

    try:
        inventory_df = _build_inventory_status_df(booking_df, hold_df)
        inv = inventory_df[inventory_df["Base Category"].eq("OUR")].copy()
        rows = []

        sold_statuses = [
            "BOOKED_PENDING",
            "STAMP_DUTY_RECEIVED",
            "AGREEMENT_LINEUP",
            "AGREEMENT_DONE",
        ]

        for wing, wing_df in inv.groupby("Wing"):
            total_units = int(len(wing_df))
            sold_units = int(wing_df["Internal Status"].isin(sold_statuses).sum())
            balance_units = max(total_units - sold_units, 0)
            rows.append({
                "Wing": wing,
                "Our Inventory": total_units,
                "Sold": sold_units,
                "Balance": balance_units,
            })

        return pd.DataFrame(rows).sort_values("Wing").reset_index(drop=True) if rows else pd.DataFrame()
    except Exception as exc:
        st.warning(f"Could not build inventory summary: {exc}")
        return pd.DataFrame()


def _dpr_fetch_raw_bookings_for_report(supabase_client) -> pd.DataFrame:
    try:
        response = supabase_client.table("bookings").select("*").execute()
        return pd.DataFrame(response.data or [])
    except Exception:
        return pd.DataFrame()


def _dpr_build_sales_data(bookings_df: pd.DataFrame, target_date: _dt.date, raw_bookings_df=None):
    if bookings_df is None or bookings_df.empty:
        return {
            "warning": "No booking data available.",
            "overall_metrics": [],
            "today_metrics": [],
            "inventory_df": pd.DataFrame(),
            "bookings_today_df": pd.DataFrame(),
        }

    df = bookings_df.copy()
    date_col = _dpr_col(df, "booking_date", "Date", "Booking Date")
    wing_col = _dpr_col(df, "wing", "Wing")
    flat_col = _dpr_col(df, "flat_number", "Flat Number")
    type_col = _dpr_col(df, "type", "Type")
    exec_col = _dpr_col(df, "sales_executive", "Sales Executive")
    stamp_col = _dpr_col(df, "stamp_duty", "Stamp Duty")
    agreement_col = _dpr_col(df, "agreement_done", "Agreement Done")

    status_df = raw_bookings_df.copy() if isinstance(raw_bookings_df, pd.DataFrame) and not raw_bookings_df.empty else df.copy()
    status_stamp_col = _dpr_col(status_df, "stamp_duty", "Stamp Duty")
    status_agreement_col = _dpr_col(status_df, "agreement_done", "Agreement Done")

    if date_col:
        df["_date"] = _dpr_date_series(df[date_col])
        today_df = df[df["_date"].dt.date == target_date].copy()
        till_df = _dpr_bookings_until(df, date_col, target_date)
    else:
        today_df = pd.DataFrame(columns=df.columns)
        till_df = df.copy()

    total_bookings_till_date = int(len(till_df))
    stamp_till_date = _dpr_status_count_until(status_df, status_stamp_col, target_date)
    agreement_till_date = _dpr_status_count_until(status_df, status_agreement_col, target_date)

    today_bookings = int(len(today_df))
    today_stamp = _dpr_status_count_on_date(status_df, status_stamp_col, target_date)
    today_agreement = _dpr_status_count_on_date(status_df, status_agreement_col, target_date)

    show_cols = [c for c in [exec_col, wing_col, flat_col, type_col] if c]
    if not today_df.empty and show_cols:
        bookings_today_df = today_df[show_cols].copy()
        bookings_today_df.columns = [
            "Sales Executive" if c == exec_col else
            "Wing" if c == wing_col else
            "Flat Number" if c == flat_col else
            "Type"
            for c in bookings_today_df.columns
        ]
    else:
        bookings_today_df = pd.DataFrame(columns=["Sales Executive", "Wing", "Flat Number", "Type"])

    return {
        "warning": None if date_col else "Booking date column not found. Today-only sales count cannot be calculated.",
        "overall_metrics": [
            _dpr_metric("Total Bookings Till Date", f"{total_bookings_till_date:,}", "Overall sales booked", "blue"),
            _dpr_metric("Stamp Duty Received Till Date", f"{stamp_till_date:,}", "Overall received count", "green"),
            _dpr_metric("Agreement Done Till Date", f"{agreement_till_date:,}", "Overall agreement count", "amber"),
        ],
        "today_metrics": [
            _dpr_metric("Bookings Today", f"{today_bookings:,}", "Selected report date", "blue"),
            _dpr_metric("Stamp Duty Today", f"{today_stamp:,}", "Selected report date", "green"),
            _dpr_metric("Agreement Done Today", f"{today_agreement:,}", "Selected report date", "amber"),
        ],
        "inventory_df": _dpr_build_inventory_table(),
        "bookings_today_df": bookings_today_df,
    }


def _dpr_build_cashflow_data(bookings_df: pd.DataFrame, slab_master_df: pd.DataFrame | None = None):
    if bookings_df is None or bookings_df.empty:
        return {
            "warning": "No booking data available.",
            "metrics": [],
            "wing_df": pd.DataFrame(),
        }

    df = bookings_df.copy()
    wing_col = _dpr_col(df, "wing", "Wing")
    agreement_col = _dpr_col(df, "agreement_cost", "Agreement Cost")
    received_col = _dpr_col(df, "received_amount", "Received Amount")
    carpet_col = _dpr_col(df, "carpet_area", "Carpet Area")
    agreement_done_col = _dpr_col(df, "agreement_done", "Agreement Done")

    if not agreement_col:
        return {
            "warning": "Agreement Cost column not found.",
            "metrics": [],
            "wing_df": pd.DataFrame(),
        }

    slab_master_df = slab_master_df if isinstance(slab_master_df, pd.DataFrame) else pd.DataFrame()

    df["_wing_label"] = df[wing_col].apply(_dpr_norm_wing) if wing_col else "All Wings"
    df["_current_stage"] = df["_wing_label"].apply(lambda w: _dpr_current_stage_for_wing(w, slab_master_df))
    df["_agreement"] = df[agreement_col].apply(_dpr_to_num)
    df["_received"] = df[received_col].apply(_dpr_to_num) if received_col else 0.0
    df["_carpet"] = df[carpet_col].apply(_dpr_to_num) if carpet_col else 0.0

    totals_till_stage = []
    received_till_stage = []
    due_till_stage = []

    for _, row in df.iterrows():
        stage = row.get("_current_stage", DPR_CONSTRUCTION_SLABS[0])
        order = _dpr_due_order_for_stage(row, stage, agreement_done_col)
        amt_map = _dpr_head_amounts(row.get(agreement_col, 0))
        total_stage = sum(_dpr_to_num(amt_map.get(head, 0)) for head in order)
        received_stage = min(_dpr_to_num(row.get("_received", 0)), total_stage)
        due_stage = max(total_stage - received_stage, 0.0)
        totals_till_stage.append(total_stage)
        received_till_stage.append(received_stage)
        due_till_stage.append(due_stage)

    df["_total_till_stage"] = totals_till_stage
    df["_received_till_stage"] = received_till_stage
    df["_due_till_stage"] = due_till_stage

    total_amount = float(df["_total_till_stage"].sum())
    total_received = float(df["_received_till_stage"].sum())
    total_due = float(df["_due_till_stage"].sum())
    carpet_sold = float(df["_carpet"].sum())

    wing_summary = pd.DataFrame()
    if wing_col:
        wing_summary = (
            df.groupby(["_wing_label", "_current_stage"], as_index=False)
            .agg(
                **{
                    "Total Till Stage": ("_total_till_stage", "sum"),
                    "Received Till Stage": ("_received_till_stage", "sum"),
                    "Due Till Stage": ("_due_till_stage", "sum"),
                    "Carpet Area Sold": ("_carpet", "sum"),
                }
            )
            .rename(columns={"_wing_label": "Wing", "_current_stage": "Current Stage"})
        )

        for col in ["Total Till Stage", "Received Till Stage", "Due Till Stage"]:
            wing_summary[col] = wing_summary[col].apply(_dpr_fmt_money)

        wing_summary["Carpet Area Sold"] = wing_summary["Carpet Area Sold"].apply(lambda x: f"{_dpr_fmt_num(x)} sqft")
        wing_summary = wing_summary.sort_values("Wing").reset_index(drop=True)

    return {
        "warning": None,
        "metrics": [
            _dpr_metric("Total Till Current Stage", _dpr_fmt_money(total_amount), "Only up to active slab/stage", "blue"),
            _dpr_metric("Received Till Current Stage", _dpr_fmt_money(total_received), "Capped to current-stage demand", "green"),
            _dpr_metric("Due Till Current Stage", _dpr_fmt_money(total_due), "Pending till active stage", "amber"),
            _dpr_metric("Carpet Area Sold", f"{_dpr_fmt_num(carpet_sold)} sqft", "Total sold carpet", "slate"),
        ],
        "wing_df": wing_summary,
    }


def _dpr_construction_work_done(floor_df, flat_df, floor_col_map, flat_col_map, target_date: _dt.date):
    rows = []

    if floor_df is not None and not floor_df.empty:
        for _, floor_row in floor_df.iterrows():
            completed_by_heading = {}
            for cp in _active_rcc_checkpoints(floor_row):
                col = floor_col_map.get(cp)
                if col:
                    d = _parse_date(floor_row.get(col))
                    if pd.notna(d) and d.date() == target_date:
                        label = cp.label
                        if _is_partial_rcc_checkpoint(cp):
                            count_label = _partial_count_label(floor_row, cp)
                            if count_label != "-":
                                label = f"{label} ({count_label})"
                        completed_by_heading.setdefault(cp.heading, []).append(label)

            for heading, completed in completed_by_heading.items():
                rows.append({
                    "Wing": _wing_value(floor_row),
                    "Floor / Level": _level_label(floor_row),
                    "Main Work": heading,
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


def _dpr_build_construction_data(supabase_client, target_date: _dt.date):
    labour_df = _dpr_fetch_table(supabase_client, LABOUR_TABLE)
    concrete_df = _dpr_fetch_table(supabase_client, CONCRETE_TABLE)

    if not labour_df.empty and "report_date" in labour_df.columns:
        labour_df["report_date"] = _dpr_date_series(labour_df["report_date"])
        labour_today = labour_df[labour_df["report_date"].dt.date == target_date].copy()
    else:
        labour_today = pd.DataFrame()

    staff = pd.DataFrame()
    labour = pd.DataFrame()
    staff_cols = ["project_manager", "senior_engineer", "junior_engineer", "supervisor"]
    labour_cols = ["carpenter", "fitter", "mason", "skilled", "unskilled", "others"]

    if not labour_today.empty:
        for col in staff_cols + labour_cols:
            if col not in labour_today.columns:
                labour_today[col] = 0
            labour_today[col] = pd.to_numeric(labour_today[col], errors="coerce").fillna(0)

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

        labour_today_nonzero = labour_today[labour_today[labour_cols].sum(axis=1) > 0].copy()

        if not labour_today_nonzero.empty:
            labour = (
                labour_today_nonzero.groupby(["wing", "contractor_name"], as_index=False)[labour_cols]
                .sum()
                .rename(columns={
                    "wing": "Wing",
                    "contractor_name": "Contractor",
                    "carpenter": "Carpenter",
                    "fitter": "Fitter",
                    "mason": "Mason",
                    "skilled": "Skilled",
                    "unskilled": "Unskilled",
                    "others": "Others",
                })
            )

    if not concrete_df.empty and "report_date" in concrete_df.columns:
        concrete_df["report_date"] = _dpr_date_series(concrete_df["report_date"])
        concrete_today = concrete_df[concrete_df["report_date"].dt.date == target_date].copy()
    else:
        concrete_today = pd.DataFrame()

    concrete_summary = pd.DataFrame()
    if not concrete_today.empty:
        if "concrete_quantity_m3" not in concrete_today.columns:
            concrete_today["concrete_quantity_m3"] = 0
        if "concrete_grade" not in concrete_today.columns:
            concrete_today["concrete_grade"] = ""
        concrete_today["wing"] = concrete_today["wing"].fillna("").astype(str).str.strip()
        concrete_today["work"] = concrete_today["work"].fillna("").astype(str).str.strip()
        concrete_today["concrete_grade"] = concrete_today["concrete_grade"].fillna("").astype(str).str.strip()
        concrete_today["concrete_quantity_m3"] = pd.to_numeric(concrete_today["concrete_quantity_m3"], errors="coerce").fillna(0)
        concrete_summary = (
            concrete_today.groupby(["wing", "work", "concrete_grade"], as_index=False)["concrete_quantity_m3"]
            .sum()
            .rename(columns={
                "wing": "Wing",
                "work": "Work",
                "concrete_grade": "Grade",
                "concrete_quantity_m3": "Concrete Quantity (M3)",
            })
        )

    floor_df, flat_df = _load_data(supabase_client)
    floor_col_map = _column_lookup(floor_df, RCC_CHECKPOINTS)
    flat_col_map = _column_lookup(flat_df, FLAT_CHECKPOINTS)
    work_done_df = _dpr_construction_work_done(floor_df, flat_df, floor_col_map, flat_col_map, target_date)

    if not work_done_df.empty:
        work_done_df = work_done_df.sort_values(["Wing", "Floor / Level", "Main Work"]).reset_index(drop=True)

    total_staff = int(staff[[c for c in ["Project Manager", "Senior Engineer", "Junior Engineer", "Supervisor"] if c in staff.columns]].sum().sum()) if not staff.empty else 0
    total_labour = int(labour[[c for c in ["Carpenter", "Fitter", "Mason", "Skilled", "Unskilled", "Others"] if c in labour.columns]].sum().sum()) if not labour.empty else 0
    concrete_total = float(concrete_summary["Concrete Quantity (M3)"].sum()) if not concrete_summary.empty else 0.0

    active_wings = set()
    for df_part, col in [(labour, "Wing"), (concrete_summary, "Wing"), (work_done_df, "Wing")]:
        if df_part is not None and not df_part.empty and col in df_part.columns:
            active_wings.update(df_part[col].dropna().astype(str).str.strip().tolist())

    return {
        "metrics": [
            _dpr_metric("Total Site Staff", f"{total_staff:,}", "Contractor staff today", "blue"),
            _dpr_metric("Total Labour", f"{total_labour:,}", "Wing-wise labour today", "green"),
            _dpr_metric("Concrete Consumed", f"{_dpr_fmt_num(concrete_total)} M3", "Today consumption", "amber"),
            _dpr_metric("Work Updates", f"{len(work_done_df):,}", "Checkpoints marked today", "slate"),
            _dpr_metric("Active Wings", f"{len([w for w in active_wings if w]):,}", "Wings with activity", "blue"),
        ],
        "staff_df": staff,
        "labour_df": labour,
        "concrete_df": concrete_summary,
        "work_done_df": work_done_df,
    }


def _dpr_build_rcc_tracking_data(supabase_client):
    floor_df, flat_df = _load_data(supabase_client)
    floor_col_map = _column_lookup(floor_df, RCC_CHECKPOINTS)
    wings = _wing_options(floor_df, flat_df)
    target_df = _load_rcc_targets(supabase_client)

    wing_cards = []
    table_rows = []
    data_by_wing = {}

    for wing in wings:
        target_days = _rcc_target_days(target_df, wing)
        delay_df = _rcc_delay_rows(floor_df, floor_col_map, wing, target_days)
        if delay_df.empty:
            continue

        started = delay_df["RCC Progress %"].gt(0).any()
        incomplete = delay_df["RCC Progress %"].lt(100).any()
        if not (started and incomplete):
            continue

        used_days = int(delay_df["Days Used"].sum())
        days_left = int(round(delay_df["Wing Days Left"].iloc[0]))
        delay_days = int(round(delay_df["Wing Delay Days"].iloc[0]))
        remaining_df = delay_df[delay_df["RCC Progress %"] < 100].copy()
        active_df = delay_df[(delay_df["RCC Progress %"] > 0) & (delay_df["RCC Progress %"] < 100)].copy()

        levels = []
        for _, row in delay_df.iterrows():
            pct = float(row["RCC Progress %"])
            used = int(round(row["Days Used"]))
            left = int(round(float(row["Days Left"])))
            if delay_days > 0 and pct < 100:
                day_text = f"Used {used}d | Delay {delay_days}d"
            else:
                day_text = f"Used {used}d | Left {left}d"

            levels.append({
                "level": row["Level"],
                "progress": pct,
                "days": day_text,
                "color": _progress_color(pct),
                "report": [],
            })

        data_by_wing[wing] = levels

        rem_table = remaining_df.sort_values("Display Order", ascending=False).head(6).copy()
        for _, row in rem_table.iterrows():
            table_rows.append({
                "Wing": f"{wing} Wing",
                "Remaining Slab": row["Level"],
                "Progress": f"{float(row['RCC Progress %']):.0f}%",
                "Remaining Days": int(round(float(row["Days Left"]))),
                "Target Days": target_days,
            })

        wing_cards.append({
            "Wing": wing,
            "Target Days": target_days,
            "Used Days": used_days,
            "Days Left": days_left,
            "Delay Days": delay_days,
            "Remaining Slabs": int(len(remaining_df)),
            "Active Slabs": int(len(active_df)),
            "Levels": levels,
            "Remaining Table": [
                {
                    "Level": row["Level"],
                    "Progress": f"{float(row['RCC Progress %']):.0f}%",
                    "Days Left": int(round(float(row["Days Left"]))),
                }
                for _, row in rem_table.iterrows()
            ],
        })

    total_target = sum(int(w["Target Days"]) for w in wing_cards)
    total_used = sum(int(w["Used Days"]) for w in wing_cards)
    total_left = sum(int(w["Days Left"]) for w in wing_cards)
    total_delay = sum(int(w["Delay Days"]) for w in wing_cards)

    return {
        "metrics": [
            _dpr_metric("Active RCC Wings", f"{len(wing_cards):,}", "Started and not completed", "blue"),
            _dpr_metric("Target Days", f"{total_target:,}", "Active wings total", "slate"),
            _dpr_metric("Used Days", f"{total_used:,}", "Across active wings", "green"),
            _dpr_metric("Days Left", f"{total_left:,}", "Allocated to pending slabs", "amber"),
            _dpr_metric("Delay Days", f"{total_delay:,}", "If used exceeds target", "slate"),
        ],
        "wing_cards": wing_cards,
        "summary_df": pd.DataFrame(table_rows),
        "data_by_wing": data_by_wing,
    }


def _dpr_render_sales_section(sales_data):
    _dpr_section_title("Sales Summary")

    if sales_data.get("warning"):
        st.warning(sales_data["warning"])

    st.markdown('<div class="dpr-table-title">Overall Sales Till Date</div>', unsafe_allow_html=True)
    _dpr_render_kpis(sales_data.get("overall_metrics", []), columns=3)

    st.markdown('<div class="dpr-table-title">Today Sales Movement</div>', unsafe_allow_html=True)
    _dpr_render_kpis(sales_data.get("today_metrics", []), columns=3)

    _dpr_display_table(
        "Wing-wise Inventory",
        sales_data.get("inventory_df", pd.DataFrame()),
        "Inventory summary is not available.",
    )

    _dpr_display_table(
        "Bookings Done Today",
        sales_data.get("bookings_today_df", pd.DataFrame()),
        "No bookings done on selected date.",
    )


def _dpr_render_cashflow_section(cashflow_data):
    _dpr_section_title("Cashflow Summary")

    if cashflow_data.get("warning"):
        st.warning(cashflow_data["warning"])

    _dpr_render_kpis(cashflow_data.get("metrics", []), columns=4)

    _dpr_display_table(
        "Wing-wise Cashflow",
        cashflow_data.get("wing_df", pd.DataFrame()),
        "Wing-wise cashflow data is not available.",
    )


def _dpr_render_construction_section(construction_data):
    _dpr_section_title("Construction Summary")

    _dpr_render_kpis(construction_data.get("metrics", []), columns=5)

    _dpr_display_table(
        "Contractor-wise Staff Count",
        construction_data.get("staff_df", pd.DataFrame()),
        "No staff entries found for selected date.",
    )

    _dpr_display_table(
        "Wing-wise Contractor-wise Labour Count",
        construction_data.get("labour_df", pd.DataFrame()),
        "No labour entries found for selected date.",
    )

    _dpr_display_table(
        "Concrete Consumption",
        construction_data.get("concrete_df", pd.DataFrame()),
        "No concrete consumption entries found for selected date.",
    )

    _dpr_display_table(
        "Work Done Today",
        construction_data.get("work_done_df", pd.DataFrame()),
        "No construction checkpoints were marked done on selected date.",
        height=360,
    )


def _dpr_render_rcc_tracking_section(rcc_data):
    _dpr_section_title("RCC Work Days Tracking")

    _dpr_render_kpis(rcc_data.get("metrics", []), columns=5)

    data_by_wing = rcc_data.get("data_by_wing", {})
    if data_by_wing:
        _render_clickable_floor_chart(data_by_wing, "RCC Work Days Tracking")
    else:
        st.info("No active RCC wing found. Wings appear here only after RCC work has started and before it is fully completed.")

    _dpr_display_table(
        "Remaining Slabs and Days",
        rcc_data.get("summary_df", pd.DataFrame()),
        "No remaining RCC slabs found for active wings.",
    )


def _dpr_pdf_safe(value):
    s = str(value if value is not None else "")
    replacements = {
        "₹": "Rs ",
        "—": "-",
        "–": "-",
        "•": "-",
        "\n": " ",
        "\r": " ",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s.encode("latin-1", "ignore").decode("latin-1")


def _dpr_pdf_section(pdf: FPDF, title: str):
    if pdf.get_y() > 260:
        pdf.add_page()

    pdf.ln(4)
    pdf.set_fill_color(235, 244, 255)
    pdf.set_draw_color(191, 219, 254)
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, _dpr_pdf_safe(title), border=1, ln=True, align="C", fill=True)
    pdf.ln(2)


def _dpr_pdf_kpis(pdf: FPDF, title: str, items, per_row=None):
    if not items:
        return

    _dpr_pdf_section(pdf, title)

    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    if per_row is None:
        per_row = min(len(items), 5)
    per_row = max(1, min(int(per_row), len(items), 5))

    gap = 3
    card_w = (page_w - gap * (per_row - 1)) / per_row
    card_h = 21
    row_y = pdf.get_y()

    for idx, item in enumerate(items):
        if idx % per_row == 0:
            if idx > 0:
                row_y += card_h + 4
            if row_y + card_h > 270:
                pdf.add_page()
                row_y = pdf.get_y()

        x = pdf.l_margin + (idx % per_row) * (card_w + gap)
        y = row_y

        pdf.set_xy(x, y)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(219, 228, 238)
        pdf.rect(x, y, card_w, card_h, style="DF")

        pdf.set_xy(x + 3, y + 3)
        pdf.set_text_color(100, 116, 139)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(card_w - 6, 4, _dpr_pdf_safe(item.get("label", "")).upper()[:42], ln=True)

        pdf.set_xy(x + 3, y + 8)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(card_w - 6, 7, _dpr_pdf_safe(item.get("value", ""))[:32], ln=True)

        pdf.set_xy(x + 3, y + 16)
        pdf.set_text_color(100, 116, 139)
        pdf.set_font("Arial", "", 7)
        pdf.cell(card_w - 6, 4, _dpr_pdf_safe(item.get("note", ""))[:42], ln=True)

    pdf.set_xy(pdf.l_margin, row_y + card_h + 4)


def _dpr_pdf_wrap(pdf: FPDF, text, width, size=7):
    pdf.set_font("Arial", "", size)
    cleaned = _dpr_pdf_safe(text)
    words = cleaned.split()
    if not words:
        return ["-"]

    lines = []
    cur = ""
    for word in words:
        probe = f"{cur} {word}".strip()
        if pdf.get_string_width(probe) <= width:
            cur = probe
        else:
            if cur:
                lines.append(cur)
            cur = word

    if cur:
        lines.append(cur)

    return lines[:4] or ["-"]


def _dpr_pdf_table(pdf: FPDF, title: str, df: pd.DataFrame, max_rows=35):
    if df is None or df.empty:
        return

    _dpr_pdf_section(pdf, title)

    out = df.copy().head(max_rows)
    cols = list(out.columns)
    max_cols = 7
    if len(cols) > max_cols:
        cols = cols[:max_cols]
        out = out[cols].copy()

    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    widths = [page_w / len(cols)] * len(cols)

    if "Work Done" in cols:
        narrow = page_w * 0.16
        widths = []
        for col in cols:
            widths.append(page_w * 0.42 if col == "Work Done" else narrow)
        scale = page_w / sum(widths)
        widths = [w * scale for w in widths]

    if pdf.get_y() + 8 > 270:
        pdf.add_page()

    pdf.set_font("Arial", "B", 7)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(203, 213, 225)

    for col, width in zip(cols, widths):
        pdf.cell(width, 7, _dpr_pdf_safe(col)[:24], border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Arial", "", 7)

    for row_idx, (_, row) in enumerate(out.iterrows()):
        wrapped = [_dpr_pdf_wrap(pdf, row.get(col, ""), width - 3, size=7) for col, width in zip(cols, widths)]
        row_h = max(7, max(len(lines) for lines in wrapped) * 4 + 3)

        if pdf.get_y() + row_h > 275:
            pdf.add_page()
            pdf.set_font("Arial", "B", 7)
            pdf.set_fill_color(15, 23, 42)
            pdf.set_text_color(255, 255, 255)
            for col, width in zip(cols, widths):
                pdf.cell(width, 7, _dpr_pdf_safe(col)[:24], border=1, align="C", fill=True)
            pdf.ln()
            pdf.set_font("Arial", "", 7)
            pdf.set_text_color(15, 23, 42)

        x0, y0 = pdf.get_x(), pdf.get_y()
        fill = row_idx % 2 == 0
        pdf.set_fill_color(248, 250, 252 if fill else 255)

        x = x0
        for width in widths:
            pdf.rect(x, y0, width, row_h, style="DF" if fill else "D")
            x += width

        x = x0
        for lines, width in zip(wrapped, widths):
            pdf.set_xy(x + 1.5, y0 + 1.5)
            for line_no, line in enumerate(lines):
                pdf.set_xy(x + 1.5, y0 + 1.5 + line_no * 4)
                pdf.cell(width - 3, 4, line[:80], border=0)
            x += width

        pdf.set_xy(pdf.l_margin, y0 + row_h)

    if len(df) > max_rows:
        pdf.set_font("Arial", "I", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"Showing first {max_rows} rows of {len(df)} total rows.", ln=True)


def _dpr_pdf_rcc_tracking(pdf: FPDF, rcc_data: dict):
    wing_cards = rcc_data.get("wing_cards", []) or []
    if not wing_cards:
        return

    if pdf.page_no() < 2:
        pdf.add_page()
    elif pdf.get_y() > 165:
        pdf.add_page()

    _dpr_pdf_section(pdf, "RCC Work Days Tracking")

    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    gap = 2.5
    per_row = 4 if len(wing_cards) > 3 else max(1, len(wing_cards))
    card_w = (page_w - gap * (per_row - 1)) / per_row
    card_h = 55
    start_x = pdf.l_margin
    y = pdf.get_y()

    for idx, wing in enumerate(wing_cards):
        if idx and idx % per_row == 0:
            y += card_h + 4

        if y + card_h > 274:
            break

        x = start_x + (idx % per_row) * (card_w + gap)
        levels = list(wing.get("Levels", []))[:16]
        rem_rows = list(wing.get("Remaining Table", []))[:3]

        pdf.set_draw_color(203, 213, 225)
        pdf.set_fill_color(248, 250, 252)
        pdf.rect(x, y, card_w, card_h, style="DF")

        pdf.set_xy(x + 2, y + 2)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(card_w - 4, 4, f"{wing.get('Wing', '')} Wing", ln=True, align="C")

        pdf.set_xy(x + 2, y + 7)
        pdf.set_font("Arial", "", 5.8)
        summary = (
            f"Total {wing.get('Target Days', 0)}d | "
            f"Used {wing.get('Used Days', 0)}d | "
            f"Left {wing.get('Days Left', 0)}d"
        )
        pdf.cell(card_w - 4, 4, _dpr_pdf_safe(summary)[:52], ln=True, align="C")

        bx = x + 4
        by = y + 14
        bw = card_w - 8
        row_h = 1.7
        max_levels = min(len(levels), 16)

        if max_levels:
            level_h = row_h * max_levels
            pdf.set_draw_color(148, 163, 184)
            pdf.rect(bx, by, bw, level_h)

            for level_idx, level in enumerate(levels[:max_levels]):
                ly = by + level_idx * row_h
                progress = max(0.0, min(float(level.get("progress", 0) or 0), 100.0))
                fill_w = bw * progress / 100.0
                if progress >= 100:
                    pdf.set_fill_color(22, 163, 74)
                elif progress > 0:
                    pdf.set_fill_color(37, 99, 235)
                else:
                    pdf.set_fill_color(226, 232, 240)
                pdf.rect(bx, ly, fill_w, row_h, style="F")
                pdf.set_draw_color(226, 232, 240)
                pdf.line(bx, ly, bx + bw, ly)

        table_y = y + 42.5
        pdf.set_xy(x + 2, table_y)
        pdf.set_font("Arial", "B", 5.2)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(card_w * 0.54, 3.2, "Remaining Slab", border=1)
        pdf.cell(card_w * 0.20, 3.2, "Prog", border=1, align="C")
        pdf.cell(card_w * 0.18, 3.2, "Days", border=1, align="C")
        pdf.ln()

        pdf.set_font("Arial", "", 5.0)
        for rem in rem_rows:
            pdf.set_x(x + 2)
            pdf.cell(card_w * 0.54, 3.0, _dpr_pdf_safe(rem.get("Level", "-"))[:15], border=1)
            pdf.cell(card_w * 0.20, 3.0, _dpr_pdf_safe(rem.get("Progress", "-")), border=1, align="C")
            pdf.cell(card_w * 0.18, 3.0, str(rem.get("Days Left", "-")), border=1, align="C")
            pdf.ln()

    pdf.set_xy(pdf.l_margin, y + card_h + 5)


class _DailyProgressPDF(FPDF):
    def footer(self):
        self.set_y(-11)
        self.set_font("Arial", "I", 7)
        self.set_text_color(100, 116, 139)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")


def _dpr_pdf_bytes(report_date: _dt.date, report_parts: dict):
    pdf = _DailyProgressPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    pdf.set_fill_color(30, 64, 175)
    pdf.rect(10, 10, 190, 26, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 17)
    pdf.set_xy(10, 15)
    pdf.cell(190, 8, "Daily Progress Report", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 7, f"Pratham Vihar | Report Date: {_dpr_date_label(report_date)}", ln=True, align="C")
    pdf.ln(6)

    sales = report_parts.get("sales", {})
    cashflow = report_parts.get("cashflow", {})
    construction = report_parts.get("construction", {})
    rcc_tracking = report_parts.get("rcc_tracking", {})

    _dpr_pdf_kpis(pdf, "Sales - Overall Till Date", sales.get("overall_metrics", []))
    _dpr_pdf_kpis(pdf, "Sales - Today", sales.get("today_metrics", []))
    _dpr_pdf_table(pdf, "Wing-wise Inventory", sales.get("inventory_df", pd.DataFrame()), max_rows=8)
    _dpr_pdf_table(pdf, "Bookings Done Today", sales.get("bookings_today_df", pd.DataFrame()), max_rows=6)

    _dpr_pdf_kpis(pdf, "Cashflow", cashflow.get("metrics", []))
    _dpr_pdf_table(pdf, "Wing-wise Cashflow", cashflow.get("wing_df", pd.DataFrame()), max_rows=8)

    _dpr_pdf_kpis(pdf, "Construction", construction.get("metrics", []))
    _dpr_pdf_table(pdf, "Contractor-wise Staff Count", construction.get("staff_df", pd.DataFrame()), max_rows=5)
    _dpr_pdf_table(pdf, "Wing-wise Contractor-wise Labour Count", construction.get("labour_df", pd.DataFrame()), max_rows=8)
    _dpr_pdf_table(pdf, "Concrete Consumption", construction.get("concrete_df", pd.DataFrame()), max_rows=6)
    _dpr_pdf_table(pdf, "Work Done Today", construction.get("work_done_df", pd.DataFrame()), max_rows=10)
    _dpr_pdf_rcc_tracking(pdf, rcc_tracking)

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin1", "ignore")

    return bytes(output)


def _dpr_clean_email_list(value):
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]

    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]

    return []


def _dpr_send_daily_report_email(pdf_bytes: bytes, report_date: _dt.date):
    try:
        email_cfg = dict(st.secrets.get("email", {}))
    except Exception:
        email_cfg = {}

    smtp_host = email_cfg.get("smtp_host", "smtp.gmail.com")
    smtp_port = int(email_cfg.get("smtp_port", 465))
    sender_email = email_cfg.get("sender_email", "")
    sender_password = email_cfg.get("sender_password", "")
    receiver_email = email_cfg.get("receiver_email", "")
    subject_prefix = email_cfg.get("daily_subject_prefix", "Pratham Vihar Daily Progress Report")

    if not sender_email or not sender_password or not receiver_email:
        return False, "Email secrets are missing. Add sender_email, sender_password, and receiver_email in Streamlit secrets."

    recipients = _dpr_clean_email_list(receiver_email)
    if not recipients:
        return False, "Receiver email is empty."

    report_label = _dpr_date_label(report_date)
    filename = f"daily_progress_report_{report_date.isoformat()}.pdf"

    msg = MIMEMultipart()
    msg["Subject"] = f"{subject_prefix} - {report_label}"
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=True)

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color:#111827;">
        <h2 style="margin-bottom:4px;">Pratham Vihar Daily Progress Report</h2>
        <p style="margin-top:0;color:#475569;">Report Date: {report_label}</p>
        <p>Please find the attached director PDF report.</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())

    return True, f"Daily report email sent to {', '.join(recipients)}."


st.header("Daily Progress Report")
_dpr_page_css()

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

    bookings_source = (
        booking_df.copy()
        if "booking_df" in globals() and isinstance(booking_df, pd.DataFrame)
        else pd.DataFrame()
    )
    slab_master_source = (
        cashflow_slab_master_df.copy()
        if "cashflow_slab_master_df" in globals() and isinstance(cashflow_slab_master_df, pd.DataFrame)
        else pd.DataFrame()
    )
    raw_bookings_source = _dpr_fetch_raw_bookings_for_report(supabase_client)

    _dpr_hero(report_date)

    with st.spinner("Preparing director report..."):
        report_parts = {
            "sales": _dpr_build_sales_data(bookings_source, report_date, raw_bookings_source),
            "cashflow": _dpr_build_cashflow_data(bookings_source, slab_master_source),
            "construction": _dpr_build_construction_data(supabase_client, report_date),
            "rcc_tracking": _dpr_build_rcc_tracking_data(supabase_client),
        }
        pdf_bytes = _dpr_pdf_bytes(report_date, report_parts)

    st.markdown(
        '<div class="dpr-download-box">Director PDF is ready. This is the same PDF that will be used for email sharing.</div>',
        unsafe_allow_html=True,
    )

    pdf_col, email_col = st.columns(2)
    with pdf_col:
        st.download_button(
            "Download Daily Progress Report PDF",
            data=pdf_bytes,
            file_name=f"daily_progress_report_{report_date.isoformat()}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with email_col:
        if st.button("Send Daily Report Email Now", type="primary", use_container_width=True):
            with st.spinner("Sending daily progress report email..."):
                ok, msg = _dpr_send_daily_report_email(pdf_bytes, report_date)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    _dpr_render_sales_section(report_parts["sales"])
    _dpr_render_cashflow_section(report_parts["cashflow"])
    _dpr_render_construction_section(report_parts["construction"])
    _dpr_render_rcc_tracking_section(report_parts["rcc_tracking"])
