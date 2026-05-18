# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.

# =========================
# TAB 13: Pratham Vihar AI
# Pure Sheet / Supabase Data Assistant
# =========================

import re
import pandas as pd
import streamlit as st


# ============================================================
# RULES
# ============================================================
PV_SHEET_RULES = """
Blank cell ALWAYS means pending / not done / not received.
Stamp Duty: remark/text present = received, blank = pending.
Agreement Done: must have done/completed/yes text, blank = pending.
FOS Given / Brokerage Given: TRUE/YES/1/GIVEN means given, blank means pending.
Never invent names or data.
Only answer from available sheet/table data.
""".strip()


# ============================================================
# SCHEMA / COLUMN MEANINGS
# ============================================================
PV_SHEET_SCHEMA = {
    "booking": {
        "sheet_name": "Booking",
        "table_names": ["booking", "bookings"],
        "description": "Main booking and customer sales database for Pratham Vihar project.",
        "columns": {
            "Date": "Booking or enquiry date",
            "Customer Name": "Name of the buyer",
            "Wing": "Tower or wing of the project",
            "Floor": "Floor number of the flat",
            "Flat Number": "Specific unit number",
            "Type": "Flat configuration such as 1BHK or 2BHK",
            "Final Price": "Total final deal value of the unit",
            "Rate": "Price per sq.ft.",
            "Agreement Cost": "Cost excluding GST, stamp duty, and registration",
            "Lead Type": "Source of the lead such as Digital, Walk-in, Reference, CP, etc.",
            "Sales Executive": "Salesperson handling the client",
            "Month": "Booking month for tracking and reporting",
            "Civil Changes": "Any customization or civil work provided",
            "Offer 1": "First promotional offer",
            "Offer 2": "Second promotional offer",
            "Offer 1 Rewarded": "Whether Offer 1 was given",
            "Offer 2 Rewarded": "Whether Offer 2 was given",
            "Referral Given": "Whether referral benefit was provided",
            "Stamp Duty": "Stamp duty status or remark",
            "Agreement Done": "Status of agreement completion",
            "Incentive": "Whether incentive given or not",
            "RCC": "Whether RCC stage of that flat has arrived or not",
            "POSSESSION HANDOVER": "Possession status of the unit",
            "Insider Banker": "Internal or tie-up bank used",
            "Outsider Banker": "External bank used by customer",
            "Carpet Area": "Net usable area of the flat",
            "BOOKING AMOUNT": "Initial token or booking amount received",
            "AGREEMENT": "Payment received at agreement stage",
            "PLINTH": "Payment at plinth completion stage",
            "3RD FLOOR": "Payment at 3rd floor slab stage",
            "7TH FLOOR": "Payment at 7th floor slab stage",
            "10TH FLOOR": "Payment at 10th floor slab stage",
            "13TH FLOOR": "Payment at 13th floor slab stage",
            "FLOORING": "Payment at flooring stage",
            "PLASTERING": "Payment at plastering stage",
            "PLUMBING": "Payment at plumbing stage",
            "ELECTRICAL": "Payment at electrical stage",
            "SANITARY & LIFT": "Payment at sanitary fittings and lift stage",
            "POSSESSION": "Final payment at possession stage",
            "First Visit Date": "Customer first site visit date",
            "Conversion Period (days)": "Days taken from visit to booking",
            "Parking Number": "Allocated parking slot number",
            "Merged Units": "Whether units are combined",
            "Location": "Customer location or locality",
            "Visit Count": "Visit number on which booking happened",
        },
    },
    "marketing": {
        "sheet_name": "Marketing Expenditure",
        "table_names": ["marketing_expenditure"],
        "description": "Marketing spend tracker for vendors, campaigns, and monthly expenses.",
        "columns": {
            "Amount": "Total money spent for the activity",
            "Purpose": "Type of marketing activity such as Digital, Hoarding, Event, etc.",
            "Date": "Date when the expense was made",
            "Month": "Month of the expense for tracking and reporting",
            "Vendor": "Agency or vendor to whom payment was made",
            "Remark": "Additional notes or details about the expense",
        },
    },
    "cp_payout": {
        "sheet_name": "CP Payout Expenditure",
        "table_names": ["cp_payout_tracker"],
        "description": "Channel partner payout tracker for FOS and brokerage releases.",
        "columns": {
            "Date of Invoice": "Date on which the invoice was generated",
            "Invoice Number": "Unique invoice reference number",
            "Firm/CP Name": "Name of the channel partner or firm involved",
            "Wing": "Tower or wing of the booked unit",
            "Flat Number": "Specific unit number",
            "Flat": "Flat details or label",
            "FOS (₹)": "Field Officer Service payout amount",
            "Brokerage (₹)": "Brokerage amount payable to channel partner or firm",
            "Recorded At": "Date and time when entry was recorded in system",
            "CP Name (FOS)": "Name of individual receiving FOS payout",
            "Firm Name (Brokerage)": "Firm receiving brokerage payment",
            "FOS Given": "Status of FOS payout",
            "FOS Given Date": "Date when FOS payment was made",
            "FOS Cheque No": "Cheque number used for FOS payment",
            "FOS Cheque Date": "Date on the FOS cheque",
            "Brokerage Given": "Status of brokerage payout",
            "Brokerage Given Date": "Date when brokerage was paid",
            "Brokerage Cheque No": "Cheque number used for brokerage payment",
            "Brokerage Cheque Date": "Date on the brokerage cheque",
        },
    },
    "daily_visits": {
        "sheet_name": "Daily Visits",
        "table_names": ["daily_visits"],
        "description": "Daily site visit, booking, cancellation, revisit, call, and executive attendance tracker.",
        "columns": {
            "Date": "Date of visit data entry",
            "Month": "Month for tracking and reporting",
            "Day": "Day of the week for trend analysis",
            "CP Visits": "Number of visits generated by channel partners",
            "Direct Walk-in": "Number of direct customer walk-ins",
            "References": "Visits through referrals",
            "Digital": "Visits generated via digital marketing channels",
            "Newspaper": "Visits generated through newspaper ads",
            "Today's Cancellation": "Number of bookings cancelled on that day",
            "Today's Booking": "Number of bookings done on that day",
            "Total Revisits": "Total number of repeat visits",
            "Tejas P Revisits": "Revisits handled by Tejas P",
            "Komal K Revisits": "Revisits handled by Komal K",
            "Ashutosh S Revisits": "Revisits handled by Ashutosh S",
            "Sailee D Revisits": "Revisits handled by Sailee D",
            "Dhanashree W Revisits": "Revisits handled by Dhanashree W",
            "Total Attended": "Total visits attended by all executives",
            "Tejas P Attended": "Total visits attended by Tejas P",
            "Komal K Attended": "Total visits attended by Komal K",
            "Ashutosh S Attended": "Total visits attended by Ashutosh S",
            "Sailee D Attended": "Total visits attended by Sailee D",
            "Dhanashree W Attended": "Total visits attended by Dhanashree W",
            "Total Calls Answered": "Total answered calls",
            "Total Calls Unanswered": "Total unanswered calls",
            "Festival 1": "First festival or offer campaign remark",
            "Festival 2": "Second festival or offer campaign remark",
            "Festival 3": "Third festival or offer campaign remark",
            "Total Visits": "Total number of visits for the day",
        },
    },
}


