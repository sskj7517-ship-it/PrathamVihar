# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.


# ============================================================
# GLOBAL FIX: BOOKING DATE → MONTH / QUARTER NORMALIZER
# Paste this ONCE before all tab code starts
# ============================================================

import re
import datetime
import pandas as pd
import streamlit as st

# Your project booking start month
PV_BOOKING_START_DATE = pd.Timestamp("2025-04-01")


# ------------------------------------------------------------
# Safe string helper — fixes pandas Categorical fillna error also
# ------------------------------------------------------------
def _safe_str_series(series):
    """
    Safe replacement for:
        series.fillna("").apply(lambda x: str(x).strip())

    This works even if the column is pandas Categorical.
    """
    if not isinstance(series, pd.Series):
        series = pd.Series(series)

    s = series.astype("object")
    s = s.where(pd.notna(s), "")
    return s.map(lambda x: "" if str(x).strip().lower() in {"nan", "nat", "none"} else str(x).strip())


def _pv_norm_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name or "").strip().lower())


def _pv_find_col(df: pd.DataFrame, possible_names):
    if df is None or df.empty:
        return None

    col_map = {_pv_norm_col(c): c for c in df.columns}

    for name in possible_names:
        hit = col_map.get(_pv_norm_col(name))
        if hit:
            return hit

    return None


def _pv_parse_single_date(x):
    if x is None or pd.isna(x):
        return pd.NaT

    if isinstance(x, pd.Timestamp):
        return x

    if isinstance(x, datetime.datetime):
        return pd.Timestamp(x)

    if isinstance(x, datetime.date):
        return pd.Timestamp(x)

    s = str(x).strip()

    if not s:
        return pd.NaT

    if s.startswith("'"):
        s = s[1:].strip()

    # Excel serial date support
    try:
        if re.fullmatch(r"\d+(\.0)?", s):
            n = float(s)
            if 30000 <= n <= 60000:
                return pd.to_datetime("1899-12-30") + pd.to_timedelta(int(n), unit="D")
    except Exception:
        pass

    formats = [
        "%d/%m/%Y",
        "%d/%m/%y",
        "%d-%m-%Y",
        "%d-%m-%y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
    ]

    for fmt in formats:
        try:
            return pd.Timestamp(datetime.datetime.strptime(s, fmt))
        except Exception:
            pass

    try:
        return pd.to_datetime(s, dayfirst=True, errors="coerce")
    except Exception:
        return pd.NaT


def _pv_parse_date_series(series: pd.Series) -> pd.Series:
    return series.apply(_pv_parse_single_date)


def _pv_quarter_label(ts):
    if pd.isna(ts):
        return ""

    m = int(ts.month)
    y = int(ts.year)

    if m in [1, 2, 3]:
        return f"January-March {y}"
    if m in [4, 5, 6]:
        return f"April-June {y}"
    if m in [7, 8, 9]:
        return f"July-September {y}"

    return f"October-December {y}"


