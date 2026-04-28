import datetime
import re
from typing import Any, Dict, Optional

import pandas as pd


# ============================================================
# TABLE NAMES
# ============================================================
BOOKINGS_TABLE = "bookings"
MARKETING_TABLE = "marketing_expenditure"
HOLDS_TABLE = "holds"
CP_PAYOUT_TABLE = "cp_payout_tracker"
DAILY_VISITS_TABLE = "daily_visits"
CASHFLOW_SLAB_MASTER_TABLE = "cashflow_slab_master"
SALES_TARGETS_TABLE = "sales_targets"


# ============================================================
# BASIC HELPERS
# ============================================================
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


def _norm_col_name(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(x or "").lower())


def _rename_existing_columns(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Renames only columns that exist.
    Keeps all extra columns also.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    rename_map = {}

    normalized_to_actual = {_norm_col_name(c): c for c in out.columns}

    for raw_name, friendly_name in mapping.items():
        key = _norm_col_name(raw_name)
        if key in normalized_to_actual:
            rename_map[normalized_to_actual[key]] = friendly_name

    out = out.rename(columns=rename_map)
    return out


def _parse_date_value(x):
    s = _safe_str(x).replace("'", "")
    if not s:
        return pd.NaT

    try:
        return pd.to_datetime(s, errors="coerce", dayfirst=True)
    except Exception:
        return pd.NaT


def _force_month_from_date(df: pd.DataFrame, date_col: str = "Date", month_col: str = "Month") -> pd.DataFrame:
    """
    Permanently avoids wrong imported Month values.
    If Date exists, Month is rebuilt from Date as APRIL 25 / MAY 25.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    if date_col not in out.columns:
        if month_col not in out.columns:
            out[month_col] = ""
        return out

    parsed = out[date_col].apply(_parse_date_value)

    if parsed.notna().any():
        out[month_col] = parsed.dt.strftime("%B %y").str.upper()
        out["_MonthSort"] = parsed.dt.strftime("%Y-%m")
    else:
        if month_col not in out.columns:
            out[month_col] = ""
        out["_MonthSort"] = ""

    return out


def _json_safe_value(v: Any):
    """
    Converts pandas/numpy/date values into JSON-safe values for Supabase insert/update.
    """
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat()

    # numpy scalar support
    try:
        if hasattr(v, "item"):
            return v.item()
    except Exception:
        pass

    return v


def make_json_safe(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _json_safe_value(v) for k, v in dict(row).items()}


# ============================================================
# SUPABASE CRUD
# ============================================================
def select_all_rows(
    supabase_client,
    table_name: str,
    order_col: Optional[str] = "id",
    page_size: int = 1000,
) -> list[dict]:
    """
    Reads all rows from Supabase using pagination.
    Works with RLS because it uses the authenticated Supabase client passed from main.py.
    """
    rows = []
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


def load_table(
    supabase_client,
    table_name: str,
    order_col: Optional[str] = "id",
) -> pd.DataFrame:
    rows = select_all_rows(
        supabase_client=supabase_client,
        table_name=table_name,
        order_col=order_col,
    )

    return pd.DataFrame(rows)


def insert_row(
    supabase_client,
    table_name: str,
    row: Dict[str, Any],
):
    payload = make_json_safe(row)
    return supabase_client.table(table_name).insert(payload).execute()


def update_row(
    supabase_client,
    table_name: str,
    row_id,
    updates: Dict[str, Any],
    id_col: str = "id",
):
    payload = make_json_safe(updates)
    return (
        supabase_client
        .table(table_name)
        .update(payload)
        .eq(id_col, row_id)
        .execute()
    )


def delete_row(
    supabase_client,
    table_name: str,
    row_id,
    id_col: str = "id",
):
    return (
        supabase_client
        .table(table_name)
        .delete()
        .eq(id_col, row_id)
        .execute()
    )


def upsert_row(
    supabase_client,
    table_name: str,
    row: Dict[str, Any],
    on_conflict: Optional[str] = None,
):
    payload = make_json_safe(row)

    if on_conflict:
        return (
            supabase_client
            .table(table_name)
            .upsert(payload, on_conflict=on_conflict)
            .execute()
        )

    return (
        supabase_client
        .table(table_name)
        .upsert(payload)
        .execute()
    )


# ============================================================
# FRIENDLY COLUMN MAPPINGS
# These keep old Google-Sheet-style tabs working.
# ============================================================
BOOKINGS_COLUMN_MAP = {
    "booking_date": "Date",
    "date": "Date",
    "customer_name": "Customer Name",
    "wing": "Wing",
    "floor": "Floor",
    "flat_number": "Flat Number",
    "flat": "Flat",
    "type": "Type",
    "unit_type": "Type",
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
    "stamp_duty_percent": "Stamp Duty %",
    "agreement_done": "Agreement Done",
    "incentive": "Incentive",
    "rcc": "RCC",
    "possession_handover": "POSSESSION HANDOVER",
    "insider_banker": "Insider Banker",
    "outsider_banker": "Outsider Banker",
    "carpet_area": "Carpet Area",
    "booking_amount": "BOOKING AMOUNT",
    "agreement": "AGREEMENT",
    "plinth": "PLINTH",
    "third_floor": "3RD FLOOR",
    "floor_3": "3RD FLOOR",
    "seventh_floor": "7TH FLOOR",
    "floor_7": "7TH FLOOR",
    "tenth_floor": "10TH FLOOR",
    "floor_10": "10TH FLOOR",
    "thirteenth_floor": "13TH FLOOR",
    "floor_13": "13TH FLOOR",
    "flooring": "FLOORING",
    "plastering": "PLASTERING",
    "plumbing": "PLUMBING",
    "electrical": "ELECTRICAL",
    "sanitary_lift": "SANITARY & LIFT",
    "sanitary_and_lift": "SANITARY & LIFT",
    "possession": "POSSESSION",
    "first_visit_date": "First Visit Date",
    "conversion_period_days": "Conversion Period (days)",
    "parking_number": "Parking Number",
    "merged_units": "Merged Units",
    "location": "Location",
    "visit_count": "Visit Count",
    "received_amount": "Received Amount",
}


MARKETING_COLUMN_MAP = {
    "amount": "Amount",
    "purpose": "Purpose",
    "expense_date": "Date",
    "date": "Date",
    "month": "Month",
    "vendor": "Vendor",
    "remark": "Remark",
}


CP_PAYOUT_COLUMN_MAP = {
    "invoice_date": "Date of Invoice",
    "invoice_number": "Invoice Number",
    "firm_cp_name": "Firm/CP Name",
    "wing": "Wing",
    "flat_number": "Flat Number",
    "flat": "Flat",
    "fos_amount": "FOS (₹)",
    "brokerage_amount": "Brokerage (₹)",
    "recorded_at": "Recorded At",
    "cp_name_fos": "CP Name (FOS)",
    "firm_name_brokerage": "Firm Name (Brokerage)",
    "fos_given": "FOS Given",
    "fos_given_date": "FOS Given Date",
    "fos_cheque_no": "FOS Cheque No",
    "fos_cheque_date": "FOS Cheque Date",
    "brokerage_given": "Brokerage Given",
    "brokerage_given_date": "Brokerage Given Date",
    "brokerage_cheque_no": "Brokerage Cheque No",
    "brokerage_cheque_date": "Brokerage Cheque Date",
}


HOLDS_COLUMN_MAP = {
    "wing": "Wing",
    "flat_number": "Flat Number",
    "hold_by": "Hold By",
    "hold_from": "Hold From",
    "hold_till": "Hold Till",
    "remarks": "Remarks",
    "entry_type": "Entry Type",
    "agreement_lineup_by": "Agreement Lineup By",
    "agreement_lineup_date": "Agreement Lineup Date",
    "agreement_lineup_remarks": "Agreement Lineup Remarks",
}


CASHFLOW_SLAB_MASTER_COLUMN_MAP = {
    "wing": "Wing",
    "slab_name": "Slab Name",
    "completed": "Completed",
    "completed_on": "Completed On",
}


DAILY_VISITS_COLUMN_MAP = {
    "visit_date": "Date",
    "date": "Date",
    "month": "Month",
    "day": "Day",

    "cp_visits": "CP Visits",
    "direct_walk_in": "Direct Walk-in",
    "references_count": "References",
    "references": "References",
    "digital": "Digital",
    "newspaper": "Newspaper",

    "todays_cancellation": "Today's Cancellation",
    "today_cancellation": "Today's Cancellation",
    "todays_booking": "Today's Booking",
    "today_booking": "Today's Booking",

    "revisit": "Revisit",
    "total_revisits": "Revisit",

    "tejas_p_revisits": "Tejas P Revisits",
    "komal_k_revisits": "Komal K Revisits",
    "ashutosh_s_revisits": "Ashutosh S Revisits",
    "sailee_d_revisits": "Sailee D Revisits",
    "sagar_b_revisits": "Sagar B Revisits",
    "harshal_s_revisits": "Harshal S Revisits",
    "alok_r_revisits": "Alok R Revisits",

    "total_attended": "Total Attended",
    "tejas_p_attended": "Tejas P Attended",
    "komal_k_attended": "Komal K Attended",
    "ashutosh_s_attended": "Ashutosh S Attended",
    "sailee_d_attended": "Sailee D Attended",
    "sagar_b_attended": "Sagar B Attended",
    "harshal_s_attended": "Harshal S Attended",
    "alok_r_attended": "Alok R Attended",

    "total_calls_answered": "Total Calls Answered",
    "tejas_p_calls_answered": "Tejas P Calls Answered",
    "komal_k_calls_answered": "Komal K Calls Answered",
    "ashutosh_s_calls_answered": "Ashutosh S Calls Answered",
    "sailee_d_calls_answered": "Sailee D Calls Answered",

    "total_calls_unanswered": "Total Calls Unanswered",
    "tejas_p_calls_unanswered": "Tejas P Calls Unanswered",
    "komal_k_calls_unanswered": "Komal K Calls Unanswered",
    "ashutosh_s_calls_unanswered": "Ashutosh S Calls Unanswered",
    "sailee_d_calls_unanswered": "Sailee D Calls Unanswered",

    "festival_1": "Festival 1",
    "festival_2": "Festival 2",
    "festival_3": "Festival 3",
    "total_visits": "Total Visits",
}


# ============================================================
# PREPARE FRIENDLY DATAFRAMES
# ============================================================
def prepare_bookings_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = _rename_existing_columns(raw_df, BOOKINGS_COLUMN_MAP)

    if df.empty:
        return pd.DataFrame()

    # Use booking Date as source of truth for Month.
    # This permanently avoids wrong imported Month values like January 25.
    df = _force_month_from_date(df, date_col="Date", month_col="Month")

    return df


def prepare_marketing_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = _rename_existing_columns(raw_df, MARKETING_COLUMN_MAP)

    if df.empty:
        return pd.DataFrame()

    # Use expense Date as source of truth for Month.
    df = _force_month_from_date(df, date_col="Date", month_col="Month")

    return df


def prepare_cp_payout_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    return _rename_existing_columns(raw_df, CP_PAYOUT_COLUMN_MAP)


def prepare_hold_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    return _rename_existing_columns(raw_df, HOLDS_COLUMN_MAP)


def prepare_cashflow_slab_master_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    return _rename_existing_columns(raw_df, CASHFLOW_SLAB_MASTER_COLUMN_MAP)


def prepare_daily_visits_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = _rename_existing_columns(raw_df, DAILY_VISITS_COLUMN_MAP)

    if df.empty:
        return pd.DataFrame()

    # Use Date as source of truth for Month.
    df = _force_month_from_date(df, date_col="Date", month_col="Month")

    return df


# ============================================================
# LOAD ALL APP DATA
# ============================================================
def load_all_data(supabase_client) -> Dict[str, pd.DataFrame]:
    """
    Loads all Supabase tables and returns both:
    - friendly Google-Sheet-style dataframes
    - raw Supabase dataframes
    """

    bookings_raw_df = load_table(supabase_client, BOOKINGS_TABLE)
    marketing_raw_df = load_table(supabase_client, MARKETING_TABLE)
    hold_raw_df = load_table(supabase_client, HOLDS_TABLE)
    cp_payout_raw_df = load_table(supabase_client, CP_PAYOUT_TABLE)
    daily_visits_raw_df = load_table(supabase_client, DAILY_VISITS_TABLE)
    cashflow_slab_master_raw_df = load_table(supabase_client, CASHFLOW_SLAB_MASTER_TABLE)

    try:
        sales_targets_raw_df = load_table(supabase_client, SALES_TARGETS_TABLE)
    except Exception:
        sales_targets_raw_df = pd.DataFrame()

    sheet_df = prepare_bookings_df(bookings_raw_df)
    marketing_df = prepare_marketing_df(marketing_raw_df)
    hold_df = prepare_hold_df(hold_raw_df)
    cp_payout_df = prepare_cp_payout_df(cp_payout_raw_df)
    daily_visits_df = prepare_daily_visits_df(daily_visits_raw_df)
    cashflow_slab_master_df = prepare_cashflow_slab_master_df(cashflow_slab_master_raw_df)

    return {
        # Friendly / old Google-Sheet-compatible names
        "sheet_df": sheet_df,
        "marketing_df": marketing_df,
        "hold_df": hold_df,
        "cp_payout_df": cp_payout_df,
        "daily_visits_df": daily_visits_df,
        "cashflow_slab_master_df": cashflow_slab_master_df,
        "sales_targets_df": sales_targets_raw_df.copy(),

        # Raw Supabase names
        "bookings_raw_df": bookings_raw_df,
        "marketing_raw_df": marketing_raw_df,
        "hold_raw_df": hold_raw_df,
        "cp_payout_raw_df": cp_payout_raw_df,
        "daily_visits_raw_df": daily_visits_raw_df,
        "cashflow_slab_master_raw_df": cashflow_slab_master_raw_df,
        "sales_targets_raw_df": sales_targets_raw_df,
    }