# ============================================================
# COLUMN ALIASES: Supports old Google Sheet headers + new Supabase snake_case
# ============================================================
PV_COLUMN_ALIASES = {
    # Booking
    "Date": ["date", "booking_date"],
    "Customer Name": ["customer_name", "customer"],
    "Wing": ["wing"],
    "Floor": ["floor"],
    "Flat Number": ["flat_number", "flat_no", "flat"],
    "Type": ["type", "unit_type"],
    "Final Price": ["final_price", "final_price_lakhs"],
    "Rate": ["rate", "psf_rate"],
    "Agreement Cost": ["agreement_cost"],
    "Lead Type": ["lead_type"],
    "Sales Executive": ["sales_executive", "sales_exec"],
    "Month": ["month", "monthyear", "month_year"],
    "Civil Changes": ["civil_changes"],
    "Offer 1": ["offer_1"],
    "Offer 2": ["offer_2"],
    "Offer 1 Rewarded": ["offer_1_rewarded"],
    "Offer 2 Rewarded": ["offer_2_rewarded"],
    "Referral Given": ["referral_given"],
    "Stamp Duty": ["stamp_duty"],
    "Agreement Done": ["agreement_done"],
    "Incentive": ["incentive"],
    "RCC": ["rcc"],
    "POSSESSION HANDOVER": ["possession_handover"],
    "Insider Banker": ["insider_banker"],
    "Outsider Banker": ["outsider_banker"],
    "Carpet Area": ["carpet_area"],
    "First Visit Date": ["first_visit_date"],
    "Conversion Period (days)": ["conversion_period_days", "conversion_period"],
    "Parking Number": ["parking_number"],
    "Merged Units": ["merged_units"],
    "Location": ["location"],
    "Visit Count": ["visit_count"],

    # Marketing
    "Amount": ["amount"],
    "Purpose": ["purpose"],
    "Vendor": ["vendor"],
    "Remark": ["remark"],

    # CP Payout
    "Date of Invoice": ["invoice_date", "date_of_invoice"],
    "Invoice Number": ["invoice_number"],
    "Firm/CP Name": ["firm_cp_name", "firm_or_cp_name"],
    "Flat": ["flat"],
    "FOS (₹)": ["fos_amount", "fos", "fos_rs"],
    "Brokerage (₹)": ["brokerage_amount", "brokerage", "brokerage_rs"],
    "Recorded At": ["recorded_at"],
    "CP Name (FOS)": ["cp_name_fos"],
    "Firm Name (Brokerage)": ["firm_name_brokerage"],
    "FOS Given": ["fos_given"],
    "FOS Given Date": ["fos_given_date"],
    "FOS Cheque No": ["fos_cheque_no"],
    "FOS Cheque Date": ["fos_cheque_date"],
    "Brokerage Given": ["brokerage_given"],
    "Brokerage Given Date": ["brokerage_given_date"],
    "Brokerage Cheque No": ["brokerage_cheque_no"],
    "Brokerage Cheque Date": ["brokerage_cheque_date"],

    # Daily Visits
    "CP Visits": ["cp_visits"],
    "Direct Walk-in": ["direct_walk_in", "direct_walkin"],
    "References": ["references_count", "references"],
    "Digital": ["digital"],
    "Newspaper": ["newspaper"],
    "Today's Cancellation": ["todays_cancellation", "today_cancellation"],
    "Today's Booking": ["todays_booking", "today_booking"],
    "Revisit": ["revisit", "total_revisits"],
    "Total Revisits": ["total_revisits", "revisit"],
    "Tejas P Revisits": ["tejas_p_revisits"],
    "Komal K Revisits": ["komal_k_revisits"],
    "Ashutosh S Revisits": ["ashutosh_s_revisits"],
    "Sailee D Revisits": ["sailee_d_revisits"],
    "Dhanashree W Revisits": ["dhanashree_w_revisits"],
    "Total Attended": ["total_attended"],
    "Tejas P Attended": ["tejas_p_attended"],
    "Komal K Attended": ["komal_k_attended"],
    "Ashutosh S Attended": ["ashutosh_s_attended"],
    "Sailee D Attended": ["sailee_d_attended"],
    "Dhanashree W Attended": ["dhanashree_w_attended"],
    "Total Calls Answered": ["total_calls_answered"],
    "Tejas P Calls Answered": ["tejas_p_calls_answered"],
    "Komal K Calls Answered": ["komal_k_calls_answered"],
    "Ashutosh S Calls Answered": ["ashutosh_s_calls_answered"],
    "Sailee D Calls Answered": ["sailee_d_calls_answered"],
    "Dhanashree W Calls Answered": ["dhanashree_w_calls_answered"],
    "Total Calls Unanswered": ["total_calls_unanswered"],
    "Tejas P Calls Unanswered": ["tejas_p_calls_unanswered"],
    "Komal K Calls Unanswered": ["komal_k_calls_unanswered"],
    "Ashutosh S Calls Unanswered": ["ashutosh_s_calls_unanswered"],
    "Sailee D Calls Unanswered": ["sailee_d_calls_unanswered"],
    "Dhanashree W Calls Unanswered": ["dhanashree_w_calls_unanswered"],
    "Festival 1": ["festival_1"],
    "Festival 2": ["festival_2"],
    "Festival 3": ["festival_3"],
    "Total Visits": ["total_visits"],
    "Day": ["day"],
}


# ============================================================
# GENERIC HELPERS
# ============================================================
def _safe_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def _col_norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).lower())


def _get_col(df: pd.DataFrame, want: str):
    if df is None or df.empty:
        return None

    cmap = {_col_norm(c): c for c in df.columns}

    # Direct name match
    direct = cmap.get(_col_norm(want))
    if direct:
        return direct

    # Alias match
    for alias in PV_COLUMN_ALIASES.get(want, []):
        hit = cmap.get(_col_norm(alias))
        if hit:
            return hit

    return None


def _to_num(series):
    try:
        return pd.to_numeric(series, errors="coerce")
    except Exception:
        return pd.Series(dtype=float)


def _truthy(v) -> bool:
    s = str(v if v is not None else "").strip().upper()
    return s in {"TRUE", "YES", "1", "DONE", "COMPLETED", "GIVEN", "RECEIVED"}


def _is_blank_or_pending(v) -> bool:
    if v is None:
        return True
    s = str(v).strip().lower()
    if s == "":
        return True
    return s in {
        "pending",
        "due",
        "remaining",
        "not received",
        "not done",
        "na",
        "n/a",
        "none",
        "null",
    }


