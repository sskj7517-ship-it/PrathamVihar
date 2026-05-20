# ============================================================
# TAB 15 — INVENTORY STATUS
# Supabase table used: public.holds
# ============================================================

from html import escape
import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------
# SUPABASE TABLE
# ------------------------------------------------------------
HOLDS_TABLE = "holds"

# ------------------------------------------------------------
# BOOKING COLUMN NAMES
# ------------------------------------------------------------
BOOKING_CUSTOMER_COL = "Customer Name"
BOOKING_WING_COL = "Wing"
BOOKING_FLOOR_COL = "Floor"
BOOKING_FLAT_COL = "Flat Number"
BOOKING_TYPE_COL = "Type"
BOOKING_STAMP_DUTY_COL = "Stamp Duty"
BOOKING_AGREEMENT_DONE_COL = "Agreement Done"

# ------------------------------------------------------------
# HOLDS TABLE DB COLUMNS
# ------------------------------------------------------------
HOLD_WING_DB = "wing"
HOLD_FLAT_DB = "flat_number"
HOLD_BY_DB = "hold_by"
HOLD_FROM_DB = "hold_from"
HOLD_TILL_DB = "hold_till"
HOLD_REMARKS_DB = "remarks"

HOLD_ENTRY_TYPE_DB = "entry_type"
LINEUP_BY_DB = "agreement_lineup_by"
LINEUP_DATE_DB = "agreement_lineup_date"
LINEUP_REMARKS_DB = "agreement_lineup_remarks"

HOLD_ENTRY_TYPE_HOLD = "HOLD"
HOLD_ENTRY_TYPE_LINEUP = "AGREEMENT_LINEUP"

HOLD_BY_OPTIONS = ["Tejas P", "Ashutosh S", "Komal K", "Sailee D", "Dhanashree W"]

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
BC_SECOND_REFUGE_FLOOR = 12
EF_SECOND_REFUGE_FLOOR = 12

