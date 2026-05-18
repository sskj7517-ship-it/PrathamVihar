# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.

import re
import io
import ssl
import smtplib
import datetime
from html import escape
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

import pandas as pd
import altair as alt
import streamlit as st

st.header("🏢 Complete Site Summary")
st.caption(
    "Detailed site-wide dashboard connected to Supabase tables: bookings, daily visits, marketing, holds, cashflow, and sales targets."
)

# ============================================================
# SUPABASE CONNECTION
# ============================================================
supabase_client = globals().get("supabase", None) or globals().get("supabase_client", None)

if supabase_client is None:
    st.error("Supabase client is not initialized. Please check your Supabase connection block.")
    st.stop()

# ============================================================
# TABLE NAMES
# ============================================================
BOOKINGS_TABLE = "bookings"
DAILY_VISITS_TABLE = "daily_visits"
MARKETING_TABLE = "marketing_expenditure"
HOLDS_TABLE = "holds"
CASHFLOW_MASTER_TABLE = "cashflow_slab_master"
SALES_TARGETS_TABLE = "sales_targets"

BOOKING_START_DATE = pd.Timestamp("2025-04-01")
TODAY = pd.Timestamp.today().normalize()
THIS_MONTH_KEY = TODAY.strftime("%Y-%m")
NEXT_MONTH_KEY = (TODAY + pd.offsets.MonthBegin(1)).strftime("%Y-%m")