def _agreement_done(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    if s == "":
        return False
    return ("done" in s) or ("complete" in s) or (s == "yes") or (s == "true")


def _extract_flat_from_question(q: str):
    q2 = str(q).upper().strip()

    patterns = [
        r"\bFLAT\s*([A-Z])\s*[- ]?\s*(\d{2,5})\b",
        r"\bWING\s*([A-Z])\s+FLAT\s*(\d{2,5})\b",
        r"\b([A-Z])\s*[- ]?\s*(\d{2,5})\b",
    ]

    for p in patterns:
        m = re.search(p, q2)
        if m:
            return m.group(1).strip(), m.group(2).strip()

    return None, None


def _find_name_match(df: pd.DataFrame, col: str, q: str):
    if not col or col not in df.columns:
        return None

    values = df[col].dropna().astype(str).str.strip()
    values = values[values != ""].unique().tolist()

    q_low = q.lower().strip()

    exact_hits = [v for v in values if str(v).lower() in q_low or q_low in str(v).lower()]
    if exact_hits:
        return exact_hits[0]

    for v in values:
        parts = str(v).lower().split()
        if any(len(p) >= 3 and p in q_low for p in parts):
            return v

    return None


def _parse_date_series(series):
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def _parse_any_date(val):
    try:
        s = str(val).strip()
        if not s:
            return pd.NaT
        return pd.to_datetime(s, errors="coerce", dayfirst=True)
    except Exception:
        return pd.NaT


def _fmt_money(v):
    try:
        return f"₹ {float(v):,.2f}"
    except Exception:
        return "₹ 0.00"


def _fmt_int(v):
    try:
        return f"{int(float(v)):,}"
    except Exception:
        return "0"


def _schema_keywords(sheet_key: str):
    info = PV_SHEET_SCHEMA.get(sheet_key, {})
    words = []

    for col, desc in info.get("columns", {}).items():
        words.append(str(col).lower())
        words.append(str(desc).lower())
        for alias in PV_COLUMN_ALIASES.get(col, []):
            words.append(str(alias).lower())

    words.append(str(info.get("description", "")).lower())
    words.append(str(info.get("sheet_name", "")).lower())

    return words


def _answer_schema_question(question: str):
    q = question.lower()

    if "what does" in q or "meaning of" in q or "what is" in q:
        for sheet_key, sheet_info in PV_SHEET_SCHEMA.items():
            for col, desc in sheet_info.get("columns", {}).items():
                possible_names = [col] + PV_COLUMN_ALIASES.get(col, [])
                if any(str(name).lower() in q or _col_norm(name) in _col_norm(q) for name in possible_names):
                    return (
                        f"**{col}** in **{sheet_info.get('sheet_name', sheet_key)}** means: {desc}",
                        None,
                        f"{col} Meaning",
                        sheet_key
                    )

    if "which sheets" in q or "what sheets" in q or "connected sheets" in q or "available sheets" in q:
        rows = []
        for sheet_key, sheet_info in PV_SHEET_SCHEMA.items():
            rows.append({
                "Sheet": sheet_info.get("sheet_name", sheet_key),
                "Supabase Table": ", ".join(sheet_info.get("table_names", [])),
                "Description": sheet_info.get("description", "")
            })
        return ("These are the connected sheets/tables and their purpose:", pd.DataFrame(rows), "Connected Sheets", "general")

    if "show columns" in q or "available columns" in q or "what columns" in q:
        rows = []
        for sheet_key, sheet_info in PV_SHEET_SCHEMA.items():
            for col, desc in sheet_info.get("columns", {}).items():
                rows.append({
                    "Sheet": sheet_info.get("sheet_name", sheet_key),
                    "Column": col,
                    "Supported Aliases": ", ".join(PV_COLUMN_ALIASES.get(col, [])),
                    "Meaning": desc
                })
        return ("Here are the available columns and their meaning:", pd.DataFrame(rows), "Column Dictionary", "general")

    return None


# ============================================================
# DATA LOADING HELPERS
# Works with:
# - existing DataFrames: sheet_df, daily_visits_df, cp_payout_df, marketing_df
# - Supabase client variable named supabase
# ============================================================
def _pv_load_supabase_table(table_names: list[str]) -> pd.DataFrame:
    if "supabase" not in globals():
        return pd.DataFrame()

    sb = globals().get("supabase")
    if sb is None:
        return pd.DataFrame()

    for table_name in table_names:
        try:
            res = sb.table(table_name).select("*").execute()
            data = getattr(res, "data", None)
            if data:
                return pd.DataFrame(data)
        except Exception:
            pass

    return pd.DataFrame()


def _pv_get_df(sheet_key: str) -> pd.DataFrame:
    # 1) Prefer existing app DataFrames
    if sheet_key == "booking":
        for var in ["sheet_df", "booking_df", "bookings_df", "df"]:
            if var in globals() and isinstance(globals()[var], pd.DataFrame) and not globals()[var].empty:
                return _safe_df(globals()[var])

    if sheet_key == "daily_visits":
        for var in ["daily_visits_df", "dv", "daily_visits"]:
            if var in globals() and isinstance(globals()[var], pd.DataFrame) and not globals()[var].empty:
                return _safe_df(globals()[var])

    if sheet_key == "cp_payout":
        for var in ["cp_payout_df", "cp_payout_tracker_df", "cp_payout_tracker"]:
            if var in globals() and isinstance(globals()[var], pd.DataFrame) and not globals()[var].empty:
                return _safe_df(globals()[var])

    if sheet_key == "marketing":
        for var in ["marketing_df", "marketing_expenditure_df", "marketing_expenditure"]:
            if var in globals() and isinstance(globals()[var], pd.DataFrame) and not globals()[var].empty:
                return _safe_df(globals()[var])

    # 2) Try Supabase
    table_names = PV_SHEET_SCHEMA.get(sheet_key, {}).get("table_names", [])
    return _safe_df(_pv_load_supabase_table(table_names))


# ============================================================
# BOOKING ANSWERS
# ============================================================
def _answer_booking_question(question: str, df: pd.DataFrame):
    q = question.strip().lower()
    df = _safe_df(df)

    if df.empty:
        return None

    cust_col = _get_col(df, "Customer Name")
    wing_col = _get_col(df, "Wing")
    flat_col = _get_col(df, "Flat Number")
    se_col = _get_col(df, "Sales Executive")
    month_col = _get_col(df, "Month")
    stamp_col = _get_col(df, "Stamp Duty")
    agr_col = _get_col(df, "Agreement Done")
    final_price_col = _get_col(df, "Final Price")
    rate_col = _get_col(df, "Rate")
    carpet_col = _get_col(df, "Carpet Area")
    lead_col = _get_col(df, "Lead Type")
    date_col = _get_col(df, "Date")
    visit_count_col = _get_col(df, "Visit Count")
    location_col = _get_col(df, "Location")
    type_col = _get_col(df, "Type")
    parking_col = _get_col(df, "Parking Number")

    # Pending Stamp Duty
    if "stamp duty" in q and any(w in q for w in ["pending", "due", "not received", "remaining", "list"]):
        if not stamp_col:
            return ("I couldn’t find the Stamp Duty column.", None, None, "booking")

        mask = df[stamp_col].apply(_is_blank_or_pending)
        cols = [c for c in [cust_col, wing_col, flat_col, se_col, month_col] if c]
        out = df.loc[mask, cols].copy()
        out["Stamp Duty Status"] = "Pending"

        return (f"Total pending stamp duty: **{len(out)}**", out, "Stamp Duty Pending", "booking")

    # Stamp Duty Received
    if "stamp duty" in q and any(w in q for w in ["received", "done", "paid"]):
        if not stamp_col:
            return ("I couldn’t find the Stamp Duty column.", None, None, "booking")

        mask = ~df[stamp_col].apply(_is_blank_or_pending)
        cols = [c for c in [cust_col, wing_col, flat_col, se_col, month_col, stamp_col] if c]
        out = df.loc[mask, cols].copy()

        return (f"Total stamp duty received: **{len(out)}**", out, "Stamp Duty Received", "booking")

    # Pending Agreement
    if "agreement" in q and any(w in q for w in ["pending", "due", "not done", "remaining", "list"]):
        if not agr_col:
            return ("I couldn’t find the Agreement Done column.", None, None, "booking")

        mask = ~df[agr_col].apply(_agreement_done)
        cols = [c for c in [cust_col, wing_col, flat_col, se_col, month_col] if c]
        out = df.loc[mask, cols].copy()
        out["Agreement Status"] = "Pending"

        return (f"Total pending agreements: **{len(out)}**", out, "Agreement Pending", "booking")

    # Agreement Done
    if "agreement" in q and any(w in q for w in ["done", "completed", "complete"]):
        if not agr_col:
            return ("I couldn’t find the Agreement Done column.", None, None, "booking")

        mask = df[agr_col].apply(_agreement_done)
        cols = [c for c in [cust_col, wing_col, flat_col, se_col, month_col, agr_col] if c]
        out = df.loc[mask, cols].copy()

        return (f"Total agreements done: **{len(out)}**", out, "Agreement Done", "booking")

    # Top Sales Executive
    if ("sales executive" in q or "executive" in q) and any(w in q for w in ["highest", "top", "most"]) and any(w in q for w in ["sales", "bookings", "booking"]):
        if not se_col:
            return ("I couldn’t find the Sales Executive column.", None, None, "booking")

        temp = df.copy()
        temp[se_col] = temp[se_col].fillna("").astype(str).str.strip()
        temp = temp[temp[se_col] != ""]

        if temp.empty:
            return ("No Sales Executive names found.", None, None, "booking")

        counts = (
            temp.groupby(se_col)
            .size()
            .reset_index(name="Bookings")
            .sort_values("Bookings", ascending=False)
        )

        top_name = counts.iloc[0][se_col]
        top_val = int(counts.iloc[0]["Bookings"])

        return (
            f"Top Sales Executive: **{top_name}** with **{top_val}** bookings.",
            counts,
            "Bookings by Sales Executive",
            "booking"
        )

    # Specific SE
    if se_col and ("sales executive" in q or "executive" in q):
        se_name = _find_name_match(df, se_col, q)

        if se_name:
            temp = df[df[se_col].fillna("").astype(str).str.strip().eq(str(se_name).strip())].copy()
            cols = [c for c in [cust_col, wing_col, flat_col, type_col, final_price_col, rate_col, month_col] if c]
            out = temp[cols].copy() if cols else temp.copy()

            return (f"Found **{len(out)}** records for Sales Executive **{se_name}**.", out, f"Records for {se_name}", "booking")

    # Flat lookup
    q_wing, q_flat = _extract_flat_from_question(question)

    if q_wing and q_flat and wing_col and flat_col:
        temp = df.copy()
        temp[wing_col] = temp[wing_col].fillna("").astype(str).str.strip().str.upper()
        temp[flat_col] = temp[flat_col].fillna("").astype(str).str.strip()

        hit = temp[(temp[wing_col] == q_wing) & (temp[flat_col] == q_flat)].copy()

        if hit.empty:
            return (f"I couldn’t find any record for flat **{q_wing} {q_flat}**.", None, None, "booking")

        preferred_cols = [c for c in [
            cust_col, wing_col, flat_col, type_col, se_col, rate_col,
            final_price_col, carpet_col, month_col, lead_col, date_col,
            stamp_col, agr_col, visit_count_col, location_col, parking_col
        ] if c]

        out = hit[preferred_cols].copy()

        if "rate" in q and rate_col:
            vals = hit[rate_col].dropna().astype(str).unique().tolist()
            return (f"Rate for **{q_wing} {q_flat}**: **{', '.join(vals) if vals else 'Not available'}**", out, f"Flat {q_wing} {q_flat}", "booking")

        if "final price" in q or "deal value" in q or "price" in q:
            if final_price_col:
                vals = hit[final_price_col].dropna().astype(str).unique().tolist()
                return (f"Final Price for **{q_wing} {q_flat}**: **{', '.join(vals) if vals else 'Not available'}**", out, f"Flat {q_wing} {q_flat}", "booking")

        if "carpet" in q and carpet_col:
            vals = hit[carpet_col].dropna().astype(str).unique().tolist()
            return (f"Carpet Area for **{q_wing} {q_flat}**: **{', '.join(vals) if vals else 'Not available'}**", out, f"Flat {q_wing} {q_flat}", "booking")

        if "customer" in q and cust_col:
            vals = hit[cust_col].dropna().astype(str).unique().tolist()
            return (f"Customer for **{q_wing} {q_flat}**: **{', '.join(vals) if vals else 'Not available'}**", out, f"Flat {q_wing} {q_flat}", "booking")

        return (f"Found **{len(out)}** record(s) for flat **{q_wing} {q_flat}**.", out, f"Flat {q_wing} {q_flat}", "booking")

    # Wing queries
    if wing_col and "wing" in q:
        m = re.search(r"\bwing\s+([a-z])\b", q)

        if m:
            want_wing = m.group(1).upper()
            temp = df[df[wing_col].fillna("").astype(str).str.strip().str.upper().eq(want_wing)].copy()

            if temp.empty:
                return (f"No records found for Wing **{want_wing}**.", None, None, "booking")

            if "count" in q or "how many" in q or "bookings" in q:
                cols = [c for c in [cust_col, flat_col, type_col, se_col, final_price_col] if c]
                return (
                    f"Total records/bookings in Wing **{want_wing}**: **{len(temp)}**.",
                    temp[cols],
                    f"Wing {want_wing}",
                    "booking"
                )

            if "average" in q and final_price_col:
                fp = _to_num(temp[final_price_col]).dropna()
                if not fp.empty:
                    cols = [c for c in [cust_col, flat_col, final_price_col] if c]
                    return (
                        f"Average Final Price in Wing **{want_wing}**: **{fp.mean():,.2f}**",
                        temp[cols],
                        f"Wing {want_wing}",
                        "booking"
                    )

            cols = [c for c in [cust_col, flat_col, type_col, se_col, final_price_col, rate_col] if c]
            return (f"Found **{len(temp)}** records in Wing **{want_wing}**.", temp[cols], f"Wing {want_wing}", "booking")

    # Rate queries
    if "rate" in q and rate_col:
        rates = _to_num(df[rate_col]).dropna()

        if not rates.empty:
            if any(w in q for w in ["highest", "max", "maximum"]):
                mx = rates.max()
                temp = df[_to_num(df[rate_col]) == mx].copy()
                cols = [c for c in [cust_col, wing_col, flat_col, rate_col, final_price_col] if c]
                return (f"Highest rate in Booking sheet: **{mx:,.2f}**", temp[cols], "Highest Rate", "booking")

            if any(w in q for w in ["lowest", "min", "minimum"]):
                mn = rates.min()
                temp = df[_to_num(df[rate_col]) == mn].copy()
                cols = [c for c in [cust_col, wing_col, flat_col, rate_col, final_price_col] if c]
                return (f"Lowest rate in Booking sheet: **{mn:,.2f}**", temp[cols], "Lowest Rate", "booking")

            if "average" in q or "avg" in q:
                return (f"Average rate in Booking sheet: **{rates.mean():,.2f}**", None, None, "booking")

    # Final price queries
    if ("final price" in q or "price" in q or "deal value" in q) and final_price_col:
        vals = _to_num(df[final_price_col]).dropna()

        if not vals.empty:
            if any(w in q for w in ["highest", "max", "maximum"]):
                mx = vals.max()
                temp = df[_to_num(df[final_price_col]) == mx].copy()
                cols = [c for c in [cust_col, wing_col, flat_col, final_price_col] if c]
                return (f"Highest Final Price: **{mx:,.2f}**", temp[cols], "Highest Final Price", "booking")

            if any(w in q for w in ["lowest", "min", "minimum"]):
                mn = vals.min()
                temp = df[_to_num(df[final_price_col]) == mn].copy()
                cols = [c for c in [cust_col, wing_col, flat_col, final_price_col] if c]
                return (f"Lowest Final Price: **{mn:,.2f}**", temp[cols], "Lowest Final Price", "booking")

            if "average" in q or "avg" in q:
                return (f"Average Final Price: **{vals.mean():,.2f}**", None, None, "booking")

    # Customer search
    if cust_col and "customer" in q:
        cust_name = _find_name_match(df, cust_col, q)

        if cust_name:
            temp = df[df[cust_col].fillna("").astype(str).str.strip().eq(str(cust_name).strip())].copy()
            cols = [c for c in [cust_col, wing_col, flat_col, type_col, se_col, final_price_col, rate_col, month_col] if c]

            return (f"Found **{len(temp)}** record(s) for customer **{cust_name}**.", temp[cols], f"Customer {cust_name}", "booking")

    # Lead type summary
    if "lead" in q and lead_col:
        temp = df.copy()
        temp[lead_col] = temp[lead_col].fillna("").astype(str).str.strip()
        temp = temp[temp[lead_col] != ""]

        if not temp.empty:
            g = temp.groupby(lead_col).size().reset_index(name="Bookings").sort_values("Bookings", ascending=False)
            return ("Here is lead type-wise booking summary.", g, "Lead Type-wise Bookings", "booking")

    # Total bookings
    if "total bookings" in q or "how many bookings" in q or q in {"bookings", "total booking"}:
        return (f"Total bookings/records in Booking sheet: **{len(df)}**", None, None, "booking")

    return None


# ============================================================
# DAILY VISITS ANSWERS
# ============================================================
def _answer_daily_visits_question(question: str, df: pd.DataFrame):
    q = question.strip().lower()
    df = _safe_df(df)

    if df.empty:
        return None

    date_col = _get_col(df, "Date")
    month_col = _get_col(df, "Month")
    revisit_col = _get_col(df, "Total Revisits") or _get_col(df, "Revisit")
    total_visits_col = _get_col(df, "Total Visits")
    booking_col = _get_col(df, "Today's Booking")
    cancellation_col = _get_col(df, "Today's Cancellation")
    direct_col = _get_col(df, "Direct Walk-in")
    cp_col = _get_col(df, "CP Visits")
    ref_col = _get_col(df, "References")
    digital_col = _get_col(df, "Digital")
    newspaper_col = _get_col(df, "Newspaper")
    calls_ans_col = _get_col(df, "Total Calls Answered")
    calls_unans_col = _get_col(df, "Total Calls Unanswered")
    total_att_col = _get_col(df, "Total Attended")

    if date_col:
        df["_date_obj"] = _parse_date_series(df[date_col])

    num_cols = [
        revisit_col, total_visits_col, booking_col, cancellation_col,
        direct_col, cp_col, ref_col, digital_col, newspaper_col,
        calls_ans_col, calls_unans_col, total_att_col
    ]

    for c in [x for x in num_cols if x]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    if "revisit" in q and any(w in q for w in ["total", "overall", "how many"]):
        if revisit_col:
            return (f"Total revisits in Daily Visits: **{int(df[revisit_col].sum())}**", None, None, "daily_visits")

    if "total visits" in q or ("visits" in q and any(w in q for w in ["total", "overall", "how many"])):
        if total_visits_col:
            return (f"Total visits in Daily Visits: **{int(df[total_visits_col].sum())}**", None, None, "daily_visits")

    if "direct walk" in q and direct_col:
        return (f"Total Direct Walk-in visits: **{int(df[direct_col].sum())}**", None, None, "daily_visits")

    if "cp visit" in q and cp_col:
        return (f"Total CP Visits: **{int(df[cp_col].sum())}**", None, None, "daily_visits")

    if "digital" in q and digital_col and "marketing" not in q:
        return (f"Total Digital visits: **{int(df[digital_col].sum())}**", None, None, "daily_visits")

    if "newspaper" in q and newspaper_col:
        return (f"Total Newspaper visits: **{int(df[newspaper_col].sum())}**", None, None, "daily_visits")

    if "reference" in q and ref_col:
        return (f"Total Reference visits: **{int(df[ref_col].sum())}**", None, None, "daily_visits")

    if "booking" in q and any(w in q for w in ["total", "overall", "how many"]):
        if booking_col:
            return (f"Total bookings in Daily Visits: **{int(df[booking_col].sum())}**", None, None, "daily_visits")

    if "cancellation" in q and any(w in q for w in ["total", "overall", "how many"]):
        if cancellation_col:
            return (f"Total cancellations in Daily Visits: **{int(df[cancellation_col].sum())}**", None, None, "daily_visits")

    if "call" in q:
        total_answered = int(df[calls_ans_col].sum()) if calls_ans_col else 0
        total_unanswered = int(df[calls_unans_col].sum()) if calls_unans_col else 0
        total_calls = total_answered + total_unanswered

        if "answered" in q and "unanswered" not in q:
            return (f"Total calls answered: **{total_answered}**", None, None, "daily_visits")

        if "unanswered" in q:
            return (f"Total calls unanswered: **{total_unanswered}**", None, None, "daily_visits")

        if "total" in q or "how many" in q:
            return (
                f"Total calls: **{total_calls}**  \nAnswered: **{total_answered}**  \nUnanswered: **{total_unanswered}**",
                None,
                None,
                "daily_visits"
            )

    if "best day" in q or "highest booking day" in q or "day with highest booking" in q:
        if date_col and booking_col and "_date_obj" in df.columns:
            temp = df.dropna(subset=["_date_obj"]).copy()

            if not temp.empty:
                temp["DayName"] = temp["_date_obj"].dt.strftime("%A")
                g = temp.groupby("DayName", as_index=False)[booking_col].sum().sort_values(booking_col, ascending=False)

                if not g.empty:
                    return (
                        f"Day with highest booking: **{g.iloc[0]['DayName']}** with **{int(g.iloc[0][booking_col])}** bookings.",
                        g.rename(columns={booking_col: "Bookings"}),
                        "Booking by Day",
                        "daily_visits"
                    )

    if "month wise" in q or "monthly" in q:
        temp = df.copy()

        if date_col and "_date_obj" in temp.columns and temp["_date_obj"].notna().any():
            temp = temp.dropna(subset=["_date_obj"]).copy()
            temp["MonthKey"] = temp["_date_obj"].dt.strftime("%B %y")
        elif month_col:
            temp["MonthKey"] = temp[month_col].astype(str).str.strip()
        else:
            return None

        agg_map = {}
        if total_visits_col:
            agg_map[total_visits_col] = "sum"
        if revisit_col:
            agg_map[revisit_col] = "sum"
        if booking_col:
            agg_map[booking_col] = "sum"
        if cancellation_col:
            agg_map[cancellation_col] = "sum"

        if agg_map:
            g = temp.groupby("MonthKey", as_index=False).agg(agg_map)
            return ("Here is the month-wise Daily Visits summary.", g, "Month-wise Daily Visits", "daily_visits")

    if "source" in q or "lead source" in q:
        rows = []

        for label, col in [
            ("CP Visits", cp_col),
            ("Direct Walk-in", direct_col),
            ("References", ref_col),
            ("Digital", digital_col),
            ("Newspaper", newspaper_col),
        ]:
            if col:
                rows.append({"Source": label, "Visits": int(df[col].sum())})

        if rows:
            out = pd.DataFrame(rows).sort_values("Visits", ascending=False)
            top = out.iloc[0]
            return (
                f"Top visit source: **{top['Source']}** with **{int(top['Visits'])}** visits.",
                out,
                "Visit Source Summary",
                "daily_visits"
            )

    if "sales executive" in q or "executive" in q:
        exec_map = [
            ("Tejas P Revisits", "Tejas P Attended", "Tejas P Calls Answered", "Tejas P Calls Unanswered", "Tejas P"),
            ("Komal K Revisits", "Komal K Attended", "Komal K Calls Answered", "Komal K Calls Unanswered", "Komal K"),
            ("Ashutosh S Revisits", "Ashutosh S Attended", "Ashutosh S Calls Answered", "Ashutosh S Calls Unanswered", "Ashutosh S"),
            ("Sailee D Revisits", "Sailee D Attended", "Sailee D Calls Answered", "Sailee D Calls Unanswered", "Sailee D"),
            ("Dhanashree W Revisits", "Dhanashree W Attended", "Dhanashree W Calls Answered", "Dhanashree W Calls Unanswered", "Dhanashree W"),
        ]

        rows = []

        for rev_name, att_name, ans_name, unans_name, name in exec_map:
            rc = _get_col(df, rev_name)
            ac = _get_col(df, att_name)
            ans_c = _get_col(df, ans_name)
            unans_c = _get_col(df, unans_name)

            revisits = pd.to_numeric(df[rc], errors="coerce").fillna(0).sum() if rc else 0
            attended = pd.to_numeric(df[ac], errors="coerce").fillna(0).sum() if ac else 0
            answered = pd.to_numeric(df[ans_c], errors="coerce").fillna(0).sum() if ans_c else 0
            unanswered = pd.to_numeric(df[unans_c], errors="coerce").fillna(0).sum() if unans_c else 0
            total_calls = answered + unanswered

            if revisits or attended or total_calls:
                rows.append({
                    "Sales Executive": name,
                    "Revisits": int(revisits),
                    "Attended": int(attended),
                    "Calls Answered": int(answered),
                    "Calls Unanswered": int(unanswered),
                    "Total Calls": int(total_calls),
                    "Revisit %": round((revisits / attended * 100), 2) if attended else None,
                    "Answer Rate %": round((answered / total_calls * 100), 2) if total_calls else None,
                })

        if rows:
            out = pd.DataFrame(rows).sort_values("Revisits", ascending=False).reset_index(drop=True)

            if any(w in q for w in ["highest", "top", "most"]):
                top = out.iloc[0]
                return (
                    f"Top executive by revisits: **{top['Sales Executive']}** with **{int(top['Revisits'])}** revisits.",
                    out,
                    "Executive-wise Daily Visits Summary",
                    "daily_visits"
                )

            return ("Here is the Daily Visits sales executive summary.", out, "Executive-wise Daily Visits Summary", "daily_visits")

    return None


# ============================================================
# CP PAYOUT ANSWERS
# ============================================================
def _answer_cp_payout_question(question: str, df: pd.DataFrame):
    q = question.strip().lower()
    df = _safe_df(df)

    if df.empty:
        return None

    fos_col = _get_col(df, "FOS (₹)")
    bro_col = _get_col(df, "Brokerage (₹)")
    fos_given_col = _get_col(df, "FOS Given")
    bro_given_col = _get_col(df, "Brokerage Given")
    wing_col = _get_col(df, "Wing")
    flat_col = _get_col(df, "Flat Number")
    flat_label_col = _get_col(df, "Flat")
    invoice_col = _get_col(df, "Date of Invoice")
    invoice_num_col = _get_col(df, "Invoice Number")
    cp_firm_col = _get_col(df, "Firm/CP Name")
    cp_name_col = _get_col(df, "CP Name (FOS)")
    firm_name_col = _get_col(df, "Firm Name (Brokerage)")
    fos_chq_date_col = _get_col(df, "FOS Cheque Date")
    bro_chq_date_col = _get_col(df, "Brokerage Cheque Date")

    if fos_col:
        df[fos_col] = pd.to_numeric(df[fos_col], errors="coerce").fillna(0)

    if bro_col:
        df[bro_col] = pd.to_numeric(df[bro_col], errors="coerce").fillna(0)

    if fos_given_col:
        df["_fos_given"] = df[fos_given_col].apply(_truthy)
    else:
        df["_fos_given"] = False

    if bro_given_col:
        df["_bro_given"] = df[bro_given_col].apply(_truthy)
    else:
        df["_bro_given"] = False

    if "fos" in q and "pending" in q:
        if fos_col:
            temp = df[(df[fos_col] > 0) & (~df["_fos_given"])].copy()
            cols = [c for c in [wing_col, flat_col, flat_label_col, cp_name_col, fos_col, fos_given_col] if c]
            return (f"Pending FOS entries: **{len(temp)}**", temp[cols], "Pending FOS", "cp_payout")

    if "brokerage" in q and "pending" in q:
        if bro_col:
            temp = df[(df[bro_col] > 0) & (~df["_bro_given"])].copy()
            cols = [c for c in [wing_col, flat_col, flat_label_col, firm_name_col, bro_col, bro_given_col] if c]
            return (f"Pending Brokerage entries: **{len(temp)}**", temp[cols], "Pending Brokerage", "cp_payout")

    if "fos" in q and any(w in q for w in ["given", "released", "paid"]):
        if fos_col:
            temp = df[(df[fos_col] > 0) & (df["_fos_given"])].copy()
            cols = [c for c in [wing_col, flat_col, flat_label_col, cp_name_col, fos_col, fos_given_col] if c]
            return (f"FOS given entries: **{len(temp)}**", temp[cols], "FOS Given", "cp_payout")

    if "brokerage" in q and any(w in q for w in ["given", "released", "paid"]):
        if bro_col:
            temp = df[(df[bro_col] > 0) & (df["_bro_given"])].copy()
            cols = [c for c in [wing_col, flat_col, flat_label_col, firm_name_col, bro_col, bro_given_col] if c]
            return (f"Brokerage given entries: **{len(temp)}**", temp[cols], "Brokerage Given", "cp_payout")

    if "total fos amount" in q or ("fos" in q and "amount" in q and "total" in q):
        if fos_col:
            return (f"Total FOS amount: **{_fmt_money(df[fos_col].sum())}**", None, None, "cp_payout")

    if "total brokerage amount" in q or ("brokerage" in q and "amount" in q and "total" in q):
        if bro_col:
            return (f"Total Brokerage amount: **{_fmt_money(df[bro_col].sum())}**", None, None, "cp_payout")

    if "average day" in q and "fos" in q and invoice_col and fos_chq_date_col:
        t = df[[invoice_col, fos_chq_date_col]].copy()
        t[invoice_col] = t[invoice_col].apply(_parse_any_date)
        t[fos_chq_date_col] = t[fos_chq_date_col].apply(_parse_any_date)
        t = t.dropna()

        if not t.empty:
            days = (t[fos_chq_date_col] - t[invoice_col]).dt.days
            days = days[days >= 0]

            if not days.empty:
                return (f"Average days to release FOS payment: **{days.mean():.1f} days**", None, None, "cp_payout")

    if "average day" in q and "brokerage" in q and invoice_col and bro_chq_date_col:
        t = df[[invoice_col, bro_chq_date_col]].copy()
        t[invoice_col] = t[invoice_col].apply(_parse_any_date)
        t[bro_chq_date_col] = t[bro_chq_date_col].apply(_parse_any_date)
        t = t.dropna()

        if not t.empty:
            days = (t[bro_chq_date_col] - t[invoice_col]).dt.days
            days = days[days >= 0]

            if not days.empty:
                return (f"Average days to release Brokerage payment: **{days.mean():.1f} days**", None, None, "cp_payout")

    q_wing, q_flat = _extract_flat_from_question(question)

    if q_wing and q_flat and wing_col and flat_col:
        temp = df.copy()
        temp[wing_col] = temp[wing_col].fillna("").astype(str).str.strip().str.upper()
        temp[flat_col] = temp[flat_col].fillna("").astype(str).str.strip()

        hit = temp[(temp[wing_col] == q_wing) & (temp[flat_col] == q_flat)].copy()

        if not hit.empty:
            cols = [c for c in [
                invoice_col, invoice_num_col, cp_firm_col, wing_col, flat_col, flat_label_col,
                fos_col, bro_col, fos_given_col, bro_given_col,
                fos_chq_date_col, bro_chq_date_col
            ] if c]

            return (
                f"Found **{len(hit)}** CP payout record(s) for **{q_wing} {q_flat}**.",
                hit[cols],
                f"CP Payout {q_wing} {q_flat}",
                "cp_payout"
            )

    return None


# ============================================================
# MARKETING ANSWERS
# ============================================================
def _answer_marketing_question(question: str, df: pd.DataFrame):
    q = question.strip().lower()
    df = _safe_df(df)

    if df.empty:
        return None

    amount_col = _get_col(df, "Amount")
    purpose_col = _get_col(df, "Purpose")
    date_col = _get_col(df, "Date")
    month_col = _get_col(df, "Month")
    vendor_col = _get_col(df, "Vendor")
    remark_col = _get_col(df, "Remark")

    if amount_col:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)

    if "total marketing" in q or ("marketing" in q and any(w in q for w in ["spend", "expense", "expenditure", "total"])):
        if amount_col:
            return (f"Total marketing expenditure: **{_fmt_money(df[amount_col].sum())}**", None, None, "marketing")

    if "vendor" in q and any(w in q for w in ["wise", "summary", "top", "highest"]):
        if vendor_col and amount_col:
            temp = df.copy()
            temp[vendor_col] = temp[vendor_col].fillna("").astype(str).str.strip()
            temp = temp[temp[vendor_col] != ""]

            if not temp.empty:
                g = (
                    temp.groupby(vendor_col, as_index=False)[amount_col]
                    .sum()
                    .sort_values(amount_col, ascending=False)
                    .rename(columns={amount_col: "Amount"})
                )

                if "top" in q or "highest" in q:
                    top = g.iloc[0]
                    return (
                        f"Top vendor by spend: **{top[vendor_col]}** with **{_fmt_money(top['Amount'])}**",
                        g,
                        "Vendor-wise Spend",
                        "marketing"
                    )

                return ("Here is the vendor-wise marketing spend summary.", g, "Vendor-wise Spend", "marketing")

    if "purpose" in q and any(w in q for w in ["wise", "summary", "top", "highest"]):
        if purpose_col and amount_col:
            temp = df.copy()
            temp[purpose_col] = temp[purpose_col].fillna("").astype(str).str.strip()
            temp = temp[temp[purpose_col] != ""]

            if not temp.empty:
                g = (
                    temp.groupby(purpose_col, as_index=False)[amount_col]
                    .sum()
                    .sort_values(amount_col, ascending=False)
                    .rename(columns={amount_col: "Amount"})
                )

                if "top" in q or "highest" in q:
                    top = g.iloc[0]
                    return (
                        f"Top purpose by spend: **{top[purpose_col]}** with **{_fmt_money(top['Amount'])}**",
                        g,
                        "Purpose-wise Spend",
                        "marketing"
                    )

                return ("Here is the purpose-wise marketing spend summary.", g, "Purpose-wise Spend", "marketing")

    if "month wise" in q or "monthly" in q:
        temp = df.copy()

        if date_col:
            temp["_date_obj"] = temp[date_col].apply(_parse_any_date)

        if date_col and "_date_obj" in temp.columns and temp["_date_obj"].notna().any():
            temp = temp.dropna(subset=["_date_obj"]).copy()
            temp["MonthKey"] = temp["_date_obj"].dt.strftime("%B %y")
        elif month_col:
            temp["MonthKey"] = temp[month_col].fillna("").astype(str).str.strip()
        else:
            return None

        temp = temp[temp["MonthKey"] != ""]

        if not temp.empty and amount_col:
            g = (
                temp.groupby("MonthKey", as_index=False)[amount_col]
                .sum()
                .rename(columns={amount_col: "Amount"})
            )
            return ("Here is the month-wise marketing spend summary.", g, "Month-wise Marketing Spend", "marketing")

    if vendor_col and "vendor" in q:
        vname = _find_name_match(df, vendor_col, q)

        if vname:
            temp = df[df[vendor_col].fillna("").astype(str).str.strip().eq(str(vname).strip())].copy()
            cols = [c for c in [vendor_col, purpose_col, amount_col, date_col, month_col, remark_col] if c]

            return (f"Found **{len(temp)}** marketing record(s) for vendor **{vname}**.", temp[cols], f"Vendor {vname}", "marketing")

    return None