SERIES_TYPE_MAP = {
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

WING_LAYOUT_ORDER = {
    "B Wing": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
    "C Wing": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
    "E Wing": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
    "F Wing": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
}

MHADA_RULES = {
    "B Wing": {"floors": {4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "C Wing": {"floors": {3, 4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "E Wing": {"floors": {4, 5, 6}, "series": {"04", "05", "06", "07"}},
    "F Wing": {"floors": {3, 4, 5, 6}, "series": {"04", "05", "06", "07"}},
}

REFUGE_RULES = {
    "B Wing": {(7, "10"), (BC_SECOND_REFUGE_FLOOR, "10")},
    "C Wing": {(7, "10"), (BC_SECOND_REFUGE_FLOOR, "10")},
    "E Wing": {(7, "01"), (EF_SECOND_REFUGE_FLOOR, "01")},
    "F Wing": {(7, "01"), (EF_SECOND_REFUGE_FLOOR, "01")},
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
        "102", "103", "110",
        "204", "205",
        "302", "303", "304", "305", "309", "310",
        "401", "402", "410",
        "509", "510",
        "610",
        "801", "803", "804",
        "904", "910",
        "1004",
        "1101", "1102", "1104",
        "1204",
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

# ------------------------------------------------------------
# COLORS
# ------------------------------------------------------------
COLOR_AVAILABLE = "#f6c343"
COLOR_HOLD = "#ff8c00"
COLOR_REFUGE = "#ff1b1b"
COLOR_BLOCKED = "#d9d9d9"
COLOR_TEXT_DARK = "#101010"

COLOR_GREEN = "#0b8a00"
COLOR_STAMP_DUTY = "#14b8a6"
COLOR_LINEUP = "#8b5cf6"
COLOR_BOOKED_PENDING = "#2563eb"

# ------------------------------------------------------------
# STREAMLIT CSS
# ------------------------------------------------------------
st.markdown("""
<style>
.inv-kpi {
    background: #ffffff;
    border: 1px solid #e8edf3;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 10px;
}
.inv-kpi h4 {
    margin: 0;
    color: #5b6675;
    font-size: 13px;
    font-weight: 600;
}
.inv-kpi p {
    margin: 8px 0 0 0;
    color: #111827;
    font-size: 28px;
    font-weight: 800;
}
.inv-legend {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin: 8px 0 10px 0;
    font-size: 13px;
    font-weight: 700;
}
.inv-pill {
    display: inline-block;
    padding: 5px 11px;
    border-radius: 999px;
}
.inv-pill-booked { background: #dcfae6; color: #067647; }
.inv-pill-hold { background: #ffe2bf; color: #c25400; }
.inv-pill-available { background: #fff2c2; color: #8a5b00; }
.inv-pill-refuge { background: #ffd7d7; color: #b10000; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# GENERAL HELPERS
# ------------------------------------------------------------
def _inv_txt(x):
    if pd.isna(x):
        return ""
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def _normalize_flat(x):
    return _inv_txt(x).upper()

def _normalize_wing(x):
    s = _inv_txt(x).upper().replace("-", " ").replace("_", " ")
    s = " ".join(s.split())

    wing_map = {
        "B": "B Wing",
        "B WING": "B Wing",
        "C": "C Wing",
        "C WING": "C Wing",
        "E": "E Wing",
        "E WING": "E Wing",
        "F": "F Wing",
        "F WING": "F Wing",
    }

    return wing_map.get(s, _inv_txt(x))

def _wing_short_code(wing_name: str) -> str:
    wing_name = _normalize_wing(wing_name)

    if wing_name.startswith("B"):
        return "B"
    if wing_name.startswith("C"):
        return "C"
    if wing_name.startswith("E"):
        return "E"
    if wing_name.startswith("F"):
        return "F"

    return wing_name[:1].upper()

def _parse_dt(x):
    s = _inv_txt(x)

    if not s:
        return pd.NaT

    return pd.to_datetime(s, errors="coerce")

def _date_iso(d):
    if isinstance(d, datetime.datetime):
        return d.date().strftime("%Y-%m-%d")

    if isinstance(d, datetime.date):
        return d.strftime("%Y-%m-%d")

    parsed = pd.to_datetime(d, errors="coerce")
    if pd.isna(parsed):
        return None

    return parsed.date().strftime("%Y-%m-%d")

def _col_lookup(df: pd.DataFrame, possible_names: list[str]):
    if df is None or df.empty:
        return None

    normal_map = {
        str(c).strip().lower().replace("_", " ").replace("-", " "): c
        for c in df.columns
    }

    for name in possible_names:
        key = str(name).strip().lower().replace("_", " ").replace("-", " ")
        if key in normal_map:
            return normal_map[key]

    return None

def _flat_number_from_floor_series(floor_no: int, series: str) -> str:
    return f"{floor_no}{series}"

def _get_unit_type(wing: str, floor_no: int, series: str, base_category: str) -> str:
    if base_category == "REFUGE":
        return "Refuge"

    if base_category == "MISSING":
        return ""

    return TYPE_OVERRIDES.get((wing, floor_no, series), SERIES_TYPE_MAP.get(series, ""))

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

def _build_visual_inventory_master() -> pd.DataFrame:
    rows = []
    wings = ["B Wing", "C Wing", "E Wing", "F Wing"]
    series_all = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

    for wing in wings:
        for floor_no in range(1, 14):
            for series in series_all:
                base_category = _base_category(wing, floor_no, series)
                flat_no = _flat_number_from_floor_series(floor_no, series)
                unit_type = _get_unit_type(wing, floor_no, series, base_category)

                rows.append({
                    "Wing": wing,
                    "Floor No.": floor_no,
                    "Series": series,
                    "Flat Number": flat_no,
                    "Base Category": base_category,
                    "Type": unit_type,
                })

    return pd.DataFrame(rows)

# ------------------------------------------------------------
# SUPABASE HELPERS FOR HOLDS TABLE
# ------------------------------------------------------------
def _holds_clear_cache():
    try:
        _fetch_holds_df.clear()
    except Exception:
        pass

@st.cache_data(ttl=120, show_spinner=False)
def _fetch_holds_df(cache_buster: int = 0) -> pd.DataFrame:
    if "supabase" not in globals() or supabase is None:
        return pd.DataFrame()

    try:
        res = (
            supabase
            .table(HOLDS_TABLE)
            .select("*")
            .order("id", desc=False)
            .execute()
        )
        data = getattr(res, "data", []) or []
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

def _insert_hold_payload(payload: dict):
    if "supabase" not in globals() or supabase is None:
        raise RuntimeError("Supabase client is not initialized.")

    return supabase.table(HOLDS_TABLE).insert(payload).execute()

def _prepare_hold_table(holds_df: pd.DataFrame):
    expected_cols = [
        "id",
        HOLD_WING_DB,
        HOLD_FLAT_DB,
        HOLD_BY_DB,
        HOLD_FROM_DB,
        HOLD_TILL_DB,
        HOLD_REMARKS_DB,
        HOLD_ENTRY_TYPE_DB,
        LINEUP_BY_DB,
        LINEUP_DATE_DB,
        LINEUP_REMARKS_DB,
    ]

    if holds_df is None or holds_df.empty:
        return pd.DataFrame(columns=[
            "id",
            "Wing",
            "Flat Number",
            "Hold By",
            "Hold From",
            "Hold Till",
            "Remarks",
            "Entry Type",
            "Agreement Lineup By",
            "Agreement Lineup Date",
            "Agreement Lineup Remarks",
        ])

    h = holds_df.copy()

    for col in expected_cols:
        if col not in h.columns:
            h[col] = ""

    h["id"] = pd.to_numeric(h["id"], errors="coerce").fillna(0).astype(int)

    h["Wing"] = h[HOLD_WING_DB].apply(_normalize_wing)
    h["Flat Number"] = h[HOLD_FLAT_DB].apply(_normalize_flat)

    h["Hold By"] = h[HOLD_BY_DB].fillna("").astype(str).str.strip()
    h["Hold From"] = h[HOLD_FROM_DB].apply(_parse_dt)
    h["Hold Till"] = h[HOLD_TILL_DB].apply(_parse_dt)
    h["Remarks"] = h[HOLD_REMARKS_DB].fillna("").astype(str).str.strip()

    h["Entry Type"] = h[HOLD_ENTRY_TYPE_DB].fillna("").astype(str).str.strip().str.upper()

    h["Agreement Lineup By"] = h[LINEUP_BY_DB].fillna("").astype(str).str.strip()
    h["Agreement Lineup Date"] = h[LINEUP_DATE_DB].apply(_parse_dt)
    h["Agreement Lineup Remarks"] = h[LINEUP_REMARKS_DB].fillna("").astype(str).str.strip()

    blank_type_mask = h["Entry Type"].eq("")

    h.loc[
        blank_type_mask &
        (
            h["Hold By"].ne("") |
            h["Hold From"].notna() |
            h["Hold Till"].notna()
        ),
        "Entry Type"
    ] = HOLD_ENTRY_TYPE_HOLD

    h.loc[
        blank_type_mask &
        (
            h["Agreement Lineup By"].ne("") |
            h["Agreement Lineup Date"].notna() |
            h["Agreement Lineup Remarks"].ne("")
        ),
        "Entry Type"
    ] = HOLD_ENTRY_TYPE_LINEUP

    h = h[(h["Wing"] != "") & (h["Flat Number"] != "")].copy()

    return h[[
        "id",
        "Wing",
        "Flat Number",
        "Hold By",
        "Hold From",
        "Hold Till",
        "Remarks",
        "Entry Type",
        "Agreement Lineup By",
        "Agreement Lineup Date",
        "Agreement Lineup Remarks",
    ]].copy()

def _get_active_holds_from_df(holds_df: pd.DataFrame):
    h = _prepare_hold_table(holds_df)

    if h.empty:
        return h

    h = h[h["Entry Type"] == HOLD_ENTRY_TYPE_HOLD].copy()

    if h.empty:
        return h

    today = pd.Timestamp(datetime.date.today())

    h = h[
        h["Hold Till"].notna() &
        (h["Hold Till"] >= today) &
        (
            h["Hold From"].isna() |
            (h["Hold From"] <= today)
        )
    ].copy()

    if h.empty:
        return h

    h = h.sort_values(["Wing", "Flat Number", "Hold Till", "Hold From", "id"])
    h = h.drop_duplicates(subset=["Wing", "Flat Number"], keep="last")

    return h

def _get_latest_lineups_from_df(holds_df: pd.DataFrame):
    h = _prepare_hold_table(holds_df)

    if h.empty:
        return h

    h = h[h["Entry Type"] == HOLD_ENTRY_TYPE_LINEUP].copy()

    if h.empty:
        return h

    h = h.sort_values(["Wing", "Flat Number", "Agreement Lineup Date", "id"], na_position="last")
    h = h.drop_duplicates(subset=["Wing", "Flat Number"], keep="last")

    return h

def _append_hold_row_supabase(wing, flat_no, hold_by, days, remarks=""):
    today = datetime.date.today()
    hold_till = today + datetime.timedelta(days=int(days))

    payload = {
        HOLD_WING_DB: _normalize_wing(wing),
        HOLD_FLAT_DB: str(flat_no).strip(),
        HOLD_BY_DB: str(hold_by).strip(),
        HOLD_FROM_DB: today.strftime("%Y-%m-%d"),
        HOLD_TILL_DB: hold_till.strftime("%Y-%m-%d"),
        HOLD_REMARKS_DB: str(remarks or "").strip(),
        HOLD_ENTRY_TYPE_DB: HOLD_ENTRY_TYPE_HOLD,
        LINEUP_BY_DB: None,
        LINEUP_DATE_DB: None,
        LINEUP_REMARKS_DB: None,
    }

    _insert_hold_payload(payload)

def _append_lineup_row_supabase(wing, flat_no, lineup_by, lineup_date, remarks=""):
    payload = {
        HOLD_WING_DB: _normalize_wing(wing),
        HOLD_FLAT_DB: str(flat_no).strip(),
        HOLD_BY_DB: None,
        HOLD_FROM_DB: None,
        HOLD_TILL_DB: None,
        HOLD_REMARKS_DB: None,
        HOLD_ENTRY_TYPE_DB: HOLD_ENTRY_TYPE_LINEUP,
        LINEUP_BY_DB: str(lineup_by).strip(),
        LINEUP_DATE_DB: _date_iso(lineup_date),
        LINEUP_REMARKS_DB: str(remarks or "").strip(),
    }

    _insert_hold_payload(payload)

# ------------------------------------------------------------
# BOOKING DATA PREP
# ------------------------------------------------------------
def _prepare_booking_sheet(booking_df):
    cols = [
        "Wing",
        "Flat Number",
        "Booked Customer Name",
        "Agreement Done Flag",
        "Stamp Duty Received Flag",
    ]

    if booking_df is None or booking_df.empty:
        return pd.DataFrame(columns=cols)

    b = booking_df.copy()
    b.columns = [str(c).strip() for c in b.columns]

    wing_col = _col_lookup(b, [BOOKING_WING_COL, "wing"])
    flat_col = _col_lookup(b, [BOOKING_FLAT_COL, "flat_number", "flat no", "flat"])
    cust_col = _col_lookup(b, [BOOKING_CUSTOMER_COL, "customer_name", "customer"])
    agreement_col = _col_lookup(b, [BOOKING_AGREEMENT_DONE_COL, "agreement_done"])
    stamp_col = _col_lookup(b, [BOOKING_STAMP_DUTY_COL, "stamp_duty"])

    b["Wing"] = b[wing_col].apply(_normalize_wing) if wing_col else ""
    b["Flat Number"] = b[flat_col].apply(_normalize_flat) if flat_col else ""

    b["Booked Customer Name"] = (
        b[cust_col].fillna("").astype(str).str.strip()
        if cust_col else ""
    )

    if agreement_col:
        b["Agreement Done Flag"] = (
            b[agreement_col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .isin(["DONE", "COMPLETED", "YES", "TRUE", "1"])
        )
    else:
        b["Agreement Done Flag"] = False

    if stamp_col:
        b["Stamp Duty Received Flag"] = (
            b[stamp_col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .isin(["RECEIVED", "RECIEVED", "DONE", "YES", "TRUE", "1"])
        )
    else:
        b["Stamp Duty Received Flag"] = False

    b = b[(b["Wing"] != "") & (b["Flat Number"] != "")].copy()
    b = b.drop_duplicates(subset=["Wing", "Flat Number"], keep="last")

    return b[cols].copy()

# ------------------------------------------------------------
# INVENTORY STATUS BUILDER
# ------------------------------------------------------------
def _build_inventory_status_df(booking_df, holds_df):
    base_df = _build_visual_inventory_master()
    booked = _prepare_booking_sheet(booking_df)
    active_holds = _get_active_holds_from_df(holds_df)
    lineups = _get_latest_lineups_from_df(holds_df)

    if not booked.empty:
        base_df = base_df.merge(booked, on=["Wing", "Flat Number"], how="left")
    else:
        base_df["Booked Customer Name"] = ""
        base_df["Agreement Done Flag"] = False
        base_df["Stamp Duty Received Flag"] = False

    if not active_holds.empty:
        base_df = base_df.merge(
            active_holds.rename(columns={
                "Hold By": "Active Hold By",
                "Hold From": "Active Hold From",
                "Hold Till": "Active Hold Till",
                "Remarks": "Active Hold Remarks",
            })[
                [
                    "Wing",
                    "Flat Number",
                    "Active Hold By",
                    "Active Hold From",
                    "Active Hold Till",
                    "Active Hold Remarks",
                ]
            ],
            on=["Wing", "Flat Number"],
            how="left"
        )
    else:
        base_df["Active Hold By"] = ""
        base_df["Active Hold From"] = pd.NaT
        base_df["Active Hold Till"] = pd.NaT
        base_df["Active Hold Remarks"] = ""

    if not lineups.empty:
        base_df = base_df.merge(
            lineups.rename(columns={
                "Agreement Lineup By": "Agreement Lineup By",
                "Agreement Lineup Date": "Agreement Lineup Date",
                "Agreement Lineup Remarks": "Agreement Lineup Remarks",
            })[
                [
                    "Wing",
                    "Flat Number",
                    "Agreement Lineup By",
                    "Agreement Lineup Date",
                    "Agreement Lineup Remarks",
                ]
            ],
            on=["Wing", "Flat Number"],
            how="left"
        )
    else:
        base_df["Agreement Lineup By"] = ""
        base_df["Agreement Lineup Date"] = pd.NaT
        base_df["Agreement Lineup Remarks"] = ""

    for c in [
        "Booked Customer Name",
        "Active Hold By",
        "Active Hold Remarks",
        "Agreement Lineup By",
        "Agreement Lineup Remarks",
    ]:
        if c in base_df.columns:
            base_df[c] = base_df[c].fillna("").astype(str).str.strip()

    for c in ["Agreement Done Flag", "Stamp Duty Received Flag"]:
        if c in base_df.columns:
            base_df[c] = base_df[c].fillna(False).astype(bool)

    base_df["Is Booked Client"] = base_df["Booked Customer Name"].ne("")
    base_df["Internal Status"] = ""
    base_df["Customer Status"] = ""

    our_mask = base_df["Base Category"].eq("OUR")
    booked_mask = our_mask & base_df["Is Booked Client"]
    hold_mask = our_mask & ~booked_mask & base_df["Active Hold Till"].notna()
    available_mask = our_mask & ~booked_mask & ~base_df["Active Hold Till"].notna()

    booked_pending_mask = booked_mask
    stamp_received_mask = booked_mask & base_df["Stamp Duty Received Flag"]
    lineup_mask = booked_mask & base_df["Stamp Duty Received Flag"] & base_df["Agreement Lineup Date"].notna()
    agreement_done_mask = booked_mask & base_df["Agreement Done Flag"]

    base_df.loc[available_mask, "Internal Status"] = "AVAILABLE"
    base_df.loc[hold_mask, "Internal Status"] = "HOLD"
    base_df.loc[booked_pending_mask, "Internal Status"] = "BOOKED_PENDING"
    base_df.loc[stamp_received_mask, "Internal Status"] = "STAMP_DUTY_RECEIVED"
    base_df.loc[lineup_mask, "Internal Status"] = "AGREEMENT_LINEUP"
    base_df.loc[agreement_done_mask, "Internal Status"] = "AGREEMENT_DONE"

    base_df.loc[our_mask & base_df["Internal Status"].eq("HOLD"), "Customer Status"] = "HOLD"
    base_df.loc[our_mask & base_df["Internal Status"].eq("AVAILABLE"), "Customer Status"] = "AVAILABLE"

    base_df.loc[
        our_mask &
        base_df["Internal Status"].isin([
            "BOOKED_PENDING",
            "STAMP_DUTY_RECEIVED",
            "AGREEMENT_LINEUP",
            "AGREEMENT_DONE",
        ]),
        "Customer Status"
    ] = "BOOKED"

    return base_df

# ------------------------------------------------------------
# COUNT HELPERS
# ------------------------------------------------------------
def _customer_counts(wing_df):
    total_inventory = int((wing_df["Base Category"] != "MISSING").sum())

    booked_inventory = int(
        (
            (wing_df["Base Category"] == "OUR") &
            (wing_df["Customer Status"] == "BOOKED")
        ).sum() +
        (wing_df["Base Category"] == "MHADA").sum() +
        (wing_df["Base Category"] == "LANDOWNER").sum()
    )

    hold_inventory = int(
        (
            (wing_df["Base Category"] == "OUR") &
            (wing_df["Customer Status"] == "HOLD")
        ).sum()
    )

    available_inventory = int(
        (
            (wing_df["Base Category"] == "OUR") &
            (wing_df["Customer Status"] == "AVAILABLE")
        ).sum()
    )

    return total_inventory, booked_inventory, hold_inventory, available_inventory

def _internal_counts(wing_df):
    return {
        "Our Inventory": int((wing_df["Base Category"] == "OUR").sum()),
        "Mhada": int((wing_df["Base Category"] == "MHADA").sum()),
        "Landowner": int((wing_df["Base Category"] == "LANDOWNER").sum()),
        "Hold": int(((wing_df["Base Category"] == "OUR") & (wing_df["Internal Status"] == "HOLD")).sum()),
        "Agreement Done": int(((wing_df["Base Category"] == "OUR") & (wing_df["Internal Status"] == "AGREEMENT_DONE")).sum()),
        "Stamp Duty Received": int(((wing_df["Base Category"] == "OUR") & (wing_df["Internal Status"] == "STAMP_DUTY_RECEIVED")).sum()),
        "Agreement Lineup": int(((wing_df["Base Category"] == "OUR") & (wing_df["Internal Status"] == "AGREEMENT_LINEUP")).sum()),
    }

# ------------------------------------------------------------
# VISUAL CELL HELPERS
# ------------------------------------------------------------
def _cell_view(row, customer_mode=False):
    base_cat = _inv_txt(row.get("Base Category", "")).upper()
    internal_status = _inv_txt(row.get("Internal Status", "")).upper()
    customer_status = _inv_txt(row.get("Customer Status", "")).upper()
    flat_no = _inv_txt(row.get("Flat Number", ""))
    unit_type = _inv_txt(row.get("Type", ""))

    if customer_mode:
        if base_cat == "MISSING":
            return "inv-hidden", "", "", ""

        if base_cat == "REFUGE":
            return "inv-refuge", "", flat_no, "Refuge"

        if base_cat == "OUR":
            if customer_status == "HOLD":
                return "inv-hold", "", flat_no, unit_type
            if customer_status == "AVAILABLE":
                return "inv-available", "", flat_no, unit_type
            return "inv-green", "", flat_no, unit_type

        return "inv-green", "", flat_no, unit_type

    if base_cat == "MISSING":
        return "inv-hidden", "", "", ""

    if base_cat == "REFUGE":
        return "inv-refuge", "", flat_no, "Refuge"

    if base_cat == "LANDOWNER":
        return "inv-landowner", "single", flat_no, unit_type

    if base_cat == "MHADA":
        return "inv-mhada", "double", flat_no, unit_type

    if base_cat == "OUR":
        if internal_status == "AVAILABLE":
            return "inv-available", "", flat_no, unit_type
        if internal_status == "HOLD":
            return "inv-hold", "", flat_no, unit_type
        if internal_status == "BOOKED_PENDING":
            return "inv-booked-pending", "", flat_no, unit_type
        if internal_status == "STAMP_DUTY_RECEIVED":
            return "inv-stamp-duty", "", flat_no, unit_type
        if internal_status == "AGREEMENT_LINEUP":
            return "inv-lineup", "", flat_no, unit_type
        if internal_status == "AGREEMENT_DONE":
            return "inv-green", "", flat_no, unit_type

        return "inv-available", "", flat_no, unit_type

    return "inv-hidden", "", "", ""

def _subtext_html(underline_mode, unit_type):
    if not unit_type:
        return "<span class='inv-unit-sub'>&nbsp;</span>"

    if underline_mode == "single":
        return f"<span class='inv-unit-sub inv-single-underline'>{escape(unit_type)}</span>"

    if underline_mode == "double":
        return f"<span class='inv-unit-sub inv-double-underline'>{escape(unit_type)}</span>"

    return f"<span class='inv-unit-sub'>{escape(unit_type)}</span>"

def _build_wing_matrix_html(wing_df, wing_name, customer_mode=False):
    layout_order = WING_LAYOUT_ORDER[wing_name]
    floors = list(range(13, 0, -1))

    html = []
    html.append("<div class='inventory-widget-wrap'>")
    html.append("<table class='inventory-widget-table'>")
    html.append("<thead>")
    html.append(f"<tr class='inventory-title-row'><th colspan='{len(layout_order)}'>{escape(wing_name)}</th></tr>")
    html.append("<tr>")

    for _ in layout_order:
        html.append("<th class='inventory-blank-head'></th>")

    html.append("</tr>")
    html.append("</thead>")
    html.append("<tbody>")

    for floor_no in floors:
        html.append("<tr>")
        floor_df = wing_df[wing_df["Floor No."] == floor_no].copy()
        floor_map = {row["Series"]: row for _, row in floor_df.iterrows()}

        for item in layout_order:
            row = floor_map[item]
            css_class, underline_mode, flat_no, unit_type = _cell_view(row, customer_mode=customer_mode)

            tooltip_parts = []

            if flat_no:
                tooltip_parts.append(f"Flat: {flat_no}")

            if unit_type:
                tooltip_parts.append(f"Type: {unit_type}")

            if not customer_mode:
                base_cat = _inv_txt(row.get("Base Category", ""))
                internal_status = _inv_txt(row.get("Internal Status", ""))

                if base_cat:
                    tooltip_parts.append(f"Category: {base_cat}")

                if internal_status:
                    tooltip_parts.append(f"Status: {internal_status.replace('_', ' ').title()}")

                if _inv_txt(row.get("Booked Customer Name", "")):
                    tooltip_parts.append(f"Customer: {_inv_txt(row.get('Booked Customer Name', ''))}")

                if _inv_txt(row.get("Agreement Lineup By", "")):
                    tooltip_parts.append(f"Lineup By: {_inv_txt(row.get('Agreement Lineup By', ''))}")

                if pd.notna(row.get("Agreement Lineup Date", pd.NaT)):
                    try:
                        tooltip_parts.append(
                            f"Lineup Date: {pd.to_datetime(row.get('Agreement Lineup Date')).strftime('%d-%m-%Y')}"
                        )
                    except Exception:
                        pass

                if _inv_txt(row.get("Active Hold By", "")):
                    tooltip_parts.append(f"Hold By: {_inv_txt(row.get('Active Hold By', ''))}")

                if pd.notna(row.get("Active Hold Till", pd.NaT)):
                    try:
                        tooltip_parts.append(
                            f"Hold Till: {pd.to_datetime(row.get('Active Hold Till')).strftime('%d-%m-%Y')}"
                        )
                    except Exception:
                        pass

            tooltip = escape("\n".join(tooltip_parts)) if tooltip_parts else ""

            sub_html = _subtext_html(underline_mode, unit_type) if flat_no else "<span class='inv-unit-sub'>&nbsp;</span>"

            html.append(
                f"<td class='inventory-cell {css_class}' title='{tooltip}'>"
                f"{escape(flat_no) if flat_no else '&nbsp;'}"
                f"{sub_html}"
                f"</td>"
            )

        html.append("</tr>")

    html.append("</tbody></table></div>")

    return "".join(html)

def _build_inventory_widget_html(inventory_status_df):
    wing_order = ["B Wing", "C Wing", "E Wing", "F Wing"]
    tabs_html = []
    panels_html = []

    for i, wing_name in enumerate(wing_order):
        wing_df = inventory_status_df[inventory_status_df["Wing"] == wing_name].copy()

        customer_total, customer_booked, customer_hold, customer_available = _customer_counts(wing_df)
        internal_counts = _internal_counts(wing_df)

        wing_id = wing_name.lower().replace(" ", "_")

        tabs_html.append(
            f"<button class='widget-tab {'active' if i == 0 else ''}' onclick=\"showWing('{wing_id}', this)\">{escape(wing_name)}</button>"
        )

        internal_kpis_html = f"""
            <div class="widget-kpis widget-kpis-7">
                <div class="widget-kpi"><div class="widget-kpi-label">Our Inventory</div><div class="widget-kpi-value">{internal_counts['Our Inventory']}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Mhada</div><div class="widget-kpi-value">{internal_counts['Mhada']}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Landowner</div><div class="widget-kpi-value">{internal_counts['Landowner']}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Hold</div><div class="widget-kpi-value">{internal_counts['Hold']}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Agreement Done</div><div class="widget-kpi-value">{internal_counts['Agreement Done']}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Stamp Duty Received</div><div class="widget-kpi-value">{internal_counts['Stamp Duty Received']}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Agreement Lineup</div><div class="widget-kpi-value">{internal_counts['Agreement Lineup']}</div></div>
            </div>
        """

        customer_kpis_html = f"""
            <div class="widget-kpis">
                <div class="widget-kpi"><div class="widget-kpi-label">Total Inventory</div><div class="widget-kpi-value">{customer_total}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Booked Inventory</div><div class="widget-kpi-value">{customer_booked}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Hold Inventory</div><div class="widget-kpi-value">{customer_hold}</div></div>
                <div class="widget-kpi"><div class="widget-kpi-label">Available Inventory</div><div class="widget-kpi-value">{customer_available}</div></div>
            </div>
        """

        panels_html.append(
            f"""
            <div class="widget-panel {'active' if i == 0 else ''}" id="{wing_id}">
                <div class="widget-mode-block internal-mode active">
                    {internal_kpis_html}
                    <div class="widget-legend">
                        <span class="widget-pill widget-pill-available">AVAILABLE</span>
                        <span class="widget-pill widget-pill-hold">HOLD</span>
                        <span class="widget-pill widget-pill-bookedpending">BOOKED PENDING</span>
                        <span class="widget-pill widget-pill-stamp">STAMP DUTY RECEIVED</span>
                        <span class="widget-pill widget-pill-lineup">AGREEMENT LINEUP</span>
                        <span class="widget-pill widget-pill-booked">AGREEMENT DONE</span>
                        <span class="widget-pill widget-pill-refuge">REFUGE</span>
                    </div>
                    <div style="font-size:12px; font-weight:700; margin-bottom:10px; color:#475467;">
                        Single underline = Landowner &nbsp;|&nbsp; Double underline = Mhada
                    </div>
                    {_build_wing_matrix_html(wing_df, wing_name, customer_mode=False)}
                </div>

                <div class="widget-mode-block customer-mode">
                    {customer_kpis_html}
                    <div class="widget-legend">
                        <span class="widget-pill widget-pill-booked">BOOKED</span>
                        <span class="widget-pill widget-pill-available">AVAILABLE</span>
                        <span class="widget-pill widget-pill-refuge">REFUGE</span>
                        <span class="widget-pill widget-pill-hold">HOLD</span>
                    </div>
                    {_build_wing_matrix_html(wing_df, wing_name, customer_mode=True)}
                </div>
            </div>
            """
        )

    return f"""
    <style>
    .inventory-shell {{
        font-family: Arial, sans-serif;
        background: #ffffff;
        color: #101828;
        padding: 12px;
        box-sizing: border-box;
    }}

    .inventory-topbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }}

    .inventory-title {{
        font-size: 22px;
        font-weight: 900;
        color: #111;
    }}

    .inventory-actions {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }}

    .inventory-btn {{
        border: none;
        background: #2f7db8;
        color: #fff;
        padding: 10px 14px;
        border-radius: 10px;
        font-weight: 700;
        cursor: pointer;
    }}

    .inventory-btn-secondary {{
        background: #0f172a;
    }}

    .widget-tabs {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }}

    .widget-tab {{
        border: none;
        padding: 10px 14px;
        border-radius: 10px;
        cursor: pointer;
        font-weight: 800;
        background: #e5edf5;
        color: #2a4158;
    }}

    .widget-tab.active {{
        background: #2f7db8;
        color: white;
    }}

    .widget-panel {{
        display: none;
    }}

    .widget-panel.active {{
        display: block;
    }}

    .widget-kpis {{
        display: grid;
        grid-template-columns: repeat(4, minmax(120px, 1fr));
        gap: 12px;
        margin-bottom: 12px;
    }}

    .widget-kpis-7 {{
        grid-template-columns: repeat(4, minmax(120px, 1fr));
    }}

    .widget-kpi {{
        background: white;
        border-radius: 14px;
        padding: 14px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #e8edf3;
    }}

    .widget-kpi-label {{
        font-size: 12px;
        color: #667085;
        font-weight: 700;
    }}

    .widget-kpi-value {{
        font-size: 30px;
        font-weight: 900;
        margin-top: 6px;
    }}

    .widget-legend {{
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 12px;
        font-weight: 700;
        font-size: 13px;
    }}

    .widget-pill {{
        padding: 5px 10px;
        border-radius: 999px;
    }}

    .widget-pill-booked {{ background:#dcfae6; color:#067647; }}
    .widget-pill-hold {{ background:#ffe2bf; color:#c25400; }}
    .widget-pill-available {{ background:#fff2c2; color:#8a5b00; }}
    .widget-pill-refuge {{ background:#ffd7d7; color:#b10000; }}
    .widget-pill-bookedpending {{ background:#dbeafe; color:#1d4ed8; }}
    .widget-pill-lineup {{ background:#ede9fe; color:#6d28d9; }}
    .widget-pill-stamp {{ background:#ccfbf1; color:#0f766e; }}

    .widget-mode-block {{
        display: none;
    }}

    .widget-mode-block.active {{
        display: block;
    }}

    .inventory-widget-wrap {{
        overflow-x: auto;
        overflow-y: visible;
        width: 100%;
    }}

    .inventory-widget-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }}

    .inventory-widget-table th,
    .inventory-widget-table td {{
        border: 2px solid #111;
    }}

    .inventory-title-row th {{
        background: #efefef;
        color: #111;
        font-size: 24px;
        font-weight: 900;
        text-decoration: underline;
        padding: 6px 8px;
    }}

    .inventory-blank-head {{
        background: #efefef;
        height: 22px;
    }}

    .inventory-cell {{
        height: 56px;
        text-align: center;
        vertical-align: middle;
        font-weight: 900;
        font-size: 18px;
        line-height: 1.0;
        padding: 2px 2px;
        color: #101010;
    }}

    .inv-unit-sub {{
        display: block;
        font-size: 10px;
        font-weight: 800;
        margin-top: 4px;
        line-height: 1.0;
    }}

    .inv-single-underline {{
        text-decoration: underline;
        text-decoration-thickness: 2px;
        text-underline-offset: 2px;
    }}

    .inv-double-underline {{
        text-decoration-line: underline;
        text-decoration-style: double;
        text-decoration-thickness: 2px;
        text-underline-offset: 2px;
    }}

    .inv-green {{
        background: #0b8a00;
        color: white;
    }}

    .inv-landowner {{
        background: #0b8a00;
        color: white;
    }}

    .inv-mhada {{
        background: #0b8a00;
        color: white;
    }}

    .inv-available {{
        background: #f6c343;
        color: #101010;
    }}

    .inv-hold {{
        background: #ff8c00;
        color: white;
    }}

    .inv-refuge {{
        background: #ff1b1b;
        color: white;
    }}

    .inv-lineup {{
        background: #8b5cf6;
        color: white;
    }}

    .inv-stamp-duty {{
        background: #14b8a6;
        color: white;
    }}

    .inv-booked-pending {{
        background: #2563eb;
        color: white;
    }}

    .inv-hidden {{
        background: #d9d9d9;
        color: #d9d9d9;
    }}

    #inventorySingleWidget:fullscreen {{
        background: white;
        width: 100vw;
        height: 100vh;
        overflow: auto;
        padding: 18px;
        box-sizing: border-box;
    }}

    #inventorySingleWidget:-webkit-full-screen {{
        background: white;
        width: 100vw;
        height: 100vh;
        overflow: auto;
        padding: 18px;
        box-sizing: border-box;
    }}

    @media (max-width: 1500px) {{
        .inventory-cell {{
            height: 50px;
            font-size: 16px;
        }}
        .inv-unit-sub {{
            font-size: 9px;
        }}
    }}
    </style>

    <div class="inventory-shell" id="inventorySingleWidget">
        <div class="inventory-topbar">
            <div class="inventory-title">Inventory Display</div>
            <div class="inventory-actions">
                <button class="inventory-btn" onclick="setMode('internal')" id="internalModeBtn">Internal View</button>
                <button class="inventory-btn inventory-btn-secondary" onclick="setMode('customer')" id="customerModeBtn">Customer View</button>
                <button class="inventory-btn" onclick="openFullScreen()">Open Full Screen</button>
            </div>
        </div>

        <div class="widget-tabs">
            {''.join(tabs_html)}
        </div>

        {''.join(panels_html)}
    </div>

    <script>
    let currentMode = 'internal';

    function showWing(id, btn) {{
        document.querySelectorAll('.widget-panel').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.widget-tab').forEach(el => el.classList.remove('active'));
        document.getElementById(id).classList.add('active');
        btn.classList.add('active');
        applyMode();
    }}

    function setMode(mode) {{
        currentMode = mode;
        applyMode();
    }}

    function applyMode() {{
        document.querySelectorAll('.widget-panel').forEach(panel => {{
            const internalBlock = panel.querySelector('.internal-mode');
            const customerBlock = panel.querySelector('.customer-mode');

            if (internalBlock) internalBlock.classList.remove('active');
            if (customerBlock) customerBlock.classList.remove('active');

            if (currentMode === 'internal') {{
                if (internalBlock) internalBlock.classList.add('active');
            }} else {{
                if (customerBlock) customerBlock.classList.add('active');
            }}
        }});

        const internalBtn = document.getElementById('internalModeBtn');
        const customerBtn = document.getElementById('customerModeBtn');

        if (currentMode === 'internal') {{
            internalBtn.classList.remove('inventory-btn-secondary');
            customerBtn.classList.add('inventory-btn-secondary');
        }} else {{
            customerBtn.classList.remove('inventory-btn-secondary');
            internalBtn.classList.add('inventory-btn-secondary');
        }}
    }}

    function openFullScreen() {{
        const elem = document.getElementById('inventorySingleWidget');
        if (elem.requestFullscreen) {{
            elem.requestFullscreen();
        }} else if (elem.webkitRequestFullscreen) {{
            elem.webkitRequestFullscreen();
        }} else if (elem.msRequestFullscreen) {{
            elem.msRequestFullscreen();
        }}
    }}

    applyMode();
    </script>
    """

# ------------------------------------------------------------
# HOLD / LINEUP OPTION HELPERS
# ------------------------------------------------------------
def _get_hold_unit_code_map(inventory_status_df):
    df = inventory_status_df[
        (inventory_status_df["Base Category"] == "OUR") &
        (inventory_status_df["Internal Status"] == "AVAILABLE")
    ].copy()

    if df.empty:
        return [""], {}

    df = df.sort_values(["Wing", "Floor No.", "Flat Number"])

    options = [""]
    option_map = {}

    for _, row in df.iterrows():
        wing_name = _normalize_wing(row["Wing"])
        flat_no = _normalize_flat(row["Flat Number"])
        option_code = f"{_wing_short_code(wing_name)}|{flat_no}"

        options.append(option_code)
        option_map[option_code] = {
            "wing": wing_name,
            "flat_no": flat_no,
        }

    return options, option_map

def _get_lineup_unit_code_map(inventory_status_df):
    df = inventory_status_df[
        (inventory_status_df["Base Category"] == "OUR") &
        (inventory_status_df["Internal Status"] == "STAMP_DUTY_RECEIVED")
    ].copy()

    if df.empty:
        return [""], {}

    df = df.sort_values(["Wing", "Floor No.", "Flat Number"])

    options = [""]
    option_map = {}

    for _, row in df.iterrows():
        wing_name = _normalize_wing(row["Wing"])
        flat_no = _normalize_flat(row["Flat Number"])
        option_code = f"{_wing_short_code(wing_name)}|{flat_no}"

        options.append(option_code)
        option_map[option_code] = {
            "wing": wing_name,
            "flat_no": flat_no,
        }

    return options, option_map

# ------------------------------------------------------------
# MULTI HOLD MANAGER
# ------------------------------------------------------------
def _render_multi_hold_manager(inventory_status_df):
    unit_options, unit_option_map = _get_hold_unit_code_map(inventory_status_df)

    st.markdown("### Multi-Unit Hold Management")
    st.caption("Select up to 5 available units from any wing in one form. Example: B|401.")

    with st.container(border=True):
        if len(unit_options) <= 1:
            st.info("No available units to hold right now.")
            return

        with st.form("multi_unit_hold_form", clear_on_submit=True):
            for i in range(5):
                st.markdown(f"**Hold Unit {i + 1}**")

                c1, c2, c3, c4 = st.columns([1.4, 1.2, 0.9, 1.8])

                with c1:
                    st.selectbox(
                        "Unit",
                        options=unit_options,
                        key=f"hold_form_unit_{i}",
                        format_func=lambda x: "Select unit (e.g. B|401)" if x == "" else x,
                    )

                with c2:
                    st.selectbox(
                        "Hold By",
                        options=HOLD_BY_OPTIONS,
                        key=f"hold_form_holdby_{i}",
                    )

                with c3:
                    st.number_input(
                        "Days",
                        min_value=1,
                        max_value=30,
                        value=5,
                        key=f"hold_form_days_{i}",
                    )

                with c4:
                    st.text_input(
                        "Remarks",
                        key=f"hold_form_remarks_{i}",
                        placeholder="Optional",
                    )

                if i < 4:
                    st.divider()

            submitted = st.form_submit_button("Hold Selected Units", use_container_width=True)

            if submitted:
                rows_to_hold = []
                errors = []
                duplicates = set()

                for i in range(5):
                    selected_unit = st.session_state.get(f"hold_form_unit_{i}", "")
                    hold_by = st.session_state.get(f"hold_form_holdby_{i}", HOLD_BY_OPTIONS[0])
                    days = int(st.session_state.get(f"hold_form_days_{i}", 5))
                    remarks = st.session_state.get(f"hold_form_remarks_{i}", "").strip()

                    if selected_unit == "":
                        continue

                    if selected_unit not in unit_option_map:
                        errors.append(f"Unit {i + 1}: invalid unit selected.")
                        continue

                    wing = unit_option_map[selected_unit]["wing"]
                    flat_no = unit_option_map[selected_unit]["flat_no"]

                    dup_key = (wing, flat_no)

                    if dup_key in duplicates:
                        errors.append(f"Unit {i + 1}: duplicate unit selected ({selected_unit}).")
                        continue

                    duplicates.add(dup_key)

                    rows_to_hold.append({
                        "unit_code": selected_unit,
                        "wing": wing,
                        "flat_no": flat_no,
                        "hold_by": hold_by,
                        "days": days,
                        "remarks": remarks,
                    })

                if not rows_to_hold and not errors:
                    st.warning("Please select at least one unit.")
                    return

                if errors:
                    st.error("Please fix these before submitting:\n\n- " + "\n- ".join(errors))
                    return

                try:
                    held_units = []

                    for row in rows_to_hold:
                        _append_hold_row_supabase(
                            wing=row["wing"],
                            flat_no=row["flat_no"],
                            hold_by=row["hold_by"],
                            days=row["days"],
                            remarks=row["remarks"],
                        )
                        held_units.append(row["unit_code"])

                    _holds_clear_cache()
                    st.success(f"Held {len(held_units)} unit(s): {', '.join(held_units)}")
                    st.rerun()

                except Exception as e:
                    st.error(f"Could not save hold entry: {e}")

# ------------------------------------------------------------
# AGREEMENT LINEUP MANAGER
# ------------------------------------------------------------
def _render_agreement_lineup_manager(inventory_status_df):
    unit_options, unit_option_map = _get_lineup_unit_code_map(inventory_status_df)

    st.markdown("### Agreement Lineup Management")
    st.caption("Only units with Stamp Duty Received are shown here.")

    with st.container(border=True):
        if len(unit_options) <= 1:
            st.info("No units available for agreement lineup right now.")
            return

        with st.form("agreement_lineup_form", clear_on_submit=True):
            for i in range(5):
                st.markdown(f"**Agreement Lineup Unit {i + 1}**")

                c1, c2, c3, c4 = st.columns([1.4, 1.2, 1.0, 1.6])

                with c1:
                    st.selectbox(
                        "Unit",
                        options=unit_options,
                        key=f"lineup_form_unit_{i}",
                        format_func=lambda x: "Select unit (e.g. B|401)" if x == "" else x,
                    )

                with c2:
                    st.selectbox(
                        "Lineup By",
                        options=HOLD_BY_OPTIONS,
                        key=f"lineup_form_by_{i}",
                    )

                with c3:
                    st.date_input(
                        "Lineup Date",
                        value=datetime.date.today(),
                        format="DD/MM/YYYY",
                        key=f"lineup_form_date_{i}",
                    )

                with c4:
                    st.text_input(
                        "Remarks",
                        key=f"lineup_form_remarks_{i}",
                        placeholder="Optional",
                    )

                if i < 4:
                    st.divider()

            submitted = st.form_submit_button("Update Agreement Lineup", use_container_width=True)

            if submitted:
                rows_to_lineup = []
                errors = []
                duplicates = set()

                for i in range(5):
                    selected_unit = st.session_state.get(f"lineup_form_unit_{i}", "")
                    lineup_by = st.session_state.get(f"lineup_form_by_{i}", HOLD_BY_OPTIONS[0])
                    lineup_date = st.session_state.get(f"lineup_form_date_{i}", datetime.date.today())
                    remarks = st.session_state.get(f"lineup_form_remarks_{i}", "").strip()

                    if selected_unit == "":
                        continue

                    if selected_unit not in unit_option_map:
                        errors.append(f"Unit {i + 1}: invalid unit selected.")
                        continue

                    wing = unit_option_map[selected_unit]["wing"]
                    flat_no = unit_option_map[selected_unit]["flat_no"]

                    dup_key = (wing, flat_no)

                    if dup_key in duplicates:
                        errors.append(f"Unit {i + 1}: duplicate unit selected ({selected_unit}).")
                        continue

                    duplicates.add(dup_key)

                    rows_to_lineup.append({
                        "unit_code": selected_unit,
                        "wing": wing,
                        "flat_no": flat_no,
                        "lineup_by": lineup_by,
                        "lineup_date": lineup_date,
                        "remarks": remarks,
                    })

                if not rows_to_lineup and not errors:
                    st.warning("Please select at least one unit.")
                    return

                if errors:
                    st.error("Please fix these before submitting:\n\n- " + "\n- ".join(errors))
                    return

                try:
                    updated_units = []

                    for row in rows_to_lineup:
                        _append_lineup_row_supabase(
                            wing=row["wing"],
                            flat_no=row["flat_no"],
                            lineup_by=row["lineup_by"],
                            lineup_date=row["lineup_date"],
                            remarks=row["remarks"],
                        )
                        updated_units.append(row["unit_code"])

                    _holds_clear_cache()
                    st.success(f"Agreement lineup updated for {len(updated_units)} unit(s): {', '.join(updated_units)}")
                    st.rerun()

                except Exception as e:
                    st.error(f"Could not save agreement lineup entry: {e}")

# ------------------------------------------------------------
# DETAILS TABLE
# ------------------------------------------------------------
def _render_inventory_details_table(wing_df):
    detail_df = wing_df.copy()

    required_cols = [
        "Wing",
        "Floor No.",
        "Flat Number",
        "Series",
        "Type",
        "Base Category",
        "Internal Status",
        "Customer Status",
        "Booked Customer Name",
        "Agreement Done Flag",
        "Stamp Duty Received Flag",
        "Active Hold By",
        "Active Hold From",
        "Active Hold Till",
        "Active Hold Remarks",
        "Agreement Lineup By",
        "Agreement Lineup Date",
        "Agreement Lineup Remarks",
    ]

    for col in required_cols:
        if col not in detail_df.columns:
            detail_df[col] = ""

    detail_df = detail_df[required_cols].copy()

    def _pretty_status(x):
        s = _inv_txt(x)

        if not s:
            return ""

        return s.replace("_", " ").title()

    detail_df["Internal Status"] = detail_df["Internal Status"].apply(_pretty_status)
    detail_df["Customer Status"] = detail_df["Customer Status"].apply(_pretty_status)

    detail_df = detail_df.rename(columns={
        "Base Category": "Inventory Category",
        "Internal Status": "Internal View Status",
        "Customer Status": "Customer View Status",
        "Agreement Done Flag": "Agreement Done?",
        "Stamp Duty Received Flag": "Stamp Duty Received?",
    })

    def _row_style(row):
        status = _inv_txt(row.get("Internal View Status", "")).upper()
        cat = _inv_txt(row.get("Inventory Category", "")).upper()

        if status == "AGREEMENT DONE":
            return ["background-color: #dcfae6; color: #067647;"] * len(row)

        if status == "STAMP DUTY RECEIVED":
            return ["background-color: #ccfbf1; color: #0f766e;"] * len(row)

        if status == "AGREEMENT LINEUP":
            return ["background-color: #ede9fe; color: #6d28d9;"] * len(row)

        if status == "BOOKED PENDING":
            return ["background-color: #dbeafe; color: #1d4ed8;"] * len(row)

        if status == "HOLD":
            return ["background-color: #ffe2bf; color: #c25400;"] * len(row)

        if status == "AVAILABLE":
            return ["background-color: #fff8df; color: #8a5b00;"] * len(row)

        if cat in ["LANDOWNER", "MHADA"]:
            return ["background-color: #e6f6e6; color: #067647;"] * len(row)

        if cat == "REFUGE":
            return ["background-color: #ffe1e1; color: #b10000;"] * len(row)

        return [""] * len(row)

    st.dataframe(
        detail_df.style.apply(_row_style, axis=1),
        use_container_width=True,
        height=460,
    )

# ------------------------------------------------------------
# TAB UI
# ------------------------------------------------------------
if selected_main_section == "Inventory Status":
    st.markdown("## Inventory Status")

    if "supabase" not in globals() or supabase is None:
        st.warning("Supabase client is not initialized.")
        st.stop()

    # Booking source fallback:
    # Uses booking_df first, then sheet_df if booking_df is not available.
    if "booking_df" in globals() and isinstance(booking_df, pd.DataFrame):
        booking_source_df = booking_df.copy()
    elif "sheet_df" in globals() and isinstance(sheet_df, pd.DataFrame):
        booking_source_df = sheet_df.copy()
    else:
        booking_source_df = pd.DataFrame()

    if "holds_cache_buster" not in st.session_state:
        st.session_state["holds_cache_buster"] = 0

    holds_df = _fetch_holds_df(st.session_state["holds_cache_buster"])

    inventory_status_df = _build_inventory_status_df(
        booking_df=booking_source_df,
        holds_df=holds_df,
    )

    components.html(
        _build_inventory_widget_html(inventory_status_df),
        height=860,
        scrolling=True,
    )

    _render_multi_hold_manager(inventory_status_df)

    st.markdown("")

    _render_agreement_lineup_manager(inventory_status_df)

    with st.expander("Show inventory details table", expanded=False):
        selected_wing_for_details = st.selectbox(
            "Select Wing for Details",
            options=["B Wing", "C Wing", "E Wing", "F Wing"],
            key="inventory_details_wing_select",
        )

        details_df = inventory_status_df[
            inventory_status_df["Wing"] == selected_wing_for_details
        ].copy()

        _render_inventory_details_table(details_df)