def _pv_quarter_key(ts):
    if pd.isna(ts):
        return ""

    q = ((int(ts.month) - 1) // 3) + 1
    return f"{int(ts.year)}-Q{q}"


def _pv_standardize_booking_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Supports both Google Sheet headers and Supabase snake_case names.
    Does NOT trust Month column.
    Month is overwritten from Date later.
    """
    if df is None:
        return pd.DataFrame()

    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    # Remove duplicated column names if any
    out = out.loc[:, ~out.columns.duplicated()].copy()

    aliases = {
        "date": "Date",
        "bookingdate": "Date",
        "dateofbooking": "Date",

        "customername": "Customer Name",
        "customer": "Customer Name",

        "wing": "Wing",
        "floor": "Floor",

        "flatnumber": "Flat Number",
        "flatno": "Flat Number",
        "flat": "Flat Number",

        "type": "Type",
        "unittype": "Type",

        "finalprice": "Final Price",
        "finalpricelakhs": "Final Price",
        "finalcost": "Final Price",

        "rate": "Rate",

        "agreementcost": "Agreement Cost",

        "leadtype": "Lead Type",

        "salesexecutive": "Sales Executive",
        "salesexec": "Sales Executive",

        "stampduty": "Stamp Duty",
        "agreementdone": "Agreement Done",

        "incentive": "Incentive",
        "rcc": "RCC",
        "possessionhandover": "POSSESSION HANDOVER",

        "insiderbanker": "Insider Banker",
        "outsiderbanker": "Outsider Banker",

        "carpetarea": "Carpet Area",

        "firstvisitdate": "First Visit Date",
        "conversionperioddays": "Conversion Period (days)",
        "conversionperiod": "Conversion Period (days)",

        "parkingnumber": "Parking Number",
        "mergedunits": "Merged Units",
        "location": "Location",
        "visitcount": "Visit Count",

        "civilchanges": "Civil Changes",

        "offer1": "Offer 1",
        "offer2": "Offer 2",
        "offer1rewarded": "Offer 1 Rewarded",
        "offer2rewarded": "Offer 2 Rewarded",
        "referralgiven": "Referral Given",

        "month": "Month",
        "monthyear": "MonthYear",
        "quarter": "Quarter",
    }

    rename_map = {}
    for c in out.columns:
        norm = _pv_norm_col(c)
        if norm in aliases and c != aliases[norm]:
            rename_map[c] = aliases[norm]

    out = out.rename(columns=rename_map)
    out = out.loc[:, ~out.columns.duplicated()].copy()

    return out


def prepare_bookings_from_date(raw_df: pd.DataFrame, start_date=PV_BOOKING_START_DATE, show_warning=False) -> pd.DataFrame:
    """
    This is the main permanent fix.

    It ignores old Month / MonthYear / Quarter values and rebuilds them from Date.
    It also removes rows before April 2025 because Pratham Vihar bookings started then.
    """
    df = _pv_standardize_booking_columns(raw_df)

    if df.empty:
        return df

    date_col = _pv_find_col(df, ["Date", "Booking Date", "Date of Booking", "booking_date"])

    if not date_col:
        if show_warning:
            st.warning("Booking Date column not found. Could not rebuild Month/Quarter from Date.")
        return df

    df["BookingDateObj"] = _pv_parse_date_series(df[date_col])

    before_count = len(df)

    # Keep only valid booking dates
    df = df[df["BookingDateObj"].notna()].copy()

    invalid_removed = before_count - len(df)

    # Remove old test / wrong months before April 2025
    if start_date is not None:
        start_ts = pd.Timestamp(start_date)
        before_start_count = len(df)
        df = df[df["BookingDateObj"] >= start_ts].copy()
        old_removed = before_start_count - len(df)
    else:
        old_removed = 0

    # Sort by actual booking date
    df = df.sort_values("BookingDateObj").reset_index(drop=True)

    # Standard Date display
    df["Date"] = df["BookingDateObj"].dt.strftime("%d/%m/%Y")

    # Date-derived month fields
    df["MonthKey"] = df["BookingDateObj"].dt.strftime("%Y-%m")
    df["Month"] = df["BookingDateObj"].dt.strftime("%B %y").str.upper()
    df["month"] = df["Month"]
    df["MonthYear"] = df["Month"]

    # Date-derived quarter fields
    df["QuarterKey"] = df["BookingDateObj"].apply(_pv_quarter_key)
    df["Quarter"] = df["BookingDateObj"].apply(_pv_quarter_label)

    # Force object dtype so pandas categorical fillna error never happens here
    for c in ["Month", "month", "MonthYear", "Quarter", "MonthKey", "QuarterKey"]:
        df[c] = df[c].astype("object")

    if show_warning and (invalid_removed > 0 or old_removed > 0):
        st.info(
            f"Booking month fixed from Date. "
            f"Ignored {invalid_removed} invalid-date row(s) and {old_removed} row(s) before April 2025."
        )

    return df


def get_ordered_month_keys(df: pd.DataFrame) -> list:
    if df is None or df.empty or "MonthKey" not in df.columns:
        return []

    return (
        df[["MonthKey"]]
        .dropna()
        .drop_duplicates()
        .sort_values("MonthKey")["MonthKey"]
        .astype(str)
        .tolist()
    )


def get_ordered_months(df: pd.DataFrame) -> list:
    if df is None or df.empty or "MonthKey" not in df.columns or "Month" not in df.columns:
        return []

    temp = (
        df[["MonthKey", "Month"]]
        .dropna()
        .drop_duplicates()
        .sort_values("MonthKey")
    )

    return temp["Month"].astype(str).tolist()


def get_ordered_quarter_keys(df: pd.DataFrame) -> list:
    if df is None or df.empty or "QuarterKey" not in df.columns:
        return []

    return (
        df[["QuarterKey"]]
        .dropna()
        .drop_duplicates()
        .sort_values("QuarterKey")["QuarterKey"]
        .astype(str)
        .tolist()
    )


def get_ordered_quarters(df: pd.DataFrame) -> list:
    if df is None or df.empty or "QuarterKey" not in df.columns or "Quarter" not in df.columns:
        return []

    temp = (
        df[["QuarterKey", "Quarter"]]
        .dropna()
        .drop_duplicates()
        .sort_values("QuarterKey")
    )

    return temp["Quarter"].astype(str).tolist()


def month_label_to_key_from_df(df: pd.DataFrame, month_label: str) -> str:
    if df is None or df.empty:
        return ""

    temp = df[df["Month"].astype(str).eq(str(month_label))]
    if temp.empty:
        return ""

    return str(temp["MonthKey"].iloc[0])


def quarter_label_to_key_from_df(df: pd.DataFrame, quarter_label: str) -> str:
    if df is None or df.empty:
        return ""

    temp = df[df["Quarter"].astype(str).eq(str(quarter_label))]
    if temp.empty:
        return ""

    return str(temp["QuarterKey"].iloc[0])


def _looks_like_booking_df(candidate_df: pd.DataFrame) -> bool:
    if candidate_df is None or not isinstance(candidate_df, pd.DataFrame) or candidate_df.empty:
        return False

    norms = {_pv_norm_col(c) for c in candidate_df.columns}

    booking_signals = {
        "customername",
        "flatnumber",
        "agreementcost",
        "salesexecutive",
        "leadtype",
        "stampduty",
        "agreementdone",
    }

    return len(norms.intersection(booking_signals)) >= 2


def apply_global_booking_date_fix(show_warning=False):
    """
    This updates your common booking dataframe names:
    sheet_df, df, booking_df, bookings_df

    So existing tabs can continue using df['Month'], df['Quarter'], etc.
    """
    candidate_names = ["sheet_df", "booking_df", "bookings_df", "df"]

    source_name = None
    source_df = None

    for name in candidate_names:
        obj = globals().get(name)
        if isinstance(obj, pd.DataFrame) and _looks_like_booking_df(obj):
            source_name = name
            source_df = obj
            break

    if source_df is None:
        if show_warning:
            st.warning("No booking dataframe found to normalize. Expected one of: sheet_df, booking_df, bookings_df, df.")
        return

    fixed = prepare_bookings_from_date(source_df, show_warning=show_warning)

    # Update all existing booking-like frames
    for name in candidate_names:
        obj = globals().get(name)
        if isinstance(obj, pd.DataFrame) and _looks_like_booking_df(obj):
            globals()[name] = fixed.copy()

    # Ensure the main names always exist
    globals()["sheet_df"] = fixed.copy()
    globals()["df"] = fixed.copy()
    globals()["booking_df"] = fixed.copy()

    # Global month / quarter orders used by existing tabs
    globals()["ordered_months"] = get_ordered_months(fixed)
    globals()["ordered_month_keys"] = get_ordered_month_keys(fixed)
    globals()["ordered_quarters"] = get_ordered_quarters(fixed)
    globals()["ordered_quarter_keys"] = get_ordered_quarter_keys(fixed)


# Run the fix once before tabs
apply_global_booking_date_fix(show_warning=True)
