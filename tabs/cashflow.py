# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.

import datetime
from html import escape

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.header("💰 Cashflow")

# ============================================================
# SUPABASE CONFIG
# ============================================================
BOOKINGS_TABLE = "bookings"
CASHFLOW_MASTER_TABLE = "cashflow_slab_master"

supabase_client = globals().get("supabase", None)

if supabase_client is None:
    st.warning("Supabase client is not initialized.")
    st.stop()

# ============================================================
# CONFIG
# ============================================================
REGISTRATION_AMOUNT = 30000.0

CASHFLOW_MASTER_HEADERS = ["id", "Wing", "Slab Name", "Completed", "Completed On"]

ALL_SLABS = [
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

GRAPH_HEAD_ORDER = ALL_SLABS[:]

# ------------------------------------------------------------
# DUE TABLE / INVENTORY-LIKE LAYOUT CONFIG
# ------------------------------------------------------------
DUE_BC_SECOND_REFUGE_FLOOR = 12
DUE_EF_SECOND_REFUGE_FLOOR = 12

DUE_SERIES_TYPE_MAP = {
    "01": "2 BHK",
    "02": "2 BHK",
    "03": "2 BHK",
    "04": "1 BHK",
    "05": "1 BHK",
    "06": "1 BHK",
    "07": "1 BHK",
    "08": "2 BHK",
    "09": "2 BHK",
    "10": "2 BHK",
}

DUE_WING_LAYOUT_ORDER = {
    "B Wing": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
    "C Wing": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
    "E Wing": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
    "F Wing": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
}

DUE_MHADA_RULES = {
    "B Wing": {"floors": {4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "C Wing": {"floors": {3, 4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "E Wing": {"floors": {4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "F Wing": {"floors": {3, 4, 5, 6}, "series": {"04", "05", "06", "07"}},
}

DUE_REFUGE_RULES = {
    "B Wing": {(7, "10"), (DUE_BC_SECOND_REFUGE_FLOOR, "10")},
    "C Wing": {(7, "10"), (DUE_BC_SECOND_REFUGE_FLOOR, "10")},
    "E Wing": {(7, "01"), (DUE_EF_SECOND_REFUGE_FLOOR, "01")},
    "F Wing": {(7, "01"), (DUE_EF_SECOND_REFUGE_FLOOR, "01")},
}

DUE_MISSING_UNITS = {
    ("B Wing", 1, "06"),
    ("C Wing", 1, "06"),
    ("E Wing", 1, "05"),
    ("F Wing", 1, "05"),
}

DUE_TYPE_OVERRIDES = {
    ("B Wing", 1, "07"): "2 BHK XL",
    ("C Wing", 1, "07"): "2 BHK XL",
    ("E Wing", 1, "04"): "2 BHK XL",
    ("F Wing", 1, "04"): "2 BHK XL",
}

DUE_LANDOWNER_FLATS = {
    "B Wing": {
        "102", "103", "110",
        "204", "205",
        "302", "303", "309", "310",
        "401", "402", "410",
        "509", "510",
        "610",
        "801", "803", "804",
        "910",
        "1004",
        "1101", "1102", "1104",
        "1301", "1302", "1304",
    },
    "C Wing": {
        "103", "110",
        "301", "302", "303", "308", "309", "310",
        "408", "409",
        "603", "608", "609", "610",
        "703", "704", "707", "708",
        "806", "807", "808",
        "906", "907", "908",
        "1002", "1004",
        "1201", "1202", "1205", "1206",
        "1303", "1304", "1305", "1306",
    },
    "E Wing": {
        "103", "110",
        "302", "303", "304", "307", "309", "310",
        "401", "402", "403", "408", "409", "410",
        "501", "502", "503", "509", "510",
        "703", "704", "705", "706", "707",
        "805", "806",
        "901", "904", "905", "906", "907", "908",
    },
    "F Wing": {
        "102", "103", "110",
        "204", "205", "210",
        "302", "303", "309", "310",
        "501", "502", "509", "510",
        "610",
        "704",
        "801", "804", "810",
        "903", "904", "910",
        "1004",
        "1101", "1102", "1104",
        "1302",
    },
}

# ============================================================
# UI STYLES
# ============================================================
st.markdown(
    """
    <style>
    .cf-card {
        border-radius: 18px;
        padding: 14px 16px;
        border: 1px solid rgba(15, 23, 42, 0.08);
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        margin-bottom: 10px;
        min-height: 108px;
    }
    .cf-card h3 {
        margin: 0 0 8px 0;
        font-size: 15px;
        font-weight: 600;
        color: #334155;
    }
    .cf-card p {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.15;
    }
    .cf-card .cf-sub {
        margin-top: 8px;
        font-size: 12px;
        color: #64748b;
        font-weight: 500;
    }
    .cf-neutral { background: #f8fafc; }
    .cf-blue    { background: #f8fbff; }
    .cf-green   { background: #f7fbf8; }
    .cf-amber   { background: #fffdf7; }
    .cf-rose    { background: #fff8f8; }
    .cf-slate   { background: #f8fafc; }

    .section-subtitle {
        margin-top: 16px;
        margin-bottom: 10px;
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def _cf_card(title, value, tone="cf-neutral", subtext=None):
    sub_html = f"<div class='cf-sub'>{subtext}</div>" if subtext else ""
    st.markdown(
        f"<div class='cf-card {tone}'><h3>{title}</h3><p>{value}</p>{sub_html}</div>",
        unsafe_allow_html=True
    )

# ============================================================
# GENERIC HELPERS
# ============================================================
def _safe_str(x):
    return "" if pd.isna(x) else str(x).strip()

def _to_num(x):
    try:
        if pd.isna(x):
            return 0.0
        s = str(x).replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
        if s == "":
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def _fmt_money(x):
    return f"₹{_to_num(x):,.0f}"

def _pct(part, whole):
    whole = _to_num(whole)
    part = _to_num(part)
    if whole <= 0:
        return 0.0
    return max(0.0, min((part / whole) * 100.0, 100.0))

def _is_done(x):
    return _safe_str(x).lower() in {"done", "completed", "complete", "yes"}

def _is_received(x):
    return _safe_str(x).lower() in {"received", "recieved", "yes", "done", "paid"}

def _cf_norm_flat(x):
    s = _safe_str(x).upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def _cf_norm_wing(x):
    s = _safe_str(x).upper().replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    wing_map = {
        "B": "B Wing", "B WING": "B Wing",
        "C": "C Wing", "C WING": "C Wing",
        "E": "E Wing", "E WING": "E Wing",
        "F": "F Wing", "F WING": "F Wing",
    }
    return wing_map.get(s, _safe_str(x))

def _date_to_iso_or_none(v):
    if v is None:
        return None
    if pd.isna(v):
        return None
    s = str(v).strip()
    if s == "" or s.lower() in {"nat", "none", "nan"}:
        return None
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.date().isoformat()
    except Exception:
        return None

# ============================================================
# SUPABASE HELPERS
# ============================================================
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

        res = query.range(start, start + page_size - 1).execute()
        batch = getattr(res, "data", None) or []

        rows.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    return rows

def _sb_insert_many(table_name: str, rows: list[dict]):
    if not rows:
        return
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        supabase_client.table(table_name).insert(rows[i:i + chunk_size]).execute()

def _snake_to_title_col(c: str) -> str:
    mapping = {
        "id": "id",
        "created_at": "Created At",

        "date": "Date",
        "booking_date": "Date",
        "customer_name": "Customer Name",
        "wing": "Wing",
        "floor": "Floor",
        "flat_number": "Flat Number",
        "type": "Type",
        "unit_type": "Type",

        "final_price": "Final Price",
        "rate": "Rate",
        "agreement_cost": "Agreement Cost",
        "lead_type": "Lead Type",
        "sales_executive": "Sales Executive",
        "month": "Month",

        "agreement_done": "Agreement Done",
        "stamp_duty": "Stamp Duty",
        "stamp_duty_percent": "Stamp Duty %",
        "received_amount": "Received Amount",
    }
    return mapping.get(str(c).strip().lower(), str(c).strip())

def _master_db_to_app_col(c: str) -> str:
    mapping = {
        "id": "id",
        "created_at": "Created At",
        "wing": "Wing",
        "slab_name": "Slab Name",
        "completed": "Completed",
        "completed_on": "Completed On",
    }
    return mapping.get(str(c).strip().lower(), str(c).strip())

def _refresh_booking_df():
    try:
        rows = _sb_select_all(BOOKINGS_TABLE, order_col="id")
        dfx = pd.DataFrame(rows)

        if dfx.empty:
            return pd.DataFrame()

        dfx = dfx.rename(columns={c: _snake_to_title_col(c) for c in dfx.columns})
        return dfx

    except Exception as e:
        st.error(f"Could not read Supabase table `{BOOKINGS_TABLE}`: {e}")
        return pd.DataFrame()

def _refresh_master_df():
    try:
        rows = _sb_select_all(CASHFLOW_MASTER_TABLE, order_col="id")
        dfx = pd.DataFrame(rows)

        if dfx.empty:
            return pd.DataFrame(columns=CASHFLOW_MASTER_HEADERS)

        dfx = dfx.rename(columns={c: _master_db_to_app_col(c) for c in dfx.columns})

        for c in CASHFLOW_MASTER_HEADERS:
            if c not in dfx.columns:
                dfx[c] = ""

        dfx["Wing"] = dfx["Wing"].apply(_cf_norm_wing)
        dfx["Slab Name"] = dfx["Slab Name"].fillna("").astype(str).str.strip().str.upper()
        dfx["Completed"] = dfx["Completed"].fillna("").astype(str).str.strip()
        dfx["Completed On"] = dfx["Completed On"].fillna("").astype(str).str.strip()

        return dfx[CASHFLOW_MASTER_HEADERS].copy()

    except Exception as e:
        st.error(f"Could not read Supabase table `{CASHFLOW_MASTER_TABLE}`: {e}")
        return pd.DataFrame(columns=CASHFLOW_MASTER_HEADERS)

def _ensure_booking_columns(dfx):
    dfx = dfx.copy()

    required = [
        "id",
        "Date",
        "Customer Name",
        "Wing",
        "Floor",
        "Flat Number",
        "Type",
        "Agreement Cost",
        "Agreement Done",
        "Stamp Duty",
        "Stamp Duty %",
        "Received Amount",
    ]

    for c in required:
        if c not in dfx.columns:
            dfx[c] = ""

    dfx["Wing"] = dfx["Wing"].apply(_cf_norm_wing)
    dfx["Flat Number"] = dfx["Flat Number"].apply(_cf_norm_flat)
    dfx["Agreement Cost"] = dfx["Agreement Cost"].apply(_to_num)
    dfx["Stamp Duty %"] = dfx["Stamp Duty %"].apply(_to_num)
    dfx.loc[dfx["Stamp Duty %"] <= 0, "Stamp Duty %"] = 7.0
    dfx["Received Amount"] = dfx["Received Amount"].apply(_to_num)

    return dfx

def _update_booking_received_amount(row_id, new_received_amount):
    try:
        if row_id in ("", None) or pd.isna(row_id):
            return False, "Booking row id missing. Cannot safely update bookings table."

        supabase_client.table(BOOKINGS_TABLE).update({
            "received_amount": float(new_received_amount)
        }).eq("id", row_id).execute()

        return True, None

    except Exception as e:
        return False, str(e)

def _ensure_master_rows(master_df, booking_df):
    master_df = master_df.copy()

    for c in CASHFLOW_MASTER_HEADERS:
        if c not in master_df.columns:
            master_df[c] = ""

    if "Wing" in master_df.columns:
        master_df["Wing"] = master_df["Wing"].apply(_cf_norm_wing)

    wings = []
    if "Wing" in booking_df.columns:
        wings = sorted(
            booking_df["Wing"]
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .unique()
            .tolist()
        )

    existing_pairs = set(
        zip(
            master_df["Wing"].astype(str).str.strip().str.upper(),
            master_df["Slab Name"].astype(str).str.strip().str.upper()
        )
    )

    add_rows = []
    for wing in wings:
        for slab in CONSTRUCTION_SLABS:
            pair = (str(wing).strip().upper(), slab.strip().upper())
            if pair not in existing_pairs:
                add_rows.append({
                    "wing": wing,
                    "slab_name": slab,
                    "completed": "",
                    "completed_on": None,
                })

    if add_rows:
        try:
            _sb_insert_many(CASHFLOW_MASTER_TABLE, add_rows)
            master_df = _refresh_master_df()
        except Exception as e:
            st.error(f"Could not seed `{CASHFLOW_MASTER_TABLE}`: {e}")

    return master_df

def _update_cashflow_master_rows(edited_df: pd.DataFrame):
    try:
        updates = 0

        for _, r in edited_df.iterrows():
            row_id = r.get("id", None)
            if row_id in ("", None) or pd.isna(row_id):
                continue

            completed_val = str(r.get("Completed", "") or "").strip()
            completed_on_val = _date_to_iso_or_none(r.get("Completed On", ""))

            supabase_client.table(CASHFLOW_MASTER_TABLE).update({
                "completed": completed_val,
                "completed_on": completed_on_val,
            }).eq("id", row_id).execute()

            updates += 1

        return True, updates, None

    except Exception as e:
        return False, 0, str(e)

# ============================================================
# CASHFLOW CALC HELPERS
# ============================================================
def _gst_rate(agreement_cost):
    return 0.05 if _to_num(agreement_cost) > 4499999 else 0.01

def _gross_agreement_value(agreement_cost):
    agr = _to_num(agreement_cost)
    gst_rate = _gst_rate(agr)
    gst_amt = round(agr * gst_rate, 2)
    gross_val = round(agr + gst_amt, 2)
    return gross_val, gst_amt

def _head_amounts(agreement_cost):
    gross_value, gst_amt = _gross_agreement_value(agreement_cost)

    amt_map = {
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
        "_GST_TOTAL": gst_amt,
        "_GROSS_VALUE": gross_value,
    }
    return amt_map

def _highest_completed_slab(wing, master_df):
    wing = _cf_norm_wing(wing).upper()
    sub = master_df[
        master_df["Wing"].astype(str).str.strip().str.upper() == wing
    ].copy()

    if sub.empty:
        return None

    completed_set = set(
        sub.loc[
            sub["Completed"].astype(str).str.strip().str.lower().eq("completed"),
            "Slab Name"
        ].astype(str).str.strip().str.upper().tolist()
    )

    highest = None
    for slab in CONSTRUCTION_SLABS:
        if slab.strip().upper() in completed_set:
            highest = slab
    return highest

def _full_allocation_order(row):
    order = ["BOOKING AMOUNT"]
    if _is_done(row.get("Agreement Done", "")):
        order.append("AGREEMENT")
        order.extend(CONSTRUCTION_SLABS)
    return order

def _due_till_date_order(row, master_df):
    order = ["BOOKING AMOUNT"]

    if _is_done(row.get("Agreement Done", "")):
        order.append("AGREEMENT")
        highest = _highest_completed_slab(row.get("Wing", ""), master_df)
        if highest is not None:
            upto = CONSTRUCTION_SLABS.index(highest)
            order.extend(CONSTRUCTION_SLABS[:upto + 1])

    return order

def _allocate_cumulative_received(row):
    amt_map = _head_amounts(row.get("Agreement Cost", 0))
    order = _full_allocation_order(row)

    total_received = _to_num(row.get("Received Amount", 0))
    remaining = round(total_received, 2)
    alloc = {}

    for head in order:
        due_amt = _to_num(amt_map.get(head, 0))
        take = min(remaining, due_amt)
        alloc[head] = round(take, 2)
        remaining = round(remaining - take, 2)
        if remaining <= 0:
            break

    for head in GRAPH_HEAD_ORDER:
        if head not in alloc:
            alloc[head] = 0.0

    return {
        "gross_received": total_received,
        "unallocated_received": max(remaining, 0.0),
        "alloc_map": alloc,
        "amt_map": amt_map,
    }

def _stamp_duty_amount(row):
    return round(
        _to_num(row.get("Agreement Cost", 0)) *
        _to_num(row.get("Stamp Duty %", 7)) / 100.0,
        2
    )

def _customer_summary(row, master_df):
    alloc_data = _allocate_cumulative_received(row)
    amt_map = alloc_data["amt_map"]
    due_order = _due_till_date_order(row, master_df)

    collection_heads_due = [h for h in due_order if h in GRAPH_HEAD_ORDER]
    collection_due_till = sum(_to_num(amt_map.get(h, 0)) for h in collection_heads_due)

    stamp_amt = _stamp_duty_amount(row)
    stamp_paid = _is_received(row.get("Stamp Duty", ""))
    registration_paid = _is_received(row.get("Stamp Duty", ""))

    received_amount_punched = _to_num(row.get("Received Amount", 0))

    collection_till_date = collection_due_till
    received_till_date = received_amount_punched
    due_till_date = max(collection_till_date - received_till_date, 0.0)

    received_pct = _pct(received_till_date, collection_till_date)
    due_pct = _pct(due_till_date, collection_till_date)

    stamp_pending = 0.0 if stamp_paid else stamp_amt
    registration_pending = 0.0 if registration_paid else REGISTRATION_AMOUNT

    customer_total_due_including_statutory = due_till_date + stamp_pending + registration_pending

    overall_order = _full_allocation_order(row)
    overall_collection_total = sum(_to_num(amt_map.get(h, 0)) for h in overall_order)
    overall_received_total = (
        received_amount_punched +
        (stamp_amt if stamp_paid else 0.0) +
        (REGISTRATION_AMOUNT if registration_paid else 0.0)
    )
    overall_pending_total = max(
        overall_collection_total + stamp_pending + registration_pending - overall_received_total,
        0.0
    )

    return {
        "alloc_data": alloc_data,
        "due_order": due_order,
        "collection_due_till": collection_due_till,
        "gross_value": _to_num(amt_map.get("_GROSS_VALUE", 0)),
        "gst_total": _to_num(amt_map.get("_GST_TOTAL", 0)),
        "stamp_amt": stamp_amt,
        "stamp_paid": stamp_paid,
        "registration_paid": registration_paid,
        "stamp_pending": stamp_pending,
        "registration_pending": registration_pending,
        "collection_till_date": collection_till_date,
        "received_till_date": received_till_date,
        "due_till_date": due_till_date,
        "received_pct": received_pct,
        "due_pct": due_pct,
        "customer_total_due_including_statutory": customer_total_due_including_statutory,
        "overall_pending_total": overall_pending_total,
        "overall_collection_total": overall_collection_total,
        "overall_received_total": overall_received_total,
    }

def _build_customer_slab_table(row, master_df):
    sm = _customer_summary(row, master_df)
    amt_map = sm["alloc_data"]["amt_map"]
    alloc_map = sm["alloc_data"]["alloc_map"]
    due_order = set(sm["due_order"])

    rows = []
    for head in GRAPH_HEAD_ORDER:
        due_amt = _to_num(amt_map.get(head, 0))
        rec_amt = _to_num(alloc_map.get(head, 0))
        rows.append({
            "Head": head,
            "Amount": due_amt,
            "Allocated from Received": rec_amt,
            "Balance": max(due_amt - rec_amt, 0.0),
            "Due Till Date?": "Yes" if head in due_order else "No"
        })

    out = pd.DataFrame(rows)
    out["Head"] = pd.Categorical(out["Head"], categories=GRAPH_HEAD_ORDER, ordered=True)
    out = out.sort_values("Head").reset_index(drop=True)
    return out

def _build_wing_summary(booking_df, master_df):
    if booking_df.empty:
        return pd.DataFrame()

    rows = []
    wings = sorted(
        booking_df["Wing"].astype(str).str.strip().replace("", pd.NA).dropna().unique().tolist()
    ) if "Wing" in booking_df.columns else []

    for wing in wings:
        sub = booking_df[booking_df["Wing"].astype(str).str.strip() == wing].copy()
        if sub.empty:
            continue

        wing_collection = 0.0
        wing_received = 0.0

        for _, r in sub.iterrows():
            sm = _customer_summary(r, master_df)
            wing_collection += sm["collection_till_date"]
            wing_received += sm["received_till_date"]

        wing_due = max(wing_collection - wing_received, 0.0)
        wing_received_pct = _pct(wing_received, wing_collection)
        wing_due_pct = _pct(wing_due, wing_collection)

        rows.append({
            "Wing": wing,
            "Collection Till Date": wing_collection,
            "Received Till Date": wing_received,
            "Due Till Date": wing_due,
            "Received %": wing_received_pct,
            "Due %": wing_due_pct,
            "Status": _highest_completed_slab(wing, master_df) or "Booking / Agreement Stage"
        })

    return pd.DataFrame(rows)

def _customer_option_label(r):
    return (
        f"{_safe_str(r.get('Customer Name'))} | "
        f"Wing {_safe_str(r.get('Wing'))} | "
        f"Floor {_safe_str(r.get('Floor'))} | "
        f"Flat {_safe_str(r.get('Flat Number'))} | "
        f"{_fmt_money(r.get('Agreement Cost', 0))}"
    )

# ============================================================
# DUE TABLE HELPERS
# ============================================================
def _cf_flat_number_from_floor_series(floor_no, series):
    return f"{floor_no}{series}"

def _cf_base_category(wing, floor_no, series):
    if (wing, floor_no, series) in DUE_MISSING_UNITS:
        return "MISSING"
    if (floor_no, series) in DUE_REFUGE_RULES.get(wing, set()):
        return "REFUGE"

    mhada_rule = DUE_MHADA_RULES.get(wing, {"floors": set(), "series": set()})
    if floor_no in mhada_rule["floors"] and series in mhada_rule["series"]:
        return "MHADA"

    flat_no = _cf_flat_number_from_floor_series(floor_no, series)
    if flat_no in DUE_LANDOWNER_FLATS.get(wing, set()):
        return "LANDOWNER"

    return "OUR"

def _cf_get_unit_type(wing, floor_no, series, base_category):
    if base_category == "REFUGE":
        return "Refuge"
    if base_category == "MISSING":
        return ""
    return DUE_TYPE_OVERRIDES.get((wing, floor_no, series), DUE_SERIES_TYPE_MAP.get(series, ""))

def _build_due_visual_inventory_master():
    rows = []
    wings = ["B Wing", "C Wing", "E Wing", "F Wing"]
    series_all = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

    for wing in wings:
        for floor_no in range(1, 14):
            for series in series_all:
                base_category = _cf_base_category(wing, floor_no, series)
                flat_no = _cf_flat_number_from_floor_series(floor_no, series)
                unit_type = _cf_get_unit_type(wing, floor_no, series, base_category)

                rows.append({
                    "Wing": wing,
                    "Floor No.": floor_no,
                    "Series": series,
                    "Flat Number": flat_no,
                    "Base Category": base_category,
                    "Type": unit_type,
                })

    return pd.DataFrame(rows)

def _prepare_due_booking_map(booking_df_in, master_df_in):
    cols = [
        "Wing", "Flat Number", "Customer Name", "Due Amount", "Collection Till Date",
        "Received Till Date", "Gross Agreement Value", "Agreement Cost", "Due %", "Received %"
    ]
    if booking_df_in is None or booking_df_in.empty:
        return pd.DataFrame(columns=cols)

    d = booking_df_in.copy()
    d["Wing"] = d["Wing"].apply(_cf_norm_wing) if "Wing" in d.columns else ""
    d["Flat Number"] = d["Flat Number"].apply(_cf_norm_flat) if "Flat Number" in d.columns else ""
    d["Customer Name"] = d["Customer Name"].fillna("").astype(str).str.strip() if "Customer Name" in d.columns else ""

    d = d[(d["Wing"] != "") & (d["Flat Number"] != "")].copy()

    rows = []
    for _, r in d.iterrows():
        sm = _customer_summary(r, master_df_in)
        rows.append({
            "Wing": _cf_norm_wing(r.get("Wing", "")),
            "Flat Number": _cf_norm_flat(r.get("Flat Number", "")),
            "Customer Name": _safe_str(r.get("Customer Name", "")),
            "Due Amount": float(sm["due_till_date"]),
            "Collection Till Date": float(sm["collection_till_date"]),
            "Received Till Date": float(sm["received_till_date"]),
            "Gross Agreement Value": float(sm["gross_value"]),
            "Agreement Cost": _to_num(r.get("Agreement Cost", 0)),
            "Due %": float(sm["due_pct"]),
            "Received %": float(sm["received_pct"]),
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=cols)

    out = out.sort_values(["Wing", "Flat Number"]).drop_duplicates(subset=["Wing", "Flat Number"], keep="last")
    return out[cols].copy()

def _build_due_matrix_df(booking_df_in, master_df_in):
    base_df = _build_due_visual_inventory_master().copy()

    due_booking_df = _prepare_due_booking_map(booking_df_in, master_df_in)
    if not due_booking_df.empty:
        base_df = base_df.merge(due_booking_df, on=["Wing", "Flat Number"], how="left")
    else:
        base_df["Customer Name"] = ""
        base_df["Due Amount"] = 0.0
        base_df["Collection Till Date"] = 0.0
        base_df["Received Till Date"] = 0.0
        base_df["Gross Agreement Value"] = 0.0
        base_df["Agreement Cost"] = 0.0
        base_df["Due %"] = 0.0
        base_df["Received %"] = 0.0

    base_df["Customer Name"] = base_df["Customer Name"].fillna("").astype(str).str.strip()

    for c in ["Due Amount", "Collection Till Date", "Received Till Date", "Gross Agreement Value", "Agreement Cost", "Due %", "Received %"]:
        base_df[c] = pd.to_numeric(base_df.get(c, 0), errors="coerce").fillna(0.0)

    special_mask = base_df["Base Category"].isin(["LANDOWNER", "MHADA"])
    base_df.loc[special_mask, "Customer Name"] = ""
    base_df.loc[special_mask, ["Due Amount", "Collection Till Date", "Received Till Date", "Gross Agreement Value", "Agreement Cost", "Due %", "Received %"]] = 0.0

    base_df["Has Booking"] = base_df["Customer Name"].ne("")
    base_df["Due Bucket"] = "AVAILABLE"

    base_df.loc[base_df["Base Category"].eq("REFUGE"), "Due Bucket"] = "REFUGE"
    base_df.loc[base_df["Base Category"].eq("MISSING"), "Due Bucket"] = "MISSING"
    base_df.loc[base_df["Base Category"].eq("LANDOWNER"), "Due Bucket"] = "LANDOWNER"
    base_df.loc[base_df["Base Category"].eq("MHADA"), "Due Bucket"] = "MHADA"

    base_df.loc[base_df["Has Booking"] & (base_df["Due Amount"] > 0.5), "Due Bucket"] = "BOOKED_DUE"
    base_df.loc[base_df["Has Booking"] & (base_df["Due Amount"] <= 0.5), "Due Bucket"] = "BOOKED_CLEAR"

    return base_df

def _truncate_name_for_cell(name, max_len=15):
    name = _safe_str(name)
    if len(name) <= max_len:
        return name
    return name[:max_len - 1] + "…"

def _due_cell_view(row):
    bucket = _safe_str(row.get("Due Bucket", "")).upper()
    flat_no = _safe_str(row.get("Flat Number", ""))
    unit_type = _safe_str(row.get("Type", ""))
    customer = _safe_str(row.get("Customer Name", ""))
    due_amt = _to_num(row.get("Due Amount", 0))
    due_pct = _to_num(row.get("Due %", 0))
    rec_pct = _to_num(row.get("Received %", 0))

    if bucket == "MISSING":
        return {"css": "due-hidden", "flat": "", "sub1": "", "sub2": "", "sub3": "", "tooltip": ""}

    if bucket == "REFUGE":
        return {
            "css": "due-refuge",
            "flat": flat_no,
            "sub1": "Refuge",
            "sub2": "",
            "sub3": "",
            "tooltip": f"Flat: {flat_no}\nCategory: Refuge"
        }

    if bucket == "LANDOWNER":
        return {
            "css": "due-landowner",
            "flat": flat_no,
            "sub1": "Landowner",
            "sub2": unit_type,
            "sub3": "",
            "tooltip": f"Flat: {flat_no}\nCategory: Landowner\nType: {unit_type}"
        }

    if bucket == "MHADA":
        return {
            "css": "due-mhada",
            "flat": flat_no,
            "sub1": "MHADA",
            "sub2": unit_type,
            "sub3": "",
            "tooltip": f"Flat: {flat_no}\nCategory: MHADA\nType: {unit_type}"
        }

    if bucket == "BOOKED_DUE":
        return {
            "css": "due-pending",
            "flat": flat_no,
            "sub1": _truncate_name_for_cell(customer, 16),
            "sub2": _fmt_money(due_amt),
            "sub3": f"D {due_pct:.0f}% | R {rec_pct:.0f}%",
            "tooltip": f"Flat: {flat_no}\nCustomer: {customer}\nDue: {_fmt_money(due_amt)}\nDue %: {due_pct:.1f}%\nReceived %: {rec_pct:.1f}%\nType: {unit_type}"
        }

    if bucket == "BOOKED_CLEAR":
        return {
            "css": "due-clear",
            "flat": flat_no,
            "sub1": _truncate_name_for_cell(customer, 16),
            "sub2": "No Due",
            "sub3": f"D {due_pct:.0f}% | R {rec_pct:.0f}%",
            "tooltip": f"Flat: {flat_no}\nCustomer: {customer}\nDue: {_fmt_money(due_amt)}\nDue %: {due_pct:.1f}%\nReceived %: {rec_pct:.1f}%\nType: {unit_type}"
        }

    return {
        "css": "due-available",
        "flat": flat_no,
        "sub1": "Available",
        "sub2": unit_type,
        "sub3": "",
        "tooltip": f"Flat: {flat_no}\nType: {unit_type}\nStatus: Available"
    }

def _build_due_wing_matrix_html(wing_df, wing_name):
    layout_order = DUE_WING_LAYOUT_ORDER[wing_name]
    floors = list(range(13, 0, -1))

    html = []
    html.append("<div class='due-grid-wrap'>")
    html.append("<table class='due-grid-table'>")
    html.append("<thead>")
    html.append(f"<tr class='due-title-row'><th colspan='{len(layout_order)}'>{escape(wing_name)} — Due Table</th></tr>")
    html.append("<tr>")
    for _ in layout_order:
        html.append("<th class='due-blank-head'></th>")
    html.append("</tr>")
    html.append("</thead>")
    html.append("<tbody>")

    for floor_no in floors:
        html.append("<tr>")
        floor_df = wing_df[wing_df["Floor No."] == floor_no].copy()
        floor_map = {row["Series"]: row for _, row in floor_df.iterrows()}

        for series in layout_order:
            row = floor_map[series]
            cell = _due_cell_view(row)
            tooltip = escape(cell["tooltip"]) if cell["tooltip"] else ""

            html.append(
                f"<td class='due-cell {cell['css']}' title='{tooltip}'>"
                f"<div class='due-flat'>{escape(cell['flat']) if cell['flat'] else '&nbsp;'}</div>"
                f"<div class='due-sub due-sub1'>{escape(cell['sub1']) if cell['sub1'] else '&nbsp;'}</div>"
                f"<div class='due-sub due-sub2'>{escape(cell['sub2']) if cell['sub2'] else '&nbsp;'}</div>"
                f"<div class='due-sub due-sub3'>{escape(cell['sub3']) if cell['sub3'] else '&nbsp;'}</div>"
                f"</td>"
            )

        html.append("</tr>")

    html.append("</tbody></table></div>")
    return "".join(html)

def _build_due_widget_html(due_matrix_df, wing_summary_df_in):
    wing_order = ["B Wing", "C Wing", "E Wing", "F Wing"]

    tabs_html = []
    panels_html = []

    for i, wing_name in enumerate(wing_order):
        wing_df = due_matrix_df[due_matrix_df["Wing"] == wing_name].copy()

        wing_collection = 0.0
        wing_received = 0.0
        wing_due = 0.0
        wing_received_pct = 0.0
        wing_due_pct = 0.0

        booked_units = 0
        due_units = 0
        clear_units = 0

        if not wing_df.empty:
            booked_units = int(wing_df["Has Booking"].sum())
            due_units = int((wing_df["Has Booking"] & (wing_df["Due Amount"] > 0.5)).sum())
            clear_units = int((wing_df["Has Booking"] & (wing_df["Due Amount"] <= 0.5)).sum())

        if not wing_summary_df_in.empty and wing_name in set(wing_summary_df_in["Wing"].astype(str).str.strip()):
            ws_row = wing_summary_df_in[wing_summary_df_in["Wing"].astype(str).str.strip() == wing_name].iloc[0]
            wing_collection = _to_num(ws_row["Collection Till Date"])
            wing_received = _to_num(ws_row["Received Till Date"])
            wing_due = _to_num(ws_row["Due Till Date"])
            wing_received_pct = _to_num(ws_row["Received %"])
            wing_due_pct = _to_num(ws_row["Due %"])

        wing_id = wing_name.lower().replace(" ", "_")

        tabs_html.append(
            f"<button class='due-tab {'active' if i == 0 else ''}' onclick=\"showDueWing('{wing_id}', this)\">{escape(wing_name)}</button>"
        )

        panels_html.append(
            f"""
            <div class="due-panel {'active' if i == 0 else ''}" id="{wing_id}">
                <div class="due-kpis">
                    <div class="due-kpi"><div class="due-kpi-label">Collection</div><div class="due-kpi-value">{_fmt_money(wing_collection)}</div></div>
                    <div class="due-kpi"><div class="due-kpi-label">Received</div><div class="due-kpi-value">{_fmt_money(wing_received)}</div></div>
                    <div class="due-kpi"><div class="due-kpi-label">Due</div><div class="due-kpi-value">{_fmt_money(wing_due)}</div></div>
                    <div class="due-kpi"><div class="due-kpi-label">Received %</div><div class="due-kpi-value">{wing_received_pct:.1f}%</div></div>
                    <div class="due-kpi"><div class="due-kpi-label">Due %</div><div class="due-kpi-value">{wing_due_pct:.1f}%</div></div>
                    <div class="due-kpi"><div class="due-kpi-label">Due Units</div><div class="due-kpi-value">{due_units}/{booked_units}</div></div>
                </div>

                <div class="due-legend">
                    <span class="due-pill due-pill-pending">Booked with Due</span>
                    <span class="due-pill due-pill-clear">Booked - No Due</span>
                    <span class="due-pill due-pill-available">Available</span>
                    <span class="due-pill due-pill-landowner">Landowner</span>
                    <span class="due-pill due-pill-mhada">MHADA</span>
                    <span class="due-pill due-pill-refuge">Refuge</span>
                </div>

                {_build_due_wing_matrix_html(wing_df, wing_name)}
            </div>
            """
        )

    return f"""
    <style>
    .due-shell {{
        font-family: Arial, sans-serif;
        background: #ffffff;
        color: #111827;
        padding: 8px;
        box-sizing: border-box;
    }}
    .due-topbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }}
    .due-title {{
        font-size: 22px;
        font-weight: 900;
        color: #111827;
    }}
    .due-btn {{
        border: none;
        background: #334155;
        color: #fff;
        padding: 10px 14px;
        border-radius: 10px;
        font-weight: 700;
        cursor: pointer;
    }}
    .due-tabs {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }}
    .due-tab {{
        border: none;
        padding: 10px 14px;
        border-radius: 10px;
        cursor: pointer;
        font-weight: 800;
        background: #e5edf5;
        color: #2a4158;
    }}
    .due-tab.active {{
        background: #2f7db8;
        color: white;
    }}
    .due-panel {{
        display: none;
    }}
    .due-panel.active {{
        display: block;
    }}
    .due-kpis {{
        display: grid;
        grid-template-columns: repeat(3, minmax(150px, 1fr));
        gap: 12px;
        margin-bottom: 12px;
    }}
    .due-kpi {{
        background: #ffffff;
        border-radius: 14px;
        padding: 14px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #e8edf3;
    }}
    .due-kpi-label {{
        font-size: 12px;
        color: #667085;
        font-weight: 700;
    }}
    .due-kpi-value {{
        font-size: 24px;
        font-weight: 900;
        margin-top: 6px;
        color: #111827;
    }}
    .due-legend {{
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 12px;
        font-weight: 700;
        font-size: 13px;
    }}
    .due-pill {{
        padding: 5px 10px;
        border-radius: 999px;
    }}
    .due-pill-pending {{ background:#ffedd5; color:#9a3412; }}
    .due-pill-clear {{ background:#dcfce7; color:#166534; }}
    .due-pill-available {{ background:#fff7cc; color:#8a5b00; }}
    .due-pill-landowner {{ background:#dcfce7; color:#166534; }}
    .due-pill-mhada {{ background:#dbeafe; color:#1d4ed8; }}
    .due-pill-refuge {{ background:#ffe1e1; color:#b10000; }}
    .due-grid-wrap {{
        overflow-x: auto;
        overflow-y: visible;
        width: 100%;
    }}
    .due-grid-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }}
    .due-grid-table th,
    .due-grid-table td {{
        border: 2px solid #111;
    }}
    .due-title-row th {{
        background: #efefef;
        color: #111;
        font-size: 22px;
        font-weight: 900;
        padding: 6px 8px;
    }}
    .due-blank-head {{
        background: #efefef;
        height: 20px;
    }}
    .due-cell {{
        height: 84px;
        text-align: center;
        vertical-align: middle;
        padding: 3px;
    }}
    .due-flat {{
        font-size: 20px;
        font-weight: 900;
        line-height: 1.0;
    }}
    .due-sub {{
        line-height: 1.0;
        font-weight: 800;
    }}
    .due-sub1 {{
        font-size: 10px;
        margin-top: 4px;
    }}
    .due-sub2 {{
        font-size: 11px;
        margin-top: 4px;
    }}
    .due-sub3 {{
        font-size: 9px;
        margin-top: 4px;
    }}
    .due-pending {{
        background: #fed7aa;
        color: #7c2d12;
    }}
    .due-clear {{
        background: #16a34a;
        color: white;
    }}
    .due-available {{
        background: #f6c343;
        color: #111827;
    }}
    .due-landowner {{
        background: #0b8a00;
        color: white;
    }}
    .due-mhada {{
        background: #2563eb;
        color: white;
    }}
    .due-refuge {{
        background: #ff1b1b;
        color: white;
    }}
    .due-hidden {{
        background: #d9d9d9;
        color: #d9d9d9;
    }}
    #dueTableWidget:fullscreen {{
        background: white;
        width: 100vw;
        height: 100vh;
        overflow: auto;
        padding: 18px;
        box-sizing: border-box;
    }}
    </style>

    <div class="due-shell" id="dueTableWidget">
        <div class="due-topbar">
            <div class="due-title">Due Table</div>
            <button class="due-btn" onclick="openDueFullScreen()">Open Full Screen</button>
        </div>

        <div class="due-tabs">
            {''.join(tabs_html)}
        </div>

        {''.join(panels_html)}
    </div>

    <script>
    function showDueWing(id, btn) {{
        document.querySelectorAll('.due-panel').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.due-tab').forEach(el => el.classList.remove('active'));
        document.getElementById(id).classList.add('active');
        btn.classList.add('active');
    }}

    function openDueFullScreen() {{
        const elem = document.getElementById('dueTableWidget');
        if (elem.requestFullscreen) {{
            elem.requestFullscreen();
        }} else if (elem.webkitRequestFullscreen) {{
            elem.webkitRequestFullscreen();
        }} else if (elem.msRequestFullscreen) {{
            elem.msRequestFullscreen();
        }}
    }}
    </script>
    """

# ============================================================
# LOAD LIVE DATA FROM SUPABASE
# ============================================================
live_booking_df = _refresh_booking_df()
live_booking_df = _ensure_booking_columns(live_booking_df)

live_master_df = _refresh_master_df()
live_master_df = _ensure_master_rows(live_master_df, live_booking_df)

wing_summary_df = _build_wing_summary(live_booking_df, live_master_df)

# ============================================================
# SUBTABS
# ============================================================
cf_receipt_tab, cf_dashboard_tab, cf_master_tab, cf_due_tab = st.tabs(
    ["Receipt Punching", "Cashflow Dashboard", "Cashflow Slab Master", "Due Table"]
)

# ============================================================
# SUBTAB 1: RECEIPT PUNCHING
# ============================================================
with cf_receipt_tab:
    st.markdown("<div class='section-subtitle'>🧾 Receipt Punching</div>", unsafe_allow_html=True)

    receipt_success_msg = st.session_state.pop("cashflow_receipt_success_msg", "")
    if receipt_success_msg:
        st.success(receipt_success_msg)

    if not live_booking_df.empty:
        form_df = live_booking_df.copy()
        form_df["_label_"] = form_df.apply(_customer_option_label, axis=1)
        form_options = form_df["_label_"].tolist()

        if "cashflow_detail_customer" not in st.session_state and form_options:
            st.session_state["cashflow_detail_customer"] = form_options[0]

        with st.form("cashflow_receipt_form", clear_on_submit=True):
            form_customer = st.selectbox("Select Customer", options=form_options, key="cashflow_form_customer")
            form_amount = st.number_input(
                "Received Amount",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                key="cashflow_form_amount"
            )

            submitted = st.form_submit_button("Add Receipt")

            if submitted:
                if not form_customer:
                    st.error("Please select a customer.")
                elif form_amount <= 0:
                    st.error("Please enter amount greater than 0.")
                else:
                    sel_idx = form_df.index[form_df["_label_"] == form_customer][0]

                    current_received = _to_num(live_booking_df.at[sel_idx, "Received Amount"])
                    new_received_amount = round(current_received + _to_num(form_amount), 2)
                    row_id = live_booking_df.at[sel_idx, "id"] if "id" in live_booking_df.columns else None

                    ok, err = _update_booking_received_amount(row_id, new_received_amount)

                    if ok:
                        st.session_state["cashflow_detail_customer"] = form_customer
                        st.session_state["cashflow_receipt_success_msg"] = (
                            f"Received Amount updated from {_fmt_money(current_received)} "
                            f"to {_fmt_money(new_received_amount)}."
                        )
                        st.rerun()
                    else:
                        st.error(f"Could not update Supabase bookings table: {err}")

    else:
        st.info("No bookings found in Supabase table `bookings`.")

# ============================================================
# SUBTAB 2: DASHBOARD
# ============================================================
with cf_dashboard_tab:
    total_collection_all = wing_summary_df["Collection Till Date"].sum() if not wing_summary_df.empty else 0.0
    total_received_all = wing_summary_df["Received Till Date"].sum() if not wing_summary_df.empty else 0.0
    total_due_all = max(total_collection_all - total_received_all, 0.0)
    total_received_pct_all = _pct(total_received_all, total_collection_all)
    total_due_pct_all = _pct(total_due_all, total_collection_all)

    t1, t2, t3 = st.columns(3)
    with t1:
        _cf_card("Total Collection — All Wings", _fmt_money(total_collection_all), "cf-blue", "30% at plinth means 30% of Agreement Cost + GST")
    with t2:
        _cf_card("Total Received — All Wings", _fmt_money(total_received_all), "cf-green", f"Received {total_received_pct_all:.1f}%")
    with t3:
        _cf_card("Total Due — All Wings", _fmt_money(total_due_all), "cf-amber", f"Due {total_due_pct_all:.1f}%")

    st.markdown("<div class='section-subtitle'>🏢 Wing-wise Cashflow Status</div>", unsafe_allow_html=True)

    if wing_summary_df.empty:
        st.info("No wing-wise data available.")
    else:
        for _, wr in wing_summary_df.iterrows():
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                _cf_card(f"{wr['Wing']} — Collection Till Date", _fmt_money(wr["Collection Till Date"]), "cf-slate")
            with c2:
                _cf_card(f"{wr['Wing']} — Received Till Date", _fmt_money(wr["Received Till Date"]), "cf-green", f"{_to_num(wr['Received %']):.1f}%")
            with c3:
                _cf_card(f"{wr['Wing']} — Due Till Date", _fmt_money(wr["Due Till Date"]), "cf-amber", f"{_to_num(wr['Due %']):.1f}%")
            with c4:
                _cf_card(f"{wr['Wing']} — Status", wr["Status"], "cf-neutral")

    st.markdown("<div class='section-subtitle'>👤 Customer-wise Details</div>", unsafe_allow_html=True)

    if not live_booking_df.empty:
        detail_df = live_booking_df.copy()
        detail_df["_label_"] = detail_df.apply(_customer_option_label, axis=1)
        detail_options = detail_df["_label_"].tolist()

        default_idx = 0
        if st.session_state.get("cashflow_detail_customer") in detail_options:
            default_idx = detail_options.index(st.session_state.get("cashflow_detail_customer"))

        selected_detail_customer = st.selectbox(
            "Select Customer to View Full Details",
            options=detail_options,
            index=default_idx,
            key="cashflow_detail_customer_selector"
        )

        st.session_state["cashflow_detail_customer"] = selected_detail_customer

        detail_idx = detail_df.index[detail_df["_label_"] == selected_detail_customer][0]
        detail_row = live_booking_df.loc[detail_idx].copy()
        detail_sm = _customer_summary(detail_row, live_master_df)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            _cf_card("Agreement Cost", _fmt_money(detail_row.get("Agreement Cost", 0)), "cf-blue")
        with d2:
            _cf_card("Gross Agreement Value", _fmt_money(detail_sm["gross_value"]), "cf-blue", "Agreement Cost + GST")
        with d3:
            _cf_card("Total Received", _fmt_money(detail_row.get("Received Amount", 0)), "cf-green", f"{detail_sm['received_pct']:.1f}%")
        with d4:
            _cf_card("Collection Till Date", _fmt_money(detail_sm["collection_till_date"]), "cf-slate", "Gross slab demand only")

        d5, d6, d7, d8 = st.columns(4)
        with d5:
            _cf_card("Due Till Date", _fmt_money(detail_sm["due_till_date"]), "cf-amber", f"{detail_sm['due_pct']:.1f}%")
        with d6:
            allocated_total = sum(_to_num(v) for v in detail_sm["alloc_data"]["alloc_map"].values())
            _cf_card("Allocated from Received", _fmt_money(allocated_total), "cf-neutral")
        with d7:
            _cf_card("GST on Agreement", _fmt_money(detail_sm["gst_total"]), "cf-neutral")
        with d8:
            highest_done_local = _highest_completed_slab(detail_row.get("Wing", ""), live_master_df) or "Booking / Agreement Stage"
            _cf_card("Current Demand Stage", highest_done_local, "cf-neutral")

        st.markdown("<div class='section-subtitle'>🧮 Customer Statutory Details</div>", unsafe_allow_html=True)
        statutory_df = pd.DataFrame([
            {
                "Head": "Stamp Duty",
                "Amount": detail_sm["stamp_amt"],
                "Status": "Paid" if detail_sm["stamp_paid"] else "Due",
                "Pending": detail_sm["stamp_pending"],
            },
            {
                "Head": "Registration",
                "Amount": REGISTRATION_AMOUNT,
                "Status": "Paid" if detail_sm["registration_paid"] else "Due",
                "Pending": detail_sm["registration_pending"],
            },
            {
                "Head": "Total Due incl. Statutory",
                "Amount": detail_sm["customer_total_due_including_statutory"],
                "Status": "",
                "Pending": detail_sm["customer_total_due_including_statutory"],
            },
        ])
        st.dataframe(statutory_df, use_container_width=True, hide_index=True)

        st.markdown("<div class='section-subtitle'>📋 Demand / Allocation Table</div>", unsafe_allow_html=True)
        slab_table = _build_customer_slab_table(detail_row, live_master_df)
        st.dataframe(slab_table, use_container_width=True, hide_index=True)

        cust_plot = slab_table.copy()[["Head", "Amount", "Allocated from Received"]]
        cust_plot["Head"] = pd.Categorical(cust_plot["Head"], categories=GRAPH_HEAD_ORDER, ordered=True)
        cust_plot = cust_plot.sort_values("Head")
        cust_plot = cust_plot.melt(id_vars="Head", var_name="Measure", value_name="Value")

        cust_chart = alt.Chart(cust_plot).mark_bar().encode(
            x=alt.X(
                "Head:N",
                title="Head",
                sort=GRAPH_HEAD_ORDER,
                axis=alt.Axis(labelAngle=0, labelLimit=220, labelOverlap=True)
            ),
            xOffset=alt.X("Measure:N", sort=["Amount", "Allocated from Received"]),
            y=alt.Y("Value:Q", title="Amount"),
            color=alt.Color("Measure:N", sort=["Amount", "Allocated from Received"], title="Measure"),
            tooltip=["Head:N", "Measure:N", alt.Tooltip("Value:Q", format=",")]
        )

        st.altair_chart(
            cust_chart.properties(
                title=alt.TitleParams(
                    "Selected Customer — Gross Slab Demand vs Allocation",
                    anchor="start",
                    fontSize=16,
                    fontWeight="bold",
                    dy=-5
                ),
                height=340,
                width=alt.Step(90)
            ).configure_title(anchor="start"),
            use_container_width=True
        )

# ============================================================
# SUBTAB 3: CASHFLOW SLAB MASTER
# ============================================================
with cf_master_tab:
    st.markdown("<div class='section-subtitle'>📄 Cashflow Slab Master</div>", unsafe_allow_html=True)
    st.info("This reads and updates Supabase table `cashflow_slab_master`.")

    if st.button("Refresh Cashflow Slab Master", use_container_width=True):
        st.rerun()

    fresh_master_df = _refresh_master_df()
    fresh_master_df = _ensure_master_rows(fresh_master_df, live_booking_df)

    if fresh_master_df.empty:
        st.info("No Cashflow Slab Master data found.")
    else:
        wings_available_master = sorted(
            fresh_master_df["Wing"].astype(str).str.strip().replace("", pd.NA).dropna().unique().tolist()
        )

        if not wings_available_master:
            st.info("No wings found in Cashflow Slab Master.")
        else:
            selected_master_wing = st.selectbox(
                "Select Wing",
                wings_available_master,
                key="cashflow_master_view_wing"
            )

            wing_df = fresh_master_df[
                fresh_master_df["Wing"].astype(str).str.strip().str.upper() ==
                selected_master_wing.strip().upper()
            ].copy()

            completed_count = int(
                wing_df["Completed"].astype(str).str.strip().str.lower().eq("completed").sum()
            ) if not wing_df.empty else 0

            highest_done = _highest_completed_slab(selected_master_wing, fresh_master_df) or "None"

            c1, c2 = st.columns(2)
            with c1:
                _cf_card("Completed Slabs", str(completed_count), "cf-neutral")
            with c2:
                _cf_card("Highest Completed Slab", highest_done, "cf-neutral")

            st.markdown("<div class='section-subtitle'>✏️ Edit Current Wing Status</div>", unsafe_allow_html=True)

            editable_cols = ["id", "Wing", "Slab Name", "Completed", "Completed On"]
            edit_df = wing_df[editable_cols].copy()

            edited_df = st.data_editor(
                edit_df,
                use_container_width=True,
                hide_index=True,
                disabled=["id", "Wing", "Slab Name"],
                column_config={
                    "Completed": st.column_config.SelectboxColumn(
                        "Completed",
                        options=["", "Completed"],
                        help="Select Completed once slab is completed."
                    ),
                    "Completed On": st.column_config.TextColumn(
                        "Completed On",
                        help="Use YYYY-MM-DD format. Leave blank if not completed."
                    ),
                },
                key=f"cashflow_master_editor_{selected_master_wing}"
            )

            if st.button("💾 Save Cashflow Slab Master Changes", use_container_width=True):
                ok, count, err = _update_cashflow_master_rows(edited_df)
                if ok:
                    st.success(f"Saved {count} row(s) to Supabase.")
                    st.rerun()
                else:
                    st.error(f"Could not save changes: {err}")

            st.markdown("<div class='section-subtitle'>📋 Full Cashflow Slab Master Table</div>", unsafe_allow_html=True)
            st.dataframe(fresh_master_df, use_container_width=True, hide_index=True)

# ============================================================
# SUBTAB 4: DUE TABLE
# ============================================================
with cf_due_tab:
    st.markdown("<div class='section-subtitle'>🏢 Due Table</div>", unsafe_allow_html=True)
    st.caption("Flat-wise due view. Booked flats show customer name, due amount, due %, and received %. MHADA and Landowner units do not carry any due logic.")

    due_matrix_df = _build_due_matrix_df(live_booking_df, live_master_df)

    overall_collection_due = wing_summary_df["Collection Till Date"].sum() if not wing_summary_df.empty else 0.0
    overall_received_due = wing_summary_df["Received Till Date"].sum() if not wing_summary_df.empty else 0.0
    overall_due_due = max(overall_collection_due - overall_received_due, 0.0)
    overall_received_pct_due = _pct(overall_received_due, overall_collection_due)
    overall_due_pct_due = _pct(overall_due_due, overall_collection_due)

    booked_units_total = int(due_matrix_df["Has Booking"].sum()) if not due_matrix_df.empty else 0
    due_units_total = int((due_matrix_df["Has Booking"] & (due_matrix_df["Due Amount"] > 0.5)).sum()) if not due_matrix_df.empty else 0
    clear_units_total = int((due_matrix_df["Has Booking"] & (due_matrix_df["Due Amount"] <= 0.5)).sum()) if not due_matrix_df.empty else 0

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        _cf_card("Overall Due", _fmt_money(overall_due_due), "cf-amber", f"{overall_due_pct_due:.1f}%")
    with d2:
        _cf_card("Overall Received", _fmt_money(overall_received_due), "cf-green", f"{overall_received_pct_due:.1f}%")
    with d3:
        _cf_card("Booked Units", f"{booked_units_total}", "cf-blue")
    with d4:
        _cf_card("Units With Due", f"{due_units_total}", "cf-rose", f"Clear: {clear_units_total}")

    if due_matrix_df.empty:
        st.info("No booking data available to build the due table.")
    else:
        components.html(
            _build_due_widget_html(due_matrix_df, wing_summary_df),
            height=980,
            scrolling=True
        )

        with st.expander("Show due details table", expanded=False):
            wing_for_due_details = st.selectbox(
                "Select Wing for Due Details",
                options=["B Wing", "C Wing", "E Wing", "F Wing"],
                key="due_details_wing_select"
            )

            wing_due_df = due_matrix_df[due_matrix_df["Wing"] == wing_for_due_details].copy()
            detail_cols = [
                "Wing", "Floor No.", "Flat Number", "Type", "Base Category",
                "Customer Name", "Collection Till Date", "Received Till Date",
                "Due Amount", "Received %", "Due %", "Gross Agreement Value",
                "Agreement Cost", "Due Bucket"
            ]

            for c in detail_cols:
                if c not in wing_due_df.columns:
                    wing_due_df[c] = ""

            wing_due_df = wing_due_df[detail_cols].copy()
            wing_due_df = wing_due_df.rename(columns={
                "Base Category": "Inventory Category",
                "Received %": "Received Percentage",
                "Due %": "Due Percentage",
                "Due Bucket": "Cell Status"
            })

            st.dataframe(wing_due_df, use_container_width=True, height=460)