# ============================================================
# ROUTER
# ============================================================
def _detect_target_sheet(question: str) -> str:
    q = question.lower()

    direct_map = {
        "daily_visits": [
            "visit", "walk-in", "walk in", "revisit", "festival",
            "daily visit", "cancellation", "booking trend", "calls answered",
            "calls unanswered", "total calls", "attended"
        ],
        "cp_payout": [
            "cp payout", "brokerage", "fos", "invoice", "cheque",
            "channel partner", "payout", "cp payment"
        ],
        "marketing": [
            "marketing", "vendor", "campaign", "spend", "expense",
            "expenditure", "promotion", "purpose"
        ],
        "booking": [
            "rate", "final price", "customer", "sales executive", "flat",
            "wing", "agreement", "stamp duty", "carpet area", "booking amount",
            "lead type", "parking"
        ],
    }

    scores = {k: 0 for k in ["booking", "daily_visits", "cp_payout", "marketing"]}

    for sheet_key, kws in direct_map.items():
        for kw in kws:
            if kw in q:
                scores[sheet_key] += 3

    for sheet_key in scores.keys():
        for w in _schema_keywords(sheet_key):
            if w and len(w) > 2 and w in q:
                scores[sheet_key] += 1

    best_sheet = max(scores, key=scores.get)

    if scores[best_sheet] == 0:
        return "booking"

    return best_sheet