# ============================================================
# BASIC HELPERS
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
        if x is None:
            return 0.0
        try:
            if pd.isna(x):
                return 0.0
        except Exception:
            pass
        s = (
            str(x)
            .replace("₹", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .replace(",", "")
            .strip()
        )
        if s == "":
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def _num_series(df, col):
    if df is None or df.empty or not col or col not in df.columns:
        return pd.Series(dtype=float)

    return pd.to_numeric(
        df[col]
        .astype("object")
        .where(pd.notna(df[col]), "")
        .astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace("Rs.", "", regex=False)
        .str.replace("Rs", "", regex=False)
        .str.replace(",", "", regex=False),
        errors="coerce",
    ).fillna(0.0)

def _fmt_money(x):
    return f"₹ {_to_num(x):,.0f}"

def _fmt_num(x):
    return f"{_to_num(x):,.0f}"

def _fmt_psf(x):
    if _to_num(x) <= 0:
        return "—"
    return f"₹{_to_num(x):,.0f}/sqft"

def _fmt_pct(x):
    try:
        if x is None or pd.isna(x):
            return "—"
        return f"{float(x):.1f}%"
    except Exception:
        return "—"

def _pct(num, den):
    den = _to_num(den)
    num = _to_num(num)
    if den <= 0:
        return 0.0
    return (num / den) * 100.0

def _psf_from_agreement_carpet(agreement_cost, carpet_area):
    """
    PSF business rule:
    Use agreement_cost and carpet_area only.
    Formula: agreement_cost / (carpet_area * 1.38)
    Do not use or average the rate column.
    """
    agreement = _to_num(agreement_cost)
    carpet = _to_num(carpet_area)
    if agreement <= 0 or carpet <= 0:
        return 0.0
    return agreement / (carpet * 1.38)

def _psf_from_df(df: pd.DataFrame):
    if df is None or df.empty:
        return 0.0
    if "_AgreementCostNum" not in df.columns or "_CarpetNum" not in df.columns:
        return 0.0
    return _psf_from_agreement_carpet(
        float(pd.to_numeric(df["_AgreementCostNum"], errors="coerce").fillna(0).sum()),
        float(pd.to_numeric(df["_CarpetNum"], errors="coerce").fillna(0).sum()),
    )

def _is_agreement_done(v):
    s = _safe_str(v).lower()
    return s in {"done", "completed", "complete", "yes"} or "done" in s or "complete" in s

def _is_stamp_received(v):
    # Business rule: blank = pending. Any meaningful remark/value = received.
    s = _safe_str(v).lower()
    if s in {"", "pending", "not received", "not recieved", "no", "n", "na", "n/a", "none"}:
        return False
    return True

def _norm_wing(v):
    s = _safe_str(v).upper().replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    wing_map = {
        "B": "B Wing", "B WING": "B Wing",
        "C": "C Wing", "C WING": "C Wing",
        "E": "E Wing", "E WING": "E Wing",
        "F": "F Wing", "F WING": "F Wing",
    }
    return wing_map.get(s, _safe_str(v))

def _norm_flat(v):
    return _safe_str(v).upper()

def _parse_date(v):
    s = _safe_str(v).replace("'", "").strip()
    if not s:
        return pd.NaT

    if isinstance(v, (datetime.date, datetime.datetime, pd.Timestamp)):
        return pd.to_datetime(v, errors="coerce")

    formats = [
        "%d/%m/%Y", "%d/%m/%y",
        "%d-%m-%Y", "%d-%m-%y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d %b %Y", "%d %B %Y",
        "%B %y", "%b %y",
        "%B %Y", "%b %Y",
        "%Y-%m",
    ]

    for fmt in formats:
        try:
            return pd.Timestamp(datetime.datetime.strptime(s.title(), fmt))
        except Exception:
            pass

    try:
        return pd.to_datetime(s, dayfirst=True, errors="coerce")
    except Exception:
        return pd.NaT

def _month_key_label_from_date(date_val):
    dt = _parse_date(date_val)
    if pd.isna(dt):
        return "9999-99", "UNKNOWN"
    return dt.strftime("%Y-%m"), dt.strftime("%B %y").upper()

def _month_key_label_from_any(date_val=None, month_val=None):
    dt = _parse_date(date_val)
    if pd.notna(dt):
        return dt.strftime("%Y-%m"), dt.strftime("%B %y").upper()

    dt = _parse_date(month_val)
    if pd.notna(dt):
        return dt.strftime("%Y-%m"), dt.strftime("%B %y").upper()

    return "9999-99", "UNKNOWN"

def _month_label_from_key(month_key: str) -> str:
    try:
        return pd.Period(month_key, freq="M").to_timestamp().strftime("%B %y").upper()
    except Exception:
        return str(month_key or "").upper()

def _clean_email_list(v):
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return []

# ============================================================
# SUPABASE READ HELPERS
# ============================================================
@st.cache_data(ttl=180, show_spinner=False)
def _sb_select_all(table_name: str, order_col: str = "id") -> list[dict]:
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

        try:
            res = query.range(start, start + page_size - 1).execute()
        except Exception:
            # Fallback for tables without id/order column
            res = (
                supabase_client
                .table(table_name)
                .select("*")
                .range(start, start + page_size - 1)
                .execute()
            )

        batch = getattr(res, "data", None) or []
        rows.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    return rows

def _load_table(table_name: str, order_col: str = "id") -> pd.DataFrame:
    try:
        rows = _sb_select_all(table_name, order_col=order_col)
        df = pd.DataFrame(rows)
        if not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.warning(f"Could not load `{table_name}`: {e}")
        return pd.DataFrame()

bookings_df = _load_table(BOOKINGS_TABLE)
daily_df = _load_table(DAILY_VISITS_TABLE)
marketing_df = _load_table(MARKETING_TABLE)
holds_df = _load_table(HOLDS_TABLE)
master_df = _load_table(CASHFLOW_MASTER_TABLE)
sales_targets_df = _load_table(SALES_TARGETS_TABLE)

# ============================================================
# STYLES
# ============================================================
st.markdown(
    """
    <style>
    .ss-section-card{
        background: linear-gradient(135deg,#2563eb 0%,#7c3aed 100%);
        color: white;
        border-radius: 22px;
        padding: 24px 18px;
        text-align: center;
        margin: 34px 0 18px 0;
        box-shadow: 0 12px 28px rgba(37,99,235,.22);
    }
    .ss-section-card h2{
        margin: 0;
        font-size: 28px;
        font-weight: 950;
        letter-spacing: .01em;
    }
    .ss-section-card p{
        margin: 8px 0 0 0;
        font-size: 13px;
        font-weight: 700;
        opacity: .92;
    }
    .ss-kpi{
        background: linear-gradient(180deg, rgba(255,255,255,0.99), rgba(248,250,252,0.98));
        border: 1px solid rgba(49,51,63,0.10);
        border-radius: 16px;
        padding: 14px 12px;
        text-align: center;
        min-height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 6px 18px rgba(0,0,0,0.04);
        margin-bottom: 10px;
    }
    .ss-kpi h3{
        margin: 0 0 8px 0;
        font-size: 12.5px;
        line-height: 1.2;
        font-weight: 800;
        color: rgba(49,51,63,0.78);
        text-align: center;
    }
    .ss-kpi p{
        margin: 0;
        font-size: 25px;
        line-height: 1.08;
        font-weight: 900;
        color: #111827;
        text-align: center;
    }
    .ss-kpi span{
        display: block;
        margin-top: 8px;
        font-size: 11.5px;
        line-height: 1.25;
        font-weight: 700;
        color: rgba(49,51,63,0.65);
        text-align: center;
    }
    .ss-blue{background:#eff6ff;}
    .ss-green{background:#ecfdf5;}
    .ss-amber{background:#fff7ed;}
    .ss-rose{background:#fff1f2;}
    .ss-purple{background:#f5f3ff;}
    .ss-gray{background:#f8fafc;}

    .ss-table-wrap{
        overflow-x:auto;
        border:1px solid #dbe4f0;
        border-radius:14px;
        margin:10px 0 20px 0;
        box-shadow:0 5px 16px rgba(15,23,42,.05);
    }
    table.ss-table{
        width:100%;
        border-collapse:collapse;
        font-size:13px;
        background:#ffffff;
    }
    table.ss-table th{
        background:linear-gradient(135deg,#1d4ed8 0%,#4f46e5 100%);
        color:white;
        padding:10px;
        text-align:left;
        font-weight:900;
        white-space:nowrap;
    }
    table.ss-table td{
        padding:9px 10px;
        border-bottom:1px solid #e5e7eb;
        white-space:nowrap;
    }
    table.ss-table tr:nth-child(even){
        background:#f8fafc;
    }
    table.ss-table tr:hover{
        background:#eef2ff;
    }

    .target-card{
        border:1px solid #e2e8f0;
        border-radius:16px;
        padding:14px 16px;
        margin:10px 0;
        box-shadow:0 4px 14px rgba(15,23,42,.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

def section_card(title, subtitle=""):
    st.markdown(
        f"""
        <div class="ss-section-card">
            <h2>{escape(str(title))}</h2>
            <p>{escape(str(subtitle))}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def kpi_card(title, value, sub="", tone="ss-gray"):
    st.markdown(
        f"""
        <div class="ss-kpi {tone}">
            <h3>{escape(str(title))}</h3>
            <p>{escape(str(value))}</p>
            <span>{escape(str(sub))}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_table(df: pd.DataFrame, max_rows=None):
    if df is None or df.empty:
        st.info("No data available.")
        return

    show_df = df.copy()
    if max_rows:
        show_df = show_df.head(max_rows).copy()

    html = show_df.to_html(index=False, escape=False, classes="ss-table")
    st.markdown(f"<div class='ss-table-wrap'>{html}</div>", unsafe_allow_html=True)

# ============================================================
# INVENTORY MASTER CONFIG
# ============================================================
SERIES_TYPE_MAP = {
    "01": "2 BHK", "02": "2 BHK", "03": "2 BHK",
    "04": "1 BHK", "05": "1 BHK", "06": "1 BHK", "07": "1 BHK",
    "08": "2 BHK", "09": "2 BHK", "10": "2 BHK",
}

MHADA_RULES = {
    "B Wing": {"floors": {4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "C Wing": {"floors": {3, 4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "E Wing": {"floors": {4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "F Wing": {"floors": {3, 4, 5, 6}, "series": {"04", "05", "06", "07"}},
}

REFUGE_RULES = {
    "B Wing": {(7, "10"), (12, "10")},
    "C Wing": {(7, "10"), (12, "10")},
    "E Wing": {(7, "01"), (12, "01")},
    "F Wing": {(7, "01"), (12, "01")},
}

MISSING_UNITS = {
    ("B Wing", 1, "06"),
    ("C Wing", 1, "06"),
    ("E Wing", 1, "05"),
    ("F Wing", 1, "05"),
}

TYPE_OVERRIDES = {
    ("B Wing", 1, "07"): "2 BHK XL",
    ("C Wing", 1, "07"): "2 BHK XL",
    ("E Wing", 1, "04"): "2 BHK XL",
    ("F Wing", 1, "04"): "2 BHK XL",
}

LANDOWNER_FLATS = {
    "B Wing": {
        "102", "103", "110", "204", "205", "302", "303", "304", "305", "309", "310",
        "401", "402", "410", "509", "510", "610", "801", "803", "804",
        "910", "904", "1004", "1101", "1102", "1104", "1204", "1301", "1302", "1304",
    },
    "C Wing": {
        "103", "110", "301", "302", "303", "308", "309", "310",
        "408", "409", "603", "608", "609", "610", "703", "704", "707",
        "708", "806", "807", "808", "906", "907", "908", "1002",
        "1004", "1201", "1202", "1205", "1206", "1303", "1304",
        "1305", "1306",
    },
    "E Wing": {
        "103", "110", "302", "303", "304", "307", "309", "310",
        "401", "402", "403", "408", "409", "410", "501", "502",
        "503", "509", "510", "703", "704", "705", "706", "707",
        "805", "806", "901", "904", "905", "906", "907", "908",
    },
    "F Wing": {
        "102", "103", "110", "204", "205", "210", "302", "303",
        "309", "310", "501", "502", "509", "510", "610", "704",
        "801", "804", "810", "903", "904", "910", "1004", "1101",
        "1102", "1104", "1302",
    },
}

def _flat_number_from_floor_series(floor_no: int, series: str) -> str:
    return f"{floor_no}{series}"

def _base_category(wing: str, floor_no: int, series: str) -> str:
    if (wing, floor_no, series) in MISSING_UNITS:
        return "MISSING"

    if (floor_no, series) in REFUGE_RULES.get(wing, set()):
        return "REFUGE"

    mhada_rule = MHADA_RULES.get(wing, {"floors": set(), "series": set()})
    if floor_no in mhada_rule["floors"] and series in mhada_rule["series"]:
        return "MHADA"

    flat_no = _flat_number_from_floor_series(floor_no, series)
    if flat_no in LANDOWNER_FLATS.get(wing, set()):
        return "LANDOWNER"

    return "OUR"

def _unit_type_for_inventory(wing, floor_no, series, category):
    if category == "REFUGE":
        return "Refuge"
    if category == "MISSING":
        return ""
    return TYPE_OVERRIDES.get((wing, floor_no, series), SERIES_TYPE_MAP.get(series, ""))

def _build_inventory_master() -> pd.DataFrame:
    rows = []
    for wing in ["B Wing", "C Wing", "E Wing", "F Wing"]:
        for floor_no in range(1, 14):
            for series in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]:
                category = _base_category(wing, floor_no, series)
                flat_no = _flat_number_from_floor_series(floor_no, series)
                rows.append({
                    "Wing": wing,
                    "Floor No.": floor_no,
                    "Series": series,
                    "Flat Number": flat_no,
                    "Base Category": category,
                    "Type": _unit_type_for_inventory(wing, floor_no, series, category),
                })
    return pd.DataFrame(rows)

inventory_master_df = _build_inventory_master()

# ============================================================
# BOOKINGS PREP — MONTH FROM BOOKING DATE ONLY
# ============================================================
b_customer_col = _col(bookings_df, "customer_name", "Customer Name")
b_wing_col = _col(bookings_df, "wing", "Wing")
b_flat_col = _col(bookings_df, "flat_number", "Flat Number")
b_type_col = _col(bookings_df, "type", "unit_type", "Type")
b_rate_col = _col(bookings_df, "rate", "Rate")
b_agreement_cost_col = _col(bookings_df, "agreement_cost", "Agreement Cost")
b_sales_exec_col = _col(bookings_df, "sales_executive", "Sales Executive")
b_lead_col = _col(bookings_df, "lead_type", "Lead Type")
b_date_col = _col(bookings_df, "booking_date", "date", "Date")
b_stamp_col = _col(bookings_df, "stamp_duty", "Stamp Duty")
b_agreement_done_col = _col(bookings_df, "agreement_done", "Agreement Done")
b_received_col = _col(bookings_df, "received_amount", "Received Amount")
b_stamp_pct_col = _col(bookings_df, "stamp_duty_percent", "stamp_duty_pct", "Stamp Duty %")
b_carpet_col = _col(bookings_df, "carpet_area", "Carpet Area")
b_visit_count_col = _col(bookings_df, "visit_count", "Visit Count")
b_conversion_col = _col(bookings_df, "conversion_period_days", "Conversion Period (days)")

if not bookings_df.empty:
    bookings_work = bookings_df.copy()

    if b_date_col:
        bookings_work["_BookingDateObj"] = bookings_work[b_date_col].apply(_parse_date)
        bookings_work = bookings_work[
            bookings_work["_BookingDateObj"].notna() &
            (bookings_work["_BookingDateObj"] >= BOOKING_START_DATE)
        ].copy()
    else:
        bookings_work["_BookingDateObj"] = pd.NaT
        st.warning("Booking date column not found. Month-wise sections cannot be generated correctly.")

    bookings_work["_WingNorm"] = bookings_work[b_wing_col].apply(_norm_wing) if b_wing_col else ""
    bookings_work["_FlatNorm"] = bookings_work[b_flat_col].apply(_norm_flat) if b_flat_col else ""
    bookings_work["_SalesExecutive"] = (
        bookings_work[b_sales_exec_col].fillna("").astype(str).str.strip()
        if b_sales_exec_col else "Unknown"
    )
    bookings_work["_TypeNorm"] = (
        bookings_work[b_type_col].fillna("").astype(str).str.strip().str.upper().str.replace(" ", "", regex=False)
        if b_type_col else ""
    )
    bookings_work["_LeadType"] = (
        bookings_work[b_lead_col].fillna("").astype(str).str.strip()
        if b_lead_col else ""
    )

    month_pairs = bookings_work["_BookingDateObj"].apply(lambda x: _month_key_label_from_date(x))
    bookings_work["_MonthSort"] = [x[0] for x in month_pairs]
    bookings_work["_MonthLabel"] = [x[1] for x in month_pairs]

    bookings_work["_AgreementDone"] = bookings_work[b_agreement_done_col].apply(_is_agreement_done) if b_agreement_done_col else False
    bookings_work["_StampReceived"] = bookings_work[b_stamp_col].apply(_is_stamp_received) if b_stamp_col else False

    bookings_work["_AgreementCostNum"] = _num_series(bookings_work, b_agreement_cost_col) if b_agreement_cost_col else 0.0
    bookings_work["_ReceivedAmountNum"] = _num_series(bookings_work, b_received_col) if b_received_col else 0.0
    bookings_work["_RateNum"] = _num_series(bookings_work, b_rate_col) if b_rate_col else 0.0
    bookings_work["_CarpetNum"] = _num_series(bookings_work, b_carpet_col) if b_carpet_col else 0.0
    bookings_work["_VisitCountNum"] = _num_series(bookings_work, b_visit_count_col) if b_visit_count_col else 0.0
    bookings_work["_ConversionDaysNum"] = _num_series(bookings_work, b_conversion_col) if b_conversion_col else 0.0

    bookings_work["_StampPctNum"] = _num_series(bookings_work, b_stamp_pct_col) if b_stamp_pct_col else 7.0
    bookings_work.loc[bookings_work["_StampPctNum"] <= 0, "_StampPctNum"] = 7.0
    bookings_work["_StampDutyAmountEst"] = bookings_work["_AgreementCostNum"] * bookings_work["_StampPctNum"] / 100.0

    bookings_work["_PSF"] = bookings_work.apply(
        lambda r: _psf_from_agreement_carpet(
            r.get("_AgreementCostNum", 0),
            r.get("_CarpetNum", 0),
        ),
        axis=1,
    )

    def _type_for_appreciation(v):
        s = _safe_str(v).upper().replace(" ", "")
        if "1BHK" in s:
            return "1 BHK"
        if "2BHK" in s:
            return "2 BHK"
        return ""

    bookings_work["_TypeForAppreciation"] = bookings_work["_TypeNorm"].apply(_type_for_appreciation)

else:
    bookings_work = pd.DataFrame()

total_bookings = int(len(bookings_work))
sold_units_distinct = int(
    bookings_work[["_WingNorm", "_FlatNorm"]].drop_duplicates().shape[0]
) if not bookings_work.empty else 0

total_agreement_done = int(bookings_work["_AgreementDone"].sum()) if not bookings_work.empty else 0
total_agreement_pending = max(total_bookings - total_agreement_done, 0)

total_stamp_received = int(bookings_work["_StampReceived"].sum()) if not bookings_work.empty else 0
total_stamp_pending = max(total_bookings - total_stamp_received, 0)

total_agreement_value = float(bookings_work["_AgreementCostNum"].sum()) if not bookings_work.empty else 0.0
total_stamp_duty_amount_est = float(bookings_work["_StampDutyAmountEst"].sum()) if not bookings_work.empty else 0.0
total_received_booking = float(bookings_work["_ReceivedAmountNum"].sum()) if not bookings_work.empty else 0.0
total_carpet_area = float(bookings_work["_CarpetNum"].sum()) if not bookings_work.empty else 0.0
avg_psf_overall = _psf_from_agreement_carpet(total_agreement_value, total_carpet_area)
avg_visits_for_booking = float(bookings_work.loc[bookings_work["_VisitCountNum"] > 0, "_VisitCountNum"].mean()) if not bookings_work.empty else 0.0
avg_conversion_days = float(bookings_work.loc[bookings_work["_ConversionDaysNum"] > 0, "_ConversionDaysNum"].mean()) if not bookings_work.empty else 0.0

avg_booking_per_month = 0.0
if not bookings_work.empty:
    valid_month_count = bookings_work["_MonthSort"].replace("9999-99", pd.NA).dropna().nunique()
    avg_booking_per_month = total_bookings / valid_month_count if valid_month_count else 0.0

# ============================================================
# APPRECIATION LOGIC
# ============================================================
def _appreciation_summary(df: pd.DataFrame, unit_type: str | None = None) -> dict:
    if df is None or df.empty:
        return {
            "pct": 0.0,
            "lowest_month": "—",
            "highest_month": "—",
            "lowest_psf": 0.0,
            "highest_psf": 0.0,
        }

    d = df.copy()
    d = d[
        d["_AgreementCostNum"].gt(0)
        & d["_CarpetNum"].gt(0)
        & d["_MonthSort"].ne("9999-99")
    ].copy()

    if unit_type:
        d = d[d["_TypeForAppreciation"].eq(unit_type)].copy()

    if d.empty:
        return {
            "pct": 0.0,
            "lowest_month": "—",
            "highest_month": "—",
            "lowest_psf": 0.0,
            "highest_psf": 0.0,
        }

    monthly_avg = (
        d.groupby(["_MonthSort", "_MonthLabel"], as_index=False)
        .agg(
            _AgreementCostNum=("_AgreementCostNum", "sum"),
            _CarpetNum=("_CarpetNum", "sum"),
        )
        .sort_values("_MonthSort")
    )
    monthly_avg["_PSF"] = monthly_avg.apply(
        lambda r: _psf_from_agreement_carpet(
            r.get("_AgreementCostNum", 0),
            r.get("_CarpetNum", 0),
        ),
        axis=1,
    )

    if monthly_avg.empty:
        return {
            "pct": 0.0,
            "lowest_month": "—",
            "highest_month": "—",
            "lowest_psf": 0.0,
            "highest_psf": 0.0,
        }

    lowest_row = monthly_avg.loc[monthly_avg["_PSF"].idxmin()]
    highest_row = monthly_avg.loc[monthly_avg["_PSF"].idxmax()]

    lowest_psf = float(lowest_row["_PSF"])
    highest_psf = float(highest_row["_PSF"])

    appreciation_pct = ((highest_psf - lowest_psf) / lowest_psf * 100.0) if lowest_psf > 0 else 0.0

    return {
        "pct": appreciation_pct,
        "lowest_month": lowest_row["_MonthLabel"].title(),
        "highest_month": highest_row["_MonthLabel"].title(),
        "lowest_psf": lowest_psf,
        "highest_psf": highest_psf,
    }

app_1bhk = _appreciation_summary(bookings_work, "1 BHK")
app_2bhk = _appreciation_summary(bookings_work, "2 BHK")
app_overall = _appreciation_summary(bookings_work, None)

# ============================================================
# HOLDS / AGREEMENT LINEUP
# ============================================================
h_wing_col = _col(holds_df, "wing", "Wing")
h_flat_col = _col(holds_df, "flat_number", "Flat Number")
h_hold_by_col = _col(holds_df, "hold_by", "Hold By")
h_hold_from_col = _col(holds_df, "hold_from", "Hold From")
h_hold_till_col = _col(holds_df, "hold_till", "Hold Till")
h_entry_type_col = _col(holds_df, "entry_type", "Entry Type")
h_lineup_by_col = _col(holds_df, "agreement_lineup_by", "Agreement Lineup By")
h_lineup_date_col = _col(holds_df, "agreement_lineup_date", "Agreement Lineup Date")

if not holds_df.empty:
    holds_work = holds_df.copy()
    holds_work["_WingNorm"] = holds_work[h_wing_col].apply(_norm_wing) if h_wing_col else ""
    holds_work["_FlatNorm"] = holds_work[h_flat_col].apply(_norm_flat) if h_flat_col else ""
    holds_work["_EntryType"] = (
        holds_work[h_entry_type_col].fillna("").astype(str).str.strip().str.upper()
        if h_entry_type_col else ""
    )
    holds_work["_HoldTill"] = holds_work[h_hold_till_col].apply(_parse_date) if h_hold_till_col else pd.NaT
    holds_work["_HoldFrom"] = holds_work[h_hold_from_col].apply(_parse_date) if h_hold_from_col else pd.NaT
    holds_work["_LineupDate"] = holds_work[h_lineup_date_col].apply(_parse_date) if h_lineup_date_col else pd.NaT

    blank_type = holds_work["_EntryType"].eq("")
    if h_hold_by_col:
        holds_work.loc[
            blank_type & holds_work[h_hold_by_col].fillna("").astype(str).str.strip().ne(""),
            "_EntryType"
        ] = "HOLD"
    if h_lineup_by_col:
        holds_work.loc[
            blank_type & holds_work[h_lineup_by_col].fillna("").astype(str).str.strip().ne(""),
            "_EntryType"
        ] = "AGREEMENT_LINEUP"

    active_holds_df = holds_work[
        holds_work["_EntryType"].eq("HOLD") &
        holds_work["_WingNorm"].ne("") &
        holds_work["_FlatNorm"].ne("") &
        holds_work["_HoldTill"].notna() &
        (holds_work["_HoldTill"] >= TODAY)
    ].copy()

    active_holds_df = (
        active_holds_df
        .sort_values(["_WingNorm", "_FlatNorm", "_HoldTill"])
        .drop_duplicates(subset=["_WingNorm", "_FlatNorm"], keep="last")
    )

    lineup_df = holds_work[
        holds_work["_EntryType"].eq("AGREEMENT_LINEUP") &
        holds_work["_WingNorm"].ne("") &
        holds_work["_FlatNorm"].ne("")
    ].copy()

    lineup_df = (
        lineup_df
        .sort_values(["_WingNorm", "_FlatNorm", "_LineupDate"], na_position="last")
        .drop_duplicates(subset=["_WingNorm", "_FlatNorm"], keep="last")
    )
else:
    active_holds_df = pd.DataFrame(columns=["_WingNorm", "_FlatNorm"])
    lineup_df = pd.DataFrame(columns=["_WingNorm", "_FlatNorm"])

active_hold_count = int(active_holds_df[["_WingNorm", "_FlatNorm"]].drop_duplicates().shape[0]) if not active_holds_df.empty else 0
agreement_lineup_count = int(lineup_df[["_WingNorm", "_FlatNorm"]].drop_duplicates().shape[0]) if not lineup_df.empty else 0

# ============================================================
# INVENTORY / PSF SUMMARY
# ============================================================
inv = inventory_master_df.copy()

sold_keys = set()
if not bookings_work.empty:
    sold_keys = set(
        tuple(x)
        for x in bookings_work[["_WingNorm", "_FlatNorm"]]
        .dropna()
        .drop_duplicates()
        .values
    )

hold_keys = set()
if not active_holds_df.empty:
    hold_keys = set(
        tuple(x)
        for x in active_holds_df[["_WingNorm", "_FlatNorm"]]
        .dropna()
        .drop_duplicates()
        .values
    )

lineup_keys = set()
if not lineup_df.empty:
    lineup_keys = set(
        tuple(x)
        for x in lineup_df[["_WingNorm", "_FlatNorm"]]
        .dropna()
        .drop_duplicates()
        .values
    )

inv["_Key"] = list(zip(inv["Wing"], inv["Flat Number"]))
inv["_IsSold"] = inv["_Key"].isin(sold_keys)
inv["_IsHold"] = inv["_Key"].isin(hold_keys)
inv["_IsLineup"] = inv["_Key"].isin(lineup_keys)

total_project_units = int(inv[~inv["Base Category"].isin(["MISSING", "REFUGE"])].shape[0])
total_our_inventory = int(inv[inv["Base Category"].eq("OUR")].shape[0])
our_sold_units = int(inv[inv["Base Category"].eq("OUR") & inv["_IsSold"]].shape[0])
our_hold_units = int(inv[inv["Base Category"].eq("OUR") & (~inv["_IsSold"]) & inv["_IsHold"]].shape[0])
our_available_units = max(total_our_inventory - our_sold_units - our_hold_units, 0)

if not bookings_work.empty:
    psf_source_df = bookings_work[
        bookings_work["_AgreementCostNum"].gt(0) &
        bookings_work["_CarpetNum"].gt(0)
    ].copy()

    wing_psf_df = (
        psf_source_df
        .groupby("_WingNorm", as_index=False)
        .agg(
            _AgreementCostNum=("_AgreementCostNum", "sum"),
            _CarpetNum=("_CarpetNum", "sum"),
        )
        .rename(columns={"_WingNorm": "Wing"})
        .sort_values("Wing")
    )
    wing_psf_df["Avg PSF"] = wing_psf_df.apply(
        lambda r: _psf_from_agreement_carpet(r["_AgreementCostNum"], r["_CarpetNum"]),
        axis=1,
    )
    wing_psf_df = wing_psf_df[["Wing", "Avg PSF"]]

    type_psf_df = (
        psf_source_df
        .groupby("_TypeForAppreciation", as_index=False)
        .agg(
            _AgreementCostNum=("_AgreementCostNum", "sum"),
            _CarpetNum=("_CarpetNum", "sum"),
        )
        .rename(columns={"_TypeForAppreciation": "Type"})
        .sort_values("Type")
    )
    type_psf_df["Avg PSF"] = type_psf_df.apply(
        lambda r: _psf_from_agreement_carpet(r["_AgreementCostNum"], r["_CarpetNum"]),
        axis=1,
    )
    type_psf_df = type_psf_df[type_psf_df["Type"].ne("")][["Type", "Avg PSF"]].copy()

    wing_type_psf_df = (
        psf_source_df
        .groupby(["_WingNorm", "_TypeForAppreciation"], as_index=False)
        .agg(
            _AgreementCostNum=("_AgreementCostNum", "sum"),
            _CarpetNum=("_CarpetNum", "sum"),
        )
        .rename(columns={"_WingNorm": "Wing", "_TypeForAppreciation": "Type"})
        .sort_values(["Wing", "Type"])
    )
    wing_type_psf_df["Avg PSF"] = wing_type_psf_df.apply(
        lambda r: _psf_from_agreement_carpet(r["_AgreementCostNum"], r["_CarpetNum"]),
        axis=1,
    )
    wing_type_psf_df = wing_type_psf_df[wing_type_psf_df["Type"].ne("")][["Wing", "Type", "Avg PSF"]].copy()
else:
    wing_psf_df = pd.DataFrame(columns=["Wing", "Avg PSF"])
    type_psf_df = pd.DataFrame(columns=["Type", "Avg PSF"])
    wing_type_psf_df = pd.DataFrame(columns=["Wing", "Type", "Avg PSF"])

wing_inventory_rows = []
for wing in ["B Wing", "C Wing", "E Wing", "F Wing"]:
    wdf = inv[inv["Wing"].eq(wing)].copy()
    our_wdf = wdf[wdf["Base Category"].eq("OUR")].copy()

    sold = int(our_wdf["_IsSold"].sum())
    hold = int((~our_wdf["_IsSold"] & our_wdf["_IsHold"]).sum())
    lineup = int((our_wdf["_IsLineup"]).sum())
    total_our = int(len(our_wdf))
    available = max(total_our - sold - hold, 0)

    psf_val = 0.0
    if not wing_psf_df.empty and wing in set(wing_psf_df["Wing"]):
        psf_val = float(wing_psf_df.loc[wing_psf_df["Wing"].eq(wing), "Avg PSF"].iloc[0])

    wing_inventory_rows.append({
        "Wing": wing,
        "Our Inventory": total_our,
        "Units Sold": sold,
        "Units Hold": hold,
        "Agreement Lineup": lineup,
        "Units Left to Sell": available,
        "Sold %": _pct(sold, total_our),
        "Avg PSF": psf_val,
    })

wing_inventory_df = pd.DataFrame(wing_inventory_rows)

# ============================================================
# MARKETING SUMMARY
# ============================================================
RECURRING_PURPOSES = {
    "hoarding", "digital marketing", "print advertisement", "radio advertisement",
    "event sponsorship", "kaman", "refreshment", "housekeeping", "garden maintenance",
    "channel partner", "fos", "referral", "wifi bill", "light bill",
    "mobile internet and recharge", "office rent", "site maintenance",
}

m_amount_col = _col(marketing_df, "amount", "Amount")
m_purpose_col = _col(marketing_df, "purpose", "Purpose")
m_vendor_col = _col(marketing_df, "vendor", "Vendor")
m_month_col = _col(marketing_df, "month", "Month")
m_date_col = _col(marketing_df, "expense_date", "Date", "date")

if not marketing_df.empty:
    marketing_work = marketing_df.copy()
    marketing_work["_AmountNum"] = _num_series(marketing_work, m_amount_col) if m_amount_col else 0.0

    month_pairs = marketing_work.apply(
        lambda r: _month_key_label_from_any(
            r.get(m_date_col, "") if m_date_col else "",
            r.get(m_month_col, "") if m_month_col else ""
        ),
        axis=1
    )
    marketing_work["_MonthSort"] = [x[0] for x in month_pairs]
    marketing_work["_MonthLabel"] = [x[1] for x in month_pairs]
    marketing_work["_PurposeNorm"] = (
        marketing_work[m_purpose_col].fillna("").astype(str).str.strip().str.casefold()
        if m_purpose_col else ""
    )
else:
    marketing_work = pd.DataFrame()

total_marketing_spend = float(marketing_work["_AmountNum"].sum()) if not marketing_work.empty else 0.0
this_month_marketing_spend = float(
    marketing_work.loc[marketing_work["_MonthSort"].eq(THIS_MONTH_KEY), "_AmountNum"].sum()
) if not marketing_work.empty else 0.0

recurring_marketing_spend = float(
    marketing_work.loc[marketing_work["_PurposeNorm"].isin(RECURRING_PURPOSES), "_AmountNum"].sum()
) if not marketing_work.empty else 0.0

marketing_spend_pct_agreement = _pct(total_marketing_spend, total_agreement_value)
recurring_spend_pct_agreement = _pct(recurring_marketing_spend, total_agreement_value)
marketing_cost_per_booking = total_marketing_spend / total_bookings if total_bookings else 0.0
recurring_cost_per_booking = recurring_marketing_spend / total_bookings if total_bookings else 0.0
marketing_spend_per_sqft = (total_marketing_spend / total_carpet_area * 1.38) if total_carpet_area else 0.0
recurring_spend_per_sqft = (recurring_marketing_spend / total_carpet_area * 1.38) if total_carpet_area else 0.0

if not marketing_work.empty:
    monthly_marketing_df = (
        marketing_work
        .groupby(["_MonthSort", "_MonthLabel"], as_index=False)["_AmountNum"]
        .sum()
        .rename(columns={"_MonthLabel": "Month", "_AmountNum": "Marketing Spend"})
        .sort_values("_MonthSort")
    )
    monthly_marketing_df = monthly_marketing_df[monthly_marketing_df["_MonthSort"].ne("9999-99")].copy()

    purpose_marketing_df = (
        marketing_work
        .assign(Purpose=marketing_work[m_purpose_col] if m_purpose_col else "")
        .groupby("Purpose", as_index=False)["_AmountNum"]
        .sum()
        .rename(columns={"_AmountNum": "Amount"})
        .sort_values("Amount", ascending=False)
    )
else:
    monthly_marketing_df = pd.DataFrame(columns=["_MonthSort", "Month", "Marketing Spend"])
    purpose_marketing_df = pd.DataFrame(columns=["Purpose", "Amount"])

# ============================================================
# DAILY VISITS SUMMARY
# ============================================================
dv_total_visits_col = _col(daily_df, "total_visits", "Total Visits")
dv_total_revisits_col = _col(daily_df, "total_revisits", "Total Revisits", "revisit", "Revisit")
dv_total_attended_col = _col(daily_df, "total_attended", "Total Attended")
dv_calls_ans_col = _col(daily_df, "total_calls_answered", "Total Calls Answered")
dv_calls_unans_col = _col(daily_df, "total_calls_unanswered", "Total Calls Unanswered")
dv_booking_col = _col(daily_df, "todays_booking", "today_booking", "Today's Booking")
dv_month_col = _col(daily_df, "month", "Month")
dv_date_col = _col(daily_df, "visit_date", "Date", "date")

source_cols = [
    _col(daily_df, "cp_visits", "CP Visits"),
    _col(daily_df, "direct_walk_in", "Direct Walk-in"),
    _col(daily_df, "references_count", "References"),
    _col(daily_df, "digital", "Digital"),
    _col(daily_df, "newspaper", "Newspaper"),
]
source_cols = [c for c in source_cols if c]

def _sum_col(df, col):
    if df is None or df.empty or not col:
        return 0.0
    return float(_num_series(df, col).sum())

total_revisits = _sum_col(daily_df, dv_total_revisits_col)
total_attended = _sum_col(daily_df, dv_total_attended_col)
total_calls_answered = _sum_col(daily_df, dv_calls_ans_col)
total_calls_unanswered = _sum_col(daily_df, dv_calls_unans_col)

if daily_df.empty:
    total_visits = 0.0
elif dv_total_visits_col:
    total_visits = _sum_col(daily_df, dv_total_visits_col)
else:
    total_visits = sum(_sum_col(daily_df, c) for c in source_cols) + total_revisits

total_calls = total_calls_answered + total_calls_unanswered
total_daily_bookings = _sum_col(daily_df, dv_booking_col)

call_answer_rate = _pct(total_calls_answered, total_calls)
visit_to_booking_pct = _pct(total_bookings, total_visits)
calls_to_visits_pct = _pct(total_attended, total_calls)
revisit_to_visit_pct = _pct(total_revisits, total_visits)

# ============================================================
# SALES EXECUTIVE PERFORMANCE
# ============================================================
KNOWN_EXECUTIVES = [
    "Alok R", "Tejas P", "Ashutosh S", "Sagar B",
    "Harshal S", "Komal K", "Sailee D", "Advait M",
    "Dhanashree W",
]

if not bookings_work.empty:
    booking_exec_names = [
        x for x in bookings_work["_SalesExecutive"].dropna().astype(str).str.strip().unique().tolist()
        if x
    ]
else:
    booking_exec_names = []

all_execs = sorted(set(KNOWN_EXECUTIVES + booking_exec_names))

def _exec_key(name):
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")

def _sum_exec_metric(df, exec_name, metric_names):
    if df is None or df.empty:
        return 0.0

    key = _exec_key(exec_name)
    possible = []

    for metric in metric_names:
        metric_key = _exec_key(metric)
        possible.extend([
            f"{key}_{metric_key}",
            f"{exec_name} {metric}",
            f"{exec_name} {metric.title()}",
            f"{exec_name} {metric.upper()}",
        ])

    for p in possible:
        c = _col(df, p)
        if c:
            return float(_num_series(df, c).sum())

    return 0.0

exec_rows = []
for exec_name in all_execs:
    attended = _sum_exec_metric(daily_df, exec_name, ["attended"])
    revisits = _sum_exec_metric(daily_df, exec_name, ["revisits", "revisit"])
    answered = _sum_exec_metric(daily_df, exec_name, ["calls_answered", "calls answered"])
    unanswered = _sum_exec_metric(daily_df, exec_name, ["calls_unanswered", "calls unanswered"])
    calls = answered + unanswered

    bookings_count = 0
    if not bookings_work.empty:
        bookings_count = int(
            bookings_work["_SalesExecutive"]
            .astype(str)
            .str.strip()
            .str.casefold()
            .eq(exec_name.casefold())
            .sum()
        )

    if bookings_count == 0 and attended == 0 and revisits == 0 and calls == 0:
        continue

    exec_rows.append({
        "Sales Executive": exec_name,
        "Bookings": bookings_count,
        "Attended Visits": int(attended),
        "Revisits": int(revisits),
        "Total Calls": int(calls),
        "Calls Answered": int(answered),
        "Calls Unanswered": int(unanswered),
        "Call Answer %": _pct(answered, calls),
        "Calls → Visits %": _pct(attended, calls),
        "Visits → Revisits %": _pct(revisits, attended),
        "Visits → Bookings %": _pct(bookings_count, attended),
        "Calls → Bookings %": _pct(bookings_count, calls),
    })

exec_summary_df = (
    pd.DataFrame(exec_rows)
    .sort_values(["Bookings", "Attended Visits", "Total Calls"], ascending=False)
    .reset_index(drop=True)
    if exec_rows else
    pd.DataFrame(columns=[
        "Sales Executive", "Bookings", "Attended Visits", "Revisits", "Total Calls",
        "Calls Answered", "Calls Unanswered", "Call Answer %", "Calls → Visits %",
        "Visits → Revisits %", "Visits → Bookings %", "Calls → Bookings %"
    ])
)

if not bookings_work.empty:
    exec_psf_df = (
        bookings_work[
            bookings_work["_SalesExecutive"].astype(str).str.strip().ne("") &
            bookings_work["_AgreementCostNum"].gt(0) &
            bookings_work["_CarpetNum"].gt(0)
        ]
        .groupby("_SalesExecutive", as_index=False)
        .agg(
            _AgreementCostNum=("_AgreementCostNum", "sum"),
            _CarpetNum=("_CarpetNum", "sum"),
        )
        .rename(columns={"_SalesExecutive": "Sales Executive"})
    )
    exec_psf_df["Avg PSF"] = exec_psf_df.apply(
        lambda r: _psf_from_agreement_carpet(r["_AgreementCostNum"], r["_CarpetNum"]),
        axis=1,
    )
    exec_psf_df = (
        exec_psf_df[["Sales Executive", "Avg PSF"]]
        .sort_values("Avg PSF", ascending=False)
        .reset_index(drop=True)
    )

    exec_conversion_days_df = (
        bookings_work[
            bookings_work["_SalesExecutive"].astype(str).str.strip().ne("") &
            bookings_work["_ConversionDaysNum"].gt(0)
        ]
        .groupby("_SalesExecutive", as_index=False)["_ConversionDaysNum"]
        .mean()
        .rename(columns={"_SalesExecutive": "Sales Executive", "_ConversionDaysNum": "Avg Conversion Days"})
        .sort_values("Avg Conversion Days")
        .reset_index(drop=True)
    )
else:
    exec_psf_df = pd.DataFrame(columns=["Sales Executive", "Avg PSF"])
    exec_conversion_days_df = pd.DataFrame(columns=["Sales Executive", "Avg Conversion Days"])

if not daily_df.empty:
    dv_work = daily_df.copy()
    month_pairs = dv_work.apply(
        lambda r: _month_key_label_from_any(
            r.get(dv_date_col, "") if dv_date_col else "",
            r.get(dv_month_col, "") if dv_month_col else ""
        ),
        axis=1
    )
    dv_work["_MonthSort"] = [x[0] for x in month_pairs]
    dv_work["_MonthLabel"] = [x[1] for x in month_pairs]
    dv_work["_TotalVisits"] = _num_series(dv_work, dv_total_visits_col) if dv_total_visits_col else 0.0
    dv_work["_TotalRevisits"] = _num_series(dv_work, dv_total_revisits_col) if dv_total_revisits_col else 0.0
    dv_work["_CallsAnswered"] = _num_series(dv_work, dv_calls_ans_col) if dv_calls_ans_col else 0.0
    dv_work["_CallsUnanswered"] = _num_series(dv_work, dv_calls_unans_col) if dv_calls_unans_col else 0.0
    dv_work["_TotalCalls"] = dv_work["_CallsAnswered"] + dv_work["_CallsUnanswered"]

    monthly_visit_call_df = (
        dv_work
        .groupby(["_MonthSort", "_MonthLabel"], as_index=False)
        .agg({
            "_TotalVisits": "sum",
            "_TotalRevisits": "sum",
            "_TotalCalls": "sum",
        })
        .rename(columns={
            "_MonthLabel": "Month",
            "_TotalVisits": "Total Visits",
            "_TotalRevisits": "Total Revisits",
            "_TotalCalls": "Total Calls",
        })
        .sort_values("_MonthSort")
    )
    monthly_visit_call_df = monthly_visit_call_df[monthly_visit_call_df["_MonthSort"].ne("9999-99")].copy()
else:
    monthly_visit_call_df = pd.DataFrame(columns=["_MonthSort", "Month", "Total Visits", "Total Revisits", "Total Calls"])

# ============================================================
# CASHFLOW / CURRENT STAGE FROM CASHFLOW SLAB MASTER
# ============================================================
CONSTRUCTION_SLABS = [
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

cm_wing_col = _col(master_df, "wing", "Wing")
cm_slab_col = _col(master_df, "slab_name", "Slab Name")
cm_completed_col = _col(master_df, "completed", "Completed")
cm_completed_on_col = _col(master_df, "completed_on", "Completed On")

if not master_df.empty:
    master_work = master_df.copy()
    master_work["_WingNorm"] = master_work[cm_wing_col].apply(_norm_wing) if cm_wing_col else ""
    master_work["_SlabNorm"] = (
        master_work[cm_slab_col].fillna("").astype(str).str.strip().str.upper()
        if cm_slab_col else ""
    )
    master_work["_Completed"] = (
        master_work[cm_completed_col].fillna("").astype(str).str.strip().str.lower().isin(["completed", "done", "yes"])
        if cm_completed_col else False
    )
    master_work["_CompletedOn"] = master_work[cm_completed_on_col].apply(_parse_date) if cm_completed_on_col else pd.NaT
else:
    master_work = pd.DataFrame()

def _highest_completed_slab(wing):
    if master_work.empty:
        return None

    sub = master_work[
        master_work["_WingNorm"].astype(str).str.strip().str.upper() ==
        _norm_wing(wing).upper()
    ].copy()

    completed_set = set(sub.loc[sub["_Completed"], "_SlabNorm"].tolist())

    highest = None
    for slab in CONSTRUCTION_SLABS:
        if slab.upper() in completed_set:
            highest = slab

    return highest

def _highest_completed_on(wing, slab):
    if master_work.empty or not slab:
        return ""
    sub = master_work[
        master_work["_WingNorm"].astype(str).str.upper().eq(_norm_wing(wing).upper()) &
        master_work["_SlabNorm"].astype(str).str.upper().eq(str(slab).upper()) &
        master_work["_Completed"]
    ].copy()
    if sub.empty:
        return ""
    dt = sub["_CompletedOn"].dropna()
    if dt.empty:
        return ""
    return pd.to_datetime(dt.max()).strftime("%d/%m/%Y")

def _gst_rate(agreement_cost):
    return 0.05 if _to_num(agreement_cost) > 4499999 else 0.01

def _gross_agreement_value(agreement_cost):
    agr = _to_num(agreement_cost)
    gst_amt = round(agr * _gst_rate(agr), 2)
    return round(agr + gst_amt, 2), gst_amt

def _head_amounts(agreement_cost):
    gross_value, gst_amt = _gross_agreement_value(agreement_cost)
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

def _due_order_for_booking(row):
    order = ["BOOKING AMOUNT"]

    if bool(row.get("_AgreementDone", False)):
        order.append("AGREEMENT")
        highest = _highest_completed_slab(row.get("_WingNorm", ""))
        if highest is not None:
            upto = CONSTRUCTION_SLABS.index(highest)
            order.extend(CONSTRUCTION_SLABS[:upto + 1])

    return order

def _customer_collection_summary(row):
    amt_map = _head_amounts(row.get("_AgreementCostNum", 0))
    due_order = _due_order_for_booking(row)
    collection_till = sum(_to_num(amt_map.get(h, 0)) for h in due_order)
    received_till = _to_num(row.get("_ReceivedAmountNum", 0))
    due_till = max(collection_till - received_till, 0.0)

    return {
        "Collection Till Date": collection_till,
        "Received Till Date": received_till,
        "Due Till Date": due_till,
        "Received %": _pct(received_till, collection_till),
        "Due %": _pct(due_till, collection_till),
    }

if not bookings_work.empty:
    wing_rows = []
    for wing, sub in bookings_work.groupby("_WingNorm"):
        if not wing:
            continue

        collection = 0.0
        received = 0.0

        for _, r in sub.iterrows():
            sm = _customer_collection_summary(r)
            collection += sm["Collection Till Date"]
            received += sm["Received Till Date"]

        due = max(collection - received, 0.0)
        stage = _highest_completed_slab(wing) or "Booking / Agreement Stage"

        wing_rows.append({
            "Wing": wing,
            "Bookings": int(len(sub)),
            "Current Stage": stage,
            "Stage Completed On": _highest_completed_on(wing, stage),
            "Collection Till Date": collection,
            "Received Till Date": received,
            "Due Till Date": due,
            "Received %": _pct(received, collection),
            "Due %": _pct(due, collection),
        })

    wing_summary_df = pd.DataFrame(wing_rows).sort_values("Wing").reset_index(drop=True)
else:
    wing_summary_df = pd.DataFrame(columns=[
        "Wing", "Bookings", "Current Stage", "Stage Completed On",
        "Collection Till Date", "Received Till Date", "Due Till Date",
        "Received %", "Due %"
    ])

total_collection = float(wing_summary_df["Collection Till Date"].sum()) if not wing_summary_df.empty else 0.0
total_cashflow_received = float(wing_summary_df["Received Till Date"].sum()) if not wing_summary_df.empty else 0.0
total_cashflow_due = float(wing_summary_df["Due Till Date"].sum()) if not wing_summary_df.empty else 0.0
total_cashflow_due_pct = _pct(total_cashflow_due, total_collection)
total_cashflow_received_pct = _pct(total_cashflow_received, total_collection)

# ============================================================
# MONTHLY BOOKING + SEPARATE PENDING TABLES
# ============================================================
if not bookings_work.empty:
    monthly_bookings_df = (
        bookings_work
        .groupby(["_MonthSort", "_MonthLabel"], as_index=False)
        .size()
        .rename(columns={"_MonthLabel": "Month", "size": "Bookings"})
        .sort_values("_MonthSort")
    )
    monthly_bookings_df = monthly_bookings_df[monthly_bookings_df["_MonthSort"].ne("9999-99")].copy()
    month_sort_order = monthly_bookings_df["Month"].tolist()

    stamp_pending_rows = bookings_work[~bookings_work["_StampReceived"]].copy()
    agreement_pending_rows = bookings_work[~bookings_work["_AgreementDone"]].copy()

    if not stamp_pending_rows.empty:
        stamp_pending_month_exec_df = (
            stamp_pending_rows
            .groupby(["_MonthSort", "_MonthLabel", "_SalesExecutive"], as_index=False)
            .size()
            .rename(columns={
                "_MonthLabel": "Month",
                "_SalesExecutive": "Sales Executive",
                "size": "Stamp Duty Pending Count",
            })
            .sort_values(["_MonthSort", "Sales Executive"])
            .drop(columns=["_MonthSort"])
            .reset_index(drop=True)
        )
    else:
        stamp_pending_month_exec_df = pd.DataFrame(columns=[
            "Month", "Sales Executive", "Stamp Duty Pending Count"
        ])

    if not agreement_pending_rows.empty:
        agreement_pending_month_exec_df = (
            agreement_pending_rows
            .groupby(["_MonthSort", "_MonthLabel", "_SalesExecutive"], as_index=False)
            .size()
            .rename(columns={
                "_MonthLabel": "Month",
                "_SalesExecutive": "Sales Executive",
                "size": "Agreement Not Done Pending Count",
            })
            .sort_values(["_MonthSort", "Sales Executive"])
            .drop(columns=["_MonthSort"])
            .reset_index(drop=True)
        )
    else:
        agreement_pending_month_exec_df = pd.DataFrame(columns=[
            "Month", "Sales Executive", "Agreement Not Done Pending Count"
        ])
else:
    monthly_bookings_df = pd.DataFrame(columns=["_MonthSort", "Month", "Bookings"])
    month_sort_order = []
    stamp_pending_month_exec_df = pd.DataFrame(columns=[
        "Month", "Sales Executive", "Stamp Duty Pending Count"
    ])
    agreement_pending_month_exec_df = pd.DataFrame(columns=[
        "Month", "Sales Executive", "Agreement Not Done Pending Count"
    ])

# ============================================================
# SALES TARGETS
# ============================================================
def _target_exec_label(col_name: str) -> str:
    raw = _safe_str(col_name)

    known_map = {
        "alokr": "Alok R",
        "tejasp": "Tejas P",
        "ashutoshs": "Ashutosh S",
        "sagarb": "Sagar B",
        "harshals": "Harshal S",
        "komalk": "Komal K",
        "saileed": "Sailee D",
        "advaitm": "Advait M",
        "dhanashreew": "Dhanashree W"
    }

    n = _norm_col(raw)
    if n in known_map:
        return known_map[n]

    for known in KNOWN_EXECUTIVES:
        if _norm_col(known) == n:
            return known

    return raw.replace("_", " ").title()

def _prepare_sales_targets(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    month_col = _col(out, "month", "Month")
    if not month_col:
        return pd.DataFrame()

    month_pairs = out[month_col].apply(lambda x: _month_key_label_from_any("", x))
    out["_TargetMonthSort"] = [x[0] for x in month_pairs]
    out["_TargetMonthLabel"] = [x[1] for x in month_pairs]

    return out

targets_work = _prepare_sales_targets(sales_targets_df)

def _get_target_row(targets_df: pd.DataFrame, month_key: str):
    if targets_df is None or targets_df.empty:
        return None

    hit = targets_df[targets_df["_TargetMonthSort"].eq(month_key)].copy()
    if hit.empty:
        return None

    return hit.iloc[-1]

def _sales_target_columns(targets_df: pd.DataFrame) -> list[str]:
    if targets_df is None or targets_df.empty:
        return []

    ignore_norms = {
        _norm_col("id"),
        _norm_col("created_at"),
        _norm_col("month"),
        _norm_col("_TargetMonthSort"),
        _norm_col("_TargetMonthLabel"),
    }

    cols = []
    for c in targets_df.columns:
        if _norm_col(c) not in ignore_norms:
            cols.append(c)

    return cols

def _target_achievement_table(month_key: str, next_key: str) -> pd.DataFrame:
    target_cols = _sales_target_columns(targets_work)

    if not target_cols:
        return pd.DataFrame(columns=[
            "Sales Executive",
            "This Month Target",
            "Achieved",
            "Pending",
            "Achievement %",
            "Next Month Target",
            "Status",
        ])

    current_row = _get_target_row(targets_work, month_key)
    next_row = _get_target_row(targets_work, next_key)

    if not bookings_work.empty:
        achieved_df = bookings_work[bookings_work["_MonthSort"].eq(month_key)].copy()
        achieved_map = (
            achieved_df["_SalesExecutive"]
            .fillna("")
            .astype(str)
            .str.strip()
            .map(_norm_col)
            .value_counts()
            .to_dict()
        )
    else:
        achieved_map = {}

    rows = []

    for col_name in target_cols:
        exec_name = _target_exec_label(col_name)
        exec_key = _norm_col(exec_name)

        this_target = _to_num(current_row.get(col_name, 0)) if current_row is not None else 0.0
        next_target = _to_num(next_row.get(col_name, 0)) if next_row is not None else 0.0

        achieved = float(achieved_map.get(exec_key, 0))
        pending = max(this_target - achieved, 0.0)
        achievement_pct = _pct(achieved, this_target)

        if this_target <= 0:
            status = "No Target"
        elif achieved >= this_target:
            status = "Achieved"
        elif achievement_pct >= 75:
            status = "On Track"
        else:
            status = "Pending"

        if this_target <= 0 and achieved <= 0 and next_target <= 0:
            continue

        rows.append({
            "Sales Executive": exec_name,
            "This Month Target": int(this_target),
            "Achieved": int(achieved),
            "Pending": int(pending),
            "Achievement %": round(achievement_pct, 1),
            "Next Month Target": int(next_target),
            "Status": status,
        })

    return pd.DataFrame(rows).sort_values(
        ["Achievement %", "Achieved"],
        ascending=False
    ).reset_index(drop=True)

target_achievement_df = _target_achievement_table(THIS_MONTH_KEY, NEXT_MONTH_KEY)

total_this_month_target = int(target_achievement_df["This Month Target"].sum()) if not target_achievement_df.empty else 0
total_this_month_achieved = int(target_achievement_df["Achieved"].sum()) if not target_achievement_df.empty else 0
total_this_month_pending = max(total_this_month_target - total_this_month_achieved, 0)
total_next_month_target = int(target_achievement_df["Next Month Target"].sum()) if not target_achievement_df.empty else 0
total_target_achievement_pct = _pct(total_this_month_achieved, total_this_month_target)

# ============================================================
# CHART HELPERS WITH LABELS
# ============================================================
def bar_chart_with_labels(df, x, y, title, x_sort=None, height=330):
    base = alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{x}:N", sort=x_sort, title=x),
        y=alt.Y(f"{y}:Q", title=y),
        tooltip=[alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{y}:Q", format=",")]
    )

    labels = alt.Chart(df).mark_text(
        dy=-7,
        fontSize=11,
        fontWeight="bold"
    ).encode(
        x=alt.X(f"{x}:N", sort=x_sort),
        y=alt.Y(f"{y}:Q"),
        text=alt.Text(f"{y}:Q", format=",.0f")
    )

    return (base + labels).properties(height=height, title=title)

def line_chart_with_labels(df, x, y, title, x_sort=None, height=340):
    line = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X(f"{x}:N", sort=x_sort, title=x),
        y=alt.Y(f"{y}:Q", title=y),
        tooltip=[alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{y}:Q", format=",")]
    )

    labels = alt.Chart(df).mark_text(
        dy=-10,
        fontSize=11,
        fontWeight="bold"
    ).encode(
        x=alt.X(f"{x}:N", sort=x_sort),
        y=alt.Y(f"{y}:Q"),
        text=alt.Text(f"{y}:Q", format=",.0f")
    )

    return (line + labels).properties(height=height, title=title)

def grouped_bar_with_labels(df, x, y, group, title, x_sort=None, height=360):
    bars = alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{x}:N", sort=x_sort, title=x),
        xOffset=alt.XOffset(f"{group}:N"),
        y=alt.Y(f"{y}:Q", title=y),
        color=alt.Color(f"{group}:N"),
        tooltip=[
            alt.Tooltip(f"{x}:N"),
            alt.Tooltip(f"{group}:N"),
            alt.Tooltip(f"{y}:Q", format=","),
        ]
    )

    labels = alt.Chart(df).mark_text(
        dy=-6,
        fontSize=9,
        fontWeight="bold"
    ).encode(
        x=alt.X(f"{x}:N", sort=x_sort),
        xOffset=alt.XOffset(f"{group}:N"),
        y=alt.Y(f"{y}:Q"),
        text=alt.Text(f"{y}:Q", format=",.0f"),
        color=alt.value("#111827")
    )

    return (bars + labels).properties(height=height, title=title)

def render_exec_metric_kpis(df: pd.DataFrame, value_col: str, value_formatter, sub_text: str, tone="ss-gray"):
    if df is None or df.empty:
        st.info("No sales executive-wise data available.")
        return

    rows = df.to_dict("records")
    for start in range(0, len(rows), 4):
        cols = st.columns(4)
        for idx, row in enumerate(rows[start:start + 4]):
            with cols[idx]:
                kpi_card(
                    _safe_str(row.get("Sales Executive", "—")),
                    value_formatter(row.get(value_col, 0)),
                    sub_text,
                    tone,
                )

# ============================================================
# SECTION 1 — BOOKING SUMMARY
# ============================================================
section_card("📌 Booking Summary", "Bookings counted from booking date only, starting April 2025.")

b1, b2, b3, b4 = st.columns(4)
with b1:
    kpi_card("Total Bookings", f"{total_bookings:,}", f"Distinct sold units: {sold_units_distinct:,}", "ss-blue")
with b2:
    kpi_card("Total Carpet Area Sold", f"{total_carpet_area:,.0f} sqft", "Carpet area", "ss-green")
with b3:
    kpi_card("Total Agreement Cost Sold", _fmt_money(total_agreement_value), "Agreement cost sold", "ss-blue")
with b4:
    kpi_card("Overall Avg PSF", _fmt_psf(avg_psf_overall), "Agreement cost / (carpet area × 1.38)", "ss-amber")

b5, b6, b7, b8 = st.columns(4)
with b5:
    kpi_card("Overall Avg Conversion Period", f"{avg_conversion_days:.1f} days", "First visit to booking", "ss-purple")
with b6:
    kpi_card("Average Visits for Booking", f"{avg_visits_for_booking:.1f}", "From Visit Count", "ss-purple")
with b7:
    kpi_card("Average Booking / Month", f"{avg_booking_per_month:.2f}", "Based on booking date months", "ss-green")
with b8:
    kpi_card("Total Units Sold", f"{sold_units_distinct:,}", "Distinct Wing + Flat", "ss-green")

appc1, appc2, appc3 = st.columns(3)

with appc1:
    kpi_card(
        "1 BHK Appreciation %",
        _fmt_pct(app_1bhk["pct"]),
        f"Lowest Avg Month ({app_1bhk['lowest_month']}): {_fmt_psf(app_1bhk['lowest_psf'])}  |  "
        f"Highest Avg Month ({app_1bhk['highest_month']}): {_fmt_psf(app_1bhk['highest_psf'])}",
        "ss-green",
    )

with appc2:
    kpi_card(
        "2 BHK Appreciation %",
        _fmt_pct(app_2bhk["pct"]),
        f"Lowest Avg Month ({app_2bhk['lowest_month']}): {_fmt_psf(app_2bhk['lowest_psf'])}  |  "
        f"Highest Avg Month ({app_2bhk['highest_month']}): {_fmt_psf(app_2bhk['highest_psf'])}",
        "ss-green",
    )

with appc3:
    kpi_card(
        "Overall Appreciation %",
        _fmt_pct(app_overall["pct"]),
        f"Lowest Avg Month ({app_overall['lowest_month']}): {_fmt_psf(app_overall['lowest_psf'])}  |  "
        f"Highest Avg Month ({app_overall['highest_month']}): {_fmt_psf(app_overall['highest_psf'])}",
        "ss-green",
    )

if not monthly_bookings_df.empty:
    st.altair_chart(
        line_chart_with_labels(
            monthly_bookings_df,
            x="Month",
            y="Bookings",
            title="Month-wise Bookings",
            x_sort=month_sort_order
        ),
        use_container_width=True
    )

# ============================================================
# SECTION 2 — AGREEMENT & STAMP DUTY
# ============================================================
section_card("✅ Agreement & Stamp Duty Status", "Separate status totals and pending tables by month and sales executive.")

a1, a2, a3 = st.columns(3)
with a1:
    kpi_card("Total Agreements", f"{total_bookings:,}", "All booked units", "ss-blue")
with a2:
    kpi_card("Agreement Done", f"{total_agreement_done:,}", f"Pending: {total_agreement_pending:,}", "ss-green")
with a3:
    kpi_card("Stamp Duty Received", f"{total_stamp_received:,}", f"Pending: {total_stamp_pending:,}", "ss-green")

st.markdown("### 🟠 Sales Executive-wise Month-wise Stamp Duty Pending / Not Received")
if stamp_pending_month_exec_df.empty:
    st.success("No stamp duty pending records found.")
else:
    render_table(stamp_pending_month_exec_df)

st.markdown("### 🔵 Sales Executive-wise Month-wise Agreement Not Done Pending")
if agreement_pending_month_exec_df.empty:
    st.success("No agreement pending records found.")
else:
    render_table(agreement_pending_month_exec_df)

# ============================================================
# SECTION 3 — INVENTORY, PSF, HOLD, LINEUP
# ============================================================
section_card("🏗️ Inventory, Wing-wise & Type-wise Sales", "Units sold, units left to sell, active holds, agreement lineup, and PSF.")

inventory_display = wing_inventory_df.copy()
inventory_display["Sold %"] = inventory_display["Sold %"].apply(_fmt_pct)
inventory_display["Avg PSF"] = inventory_display["Avg PSF"].apply(_fmt_psf)
render_table(inventory_display)

g_inv1, g_inv2 = st.columns(2)

with g_inv1:
    inv_plot = wing_inventory_df[["Wing", "Units Sold", "Units Hold", "Agreement Lineup", "Units Left to Sell"]].melt(
        id_vars="Wing",
        var_name="Metric",
        value_name="Count"
    )
    st.altair_chart(
        grouped_bar_with_labels(
            inv_plot,
            x="Wing",
            y="Count",
            group="Metric",
            title="Wing-wise Sold, Hold, Lineup & Left to Sell"
        ),
        use_container_width=True
    )

with g_inv2:
    if wing_type_psf_df.empty:
        st.info("No wing/type PSF data available.")
    else:
        st.altair_chart(
            grouped_bar_with_labels(
                wing_type_psf_df,
                x="Wing",
                y="Avg PSF",
                group="Type",
                title="Wing-wise × Type-wise Avg PSF"
            ),
            use_container_width=True
        )

psf1, psf2 = st.columns(2)

with psf1:
    if wing_psf_df.empty:
        st.info("No wing-wise PSF available.")
    else:
        st.altair_chart(
            bar_chart_with_labels(
                wing_psf_df,
                x="Wing",
                y="Avg PSF",
                title="Wing-wise Avg PSF"
            ),
            use_container_width=True
        )

with psf2:
    if type_psf_df.empty:
        st.info("No type-wise PSF available.")
    else:
        st.altair_chart(
            bar_chart_with_labels(
                type_psf_df,
                x="Type",
                y="Avg PSF",
                title="Type-wise Avg PSF"
            ),
            use_container_width=True
        )

# ============================================================
# SECTION 4 — MARKETING EXPENDITURE
# ============================================================
section_card("📣 Marketing Expenditure Summary", "Total spend, this month spend, recurring spend, agreement percentage, and cost per sqft.")

m1, m2, m3, m4 = st.columns(4)
with m1:
    kpi_card("Total Marketing Spend", _fmt_money(total_marketing_spend), f"{_fmt_pct(marketing_spend_pct_agreement)} of Agreement Value", "ss-rose")
with m2:
    kpi_card("This Month Spend", _fmt_money(this_month_marketing_spend), TODAY.strftime("%B %Y"), "ss-blue")
with m3:
    kpi_card("Recurring Spend", _fmt_money(recurring_marketing_spend), f"{_fmt_pct(recurring_spend_pct_agreement)} of Agreement Value", "ss-amber")
with m4:
    kpi_card("Marketing Cost / Sqft", _fmt_money(marketing_spend_per_sqft), f"Recurring: {_fmt_money(recurring_spend_per_sqft)}", "ss-green")

m5, m6 = st.columns(2)
with m5:
    kpi_card("Marketing Cost / Booking", _fmt_money(marketing_cost_per_booking), "Total spend / bookings", "ss-gray")
with m6:
    kpi_card("Recurring Cost / Booking", _fmt_money(recurring_cost_per_booking), "Recurring spend / bookings", "ss-gray")

mg1, mg2 = st.columns(2)

with mg1:
    if monthly_marketing_df.empty:
        st.info("No monthly marketing data available.")
    else:
        st.altair_chart(
            bar_chart_with_labels(
                monthly_marketing_df,
                x="Month",
                y="Marketing Spend",
                title="Month-wise Marketing Spend",
                x_sort=monthly_marketing_df["Month"].tolist()
            ),
            use_container_width=True
        )

with mg2:
    if purpose_marketing_df.empty:
        st.info("No purpose-wise marketing data available.")
    else:
        top_purpose_df = purpose_marketing_df.head(10).copy()
        st.altair_chart(
            bar_chart_with_labels(
                top_purpose_df,
                x="Purpose",
                y="Amount",
                title="Top Purpose-wise Marketing Spend"
            ),
            use_container_width=True
        )

# ============================================================
# SECTION 5 — DAILY VISITS SUMMARY
# ============================================================
section_card("📆 Sales Executive Daily visits , call & Conversion summary", "Visits, revisits, calls, call answer rate, conversion ratios, executive-wise PSF, and conversion days.")

d1, d2, d3, d4 = st.columns(4)
with d1:
    kpi_card("Total Visits", f"{int(total_visits):,}", "From Daily Visits", "ss-blue")
with d2:
    kpi_card("Total Revisits", f"{int(total_revisits):,}", f"{_fmt_pct(revisit_to_visit_pct)} of visits", "ss-purple")
with d3:
    kpi_card("Total Calls", f"{int(total_calls):,}", f"Answered: {int(total_calls_answered):,}", "ss-gray")
with d4:
    kpi_card("Call Answer Rate", _fmt_pct(call_answer_rate), "Answered / total calls", "ss-green")

d5, d6, d7 = st.columns(3)
with d5:
    kpi_card("Calls → Visits", _fmt_pct(calls_to_visits_pct), "Attended visits / calls", "ss-amber")
with d6:
    kpi_card("Visits → Bookings", _fmt_pct(visit_to_booking_pct), "Bookings / total visits", "ss-green")
with d7:
    kpi_card("Daily Booking Entries", f"{int(total_daily_bookings):,}", "From daily visits table", "ss-blue")

st.markdown("### 💸 Sales Executive-wise Avg PSF Rate")
render_exec_metric_kpis(
    exec_psf_df,
    "Avg PSF",
    lambda x: _fmt_psf(x),
    "Agreement cost / (carpet area × 1.38)",
    "ss-amber",
)

st.markdown("### ⏱️ Sales Executive-wise Avg Conversion Days")
render_exec_metric_kpis(
    exec_conversion_days_df,
    "Avg Conversion Days",
    lambda x: f"{_to_num(x):.1f} days" if _to_num(x) > 0 else "—",
    "Average booking conversion period",
    "ss-purple",
)

if not monthly_visit_call_df.empty:
    visit_long = monthly_visit_call_df[["Month", "Total Visits", "Total Revisits", "Total Calls"]].melt(
        id_vars="Month",
        var_name="Metric",
        value_name="Count"
    )
    st.altair_chart(
        grouped_bar_with_labels(
            visit_long,
            x="Month",
            y="Count",
            group="Metric",
            title="Month-wise Visits, Revisits & Calls",
            x_sort=monthly_visit_call_df["Month"].tolist()
        ),
        use_container_width=True
    )

st.markdown("### 👥 Sales Executive Call → Visit → Revisit → Booking Table")
if exec_summary_df.empty:
    st.info("No sales executive summary available.")
else:
    exec_display = exec_summary_df.copy()
    for c in ["Call Answer %", "Calls → Visits %", "Visits → Revisits %", "Visits → Bookings %", "Calls → Bookings %"]:
        exec_display[c] = exec_display[c].apply(_fmt_pct)

    render_table(exec_display)

    exec_plot = exec_summary_df[["Sales Executive", "Bookings", "Attended Visits", "Revisits", "Total Calls"]].melt(
        id_vars="Sales Executive",
        var_name="Metric",
        value_name="Count"
    )

    st.altair_chart(
        grouped_bar_with_labels(
            exec_plot,
            x="Sales Executive",
            y="Count",
            group="Metric",
            title="Executive-wise Calls, Visits, Revisits & Bookings"
        ),
        use_container_width=True
    )

# ============================================================
# SECTION 6 — COLLECTION / CASHFLOW
# ============================================================
section_card("💰 Collection, Received, Due & Current Construction Stage", "Current stage is read directly from the cashflow_slab_master table.")

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Total Collection Till Date", _fmt_money(total_collection), "Based on completed slabs", "ss-blue")
with c2:
    kpi_card("Total Received Till Date", _fmt_money(total_cashflow_received), f"Received: {_fmt_pct(total_cashflow_received_pct)}", "ss-green")
with c3:
    kpi_card("Total Due Till Date", _fmt_money(total_cashflow_due), f"Due: {_fmt_pct(total_cashflow_due_pct)}", "ss-amber")
with c4:
    kpi_card("Booking Received Amount", _fmt_money(total_received_booking), "Received amount in bookings table", "ss-purple")

if not wing_summary_df.empty:
    stage_cols = st.columns(min(4, len(wing_summary_df)))
    for idx, (_, wr) in enumerate(wing_summary_df.iterrows()):
        with stage_cols[idx % len(stage_cols)]:
            kpi_card(
                f"{wr['Wing']} Current Stage",
                wr["Current Stage"],
                f"Completed On: {wr['Stage Completed On'] or '—'}",
                "ss-gray"
            )

    wing_display = wing_summary_df.copy()
    for c in ["Collection Till Date", "Received Till Date", "Due Till Date"]:
        wing_display[c] = wing_display[c].apply(_fmt_money)
    for c in ["Received %", "Due %"]:
        wing_display[c] = wing_display[c].apply(_fmt_pct)

    render_table(wing_display)
else:
    st.info("No wing-wise cashflow data available.")

# ============================================================
# SECTION 7 — SALES TARGETS
# ============================================================
section_card(
    "🎯 Sales Target & Achievement",
    "This month target, achieved bookings, pending target, achievement percentage, and next month target."
)

tc1, tc2, tc3, tc4 = st.columns(4)

with tc1:
    kpi_card("Current Month", _month_label_from_key(THIS_MONTH_KEY), "Target month", "ss-blue")

with tc2:
    kpi_card(
        "This Month Target",
        f"{total_this_month_target:,}",
        f"Next month: {total_next_month_target:,}",
        "ss-purple",
    )

with tc3:
    kpi_card(
        "Achieved",
        f"{total_this_month_achieved:,}",
        f"Pending: {total_this_month_pending:,}",
        "ss-green",
    )

with tc4:
    kpi_card(
        "Achievement %",
        _fmt_pct(total_target_achievement_pct),
        "Achieved / target",
        "ss-amber",
    )

if target_achievement_df.empty:
    st.info("No sales target data found. Please add targets in the sales_targets table.")
else:
    st.markdown("### 🎯 Executive-wise Target Progress")

    st.dataframe(
        target_achievement_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "This Month Target": st.column_config.NumberColumn("This Month Target", format="%d"),
            "Achieved": st.column_config.NumberColumn("Achieved", format="%d"),
            "Pending": st.column_config.NumberColumn("Pending", format="%d"),
            "Achievement %": st.column_config.ProgressColumn(
                "Achievement %",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
            "Next Month Target": st.column_config.NumberColumn(
                f"Next Month Target ({_month_label_from_key(NEXT_MONTH_KEY)})",
                format="%d",
            ),
        },
    )

# ============================================================
# EMAIL REPORT HELPERS
# ============================================================
def _df_to_email_table(df: pd.DataFrame, max_rows=40):
    if df is None or df.empty:
        return "<p>No data available.</p>"

    show_df = df.head(max_rows).copy()
    return show_df.to_html(index=False, border=0, classes="email-table")

def _make_matplotlib_chart(chart_type: str, df: pd.DataFrame, title: str):
    import matplotlib.pyplot as plt
    import numpy as np

    if df is not None and not df.empty:
        df = df.copy()
        if "_MonthSort" in df.columns:
            df = df[df["_MonthSort"].astype(str).ne("9999-99")].sort_values("_MonthSort").copy()

    buf = io.BytesIO()
    fig, ax = plt.subplots(figsize=(11, 5.2))

    if df is None or df.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        ax.set_axis_off()

    elif chart_type == "monthly_bookings":
        ax.plot(df["Month"], df["Bookings"], marker="o")
        ax.set_ylabel("Bookings")
        ax.set_xlabel("Month")
        ax.tick_params(axis="x", rotation=35)
        for x, y in zip(df["Month"], df["Bookings"]):
            ax.annotate(f"{int(y)}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)

    elif chart_type == "inventory":
        plot_df = df[["Wing", "Units Sold", "Units Hold", "Agreement Lineup", "Units Left to Sell"]].copy()
        x = np.arange(len(plot_df))
        width = 0.2
        series = [
            ("Sold", plot_df["Units Sold"], -1.5 * width),
            ("Hold", plot_df["Units Hold"], -0.5 * width),
            ("Lineup", plot_df["Agreement Lineup"], 0.5 * width),
            ("Left", plot_df["Units Left to Sell"], 1.5 * width),
        ]
        for label, values, offset in series:
            bars = ax.bar(x + offset, values, width=width, label=label)
            ax.bar_label(bars, padding=3, fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(plot_df["Wing"])
        ax.set_ylabel("Units")
        ax.legend()

    elif chart_type == "monthly_marketing":
        bars = ax.bar(df["Month"], df["Marketing Spend"])
        ax.bar_label(bars, padding=3, fontsize=8, fmt="%.0f")
        ax.set_ylabel("Marketing Spend")
        ax.set_xlabel("Month")
        ax.tick_params(axis="x", rotation=35)

    elif chart_type == "wing_type_psf":
        plot_df = df[["Wing", "Type", "Avg PSF"]].copy()
        x_labels = plot_df["Wing"].drop_duplicates().tolist()
        type_labels = plot_df["Type"].drop_duplicates().tolist()
        x = np.arange(len(x_labels))
        width = 0.8 / max(len(type_labels), 1)
        for idx, type_name in enumerate(type_labels):
            vals = []
            for wing in x_labels:
                hit = plot_df[plot_df["Wing"].eq(wing) & plot_df["Type"].eq(type_name)]
                vals.append(float(hit["Avg PSF"].iloc[0]) if not hit.empty else 0.0)
            offset = (idx - (len(type_labels) - 1) / 2) * width
            bars = ax.bar(x + offset, vals, width=width, label=type_name)
            ax.bar_label(bars, padding=3, fontsize=7, fmt="%.0f")
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels)
        ax.set_ylabel("Avg PSF")
        ax.legend()

    elif chart_type == "wing_psf":
        bars = ax.bar(df["Wing"], df["Avg PSF"])
        ax.bar_label(bars, padding=3, fontsize=8, fmt="%.0f")
        ax.set_ylabel("Avg PSF")
        ax.set_xlabel("Wing")

    elif chart_type == "type_psf":
        bars = ax.bar(df["Type"], df["Avg PSF"])
        ax.bar_label(bars, padding=3, fontsize=8, fmt="%.0f")
        ax.set_ylabel("Avg PSF")
        ax.set_xlabel("Type")

    elif chart_type == "purpose_marketing":
        plot_df = df.head(10).copy()
        bars = ax.bar(plot_df["Purpose"].astype(str), plot_df["Amount"])
        ax.bar_label(bars, padding=3, fontsize=8, fmt="%.0f")
        ax.set_ylabel("Amount")
        ax.set_xlabel("Purpose")
        ax.tick_params(axis="x", rotation=35)

    elif chart_type == "exec_summary":
        plot_df = df[["Sales Executive", "Bookings", "Attended Visits", "Revisits", "Total Calls"]].copy()
        x = np.arange(len(plot_df))
        width = 0.18
        series = [
            ("Bookings", plot_df["Bookings"], -2 * width),
            ("Attended", plot_df["Attended Visits"], -width),
            ("Revisits", plot_df["Revisits"], 0),
            ("Calls", plot_df["Total Calls"], width),
        ]
        for label, values, offset in series:
            bars = ax.bar(x + offset, values, width=width, label=label)
            ax.bar_label(bars, padding=3, fontsize=7)
        ax.set_xticks(x)
        ax.set_xticklabels(plot_df["Sales Executive"], rotation=20, ha="right")
        ax.set_ylabel("Count")
        ax.legend()

    elif chart_type == "visit_call":
        ax.plot(df["Month"], df["Total Visits"], marker="o", label="Visits")
        ax.plot(df["Month"], df["Total Revisits"], marker="o", label="Revisits")
        ax.plot(df["Month"], df["Total Calls"], marker="o", label="Calls")
        for col in ["Total Visits", "Total Revisits", "Total Calls"]:
            for x, y in zip(df["Month"], df[col]):
                ax.annotate(f"{int(y)}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7)
        ax.set_ylabel("Count")
        ax.set_xlabel("Month")
        ax.tick_params(axis="x", rotation=35)
        ax.legend()

    elif chart_type == "target":
        plot_df = df[["Sales Executive", "This Month Target", "Achieved", "Pending"]].copy()
        x = np.arange(len(plot_df))
        width = 0.25
        series = [
            ("Target", plot_df["This Month Target"], -width),
            ("Achieved", plot_df["Achieved"], 0),
            ("Pending", plot_df["Pending"], width),
        ]
        for label, values, offset in series:
            bars = ax.bar(x + offset, values, width=width, label=label)
            ax.bar_label(bars, padding=3, fontsize=7)
        ax.set_xticks(x)
        ax.set_xticklabels(plot_df["Sales Executive"], rotation=20, ha="right")
        ax.set_ylabel("Bookings")
        ax.legend()

    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def _build_email_html(image_cids: dict):
    def email_section(title, subtitle=""):
        return f"""
        <div class="email-section-card">
            <h2>{escape(str(title))}</h2>
            <p>{escape(str(subtitle))}</p>
        </div>
        """

    def email_kpi_card(title, value, sub="", tone="ss-gray"):
        return f"""
        <div class="email-kpi {tone}">
            <div class="email-kpi-title">{escape(str(title))}</div>
            <div class="email-kpi-value">{escape(str(value))}</div>
            <div class="email-kpi-sub">{escape(str(sub))}</div>
        </div>
        """

    def email_kpi_grid(cards, cols=4):
        if not cards:
            return ""
        return """
        <div class="email-grid" style="grid-template-columns: repeat({cols}, minmax(0, 1fr));">
            {cards_html}
        </div>
        """.format(
            cols=cols,
            cards_html="".join(email_kpi_card(*card) for card in cards),
        )

    def email_exec_metric_cards(df: pd.DataFrame, value_col: str, value_formatter, sub_text: str, tone="ss-gray"):
        if df is None or df.empty:
            return "<p class='email-empty'>No sales executive-wise data available.</p>"
        cards = []
        for _, row in df.iterrows():
            cards.append((
                row.get("Sales Executive", "—"),
                value_formatter(row.get(value_col, 0)),
                sub_text,
                tone,
            ))
        return email_kpi_grid(cards, cols=4)

    def email_chart(title):
        cid = image_cids.get(title, "")
        if not cid:
            return ""
        return f"""
        <div class="email-chart-card">
            <h3>{escape(str(title))}</h3>
            <img src="cid:{cid}" />
        </div>
        """

    exec_email_df = exec_summary_df.copy()
    if not exec_email_df.empty:
        for c in ["Call Answer %", "Calls → Visits %", "Visits → Revisits %", "Visits → Bookings %", "Calls → Bookings %"]:
            exec_email_df[c] = exec_email_df[c].apply(_fmt_pct)

    wing_email_df = wing_summary_df.copy()
    if not wing_email_df.empty:
        for c in ["Collection Till Date", "Received Till Date", "Due Till Date"]:
            wing_email_df[c] = wing_email_df[c].apply(_fmt_money)
        for c in ["Received %", "Due %"]:
            wing_email_df[c] = wing_email_df[c].apply(_fmt_pct)

    inv_email_df = wing_inventory_df.copy()
    if not inv_email_df.empty:
        inv_email_df["Sold %"] = inv_email_df["Sold %"].apply(_fmt_pct)
        inv_email_df["Avg PSF"] = inv_email_df["Avg PSF"].apply(_fmt_psf)

    generated_at = datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p")

    booking_cards_row_1 = [
        ("Total Bookings", f"{total_bookings:,}", f"Distinct sold units: {sold_units_distinct:,}", "ss-blue"),
        ("Total Carpet Area Sold", f"{total_carpet_area:,.0f} sqft", "Carpet area", "ss-green"),
        ("Total Agreement Cost Sold", _fmt_money(total_agreement_value), "Agreement cost sold", "ss-blue"),
        ("Overall Avg PSF", _fmt_psf(avg_psf_overall), "Agreement cost / (carpet area × 1.38)", "ss-amber"),
    ]
    booking_cards_row_2 = [
        ("Overall Avg Conversion Period", f"{avg_conversion_days:.1f} days", "First visit to booking", "ss-purple"),
        ("Average Visits for Booking", f"{avg_visits_for_booking:.1f}", "From Visit Count", "ss-purple"),
        ("Average Booking / Month", f"{avg_booking_per_month:.2f}", "Based on booking date months", "ss-green"),
        ("Total Units Sold", f"{sold_units_distinct:,}", "Distinct Wing + Flat", "ss-green"),
    ]
    appreciation_cards = [
        (
            "1 BHK Appreciation %",
            _fmt_pct(app_1bhk["pct"]),
            f"Lowest ({app_1bhk['lowest_month']}): {_fmt_psf(app_1bhk['lowest_psf'])} | Highest ({app_1bhk['highest_month']}): {_fmt_psf(app_1bhk['highest_psf'])}",
            "ss-green",
        ),
        (
            "2 BHK Appreciation %",
            _fmt_pct(app_2bhk["pct"]),
            f"Lowest ({app_2bhk['lowest_month']}): {_fmt_psf(app_2bhk['lowest_psf'])} | Highest ({app_2bhk['highest_month']}): {_fmt_psf(app_2bhk['highest_psf'])}",
            "ss-green",
        ),
        (
            "Overall Appreciation %",
            _fmt_pct(app_overall["pct"]),
            f"Lowest ({app_overall['lowest_month']}): {_fmt_psf(app_overall['lowest_psf'])} | Highest ({app_overall['highest_month']}): {_fmt_psf(app_overall['highest_psf'])}",
            "ss-green",
        ),
    ]

    agreement_cards = [
        ("Total Agreements", f"{total_bookings:,}", "All booked units", "ss-blue"),
        ("Agreement Done", f"{total_agreement_done:,}", f"Pending: {total_agreement_pending:,}", "ss-green"),
        ("Stamp Duty Received", f"{total_stamp_received:,}", f"Pending: {total_stamp_pending:,}", "ss-green"),
    ]

    marketing_cards_row_1 = [
        ("Total Marketing Spend", _fmt_money(total_marketing_spend), f"{_fmt_pct(marketing_spend_pct_agreement)} of Agreement Value", "ss-rose"),
        ("This Month Spend", _fmt_money(this_month_marketing_spend), TODAY.strftime("%B %Y"), "ss-blue"),
        ("Recurring Spend", _fmt_money(recurring_marketing_spend), f"{_fmt_pct(recurring_spend_pct_agreement)} of Agreement Value", "ss-amber"),
        ("Marketing Cost / Sqft", _fmt_money(marketing_spend_per_sqft), f"Recurring: {_fmt_money(recurring_spend_per_sqft)}", "ss-green"),
    ]
    marketing_cards_row_2 = [
        ("Marketing Cost / Booking", _fmt_money(marketing_cost_per_booking), "Total spend / bookings", "ss-gray"),
        ("Recurring Cost / Booking", _fmt_money(recurring_cost_per_booking), "Recurring spend / bookings", "ss-gray"),
    ]

    daily_cards_row_1 = [
        ("Total Visits", f"{int(total_visits):,}", "From Daily Visits", "ss-blue"),
        ("Total Revisits", f"{int(total_revisits):,}", f"{_fmt_pct(revisit_to_visit_pct)} of visits", "ss-purple"),
        ("Total Calls", f"{int(total_calls):,}", f"Answered: {int(total_calls_answered):,}", "ss-gray"),
        ("Call Answer Rate", _fmt_pct(call_answer_rate), "Answered / total calls", "ss-green"),
    ]
    daily_cards_row_2 = [
        ("Calls → Visits", _fmt_pct(calls_to_visits_pct), "Attended visits / calls", "ss-amber"),
        ("Visits → Bookings", _fmt_pct(visit_to_booking_pct), "Bookings / total visits", "ss-green"),
        ("Daily Booking Entries", f"{int(total_daily_bookings):,}", "From daily visits table", "ss-blue"),
    ]

    collection_cards = [
        ("Total Collection Till Date", _fmt_money(total_collection), "Based on completed slabs", "ss-blue"),
        ("Total Received Till Date", _fmt_money(total_cashflow_received), f"Received: {_fmt_pct(total_cashflow_received_pct)}", "ss-green"),
        ("Total Due Till Date", _fmt_money(total_cashflow_due), f"Due: {_fmt_pct(total_cashflow_due_pct)}", "ss-amber"),
        ("Booking Received Amount", _fmt_money(total_received_booking), "Received amount in bookings table", "ss-purple"),
    ]

    stage_cards = []
    if not wing_summary_df.empty:
        for _, wr in wing_summary_df.iterrows():
            stage_cards.append((
                f"{wr['Wing']} Current Stage",
                wr["Current Stage"],
                f"Completed On: {wr['Stage Completed On'] or '—'}",
                "ss-gray",
            ))

    target_cards = [
        ("Current Month", _month_label_from_key(THIS_MONTH_KEY), "Target month", "ss-blue"),
        ("This Month Target", f"{total_this_month_target:,}", f"Next month: {total_next_month_target:,}", "ss-purple"),
        ("Achieved", f"{total_this_month_achieved:,}", f"Pending: {total_this_month_pending:,}", "ss-green"),
        ("Achievement %", _fmt_pct(total_target_achievement_pct), "Achieved / target", "ss-amber"),
    ]

    return f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f8fafc;
                color: #0f172a;
                padding: 18px;
                margin: 0;
            }}
            .shell {{
                max-width: 1180px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 20px;
                padding: 22px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 8px 24px rgba(15,23,42,.06);
            }}
            h1 {{
                margin: 0 0 4px 0;
                font-size: 28px;
                text-align: center;
                color: #0f172a;
            }}
            h3 {{
                margin: 0 0 12px 0;
                font-size: 16px;
                color: #0f172a;
            }}
            .muted {{
                color: #64748b;
                font-size: 13px;
                margin-bottom: 18px;
                text-align: center;
                font-weight: 700;
            }}
            .email-section-card {{
                background: linear-gradient(135deg,#2563eb 0%,#7c3aed 100%);
                color: white;
                border-radius: 22px;
                padding: 22px 18px;
                text-align: center;
                margin: 32px 0 16px 0;
                box-shadow: 0 12px 28px rgba(37,99,235,.18);
            }}
            .email-section-card h2 {{
                margin: 0;
                font-size: 24px;
                font-weight: 900;
                color: #ffffff;
            }}
            .email-section-card p {{
                margin: 8px 0 0 0;
                font-size: 13px;
                font-weight: 700;
                opacity: .92;
            }}
            .email-grid {{
                display: grid;
                gap: 12px;
                margin: 10px 0 12px 0;
            }}
            .email-kpi {{
                border: 1px solid rgba(49,51,63,0.10);
                border-radius: 16px;
                padding: 14px 12px;
                text-align: center;
                min-height: 104px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.04);
                box-sizing: border-box;
            }}
            .email-kpi-title {{
                font-size: 12px;
                line-height: 1.2;
                font-weight: 800;
                color: rgba(49,51,63,0.78);
            }}
            .email-kpi-value {{
                font-size: 23px;
                line-height: 1.08;
                font-weight: 900;
                color: #111827;
                margin-top: 8px;
            }}
            .email-kpi-sub {{
                margin-top: 8px;
                font-size: 11.5px;
                line-height: 1.25;
                font-weight: 700;
                color: rgba(49,51,63,0.65);
            }}
            .ss-blue{{background:#eff6ff;}}
            .ss-green{{background:#ecfdf5;}}
            .ss-amber{{background:#fff7ed;}}
            .ss-rose{{background:#fff1f2;}}
            .ss-purple{{background:#f5f3ff;}}
            .ss-gray{{background:#f8fafc;}}
            .email-chart-row {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
                margin: 12px 0;
            }}
            .email-chart-card {{
                border: 1px solid #dbe4f0;
                border-radius: 16px;
                padding: 12px;
                background: #ffffff;
                box-shadow: 0 5px 16px rgba(15,23,42,.05);
                margin: 12px 0;
            }}
            .email-chart-card img {{
                max-width: 100%;
                width: 100%;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                display: block;
            }}
            .email-table-wrap {{
                overflow-x: auto;
                border: 1px solid #dbe4f0;
                border-radius: 14px;
                margin: 10px 0 20px 0;
                box-shadow: 0 5px 16px rgba(15,23,42,.05);
            }}
            table.email-table {{
                border-collapse: collapse;
                width: 100%;
                font-size: 12px;
                background: #ffffff;
            }}
            table.email-table th {{
                background: linear-gradient(135deg,#1d4ed8 0%,#4f46e5 100%);
                color: white;
                padding: 9px;
                text-align: left;
                font-weight: 900;
                white-space: nowrap;
            }}
            table.email-table td {{
                border-bottom: 1px solid #e5e7eb;
                padding: 8px 9px;
                white-space: nowrap;
            }}
            table.email-table tr:nth-child(even) {{
                background: #f8fafc;
            }}
            .email-empty {{
                color: #64748b;
                font-weight: 700;
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 12px;
            }}
            @media only screen and (max-width: 760px) {{
                .email-grid, .email-chart-row {{
                    display: block;
                }}
                .email-kpi, .email-chart-card {{
                    margin-bottom: 12px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="shell">
            <h1>Pratham Vihar — Complete Site Summary</h1>
            <div class="muted">Generated on {generated_at}</div>

            {email_section("📌 Booking Summary", "Bookings counted from booking date only, starting April 2025.")}
            {email_kpi_grid(booking_cards_row_1, cols=4)}
            {email_kpi_grid(booking_cards_row_2, cols=4)}
            {email_kpi_grid(appreciation_cards, cols=3)}
            {email_chart("Month-wise Bookings")}

            {email_section("✅ Agreement & Stamp Duty Status", "Separate status totals and pending tables by month and sales executive.")}
            {email_kpi_grid(agreement_cards, cols=3)}
            <h3>🟠 Sales Executive-wise Month-wise Stamp Duty Pending / Not Received</h3>
            <div class="email-table-wrap">{_df_to_email_table(stamp_pending_month_exec_df, max_rows=80)}</div>
            <h3>🔵 Sales Executive-wise Month-wise Agreement Not Done Pending</h3>
            <div class="email-table-wrap">{_df_to_email_table(agreement_pending_month_exec_df, max_rows=80)}</div>

            {email_section("🏗️ Inventory, Wing-wise & Type-wise Sales", "Units sold, units left to sell, active holds, agreement lineup, and PSF.")}
            <div class="email-table-wrap">{_df_to_email_table(inv_email_df, max_rows=20)}</div>
            <div class="email-chart-row">
                {email_chart("Wing-wise Sold, Hold, Lineup & Left to Sell")}
                {email_chart("Wing-wise × Type-wise Avg PSF")}
            </div>
            <div class="email-chart-row">
                {email_chart("Wing-wise Avg PSF")}
                {email_chart("Type-wise Avg PSF")}
            </div>

            {email_section("📣 Marketing Expenditure Summary", "Total spend, this month spend, recurring spend, agreement percentage, and cost per sqft.")}
            {email_kpi_grid(marketing_cards_row_1, cols=4)}
            {email_kpi_grid(marketing_cards_row_2, cols=2)}
            <div class="email-chart-row">
                {email_chart("Month-wise Marketing Spend")}
                {email_chart("Top Purpose-wise Marketing Spend")}
            </div>

            {email_section("📆 Sales Executive Daily visits , call & Conversion summary", "Visits, revisits, calls, call answer rate, conversion ratios, executive-wise PSF, and conversion days.")}
            {email_kpi_grid(daily_cards_row_1, cols=4)}
            {email_kpi_grid(daily_cards_row_2, cols=3)}
            <h3>💸 Sales Executive-wise Avg PSF Rate</h3>
            {email_exec_metric_cards(exec_psf_df, "Avg PSF", lambda x: _fmt_psf(x), "Agreement cost / (carpet area × 1.38)", "ss-amber")}
            <h3>⏱️ Sales Executive-wise Avg Conversion Days</h3>
            {email_exec_metric_cards(exec_conversion_days_df, "Avg Conversion Days", lambda x: f"{_to_num(x):.1f} days" if _to_num(x) > 0 else "—", "Average booking conversion period", "ss-purple")}
            {email_chart("Month-wise Visits, Revisits & Calls")}
            <h3>👥 Sales Executive Call → Visit → Revisit → Booking Table</h3>
            <div class="email-table-wrap">{_df_to_email_table(exec_email_df, max_rows=30)}</div>
            {email_chart("Executive-wise Calls, Visits, Revisits & Bookings")}

            {email_section("💰 Collection, Received, Due & Current Construction Stage", "Current stage is read directly from the cashflow_slab_master table.")}
            {email_kpi_grid(collection_cards, cols=4)}
            {email_kpi_grid(stage_cards, cols=4)}
            <div class="email-table-wrap">{_df_to_email_table(wing_email_df, max_rows=20)}</div>

            {email_section("🎯 Sales Target & Achievement", "This month target, achieved bookings, pending target, achievement percentage, and next month target.")}
            {email_kpi_grid(target_cards, cols=4)}
            <div class="email-table-wrap">{_df_to_email_table(target_achievement_df, max_rows=30)}</div>
        </div>
    </body>
    </html>
    """


def _send_summary_email():
    email_cfg = {}
    try:
        email_cfg = dict(st.secrets.get("email", {}))
    except Exception:
        email_cfg = {}

    smtp_host = email_cfg.get("smtp_host", "smtp.gmail.com")
    smtp_port = int(email_cfg.get("smtp_port", 465))
    sender_email = email_cfg.get("sender_email", "")
    sender_password = email_cfg.get("sender_password", "")
    receiver_email = email_cfg.get("receiver_email", "")
    subject_prefix = email_cfg.get("subject_prefix", "Pratham Vihar Complete Site Summary")

    if not sender_email or not sender_password or not receiver_email:
        return False, "Email secrets are missing. Add sender_email, sender_password, and receiver_email in Streamlit secrets."

    recipients = _clean_email_list(receiver_email)

    if not recipients:
        return False, "Receiver email is empty."

    chart_specs = [
        ("Month-wise Bookings", "monthly_bookings", monthly_bookings_df),
        ("Wing-wise Sold, Hold, Lineup & Left to Sell", "inventory", wing_inventory_df),
        ("Wing-wise × Type-wise Avg PSF", "wing_type_psf", wing_type_psf_df),
        ("Wing-wise Avg PSF", "wing_psf", wing_psf_df),
        ("Type-wise Avg PSF", "type_psf", type_psf_df),
        ("Month-wise Marketing Spend", "monthly_marketing", monthly_marketing_df),
        ("Top Purpose-wise Marketing Spend", "purpose_marketing", purpose_marketing_df),
        ("Month-wise Visits, Revisits & Calls", "visit_call", monthly_visit_call_df),
        ("Executive-wise Calls, Visits, Revisits & Bookings", "exec_summary", exec_summary_df),
    ]

    image_cids = {}
    image_payloads = []

    for title, chart_type, chart_df in chart_specs:
        cid = make_msgid(domain="prathamvihar.local")[1:-1]
        image_cids[title] = cid
        png_bytes = _make_matplotlib_chart(chart_type, chart_df, title)
        image_payloads.append((cid, png_bytes, f"{chart_type}.png"))

    html_body = _build_email_html(image_cids)

    sent_on = datetime.datetime.now()
    sent_on_label = f"{sent_on.strftime('%B')} {sent_on.day}"

    msg = MIMEMultipart("related")
    msg["Subject"] = f"{subject_prefix} — {sent_on_label}"
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=True)

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText("Please view this email in HTML format.", "plain"))
    alt_part.attach(MIMEText(html_body, "html"))
    msg.attach(alt_part)

    for cid, png_bytes, filename in image_payloads:
        img = MIMEImage(png_bytes, _subtype="png")
        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline", filename=filename)
        msg.attach(img)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())

    return True, f"Summary email sent to {', '.join(recipients)}."

# ============================================================
# EMAIL BUTTON
# ============================================================
section_card("📧 Send Complete Summary on Email", "Sends the same screen-style section structure with colored KPI cards, graphs, tables, pending summaries, targets, and cashflow stage summary.")

if st.button("📧 Send Complete Site Summary Email", type="primary", use_container_width=True):
    with st.spinner("Preparing and sending summary email..."):
        ok, msg = _send_summary_email()

    if ok:
        st.success(msg)
    else:
        st.error(msg)