def _sheet_ai_router(question: str, all_dfs: dict):
    schema_res = _answer_schema_question(question)
    if schema_res:
        return schema_res

    target = _detect_target_sheet(question)

    ordered_handlers = []

    if target == "booking":
        ordered_handlers = [
            (_answer_booking_question, "booking"),
            (_answer_daily_visits_question, "daily_visits"),
            (_answer_cp_payout_question, "cp_payout"),
            (_answer_marketing_question, "marketing"),
        ]
    elif target == "daily_visits":
        ordered_handlers = [
            (_answer_daily_visits_question, "daily_visits"),
            (_answer_booking_question, "booking"),
            (_answer_cp_payout_question, "cp_payout"),
            (_answer_marketing_question, "marketing"),
        ]
    elif target == "cp_payout":
        ordered_handlers = [
            (_answer_cp_payout_question, "cp_payout"),
            (_answer_booking_question, "booking"),
            (_answer_daily_visits_question, "daily_visits"),
            (_answer_marketing_question, "marketing"),
        ]
    elif target == "marketing":
        ordered_handlers = [
            (_answer_marketing_question, "marketing"),
            (_answer_booking_question, "booking"),
            (_answer_daily_visits_question, "daily_visits"),
            (_answer_cp_payout_question, "cp_payout"),
        ]

    for fn, key in ordered_handlers:
        res = fn(question, all_dfs.get(key, pd.DataFrame()))
        if res:
            return res

    available = []

    if not _safe_df(all_dfs.get("booking", pd.DataFrame())).empty:
        available.append("Booking")
    if not _safe_df(all_dfs.get("daily_visits", pd.DataFrame())).empty:
        available.append("Daily Visits")
    if not _safe_df(all_dfs.get("cp_payout", pd.DataFrame())).empty:
        available.append("CP Payout")
    if not _safe_df(all_dfs.get("marketing", pd.DataFrame())).empty:
        available.append("Marketing")

    msg = "I couldn’t match that question exactly from your available sheet/table data."

    if available:
        msg += f"\n\nConnected data sources: **{', '.join(available)}**."

    msg += (
        "\n\nTry questions like:"
        "\n- Which sales executive has highest bookings?"
        "\n- What is the rate of E 706?"
        "\n- What is the final price of F 503?"
        "\n- Show pending stamp duty list"
        "\n- Show pending agreement list"
        "\n- Total revisits in Daily Visits"
        "\n- Day with highest booking in Daily Visits"
        "\n- Total calls answered"
        "\n- Pending FOS entries"
        "\n- Pending brokerage entries"
        "\n- Total brokerage amount"
        "\n- Average days to release FOS payment"
        "\n- Vendor-wise marketing spend"
        "\n- Top purpose by marketing spend"
        "\n- What does Agreement Cost mean?"
        "\n- Which sheets are connected?"
        "\n- Show available columns"
    )

    return (msg, None, None, "general")


# ============================================================
# TAB 13 UI
# ============================================================

    st.subheader("🤖 Pratham Vihar AI")
    st.caption(
        "Ask anything about Booking, Daily Visits, CP Payout, and Marketing data. "
        "This assistant answers only from available sheet/table data."
    )

    st.markdown(
        """
        <style>
        .pv-ai-card{
            background: rgba(255,255,255,0.96);
            border: 1px solid rgba(49,51,63,0.12);
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 8px 20px rgba(15,23,42,0.06);
            margin-bottom: 12px;
        }
        .pv-ai-chip-wrap{
            display:flex;
            flex-wrap:wrap;
            gap:8px;
            margin: 8px 0 12px 0;
        }
        .pv-ai-chip{
            display:inline-flex;
            align-items:center;
            gap:7px;
            border-radius:999px;
            padding:6px 10px;
            font-size:12.5px;
            font-weight:800;
            background:#f8fafc;
            border:1px solid #e2e8f0;
            color:#0f172a;
        }
        .pv-ai-chip.ok{
            background:#ecfdf5;
            border-color:#bbf7d0;
            color:#166534;
        }
        .pv-ai-chip.warn{
            background:#fff7ed;
            border-color:#fed7aa;
            color:#9a3412;
        }
        .pv-ai-dot{
            width:8px;
            height:8px;
            border-radius:999px;
            background:#6366f1;
            display:inline-block;
        }
        .pv-ai-chip.ok .pv-ai-dot{
            background:#10b981;
        }
        .pv-ai-chip.warn .pv-ai-dot{
            background:#f59e0b;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if "pv_ai_history" not in st.session_state:
        st.session_state["pv_ai_history"] = []

    # Load data from existing DataFrames or Supabase
    all_sheet_dfs = {
        "booking": _pv_get_df("booking"),
        "daily_visits": _pv_get_df("daily_visits"),
        "cp_payout": _pv_get_df("cp_payout"),
        "marketing": _pv_get_df("marketing"),
    }

    source_chips = []
    for key, label in [
        ("booking", "Booking"),
        ("daily_visits", "Daily Visits"),
        ("cp_payout", "CP Payout"),
        ("marketing", "Marketing"),
    ]:
        n = len(all_sheet_dfs.get(key, pd.DataFrame()))
        cls = "ok" if n > 0 else "warn"
        source_chips.append(
            f"<span class='pv-ai-chip {cls}'><span class='pv-ai-dot'></span>{label}: {n:,} rows</span>"
        )

    st.markdown(
        f"<div class='pv-ai-chip-wrap'>{''.join(source_chips)}</div>",
        unsafe_allow_html=True
    )

    with st.expander("Examples you can ask"):
        st.markdown("""
- Which sales executive has highest bookings?
- What is the rate of E 706?
- What is the final price of F 503?
- Show pending stamp duty list
- Show pending agreement list
- Total revisits in Daily Visits
- Total visits in Daily Visits
- Day with highest booking in Daily Visits
- Total calls answered
- Total calls unanswered
- Source-wise visits
- Pending FOS entries
- Pending brokerage entries
- Total FOS amount
- Total brokerage amount
- Average days to release FOS payment
- Average days to release brokerage payment
- Vendor-wise marketing spend
- Purpose-wise marketing spend
- Top purpose by marketing spend
- What does Agreement Cost mean?
- Which sheets are connected?
- Show available columns
        """)

    user_q = st.text_input(
        "Ask your sheet AI",
        placeholder="e.g. What is the rate of E 706? / Total revisits / Pending FOS entries",
        key="pv_ai_question"
    )

    ask_btn = st.button("Ask AI", type="primary", use_container_width=True, key="pv_ai_ask_btn")

    if ask_btn and user_q.strip():
        answer, result_df, title, source_sheet = _sheet_ai_router(user_q, all_sheet_dfs)

        st.session_state["pv_ai_history"].append({
            "q": user_q,
            "a": answer,
            "source": source_sheet,
        })

        st.markdown("<div class='pv-ai-card'>", unsafe_allow_html=True)
        st.markdown(answer)
        st.markdown(f"**Source:** `{source_sheet}`")
        st.markdown("</div>", unsafe_allow_html=True)

        if result_df is not None and isinstance(result_df, pd.DataFrame) and not result_df.empty:
            st.markdown(f"### {title or 'Result'}")
            st.dataframe(result_df, use_container_width=True, hide_index=True)

            csv_bytes = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Result CSV",
                data=csv_bytes,
                file_name=f"{(title or 'pv_ai_result').replace(' ', '_').lower()}.csv",
                mime="text/csv",
                use_container_width=True,
                key="pv_ai_result_download"
            )

    if st.session_state["pv_ai_history"]:
        with st.expander("Recent Questions"):
            for i, item in enumerate(reversed(st.session_state["pv_ai_history"][-10:]), start=1):
                st.markdown(f"**Q{i}:** {item['q']}")
                st.markdown(f"**Source:** `{item.get('source', 'general')}`")
                st.markdown(item["a"])
                st.markdown("---")

    st.info(PV_SHEET_RULES)
