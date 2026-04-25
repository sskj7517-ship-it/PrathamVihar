import streamlit as st
import datetime
import pandas as pd
import math
from fpdf import FPDF
import base64
import io
from io import StringIO
import altair as alt
import os
from typing import Optional, Tuple, List, Dict
import streamlit.components.v1 as components

from supabase_connector import load_all_data, insert_row, update_row, delete_row
from supabase import create_client
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

sheets_connected = True


# ---------------- SUPABASE DATA LOAD ----------------
try:
    data = load_all_data()

    sheet_df = data["sheet_df"]
    marketing_df = data["marketing_df"]
    hold_df = data["hold_df"]
    cp_payout_df = data["cp_payout_df"]
    daily_visits_df = data["daily_visits_df"]
    cashflow_slab_master_df = data["cashflow_slab_master_df"]

    sheets_connected = True
    supabase_connected = True

    booking_df = sheet_df.copy()

except Exception as e:
    st.error(f"❌ Error connecting to Supabase: {str(e)}")

    sheet_df = pd.DataFrame()
    marketing_df = pd.DataFrame()
    hold_df = pd.DataFrame()
    cp_payout_df = pd.DataFrame()
    daily_visits_df = pd.DataFrame()
    cashflow_slab_master_df = pd.DataFrame()
    booking_df = pd.DataFrame()

    sheets_connected = False
    supabase_connected = False


# ---------------- UI CODE ----------------
st.set_page_config(
    page_title="Rate Guard - PRATHAM VIHAR",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- LAYOUT TOGGLE ----------------
if "layout_mode" not in st.session_state:
    st.session_state.layout_mode = "wide"

st.markdown("### ⚙️ Layout Settings")
use_wide_mode = st.toggle(
    "Use Wide Mode",
    value=(st.session_state.layout_mode == "wide"),
    help="Turn on for full-width layout, turn off for normal centered layout."
)

st.session_state.layout_mode = "wide" if use_wide_mode else "normal"

if st.session_state.layout_mode == "wide":
    container_width = "96%"
    content_padding_left = "2rem"
    content_padding_right = "2rem"
    header_width = "100%"
    card_max_width = "1100px"
else:
    container_width = "900px"
    content_padding_left = "1rem"
    content_padding_right = "1rem"
    header_width = "100%"
    card_max_width = "700px"

# ---------------- CUSTOM CSS ----------------
st.markdown(f"""
<style>
    .block-container {{
        max-width: {container_width} !important;
        padding-top: 1rem;
        padding-left: {content_padding_left};
        padding-right: {content_padding_right};
        padding-bottom: 1rem;
    }}

    .main {{
        padding: 0rem;
    }}

    div[data-testid="stAppViewContainer"] > .main {{
        padding-top: 0rem;
    }}

    .main-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}

    .main-header h1 {{
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}

    .main-header p {{
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }}

    .layout-toggle-box {{
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        min-height: 50px;
        padding: 0px 20px;
        background-color: white;
        border-radius: 8px;
        color: #495057;
        font-weight: 600;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }}

    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: 2px solid #667eea;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
    }}

    [data-testid="metric-container"] {{
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }}

    [data-testid="metric-container"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}

    .stButton > button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
    }}

    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
    }}

    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }}

    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    .stSuccess {{
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #28a745;
        border-radius: 8px;
        padding: 1rem;
    }}

    .stError {{
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #dc3545;
        border-radius: 8px;
        padding: 1rem;
    }}

    .stWarning {{
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
    }}

    .stPlotlyChart, .stAltairChart {{
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }}

    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}

    .stSelectbox > div > div,
    .stTextInput > div > div,
    .stNumberInput > div > div,
    .stDateInput > div > div,
    .stTextArea > div > div {{
        border-radius: 8px;
    }}

    .sidebar-content {{
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}

    div[data-testid="stToggle"] {{
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
    }}
</style>
""", unsafe_allow_html=True)

st.caption(f"Current layout: {st.session_state.layout_mode.title()} Mode")

# RateGuard top card
st.markdown(f"""
<div style="
    width: {header_width};
    max-width: {card_max_width};
    margin: 0 auto 0 auto;
    border-radius: 26px 26px 0 0;
    background: linear-gradient(90deg, #3751be 0%, #7967f9 100%);
    box-shadow: 0 4px 12px rgba(65,88,208,0.12);
    padding: 26px 0 0 0;
    text-align: center;
    font-family: 'Segoe UI', 'sans-serif';
">
    <h1 style="
        margin-bottom: 2px;
        font-size: 2.5rem;
        font-weight: 700;
        color: #fff;
        letter-spacing: 2px;
        text-shadow: 0 1px 7px rgba(65,88,208,0.09);
    ">RATE GUARD</h1>
</div>
""", unsafe_allow_html=True)

# Pratham Vihar bottom card
st.markdown(f"""
<div style="
    width: {header_width};
    max-width: {card_max_width};
    margin: 0 auto 12px auto;
    border-radius: 0 0 26px 26px;
    background: linear-gradient(90deg, #6a81ec 0%, #9fa7fa 100%);
    box-shadow: 0 4px 12px rgba(65,88,208,0.12);
    padding: 13px 0 18px 0;
    text-align: center;
">
    <h1 style="
        margin-bottom: 0px;
        font-size: 2.1rem;
        font-weight: 700;
        color: #fff;
        letter-spacing: 1.4px;
    ">🏢 Pratham Vihar</h1>
    <div style="
        font-size: 1.15rem;
        color: rgba(255,255,255,0.93);
        margin-top: 7px;
    ">Comprehensive Property Management System</div>
</div>
""", unsafe_allow_html=True)

# Create tabs - same sequence as old app
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16 = st.tabs([
    "**Dashboard**",
    "**Calculators**",
    "**Booking Punch**",
    "**Total Package & Schedule**",
    "**Agreement Done Tracker**",
    "**CP Payout Tracker**",
    "**Marketing**",
    "**Civil Changes Lookup**",
    "**Monthly Marketing Input**",
    "**Marketing Plan Summary**",
    "**Secure Tab**",
    "**Agreement Document Editor**",
    "**Pratham Vihar AI**",
    "**Daily Visits**",
    "**Inventory Status**",
    "**CashFlow**"
])

# --- Custom Quarter Function ---
def get_custom_quarter_label(date):
    year = date.year
    if date.month in [4, 5, 6]:
        return f"April-June {year}"
    elif date.month in [7, 8, 9]:
        return f"July-September {year}"
    elif date.month in [10, 11, 12]:
        return f"October-December {year}"
    else:
        return f"January-March {year}"

with tab5:
    st.title("📑 Agreement Done Tracker")

    # ---- Keep state across reruns ----
    if "tab5_filters_active" not in st.session_state:
        st.session_state.tab5_filters_active = False
    if "tab5_customer" not in st.session_state:
        st.session_state.tab5_customer = "ALL"

    defaults = {
        "tab5_month": "ALL",
        "tab5_exec": "ALL",
        "tab5_wing": "ALL",
        "tab5_filter_field": "ALL (no extra filter)",
        "tab5_addr_contains": "",
        "tab5_name_contains": "",
        "tab5_stamp_choice": "Received",
        "tab5_agree_choice": "Done",
        "tab5_incentive_choice": "Given",
        "tab5_insider_choice": "Yes",
        "tab5_outsider_choice": "Yes",
        "tab5_o1_choice": "Has Offer",
        "tab5_o2_choice": "Has Offer",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    def _tab5_apply_filters():
        st.session_state.tab5_filters_active = True

    def _tab5_reset_filters():
        st.session_state.tab5_filters_active = False
        st.session_state.tab5_customer = "ALL"
        for k, v in defaults.items():
            st.session_state[k] = v

    def _norm(v):
        return str(v or "").strip().lower()

    def _clean(v):
        return "" if v is None else str(v).strip()

    if not sheets_connected:
        st.warning("📋 Please connect to Supabase to use this feature.")
    else:
        try:
            response = supabase.table("bookings").select("*").order("id", desc=False).execute()
            data = response.data or []
            df = pd.DataFrame(data)
        except Exception as e:
            st.error(f"❌ Error loading Supabase data: {e}")
            st.stop()

        if df.empty:
            st.warning("No data available in Supabase.")
        else:
            required_cols = [
                "id",
                "month",
                "customer_name",
                "sales_executive",
                "wing",
                "flat_number",
                "agreement_done",
                "stamp_duty",
                "incentive",
                "rcc",
                "possession_handover",
                "lead_type",
                "referral_given",
                "insider_banker",
                "outsider_banker",
                "offer_1",
                "offer_2",
                "offer_1_rewarded",
                "offer_2_rewarded",
            ]

            missing = [c for c in required_cols if c not in df.columns]

            if missing:
                st.error(f"Missing required columns in Supabase: {', '.join(missing)}")
            else:
                df["flat_address"] = (
                    df["wing"].fillna("").astype(str).str.strip()
                    + " "
                    + df["flat_number"].fillna("").astype(str).str.strip()
                ).str.strip()

                def make_label(row):
                    wf = str(row.get("flat_address", "")).strip()
                    nm = str(row.get("customer_name", "")).strip()
                    return f"{wf} - {nm}" if wf else nm

                base_preview = df.copy()

                pre_month = st.session_state.get("tab5_month", "ALL")
                pre_exec = st.session_state.get("tab5_exec", "ALL")
                pre_wing = st.session_state.get("tab5_wing", "ALL")

                if pre_month != "ALL":
                    base_preview = base_preview[base_preview["month"] == pre_month]

                if pre_exec != "ALL":
                    base_preview = base_preview[base_preview["sales_executive"].astype(str) == pre_exec]

                if pre_wing != "ALL":
                    base_preview = base_preview[base_preview["wing"].astype(str).str.strip() == pre_wing]

                label_map_preview = {idx: make_label(r) for idx, r in base_preview.iterrows()}
                customer_options = ["ALL"] + [label_map_preview[i] for i in base_preview.index]

                cust_default_idx = (
                    customer_options.index(st.session_state.tab5_customer)
                    if st.session_state.tab5_customer in customer_options
                    else 0
                )

                # -------------------- FILTER FORM --------------------
                with st.form("agreement_filter_form"):
                    month_values = sorted(
                        [x for x in df["month"].dropna().astype(str).unique() if x.strip() != ""],
                        reverse=True,
                    )
                    month_options = ["ALL"] + month_values

                    st.selectbox(
                        "Month (fixed)",
                        month_options,
                        key="tab5_month",
                        help="Always applied. Choose ALL to include all months.",
                    )

                    exec_values = sorted(
                        [x for x in df["sales_executive"].dropna().astype(str).unique() if x.strip() != ""]
                    )
                    exec_options = ["ALL"] + exec_values

                    st.selectbox(
                        "Sales Executive (fixed)",
                        exec_options,
                        key="tab5_exec",
                        help="Always applied. Choose ALL to include all executives.",
                    )

                    wing_values = df["wing"].dropna().astype(str).str.strip().unique().tolist()
                    wing_values = sorted([w for w in wing_values if w != ""])
                    wing_options = ["ALL"] + wing_values

                    st.selectbox(
                        "Wing (fixed)",
                        wing_options,
                        key="tab5_wing",
                        help="Always applied. Choose ALL to include all wings.",
                    )

                    var_fields = [
                        "ALL (no extra filter)",
                        "Customer",
                        "Flat Address (contains)",
                        "Customer Name (contains)",
                        "Stamp Duty",
                        "Agreement Done",
                        "Incentive",
                        "Insider Banker",
                        "Outsider Banker",
                        "Offer 1 (Has/Rewarded)",
                        "Offer 2 (Has/Rewarded)",
                    ]

                    st.selectbox(
                        "Additional filter (only one active):",
                        options=var_fields,
                        index=var_fields.index(st.session_state.tab5_filter_field)
                        if st.session_state.tab5_filter_field in var_fields
                        else 0,
                        key="tab5_filter_field",
                    )

                    ff = st.session_state.tab5_filter_field

                    if ff == "Customer":
                        st.selectbox(
                            "Customer (Wing Flat – Name)",
                            options=customer_options,
                            index=cust_default_idx,
                            key="tab5_customer",
                        )

                    elif ff == "Flat Address (contains)":
                        st.text_input("Address contains…", key="tab5_addr_contains")

                    elif ff == "Customer Name (contains)":
                        st.text_input("Customer name contains…", key="tab5_name_contains")

                    elif ff == "Stamp Duty":
                        st.selectbox("Stamp Duty Status", ["Received", "Pending"], key="tab5_stamp_choice")

                    elif ff == "Agreement Done":
                        st.selectbox("Agreement Status", ["Done", "Pending"], key="tab5_agree_choice")

                    elif ff == "Incentive":
                        st.selectbox("Incentive Status", ["Given", "Pending"], key="tab5_incentive_choice")

                    elif ff == "Insider Banker":
                        st.selectbox("Insider Banker", ["Yes", "No"], key="tab5_insider_choice")

                    elif ff == "Outsider Banker":
                        st.selectbox("Outsider Banker", ["Yes", "No"], key="tab5_outsider_choice")

                    elif ff == "Offer 1 (Has/Rewarded)":
                        st.selectbox(
                            "Offer 1 Filter",
                            ["Has Offer", "No Offer", "Rewarded", "Not Rewarded"],
                            key="tab5_o1_choice",
                        )

                    elif ff == "Offer 2 (Has/Rewarded)":
                        st.selectbox(
                            "Offer 2 Filter",
                            ["Has Offer", "No Offer", "Rewarded", "Not Rewarded"],
                            key="tab5_o2_choice",
                        )

                    c1, c2 = st.columns(2)

                    with c1:
                        st.form_submit_button("Find", on_click=_tab5_apply_filters)

                    with c2:
                        st.form_submit_button("Reset", on_click=_tab5_reset_filters)

                # -------------------- RESULTS --------------------
                if not st.session_state.tab5_filters_active:
                    st.info("Set Month, Sales Executive & Wing, choose one additional filter, then click **Find**.")
                else:
                    post_df = df.copy()

                    if st.session_state.tab5_month != "ALL":
                        post_df = post_df[post_df["month"] == st.session_state.tab5_month]

                    if st.session_state.tab5_exec != "ALL":
                        post_df = post_df[post_df["sales_executive"].astype(str) == st.session_state.tab5_exec]

                    if st.session_state.tab5_wing != "ALL":
                        post_df = post_df[post_df["wing"].astype(str).str.strip() == st.session_state.tab5_wing]

                    ff = st.session_state.tab5_filter_field

                    if ff == "Customer" and st.session_state.tab5_customer != "ALL":
                        label_map = {idx: make_label(r) for idx, r in post_df.iterrows()}
                        chosen = [i for i, lab in label_map.items() if lab == st.session_state.tab5_customer]
                        post_df = post_df.loc[chosen]

                    elif ff == "Flat Address (contains)":
                        q = st.session_state.tab5_addr_contains.strip().lower()
                        if q:
                            post_df = post_df[
                                post_df["flat_address"].astype(str).str.lower().str.contains(q, na=False)
                            ]

                    elif ff == "Customer Name (contains)":
                        q = st.session_state.tab5_name_contains.strip().lower()
                        if q:
                            post_df = post_df[
                                post_df["customer_name"].astype(str).str.lower().str.contains(q, na=False)
                            ]

                    elif ff == "Stamp Duty":
                        want_received = st.session_state.tab5_stamp_choice == "Received"
                        post_df = post_df[
                            post_df["stamp_duty"].apply(lambda v: _norm(v) == "received") == want_received
                        ]

                    elif ff == "Agreement Done":
                        want_done = st.session_state.tab5_agree_choice == "Done"
                        post_df = post_df[
                            post_df["agreement_done"].apply(lambda v: _norm(v) == "done") == want_done
                        ]

                    elif ff == "Incentive":
                        want_given = st.session_state.tab5_incentive_choice == "Given"
                        post_df = post_df[
                            post_df["incentive"].apply(lambda v: _norm(v) == "given") == want_given
                        ]

                    elif ff == "Insider Banker":
                        want_yes = st.session_state.tab5_insider_choice == "Yes"
                        post_df = post_df[
                            post_df["insider_banker"].apply(lambda v: _norm(v) == "yes") == want_yes
                        ]

                    elif ff == "Outsider Banker":
                        want_yes = st.session_state.tab5_outsider_choice == "Yes"
                        post_df = post_df[
                            post_df["outsider_banker"].apply(lambda v: _norm(v) == "yes") == want_yes
                        ]

                    elif ff == "Offer 1 (Has/Rewarded)":
                        choice = st.session_state.tab5_o1_choice

                        if choice == "Has Offer":
                            post_df = post_df[post_df["offer_1"].astype(str).str.strip() != ""]

                        elif choice == "No Offer":
                            post_df = post_df[post_df["offer_1"].astype(str).str.strip() == ""]

                        elif choice == "Rewarded":
                            post_df = post_df[
                                post_df["offer_1_rewarded"].apply(
                                    lambda x: _norm(x) in ("rewarded 1", "true", "yes", "1", "y", "✓")
                                )
                            ]

                        elif choice == "Not Rewarded":
                            post_df = post_df[
                                ~post_df["offer_1_rewarded"].apply(
                                    lambda x: _norm(x) in ("rewarded 1", "true", "yes", "1", "y", "✓")
                                )
                            ]

                    elif ff == "Offer 2 (Has/Rewarded)":
                        choice = st.session_state.tab5_o2_choice

                        if choice == "Has Offer":
                            post_df = post_df[post_df["offer_2"].astype(str).str.strip() != ""]

                        elif choice == "No Offer":
                            post_df = post_df[post_df["offer_2"].astype(str).str.strip() == ""]

                        elif choice == "Rewarded":
                            post_df = post_df[
                                post_df["offer_2_rewarded"].apply(
                                    lambda x: _norm(x) in ("rewarded 2", "true", "yes", "1", "y", "✓")
                                )
                            ]

                        elif choice == "Not Rewarded":
                            post_df = post_df[
                                ~post_df["offer_2_rewarded"].apply(
                                    lambda x: _norm(x) in ("rewarded 2", "true", "yes", "1", "y", "✓")
                                )
                            ]

                    month_label = st.session_state.tab5_month if st.session_state.tab5_month != "ALL" else "All Months"
                    exec_label = st.session_state.tab5_exec if st.session_state.tab5_exec != "ALL" else "All Executives"
                    wing_label = st.session_state.tab5_wing if st.session_state.tab5_wing != "ALL" else "All Wings"

                    extra = st.session_state.tab5_filter_field

                    if extra == "Customer":
                        extra += f" = {st.session_state.tab5_customer}"
                    elif extra == "Flat Address (contains)":
                        extra += f" '{st.session_state.tab5_addr_contains}'"
                    elif extra == "Customer Name (contains)":
                        extra += f" '{st.session_state.tab5_name_contains}'"
                    elif extra == "Stamp Duty":
                        extra += f" = {st.session_state.tab5_stamp_choice}"
                    elif extra == "Agreement Done":
                        extra += f" = {st.session_state.tab5_agree_choice}"
                    elif extra == "Incentive":
                        extra += f" = {st.session_state.tab5_incentive_choice}"
                    elif extra == "Insider Banker":
                        extra += f" = {st.session_state.tab5_insider_choice}"
                    elif extra == "Outsider Banker":
                        extra += f" = {st.session_state.tab5_outsider_choice}"
                    elif extra == "Offer 1 (Has/Rewarded)":
                        extra += f" = {st.session_state.tab5_o1_choice}"
                    elif extra == "Offer 2 (Has/Rewarded)":
                        extra += f" = {st.session_state.tab5_o2_choice}"

                    st.subheader(f"Customers • {month_label} • {exec_label} • {wing_label} • {extra}")

                    if post_df.empty:
                        st.info("No customers match the selected filters.")
                    else:
                        h = st.columns([2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3])
                        h[0].markdown("**Flat Address**")
                        h[1].markdown("**Customer Name**")
                        h[2].markdown("**Stamp Duty**")
                        h[3].markdown("**Agreement**")
                        h[4].markdown("**Incentive**")
                        h[5].markdown("**RCC**")
                        h[6].markdown("**Possession Handover**")
                        h[7].markdown("**Referral Given**")
                        h[8].markdown("**Insider Banker**")
                        h[9].markdown("**Outsider Banker**")
                        h[10].markdown("**Offer 1**")
                        h[11].markdown("**Offer 2**")

                        for idx, row in post_df.iterrows():
                            row_id = int(row["id"])

                            flat_addr = row.get("flat_address", "")
                            cust_name = row.get("customer_name", "")

                            is_agreement_done = _norm(row.get("agreement_done")) == "done"
                            is_stamp_received = _norm(row.get("stamp_duty")) == "received"
                            is_incentive_given = _norm(row.get("incentive")) == "given"
                            is_referral_given = _norm(row.get("referral_given")) == "given"

                            is_rcc_completed = _norm(row.get("rcc")) == "completed"
                            is_poss_handover = _norm(row.get("possession_handover")) == "handover"

                            is_referral_lead = _norm(row.get("lead_type")) == "referral"
                            is_insider = _norm(row.get("insider_banker")) == "yes"
                            is_outsider = _norm(row.get("outsider_banker")) == "yes"

                            offer1_text = _clean(row.get("offer_1"))
                            offer2_text = _clean(row.get("offer_2"))

                            has_offer1 = offer1_text != ""
                            has_offer2 = offer2_text != ""

                            is_o1_rewarded = _norm(row.get("offer_1_rewarded")) in (
                                "rewarded 1",
                                "true",
                                "yes",
                                "1",
                                "y",
                                "✓",
                            )

                            is_o2_rewarded = _norm(row.get("offer_2_rewarded")) in (
                                "rewarded 2",
                                "true",
                                "yes",
                                "1",
                                "y",
                                "✓",
                            )

                            col0, col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(
                                [2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3]
                            )

                            col0.write(flat_addr)
                            col1.write(cust_name)

                            stamp_checked = col2.checkbox(
                                "Received",
                                value=is_stamp_received,
                                key=f"tab5_stamp_{row_id}",
                            )

                            agreement_checked = col3.checkbox(
                                "Done",
                                value=is_agreement_done,
                                key=f"tab5_agree_{row_id}",
                            )

                            incentive_checked = col4.checkbox(
                                "Given",
                                value=is_incentive_given,
                                key=f"tab5_incentive_{row_id}",
                            )

                            rcc_checked = col5.checkbox(
                                "Completed",
                                value=is_rcc_completed,
                                key=f"tab5_rcc_{row_id}",
                            )

                            pos_checked = col6.checkbox(
                                "Handover",
                                value=is_poss_handover,
                                key=f"tab5_pos_{row_id}",
                            )

                            if is_referral_lead:
                                referral_checked = col7.checkbox(
                                    "Given",
                                    value=is_referral_given,
                                    key=f"tab5_referral_{row_id}",
                                )
                            else:
                                col7.write("Given" if is_referral_given else "—")
                                referral_checked = is_referral_given

                            insider_checked = col8.checkbox(
                                "Yes",
                                value=is_insider,
                                key=f"tab5_insider_{row_id}",
                            )

                            outsider_checked = col9.checkbox(
                                "Yes",
                                value=is_outsider,
                                key=f"tab5_outsider_{row_id}",
                            )

                            if has_offer1:
                                o1_checked = col10.checkbox(
                                    offer1_text,
                                    value=is_o1_rewarded,
                                    key=f"tab5_offer1_{row_id}",
                                )
                            else:
                                col10.write("—")
                                o1_checked = is_o1_rewarded

                            if has_offer2:
                                o2_checked = col11.checkbox(
                                    offer2_text,
                                    value=is_o2_rewarded,
                                    key=f"tab5_offer2_{row_id}",
                                )
                            else:
                                col11.write("—")
                                o2_checked = is_o2_rewarded

                            update_data = {}

                            new_stamp = "Received" if stamp_checked else ""
                            if new_stamp != _clean(row.get("stamp_duty")):
                                update_data["stamp_duty"] = new_stamp

                            new_agreement = "Done" if agreement_checked else ""
                            if new_agreement != _clean(row.get("agreement_done")):
                                update_data["agreement_done"] = new_agreement

                            new_incentive = "Given" if incentive_checked else ""
                            if new_incentive != _clean(row.get("incentive")):
                                update_data["incentive"] = new_incentive

                            new_rcc = "Completed" if rcc_checked else ""
                            if new_rcc != _clean(row.get("rcc")):
                                update_data["rcc"] = new_rcc

                            new_pos = "Handover" if pos_checked else ""
                            if new_pos != _clean(row.get("possession_handover")):
                                update_data["possession_handover"] = new_pos

                            if is_referral_lead:
                                new_referral = "Given" if referral_checked else ""
                                if new_referral != _clean(row.get("referral_given")):
                                    update_data["referral_given"] = new_referral

                            new_insider = "Yes" if insider_checked else ""
                            if new_insider != _clean(row.get("insider_banker")):
                                update_data["insider_banker"] = new_insider

                            new_outsider = "Yes" if outsider_checked else ""
                            if new_outsider != _clean(row.get("outsider_banker")):
                                update_data["outsider_banker"] = new_outsider

                            if has_offer1:
                                new_o1 = "Rewarded 1" if o1_checked else ""
                                if new_o1 != _clean(row.get("offer_1_rewarded")):
                                    update_data["offer_1_rewarded"] = new_o1

                            if has_offer2:
                                new_o2 = "Rewarded 2" if o2_checked else ""
                                if new_o2 != _clean(row.get("offer_2_rewarded")):
                                    update_data["offer_2_rewarded"] = new_o2

                            if update_data:
                                try:
                                    supabase.table("bookings").update(update_data).eq("id", row_id).execute()

                                    if "agreement_done" in update_data and update_data["agreement_done"] == "Done":
                                        st.balloons()
                                        st.markdown(
                                            f"""
                                            <div style='text-align: center; padding: 40px 0;'>
                                                <h1 style='font-size: 60px;'>🎉 CONGRATULATIONS 🎉</h1>
                                                <h2 style='font-size: 40px;'>Agreement Done for
                                                    <span style='color: #1f77b4;'>{cust_name}</span>
                                                </h2>
                                            </div>
                                            """,
                                            unsafe_allow_html=True,
                                        )

                                    st.success("✅ Status updated in Supabase.")

                                except Exception as e:
                                    st.error(f"❌ Error updating Supabase: {e}")

                st.caption(
                    "**Note:** Month, Sales Executive & Wing are fixed filters. "
                    "Exactly one additional filter is applied at a time. "
                    "Checkboxes update Supabase immediately."
                )
    import math, datetime, re
    import pandas as pd
    import altair as alt
    import streamlit as st
    from collections import defaultdict
    from dataclasses import dataclass
    from datetime import date, timedelta, timezone, datetime as dt_datetime
    from typing import Dict, List, Optional, Tuple

    SALE_FACTOR = 1.38  # saleable area = Carpet * 1.38

    # ---- connection checks ----
    if not sheets_connected:
        st.warning("📋 Please connect to Supabase to view dashboard data.")
        st.stop()

    if sheet_df.empty:
        st.warning("No booking data available yet.")
        st.stop()

    # ---- GLOBAL SMALL STYLES ----
    st.markdown("""
    <style>
      .metric-card { background: #fff; padding: 16px; border-radius: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                     text-align: center; margin-bottom: 14px; border: 1px solid #e5e7eb; }
      .metric-card h3 { font-size: 16px; font-weight: 700; color: #374151; margin: 0 0 6px 0; }
      .metric-card p { font-size: 22px; font-weight: 900; color: #111827; margin: 0; }
      .metric-sub { font-size: 12px; color: #6b7280; font-weight: 600; margin-top: 4px; }
      .section-subtitle { font-weight: 800; font-size: 18px; margin: 14px 0 8px 0; color: #0f172a; }
      .styled-table { border-collapse: collapse; width: 100%; border-radius: 12px; overflow: hidden;
                      box-shadow: 0 4px 10px rgba(0,0,0,.08); margin: 15px 0; }
      .styled-table th { background: #2563eb; color: white; text-align: left; padding: 10px; font-size: 14px; }
      .styled-table td { padding: 10px; font-size: 13px; border-bottom: 1px solid #e2e8f0; }
      .styled-table tr:nth-child(even) { background: #f8fafc; }
      .styled-table tr:last-child td { font-weight: 700; background: #f1f5f9; }
      .chips{display:flex; flex-wrap:wrap; gap:8px; margin:10px 0;}
      .chip{display:inline-flex; align-items:center; gap:6px; padding:6px 10px; border:1px solid #e5e7eb;
            border-radius:999px; background:#f8fafc; font-size:12px; font-weight:700; color:#111827;}
      .chip .dot{width:8px; height:8px; border-radius:999px; background:#6366f1;}
      .chip.ok .dot{background:#10b981;}
      .chip.warn .dot{background:#f59e0b;}
      .list-wrap { text-align:left; margin-top:6px }
      .list-wrap ul{ margin:6px 0 0; padding-left:18px; text-align:left }
      .list-wrap li{ font-size:13px; font-weight:700; color:#111827; margin:4px 0 }
    </style>
    """, unsafe_allow_html=True)

    # ---- DATA PREP ----
    df = sheet_df.copy()

    # Convert Supabase column names to old Google Sheet names
    supabase_to_old_cols = {
        "booking_date": "Date",
        "customer_name": "Customer Name",
        "wing": "Wing",
        "floor": "Floor",
        "flat_number": "Flat Number",
        "unit_type": "Type",
        "final_price": "Final Price",
        "rate": "Rate",
        "agreement_cost": "Agreement Cost",
        "lead_type": "Lead Type",
        "sales_executive": "Sales Executive",
        "month": "month",
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
        "booking_amount": "BOOKING AMOUNT",
        "agreement": "AGREEMENT",
        "plinth": "PLINTH",
        "third_floor": "3RD FLOOR",
        "seventh_floor": "7TH FLOOR",
        "tenth_floor": "10TH FLOOR",
        "thirteenth_floor": "13TH FLOOR",
        "flooring": "FLOORING",
        "plastering": "PLASTERING",
        "plumbing": "PLUMBING",
        "electrical": "ELECTRICAL",
        "sanitary_lift": "SANITARY & LIFT",
        "possession": "POSSESSION",
        "first_visit_date": "First Visit Date",
        "conversion_period_days": "Conversion Period (days)",
        "parking_number": "Parking Number",
        "merged_units": "Merged Units",
        "location": "Location",
        "visit_count": "Visit Count",
        "received_amount": "Received Amount",
        "stamp_duty_percent": "Stamp Duty %"
    }

    df = df.rename(columns=supabase_to_old_cols)

    required_old_cols = [
        "Date", "Customer Name", "Wing", "Floor", "Flat Number", "Type",
        "Final Price", "Rate", "Agreement Cost", "Lead Type",
        "Sales Executive", "month", "Civil Changes", "Offer 1", "Offer 2",
        "Offer 1 Rewarded", "Offer 2 Rewarded", "Referral Given",
        "Stamp Duty", "Agreement Done", "Incentive", "RCC",
        "POSSESSION HANDOVER", "Insider Banker", "Outsider Banker",
        "Carpet Area", "First Visit Date", "Conversion Period (days)",
        "Parking Number", "Merged Units", "Location", "Visit Count"
    ]

    for col in required_old_cols:
        if col not in df.columns:
            df[col] = ""

    def bool_to_status(value, true_text):
        if value is True:
            return true_text
        if value is False or value is None:
            return ""
        return str(value)

    df["Agreement Done"] = df["Agreement Done"].apply(lambda x: bool_to_status(x, "Done"))
    df["POSSESSION HANDOVER"] = df["POSSESSION HANDOVER"].apply(lambda x: bool_to_status(x, "Handover"))
    df["Referral Given"] = df["Referral Given"].apply(lambda x: bool_to_status(x, "Given"))
    df["Offer 1 Rewarded"] = df["Offer 1 Rewarded"].apply(lambda x: bool_to_status(x, "Rewarded 1"))
    df["Offer 2 Rewarded"] = df["Offer 2 Rewarded"].apply(lambda x: bool_to_status(x, "Rewarded 2"))

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Month'] = df['Date'].dt.strftime("%B %y")
    df['Quarter'] = df['Date'].apply(get_custom_quarter_label)
    df['MonthYear'] = df['Date'].dt.strftime("%B %y")
    df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')

    # Clean Agreement Cost & Carpet Area for PSF calc
    df['Agreement Cost'] = pd.to_numeric(df['Agreement Cost'], errors='coerce').fillna(0.0)
    df['Carpet Area'] = pd.to_numeric(df['Carpet Area'], errors='coerce').fillna(0.0)

    # Normalize status cols
    df['Agreement Done'] = df['Agreement Done'].fillna('').astype(str).str.strip().str.lower()
    df['Stamp Duty'] = df['Stamp Duty'].fillna('').astype(str).str.strip().str.lower()

    # Final Price cleaning (Lakhs → ₹ full amount)
    df['_FinalPrice_L'] = pd.to_numeric(df['Final Price'], errors='coerce')
    df['_FinalPrice_Full'] = (df['_FinalPrice_L'] * 100000).astype('float')

    # Totals
    total_carpet_area = df['Carpet Area'].sum()
    total_bookings = len(df)
    agreement_done_count = (df['Agreement Done'] == 'done').sum()
    agreement_pending_count = (df['Agreement Done'] != 'done').sum()
    stamp_duty_received = (df['Stamp Duty'] == 'received').sum()
    stamp_duty_pending = (df['Stamp Duty'] != 'received').sum()
    total_stamp_duty = int(stamp_duty_received + stamp_duty_pending)
    total_agreements = int(agreement_done_count + agreement_pending_count)

    # Avg conversion days
    avg_conv_days_display = "—"
    if 'Conversion Period (days)' in df.columns:
        conv_series = pd.to_numeric(df['Conversion Period (days)'], errors='coerce')
        if conv_series.notna().any():
            avg_conv_days_display = round(conv_series.mean(), 1)

    # Month ordering
    df['Month_dt'] = df['Date'].dt.to_period('M')
    month_order = sorted([m for m in df['Month_dt'].unique() if pd.notna(m)])
    ordered_months = [pd.to_datetime(str(m)).strftime("%B %y") for m in month_order]
    df['Month'] = pd.Categorical(df['Month'], categories=ordered_months, ordered=True)

    wing_wise = df['Wing'].value_counts()
    month_wise = df['Month'].value_counts().sort_index()
    type_wise = df['Type'].value_counts()
    sales_exec_wise = df['Sales Executive'].value_counts()

    # ==========================================================
    # INVENTORY CONSTANTS / HELPERS (B/C & podium included)
    # ==========================================================
    CARPET_SIZES  = [480.94, 482.12, 545.00, 655.10, 665.65, 666.29, 678.00, 689.00, 756.00, 790.00]
    CARPET_LABELS = [f"{s:.2f}" for s in CARPET_SIZES]
    AREA_TOL      = 0.25
    PODIUM_SIZES = [545.00, 678.00, 689.00, 756.00, 790.00]

    SIZE_TYPE_MAP = {
        480.94:'1BHK', 482.12:'1BHK', 545.00:'1BHK',
        655.10:'2BHK', 665.65:'2BHK', 666.29:'2BHK', 678.00:'2BHK', 689.00:'2BHK', 756.00:'2BHK', 790.00:'2BHK'
    }

    FACING_MAP = {
        "Garden Facing": [480.94, 482.12, 665.65, 790.00, 545.00, 756.00],
        "Road Facing":   [655.10, 666.29, 678.00, 689.00]
    }
    FACING_DOMAIN = ["Garden Facing", "Road Facing"]

    CARPET_TOTALS = {
        ('E', 480.94): 12, ('E', 482.12): 12, ('E', 655.10): 16, ('E', 665.65): 18, ('E', 666.29): 18,
        ('E', 678.00): 1,  ('E', 689.00): 2,  ('E', 790.00): 1,  ('E', 545.00): 2,  ('E', 756.00): 1,
        ('F', 480.94):  9, ('F', 482.12): 15, ('F', 655.10): 13, ('F', 665.65): 22, ('F', 666.29): 18,
        ('F', 678.00): 1,  ('F', 689.00): 1,  ('F', 790.00): 1,  ('F', 545.00): 2,  ('F', 756.00): 1,
        ('B', 655.10): 13, ('B', 666.29): 18, ('B', 665.65): 22, ('B', 480.94): 10,  ('B', 482.12): 16,
        ('B', 678.00): 1,  ('B', 689.00): 1,  ('B', 790.00): 1,  ('B', 545.00): 2,  ('B', 756.00): 1,
        ('C', 655.10): 18, ('C', 666.29): 18, ('C', 665.65): 14, ('C', 480.94): 10, ('C', 482.12): 10,
        ('C', 678.00): 1,  ('C', 689.00): 2,  ('C', 790.00): 1,  ('C', 545.00): 2,  ('C', 756.00): 1,
    }

    # ---- helpers for sizes/areas/PSF ----
    def nearest_size(val: float):
        if pd.isna(val): return None
        try:
            v = float(val)
        except:
            return None
        for s in CARPET_SIZES:
            if abs(v - s) <= AREA_TOL:
                return s
        return None

    def fmt_psf(x):
        return f"₹{x:,.0f}/sqft" if pd.notna(x) and x >= 0 else "—"

    def sum_rev(sub):
        return pd.to_numeric(sub['Agreement Cost'], errors='coerce').fillna(0).sum()

    def sum_sale_area(sub):
        return (pd.to_numeric(sub['Carpet Area'], errors='coerce').fillna(0) * SALE_FACTOR).sum()

    def avg_psf(sub):
        A = sum_sale_area(sub)
        R = sum_rev(sub)
        return (R / A) if A > 0 else float('nan')

    # Booked counts by Wing×Size
    size_booked = (
        df.assign(_size=pd.to_numeric(df.get('Carpet Area', pd.Series()), errors='coerce').apply(nearest_size))
          .dropna(subset=['_size'])
          .groupby(['Wing', '_size']).size()
          .to_dict()
    )

    # Derived inventories by type
    WING_TYPE_TOTALS = defaultdict(int)
    for (w, s), tot in CARPET_TOTALS.items():
        t = SIZE_TYPE_MAP.get(s)
        if t:
            WING_TYPE_TOTALS[(w, t)] += int(tot)
    WING_TYPE_TOTALS = dict(WING_TYPE_TOTALS)

    WING_TOTALS = defaultdict(int)
    for (w, t), tot in WING_TYPE_TOTALS.items():
        WING_TOTALS[w] += int(tot)
    WING_TOTALS = dict(WING_TOTALS)

    WINGS_ORDER = ['E', 'F', 'B', 'C']
    WINGS = [w for w in WINGS_ORDER if any(k[0] == w for k in WING_TYPE_TOTALS.keys())]
    TYPE_DOMAIN   = ['1BHK', '2BHK']
    METRICS       = ["Booked", "Available", "Total"]
    METRIC_COLORS = ["#10b981", "#f59e0b", "#6366f1"]

    # Pre-derive a clean Type for floor-wise splits
    df['_NearestSize'] = pd.to_numeric(df.get('Carpet Area', 0), errors='coerce').apply(nearest_size)
    df['_DerivedType'] = df['_NearestSize'].map(SIZE_TYPE_MAP).fillna(df.get('Type', ''))

    # ---------- chart helpers ----------
    def wing_type_chart(wing_df: pd.DataFrame, wing: str):
        BAR_SIZE = 12
        base = alt.Chart(wing_df)
        bars = base.mark_bar(size=BAR_SIZE).encode(
            x=alt.X('Type:N', sort=TYPE_DOMAIN, title='Type',
                    scale=alt.Scale(paddingInner=0.35, paddingOuter=0.35),
                    axis=alt.Axis(labelFontSize=13, titleFontSize=14, labelAngle=0, labelLimit=140, labelOverlap=True)),
            xOffset=alt.X('Metric:N', sort=METRICS),
            y=alt.Y('Count:Q', title='Units', axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
            color=alt.Color('Metric:N', scale=alt.Scale(domain=METRICS, range=METRIC_COLORS),
                            legend=alt.Legend(title="", orient='top', labelFontSize=12)),
            tooltip=['Type:N', 'Metric:N', 'Count:Q']
        )
        labels = base.mark_text(dy=-8, fontSize=12, fontWeight='bold', color='#0f172a').encode(
            x=alt.X('Type:N', sort=TYPE_DOMAIN),
            xOffset=alt.X('Metric:N', sort=METRICS),
            y='Count:Q', text='Count:Q'
        )
        return (bars + labels).properties(
            title=alt.TitleParams(f"Wing {wing} — Inventory by Type", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
            height=360, width=alt.Step(90)
        ).configure_title(anchor='start')

    def grouped_bar_with_gaps(df_chart: pd.DataFrame, x_field: str, x_domain: list, title: str):
        BAR_SIZE = 12
        base = alt.Chart(df_chart)
        bars = base.mark_bar(size=BAR_SIZE).encode(
            x=alt.X(f'{x_field}:N', sort=x_domain, title=x_field,
                    scale=alt.Scale(paddingInner=0.35, paddingOuter=0.35),
                    axis=alt.Axis(labelFontSize=13, titleFontSize=14, labelAngle=0, labelLimit=160, labelOverlap=True)),
            xOffset=alt.X('Metric:N', sort=METRICS),
            y=alt.Y('Count:Q', title='Units', axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
            color=alt.Color('Metric:N', scale=alt.Scale(domain=METRICS, range=METRIC_COLORS),
                            legend=alt.Legend(title="", orient='top', labelFontSize=12)),
            tooltip=[alt.Tooltip(f'{x_field}:N', title=x_field), alt.Tooltip('Metric:N'), alt.Tooltip('Count:Q')]
        )
        labels = base.mark_text(dy=-8, fontSize=12, fontWeight='bold', color='#0f172a').encode(
            x=alt.X(f'{x_field}:N', sort=x_domain),
            xOffset=alt.X('Metric:N', sort=METRICS),
            y='Count:Q', text='Count:Q'
        )
        return (bars + labels).properties(
            title=alt.TitleParams(title, anchor='start', fontSize=16, fontWeight='bold', dy=-5),
            height=360, width=alt.Step(70)
        ).configure_title(anchor='start')

    # -------- Config (you can tweak) --------
    PSD_PROJECT_START_DATE = date(2026, 4, 25)
    PSD_PROJECT_YEARS = 3
    PSD_PROJECT_END_DATE = date(
        PSD_PROJECT_START_DATE.year + PSD_PROJECT_YEARS,
        PSD_PROJECT_START_DATE.month,
        PSD_PROJECT_START_DATE.day
    ) - timedelta(days=1)
    
    PSD_TOTAL_FLATS_TARGET = 588
    
    PSD_GOOD_DAY_WEIGHT = 1.25
    PSD_NORMAL_DAY_WEIGHT = 1.0
    PSD_BAD_DAY_WEIGHT = 0.0
    
    # -------- Utilities --------
    def psd_month_start(d: date) -> date:
        return date(d.year, d.month, 1)
    
    def psd_next_month(d: date) -> date:
        return date(d.year + (d.month // 12), (d.month % 12) + 1, 1)
    
    def psd_add_months(d: date, n: int) -> date:
        y = d.year + (d.month - 1 + n) // 12
        m = (d.month - 1 + n) % 12 + 1
        return date(y, m, 1)
    
    def psd_iter_days(s: date, e: date):
        cur = s
        while cur <= e:
            yield cur
            cur += timedelta(days=1)
    
    def psd_month_label(d: date) -> str:
        return d.strftime("%B %y").upper()
    
    def psd_parse_month_label(val: str) -> Optional[Tuple[int, int]]:
        if val is None:
            return None
        s = str(val).strip()
        if not s or s.lower() == "nan":
            return None
        s_norm = " ".join(s.replace("-", " ").split())
        for fmt in ("%B %y", "%b %y", "%B %Y", "%b %Y"):
            try:
                dt = dt_datetime.strptime(s_norm.title(), fmt)
                return (dt.year, dt.month)
            except Exception:
                continue
        return None
    
    def psd_quarter_start(d: date) -> date:
        q_m = ((d.month - 1) // 3) * 3 + 1
        return date(d.year, q_m, 1)
    
    def psd_quarter_end(d: date) -> date:
        qs = psd_quarter_start(d)
        return psd_add_months(qs, 3) - timedelta(days=1)
    
    # -------- Amavasya approx (as provided) --------
    def psd_to_jd(dt_utc: datetime) -> float:
        year, month, day = dt_utc.year, dt_utc.month, dt_utc.day
        hour = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600 + dt_utc.microsecond / 3_600_000_000
        if month <= 2:
            year -= 1
            month += 12
        A = year // 100
        B = 2 - A + (A // 4)
        jd0 = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
        return jd0 + hour / 24.0
    
    def psd_from_jd(jd: float) -> datetime:
        jd += 0.5
        Z = int(jd)
        F = jd - Z
        if Z < 2299161:
            A = Z
        else:
            alpha = int((Z - 1867216.25) / 36524.25)
            A = Z + 1 + alpha - int(alpha / 4)
        B = A + 1524
        C = int((B - 122.1) / 365.25)
        D = int(365.25 * C)
        E = int((B - D) / 30.6001)
        day = B - D - int(30.6001 * E) + F
        month = E - 1 if E < 14 else E - 13
        year = C - 4716 if month > 2 else C - 4715
        day_int = int(day)
        frac = day - day_int
        hours = frac * 24
        h = int(hours)
        minutes = (hours - h) * 60
        m = int(minutes)
        seconds = (minutes - m) * 60
        s = int(seconds)
        micros = int((seconds - s) * 1_000_000)
        return dt_datetime(year, month, day_int, h, m, s, micros, tzinfo=timezone.utc)
    
    def psd_approx_new_moon_jde(k: float) -> float:
        return (
            2451550.09765
            + 29.530588853 * k
            + 0.0001337 * (k**2)
            - 0.000000150 * (k**3)
            + 0.00000000073 * (k**4)
        )
    
    def psd_get_amavasya_dates_ist(start: date, end: date) -> List[date]:
        ist_offset = timedelta(hours=5, minutes=30)
        start_dt_utc = dt_datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
        end_dt_utc = dt_datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc)
        jd_start = psd_to_jd(start_dt_utc)
        jd_end = psd_to_jd(end_dt_utc)
        k_start = (jd_start - 2451550.09765) / 29.530588853
        k_end = (jd_end - 2451550.09765) / 29.530588853
        ks = math.floor(k_start) - 2
        ke = math.ceil(k_end) + 2
        out = set()
        for k in range(ks, ke + 1):
            jde = psd_approx_new_moon_jde(k)
            dt_utc = psd_from_jd(jde)
            d_ist = (dt_utc + ist_offset).date()
            if start <= d_ist <= end:
                out.add(d_ist)
        return sorted(out)
    
    # -------- Festivals Model --------
    @dataclass(frozen=True)
    class psd_FestDay:
        name: str
        d: date
        kind: str
    
    def psd_add_range(out: List[psd_FestDay], name: str, s: date, e: date, kind: str):
        cur = s
        while cur <= e:
            out.append(psd_FestDay(name, cur, kind))
            cur += timedelta(days=1)
    
    def psd_fixed_public_holidays(start: date, end: date) -> List[psd_FestDay]:
        out: List[psd_FestDay] = []
        for y in range(start.year, end.year + 1):
            fixed = [
                ("New Year", date(y, 1, 1)), ("Republic Day", date(y, 1, 26)),
                ("Shivaji Jayanti (MH)", date(y, 2, 19)), ("Ambedkar Jayanti", date(y, 4, 14)),
                ("Maharashtra Day", date(y, 5, 1)), ("Independence Day", date(y, 8, 15)),
                ("Gandhi Jayanti", date(y, 10, 2)), ("Christmas", date(y, 12, 25)),
            ]
            for n, d in fixed:
                if start <= d <= end:
                    out.append(psd_FestDay(n, d, "HOLIDAY"))
        return out
    
    def psd_festival_days_between(start: date, end: date) -> List[psd_FestDay]:
        f: List[psd_FestDay] = []
    
        GOOD_DATES: Dict[int, List[Tuple[str, date]]] = {
            2026: [("Nag Panchami", date(2026, 8, 17)), ("Onam", date(2026, 8, 26)),
                   ("Ganesh Chaturthi / Ganesh Sthapana", date(2026, 9, 14)),
                   ("Dhanteras", date(2026, 10, 29)), ("Diwali (Lakshmi Puja)", date(2026, 10, 31))],
            2027: [("Makar Sankranti", date(2027, 1, 15)), ("Pongal", date(2027, 1, 15)),
                   ("Vasant Panchami", date(2027, 2, 11)), ("Mahashivratri", date(2027, 3, 6)),
                   ("Holika Dahan (before Holi)", date(2027, 3, 21)), ("Ugadi", date(2027, 4, 7)),
                   ("Gudi Padwa", date(2027, 4, 7)), ("Chaitra Navratri Begins", date(2027, 4, 7)),
                   ("Ram Navami", date(2027, 4, 15)), ("Akshaya Tritiya", date(2027, 5, 9)),
                   ("Nag Panchami", date(2027, 8, 6)), ("Ganesh Chaturthi / Ganesh Sthapana", date(2027, 9, 4)),
                   ("Onam", date(2027, 9, 12)), ("Dhanteras", date(2027, 10, 27)),
                   ("Diwali (Lakshmi Puja)", date(2027, 10, 29))],
            2028: [("Makar Sankranti", date(2028, 1, 15)), ("Pongal", date(2028, 1, 15)),
                   ("Vasant Panchami", date(2028, 1, 31)), ("Mahashivratri", date(2028, 2, 23)),
                   ("Holika Dahan (before Holi)", date(2028, 3, 10)), ("Ugadi", date(2028, 3, 27)),
                   ("Gudi Padwa", date(2028, 3, 27)), ("Chaitra Navratri Begins", date(2028, 3, 27)),
                   ("Ram Navami", date(2028, 4, 3)), ("Akshaya Tritiya", date(2028, 4, 27)),
                   ("Nag Panchami", date(2028, 7, 26)), ("Ganesh Chaturthi / Ganesh Sthapana", date(2028, 8, 23)),
                   ("Onam", date(2028, 9, 1)), ("Dhanteras", date(2028, 10, 15)),
                   ("Diwali (Lakshmi Puja)", date(2028, 10, 17))],
            2029: [("Makar Sankranti", date(2029, 1, 14)), ("Pongal", date(2029, 1, 14)),
                   ("Vasant Panchami", date(2029, 1, 19)), ("Mahashivratri", date(2029, 2, 11)),
                   ("Holika Dahan (before Holi)", date(2029, 2, 28)), ("Ugadi", date(2029, 4, 14)),
                   ("Gudi Padwa", date(2029, 4, 14)), ("Chaitra Navratri Begins", date(2029, 4, 14)),
                   ("Ram Navami", date(2029, 4, 23))],
        }
        for y, items in GOOD_DATES.items():
            for name, d in items:
                if start <= d <= end:
                    f.append(psd_FestDay(name, d, "GOOD"))
    
        for y in range(start.year, end.year + 1):
            d = date(y, 4, 13)
            if start <= d <= end:
                f.append(psd_FestDay("Baisakhi", d, "GOOD"))
    
        for y in [2027, 2028, 2029]:
            begins = next((d for (n, d) in GOOD_DATES.get(y, []) if "Chaitra Navratri Begins" in n), None)
            if begins and start <= begins <= end:
                psd_add_range(f, "Chaitra Navratri", begins, begins + timedelta(days=8), "GOOD")
    
        sharad_starts = {2026: date(2026, 10, 11), 2027: date(2027, 9, 30), 2028: date(2028, 9, 19)}
        for y, d in sharad_starts.items():
            if start <= d <= end:
                psd_add_range(f, "Sharad Navratri", d, d + timedelta(days=8), "GOOD")
                dus = d + timedelta(days=9)
                if start <= dus <= end:
                    f.append(psd_FestDay("Dussehra / Vijayadashami", dus, "GOOD"))
    
        for y in range(start.year, end.year + 1):
            ss, ee = date(y, 8, 1), date(y, 8, 31)
            s = max(ss, start); e = min(ee, end)
            if s <= e:
                psd_add_range(f, "Shravan Maas (season)", s, e, "GOOD")
    
        pitru = {
            2026: (date(2026, 9, 27), date(2026, 10, 10)),
            2027: (date(2027, 9, 16), date(2027, 9, 29)),
            2028: (date(2028, 9, 4), date(2028, 9, 17)),
        }
        for _, (ps, pe) in pitru.items():
            s = max(ps, start); e = min(pe, end)
            if s <= e:
                psd_add_range(f, "Pitru Paksha", s, e, "BAD")
    
        for s, e, nm in [(date(2026, 5, 17), date(2026, 6, 15), "Adhik Maas (Mal Maas)"),
                         (date(2029, 3, 17), date(2029, 4, 13), "Adhik Maas (Mal Maas)")]:
            ss = max(s, start); ee = min(e, end)
            if ss <= ee:
                psd_add_range(f, nm, ss, ee, "BAD")
    
        for d in psd_get_amavasya_dates_ist(start, end):
            f.append(psd_FestDay("Amavasya", d, "BAD"))
    
        eclipse_bad = [
            ("Solar Eclipse", date(2026, 8, 12)), ("Lunar Eclipse", date(2026, 8, 28)),
            ("Solar Eclipse", date(2027, 2, 6)),  ("Lunar Eclipse", date(2027, 2, 21)),
            ("Solar Eclipse", date(2027, 8, 2)),  ("Lunar Eclipse", date(2027, 8, 17)),
            ("Lunar Eclipse", date(2028, 1, 12)), ("Solar Eclipse", date(2028, 1, 26)),
            ("Solar Eclipse", date(2029, 1, 14)),
        ]
        for nm, d in eclipse_bad:
            if start <= d <= end:
                f.append(psd_FestDay(nm, d, "BAD"))
    
        for y in range(start.year, end.year + 1):
            for m in range(1, 13):
                if m == 1:
                    continue
                try:
                    d = date(y, m, 14)
                except ValueError:
                    continue
                if start <= d <= end:
                    f.append(psd_FestDay("Sankranti Day (approx)", d, "BAD"))
    
        f.extend(psd_fixed_public_holidays(start, end))
        f = [x for x in f if start <= x.d <= end]
        f.sort(key=lambda x: (x.d, x.kind, x.name))
        return f
    
    def psd_day_weight(d: date, by_date: Dict[date, List[psd_FestDay]]) -> float:
        items = by_date.get(d, [])
        if any(x.kind in ("BAD", "HOLIDAY") for x in items):
            return PSD_BAD_DAY_WEIGHT
        if any(x.kind == "GOOD" for x in items):
            return PSD_GOOD_DAY_WEIGHT
        return PSD_NORMAL_DAY_WEIGHT
    
    def psd_weighted_days(s: date, e: date, by_date: Dict[date, List[psd_FestDay]]) -> float:
        return sum(psd_day_weight(d, by_date) for d in psd_iter_days(s, e))
    
    def psd_selling_days_count(s: date, e: date, by_date: Dict[date, List[psd_FestDay]]) -> int:
        return sum(1 for d in psd_iter_days(s, e) if psd_day_weight(d, by_date) > 0)
    
    # -------- Supabase booking reader + target engine --------
    def psd_safe_header_idx(headers: List[str], target: str) -> Optional[int]:
        t = (target or "").strip().lower()
        for i, h in enumerate(headers):
            if (h or "").strip().lower() == t:
                return i
        return None
    
    @st.cache_data(ttl=120)
    def psd_read_booking_sheet_cached(df_source) -> Tuple[int, Dict[Tuple[int, int], int]]:
        achieved_by_ym: Dict[Tuple[int, int], int] = {}

        if df_source is None or df_source.empty:
            return 0, {}

        temp = df_source.copy()

        if "booking_date" in temp.columns:
            date_col = "booking_date"
        elif "Date" in temp.columns:
            date_col = "Date"
        else:
            date_col = None

        if "month" in temp.columns:
            month_col = "month"
        elif "Month" in temp.columns:
            month_col = "Month"
        else:
            month_col = None

        total = len(temp)

        if month_col:
            for val in temp[month_col].dropna():
                parsed = psd_parse_month_label(str(val))
                if parsed:
                    achieved_by_ym[parsed] = achieved_by_ym.get(parsed, 0) + 1

        if not achieved_by_ym and date_col:
            temp["_psd_date"] = pd.to_datetime(temp[date_col], errors="coerce")
            for d in temp["_psd_date"].dropna():
                parsed = (int(d.year), int(d.month))
                achieved_by_ym[parsed] = achieved_by_ym.get(parsed, 0) + 1

        return total, achieved_by_ym
    
    def psd_build_month_list(start: date, end: date) -> List[Tuple[int, int]]:
        out = []
        cur = psd_month_start(start)
        while cur <= end:
            out.append((cur.year, cur.month))
            cur = psd_next_month(cur)
        return out
    
    def psd_month_range(ym: Tuple[int, int], project_end: date) -> Tuple[date, date]:
        y, m = ym
        s = date(y, m, 1)
        e = min(project_end, psd_next_month(s) - timedelta(days=1))
        return s, e
    
    def psd_compute_month_targets_with_carry(month_list, month_weight, achieved_by_ym, total_target) -> Dict[Tuple[int, int], int]:
        targets: Dict[Tuple[int, int], int] = {}
        rem = int(total_target)
        for ym in month_list:
            w_this = month_weight.get(ym, 0.0)
            w_remaining = sum(month_weight.get(x, 0.0) for x in month_list if x >= ym)
            if rem <= 0 or w_remaining <= 0 or w_this <= 0:
                t = 0
            else:
                t = int(math.ceil(rem * (w_this / w_remaining)))
            targets[ym] = t
            rem = max(0, rem - int(achieved_by_ym.get(ym, 0)))
        return targets

    # =============================
    # Create sub-tabs INSIDE tab1
    # =============================
    TAB_BOOKING, TAB_AGREEMENT, TAB_INVENTORY, TAB_MONTHLY, TAB_OFFERS_DASH, TAB_SE_PERFORMANCE, TAB_PROJECTED = st.tabs([
        "Booking Dashboard",
        "Agreement Dashboard",
        "Inventory Dashboard",
        "Monthly Stamp Duty & Agreement Status",
        "Offers Dashboard",
        "Sales Performance Command Center",
        "Projected Sales Dashboard",
    ])
    # ------------------------------------------------------------
    # TAB 1: Booking Dashboard
    # ------------------------------------------------------------
    with TAB_BOOKING:
        st.header("📊 Booking Dashboard")
    
        # ============================================================
        # SECTION HEADING CARD STYLE
        # ============================================================
        st.markdown("""
        <style>
        .section-kpi-card {
            width: 100%;
            background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 45%, #3b82f6 100%);
            border: 1px solid rgba(37, 99, 235, 0.35);
            border-radius: 18px;
            padding: 20px 24px;
            margin: 26px 0 16px 0;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 82px;
        }
        .section-kpi-card h2 {
            margin: 0;
            font-size: 28px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 0.4px;
            text-align: center;
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)
    
        def section_heading_card(title: str):
            st.markdown(
                f"""
                <div class="section-kpi-card">
                    <h2>{title}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
    
        # ============================================================
        # HELPERS / PREP
        # ============================================================
        def _fiscal_qidx(m: int) -> int:
            if 4 <= m <= 6:
                return 1  # Apr-Jun
            if 7 <= m <= 9:
                return 2  # Jul-Sep
            if 10 <= m <= 12:
                return 3  # Oct-Dec
            return 4      # Jan-Mar
    
        def _pct(booked, total):
            return (booked / total * 100.0) if total > 0 else 0.0
    
        def fmt_visits(x):
            return f"{x:.2f}" if pd.notna(x) else "—"
    
        def fmt_avg_bookings(x):
            return f"{x:.2f}" if pd.notna(x) else "—"
    
        def fmt_rate(x):
            return f"₹{x:,.0f}/sqft" if pd.notna(x) and x > 0 else "—"
    
        def wing_pct_sold(wing_code: str) -> float:
            booked = int(booked_by_wing_counts.get(wing_code, 0))
            total = int(WING_TOTALS.get(wing_code, 0))
            return (booked / total * 100.0) if total > 0 else 0.0
    
        # Ensure Quarter exists
        if 'Quarter' not in df.columns and 'Date' in df.columns:
            df['Quarter'] = df['Date'].apply(get_custom_quarter_label)
    
        # Ordered quarters
        ordered_quarters = []
        if {'Date', 'Quarter'}.issubset(df.columns):
            qorder_df = (
                df.dropna(subset=['Date', 'Quarter'])
                  .assign(
                      _FY=lambda d: d['Date'].dt.year - (d['Date'].dt.month < 4),
                      _QIDX=lambda d: d['Date'].dt.month.apply(_fiscal_qidx)
                  )
                  .groupby('Quarter', as_index=False)[['_FY', '_QIDX']].median()
            )
            ordered_quarters = (
                qorder_df.sort_values(['_FY', '_QIDX'])['Quarter'].tolist()
                if not qorder_df.empty else df['Quarter'].dropna().unique().tolist()
            )
    
        # Avg visits for booking
        VISIT_COL = "Visit Count"
        if VISIT_COL in df.columns:
            visit_vals = pd.to_numeric(df[VISIT_COL], errors="coerce")
            visit_vals = visit_vals[visit_vals.notna() & (visit_vals > 0)]
            avg_visits_for_booking = float(visit_vals.mean()) if len(visit_vals) else float("nan")
        else:
            avg_visits_for_booking = float("nan")
    
        # Avg bookings per month
        MONTH_KEY = "MonthYear" if "MonthYear" in df.columns else ("Month" if "Month" in df.columns else None)
        if MONTH_KEY is None or df.empty:
            avg_bookings_per_month = float("nan")
        else:
            m = df[MONTH_KEY].astype(str).str.strip()
            m = m[m != ""]
            n_months = int(m.nunique()) if len(m) else 0
            avg_bookings_per_month = (len(m) / n_months) if n_months > 0 else float("nan")
    
        # PSF cards
        if 'Type' in df.columns:
            type_norm = df['Type'].astype(str).str.strip().str.upper()
        else:
            type_norm = pd.Series(index=df.index, dtype=str)
    
        avg_psf_1 = avg_psf(df[type_norm.eq('1BHK')]) if 'Type' in df.columns else float('nan')
        avg_psf_2 = avg_psf(df[type_norm.eq('2BHK')]) if 'Type' in df.columns else float('nan')
        avg_psf_all = avg_psf(df)
    
        # Booking % cards
        booked_by_wing_counts = wing_wise.to_dict()
        ef_total_units = int(WING_TOTALS.get('E', 0) + WING_TOTALS.get('F', 0))
        ef_booked = int(booked_by_wing_counts.get('E', 0) + booked_by_wing_counts.get('F', 0))
        ef_pct = _pct(ef_booked, ef_total_units)
    
        bc_total_units = int(WING_TOTALS.get('B', 0) + WING_TOTALS.get('C', 0))
        bc_booked = int(booked_by_wing_counts.get('B', 0) + booked_by_wing_counts.get('C', 0))
        bc_pct = _pct(bc_booked, bc_total_units)
    
        phase_total_units = int(sum(WING_TOTALS.get(w, 0) for w in ['E', 'F', 'B', 'C']))
        phase_booked = int(sum(booked_by_wing_counts.get(w, 0) for w in ['E', 'F', 'B', 'C']))
        phase_pct = _pct(phase_booked, phase_total_units)
    
        # Appreciation KPIs
        BASE_MONTH_LABEL = "April 25"
    
        def _avg_psf_for(month_label: str, type_code: str | None):
            if month_label is None or 'Month' not in df.columns:
                return float('nan')
            sub = df[df['Month'] == month_label]
            if type_code is not None and 'Type' in sub.columns:
                sub = sub[sub['Type'].astype(str).str.strip().str.upper() == type_code]
            val = avg_psf(sub)
            return float(val) if pd.notna(val) else float('nan')
    
        def _appr_pct(base_val, curr_val):
            if pd.isna(base_val) or pd.isna(curr_val) or base_val == 0:
                return float('nan')
            return ((curr_val - base_val) / base_val) * 100.0
    
        latest_month_label = ordered_months[-1] if ordered_months else None
    
        base_1 = _avg_psf_for(BASE_MONTH_LABEL, '1BHK')
        curr_1 = _avg_psf_for(latest_month_label, '1BHK')
        appr_1 = _appr_pct(base_1, curr_1)
    
        base_2 = _avg_psf_for(BASE_MONTH_LABEL, '2BHK')
        curr_2 = _avg_psf_for(latest_month_label, '2BHK')
        appr_2 = _appr_pct(base_2, curr_2)
    
        base_all = _avg_psf_for(BASE_MONTH_LABEL, None)
        curr_all = _avg_psf_for(latest_month_label, None)
        appr_all = _appr_pct(base_all, curr_all)
    
        # ============================================================
        # SUMMARY
        # ============================================================
        section_heading_card("Summary")
        
        def _subset_by_type(dataframe, type_code=None):
            if type_code is None:
                return dataframe.copy()
            if 'Type' not in dataframe.columns:
                return dataframe.iloc[0:0].copy()
            tnorm = dataframe['Type'].astype(str).str.strip().str.upper()
            return dataframe[tnorm.eq(str(type_code).strip().upper())].copy()
        
        def _subset_by_lead_type(dataframe, lead_types=None):
            if not lead_types:
                return dataframe.copy()
            if 'Lead Type' not in dataframe.columns:
                return dataframe.iloc[0:0].copy()
            lnorm = dataframe['Lead Type'].astype(str).str.strip().str.upper()
            lead_types_norm = [str(x).strip().upper() for x in lead_types]
            return dataframe[lnorm.isin(lead_types_norm)].copy()
        
        def _avg_conversion(dataframe, type_code=None):
            if 'Conversion Period (days)' not in dataframe.columns:
                return float("nan")
            sub = _subset_by_type(dataframe, type_code)
            vals = pd.to_numeric(sub['Conversion Period (days)'], errors='coerce')
            vals = vals[vals.notna() & (vals >= 0)]
            return float(vals.mean()) if len(vals) else float("nan")
        
        def _avg_conversion_by_lead_type(dataframe, lead_types=None):
            if 'Conversion Period (days)' not in dataframe.columns:
                return float("nan")
            sub = _subset_by_lead_type(dataframe, lead_types)
            vals = pd.to_numeric(sub['Conversion Period (days)'], errors='coerce')
            vals = vals[vals.notna() & (vals >= 0)]
            return float(vals.mean()) if len(vals) else float("nan")
        
        def _avg_visits(dataframe, type_code=None):
            if 'Visit Count' not in dataframe.columns:
                return float("nan")
            sub = _subset_by_type(dataframe, type_code)
            vals = pd.to_numeric(sub['Visit Count'], errors='coerce')
            vals = vals[vals.notna() & (vals > 0)]
            return float(vals.mean()) if len(vals) else float("nan")
        
        def _avg_bookings_per_month(dataframe, type_code=None):
            sub = _subset_by_type(dataframe, type_code)
            month_key = "MonthYear" if "MonthYear" in sub.columns else ("Month" if "Month" in sub.columns else None)
            if month_key is None or sub.empty:
                return float("nan")
            m = sub[month_key].astype(str).str.strip()
            m = m[m != ""]
            n_months = int(m.nunique()) if len(m) else 0
            return (len(m) / n_months) if n_months > 0 else float("nan")
        
        def _fmt_1_dec(x):
            return f"{x:.1f}" if pd.notna(x) else "—"
        
        def _fmt_0_dec(x):
            return f"{x:.0f}" if pd.notna(x) else "—"
        
        def _avg_psf(dataframe, type_code=None):
            sub = _subset_by_type(dataframe, type_code)
        
            if sub.empty or 'Agreement Cost' not in sub.columns or 'Carpet Area' not in sub.columns:
                return float("nan")
        
            agreement_cost = pd.to_numeric(sub['Agreement Cost'], errors='coerce')
            carpet_area = pd.to_numeric(sub['Carpet Area'], errors='coerce')
            saleable_area = carpet_area * 1.38
        
            valid = agreement_cost.notna() & saleable_area.notna() & (saleable_area > 0)
            if not valid.any():
                return float("nan")
        
            total_agreement_cost = agreement_cost[valid].sum()
            total_saleable_area = saleable_area[valid].sum()
        
            return float(total_agreement_cost / total_saleable_area) if total_saleable_area > 0 else float("nan")
        
        def _monthly_weighted_psf_stats(dataframe, type_code=None):
            sub = _subset_by_type(dataframe, type_code)
        
            if sub.empty or 'Month' not in sub.columns:
                return float("nan"), float("nan"), float("nan"), None, None
        
            ac = pd.to_numeric(sub['Agreement Cost'], errors='coerce') if 'Agreement Cost' in sub.columns else pd.Series(index=sub.index, dtype=float)
            ca = pd.to_numeric(sub['Carpet Area'], errors='coerce') if 'Carpet Area' in sub.columns else pd.Series(index=sub.index, dtype=float)
            saleable = ca * 1.38
        
            temp = sub.copy()
            temp['_AgreementCostNum'] = ac
            temp['_SaleableArea'] = saleable
        
            temp = temp[
                temp['Month'].notna() &
                temp['_AgreementCostNum'].notna() &
                temp['_SaleableArea'].notna() &
                (temp['_SaleableArea'] > 0)
            ].copy()
        
            if temp.empty:
                return float("nan"), float("nan"), float("nan"), None, None
        
            month_tbl = (
                temp.groupby('Month', as_index=False)
                    .agg(
                        TotalAgreementCost=('_AgreementCostNum', 'sum'),
                        TotalSaleableArea=('_SaleableArea', 'sum')
                    )
            )
        
            month_tbl['WeightedAvgPSF'] = month_tbl['TotalAgreementCost'] / month_tbl['TotalSaleableArea']
        
            if 'ordered_months' in locals() and ordered_months:
                month_tbl['Month'] = pd.Categorical(month_tbl['Month'], categories=ordered_months, ordered=True)
                month_tbl = month_tbl.sort_values('Month')
        
            if month_tbl.empty:
                return float("nan"), float("nan"), float("nan"), None, None
        
            low_row = month_tbl.loc[month_tbl['WeightedAvgPSF'].idxmin()]
            high_row = month_tbl.loc[month_tbl['WeightedAvgPSF'].idxmax()]
        
            low_psf = float(low_row['WeightedAvgPSF']) if pd.notna(low_row['WeightedAvgPSF']) else float("nan")
            high_psf = float(high_row['WeightedAvgPSF']) if pd.notna(high_row['WeightedAvgPSF']) else float("nan")
            appr_pct = ((high_psf - low_psf) / low_psf * 100.0) if pd.notna(low_psf) and pd.notna(high_psf) and low_psf > 0 else float("nan")
        
            low_month = str(low_row['Month']) if pd.notna(low_row['Month']) else None
            high_month = str(high_row['Month']) if pd.notna(high_row['Month']) else None
        
            return low_psf, high_psf, appr_pct, low_month, high_month
        
        # ============================================================
        # PRE-CALCULATIONS
        # ============================================================
        booked_by_wing_counts = wing_wise.to_dict()
        
        ef_total_units = int(WING_TOTALS.get('E', 0) + WING_TOTALS.get('F', 0))
        ef_booked = int(booked_by_wing_counts.get('E', 0) + booked_by_wing_counts.get('F', 0))
        ef_pct = _pct(ef_booked, ef_total_units)
        
        bc_total_units = int(WING_TOTALS.get('B', 0) + WING_TOTALS.get('C', 0))
        bc_booked = int(booked_by_wing_counts.get('B', 0) + booked_by_wing_counts.get('C', 0))
        bc_pct = _pct(bc_booked, bc_total_units)
        
        phase_total_units = int(sum(WING_TOTALS.get(w, 0) for w in ['E', 'F', 'B', 'C']))
        phase_booked = int(sum(booked_by_wing_counts.get(w, 0) for w in ['E', 'F', 'B', 'C']))
        phase_pct = _pct(phase_booked, phase_total_units)
        
        def wing_pct_sold(wing_code: str) -> float:
            booked = int(booked_by_wing_counts.get(wing_code, 0))
            total = int(WING_TOTALS.get(wing_code, 0))
            return (booked / total * 100.0) if total > 0 else 0.0
        
        # Agreement status counts
        if 'Agreement Done' in df.columns:
            agreement_status = df['Agreement Done'].astype(str).str.strip()
            agreement_done_count = int(agreement_status.str.upper().eq('DONE').sum())
            agreement_pending_count = int(((agreement_status.eq('')) | (df['Agreement Done'].isna())).sum())
            total_agreements_count = agreement_done_count + agreement_pending_count
        else:
            agreement_done_count = 0
            agreement_pending_count = 0
            total_agreements_count = 0
        
        # Average conversion
        avg_conv_all = _avg_conversion(df, None)
        avg_conv_1 = _avg_conversion(df, '1BHK')
        avg_conv_2 = _avg_conversion(df, '2BHK') 
        
        # Avg visits
        avg_visits_all = _avg_visits(df, None)
        avg_visits_1 = _avg_visits(df, '1BHK')
        avg_visits_2 = _avg_visits(df, '2BHK')
        
        # Avg bookings per month
        avg_bpm_all = _avg_bookings_per_month(df, None)
        avg_bpm_1 = _avg_bookings_per_month(df, '1BHK')
        avg_bpm_2 = _avg_bookings_per_month(df, '2BHK')
        
        # Avg PSF
        avg_psf_1 = _avg_psf(df, '1BHK')
        avg_psf_2 = _avg_psf(df, '2BHK')
        avg_psf_all = _avg_psf(df, None)
        
        # Appreciation based on LOWEST MONTHLY AVG PSF vs HIGHEST MONTHLY AVG PSF
        low_1, high_1, appr_1, low_month_1, high_month_1 = _monthly_weighted_psf_stats(df, '1BHK')
        low_2, high_2, appr_2, low_month_2, high_month_2 = _monthly_weighted_psf_stats(df, '2BHK')
        low_all, high_all, appr_all, low_month_all, high_month_all = _monthly_weighted_psf_stats(df, None)
        
        # ============================================================
        # KPI ROWS
        # ============================================================
        
        # Row 1
        r1 = st.columns(1)
        with r1[0]:
            st.markdown(
                f"<div class='metric-card'><h3>Total Bookings</h3><p>{total_bookings}</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 2
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            st.markdown(
                f"<div class='metric-card'><h3>Total Stamp Duty</h3><p>{total_stamp_duty}</p></div>",
                unsafe_allow_html=True
            )
        with r2c2:
            st.markdown(
                f"<div class='metric-card'><h3>Stamp Duty Received</h3><p>{stamp_duty_received}</p></div>",
                unsafe_allow_html=True
            )
        with r2c3:
            st.markdown(
                f"<div class='metric-card'><h3>Stamp Duty Pending</h3><p>{stamp_duty_pending}</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 3 — Agreements
        r3c1, r3c2, r3c3 = st.columns(3)
        with r3c1:
            st.markdown(
                f"<div class='metric-card'><h3>Total Agreements</h3><p>{total_agreements_count}</p></div>",
                unsafe_allow_html=True
            )
        with r3c2:
            st.markdown(
                f"<div class='metric-card'><h3>Agreement Done</h3><p>{agreement_done_count}</p></div>",
                unsafe_allow_html=True
            )
        with r3c3:
            st.markdown(
                f"<div class='metric-card'><h3>Agreement Pending</h3><p>{agreement_pending_count}</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 4 — Avg PSF
        r4c1, r4c2, r4c3 = st.columns(3)
        with r4c1:
            st.markdown(
                f"<div class='metric-card'><h3>Avg PSF 1 BHK</h3><p>{('—' if pd.isna(avg_psf_1) else f'₹{avg_psf_1:,.0f}/sqft')}</p></div>",
                unsafe_allow_html=True
            )
        with r4c2:
            st.markdown(
                f"<div class='metric-card'><h3>Avg PSF 2 BHK</h3><p>{('—' if pd.isna(avg_psf_2) else f'₹{avg_psf_2:,.0f}/sqft')}</p></div>",
                unsafe_allow_html=True
            )
        with r4c3:
            st.markdown(
                f"<div class='metric-card'><h3>Overall Avg PSF</h3><p>{('—' if pd.isna(avg_psf_all) else f'₹{avg_psf_all:,.0f}/sqft')}</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 5
        r5c1, r5c2 = st.columns(2)
        with r5c1:
            st.markdown(
                f"<div class='metric-card'><h3>Total Carpet Area Sold</h3><p>{total_carpet_area:,.0f} sq ft</p></div>",
                unsafe_allow_html=True
            )
        with r5c2:
            st.markdown(
                f"<div class='metric-card'><h3>Total Agreement Cost Sold (₹)</h3><p>{sum_rev(df):,.0f}</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 6
        r6c1, r6c2, r6c3 = st.columns(3)
        with r6c1:
            st.markdown(
                f"<div class='metric-card'><h3>Average Conversion Period</h3><p>{_fmt_1_dec(avg_conv_all)} days</p></div>",
                unsafe_allow_html=True
            )
        with r6c2:
            st.markdown(
                f"<div class='metric-card'><h3>Average Conversion Period — 1 BHK</h3><p>{_fmt_1_dec(avg_conv_1)} days</p></div>",
                unsafe_allow_html=True
            )
        with r6c3:
            st.markdown(
                f"<div class='metric-card'><h3>Average Conversion Period — 2 BHK</h3><p>{_fmt_1_dec(avg_conv_2)} days</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 7 — Conversion by Lead Type
        if 'Lead Type' in df.columns:
            lead_type_series = df['Lead Type'].astype(str).str.strip()
            lead_types = sorted(
                [
                    str(x).strip()
                    for x in lead_type_series.unique()
                    if pd.notna(x) and str(x).strip() != "" and str(x).strip().upper() != "NAN"
                ]
            )
        else:
            lead_types = []
        
        if lead_types:
            r7_cols = st.columns(len(lead_types))
            for i, lead_type in enumerate(lead_types):
                avg_conv_lt = _avg_conversion_by_lead_type(df, [lead_type])
                with r7_cols[i]:
                    st.markdown(
                        f"<div class='metric-card'><h3>{lead_type} — Avg Conversion Days</h3><p>{_fmt_1_dec(avg_conv_lt)} days</p></div>",
                        unsafe_allow_html=True
                    )
        else:
            r7 = st.columns(1)
            with r7[0]:
                st.markdown(
                    "<div class='metric-card'><h3>Lead Type Conversion Days</h3><p>—</p></div>",
                    unsafe_allow_html=True
                )
        
        # Row 8
        r8c1, r8c2, r8c3 = st.columns(3)
        with r8c1:
            st.markdown(
                f"<div class='metric-card'><h3>Average Visits for Booking</h3><p>{_fmt_0_dec(avg_visits_all)}</p></div>",
                unsafe_allow_html=True
            )
        with r8c2:
            st.markdown(
                f"<div class='metric-card'><h3>Average Visits for Booking — 1 BHK</h3><p>{_fmt_0_dec(avg_visits_1)}</p></div>",
                unsafe_allow_html=True
            )
        with r8c3:
            st.markdown(
                f"<div class='metric-card'><h3>Average Visits for Booking — 2 BHK</h3><p>{_fmt_0_dec(avg_visits_2)}</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 9
        r9c1, r9c2, r9c3 = st.columns(3)
        with r9c1:
            st.markdown(
                f"<div class='metric-card'><h3>Avg Booking Count / Month</h3><p>{fmt_avg_bookings(avg_bpm_all)}</p></div>",
                unsafe_allow_html=True
            )
        with r9c2:
            st.markdown(
                f"<div class='metric-card'><h3>Avg Booking Count / Month — 1 BHK</h3><p>{fmt_avg_bookings(avg_bpm_1)}</p></div>",
                unsafe_allow_html=True
            )
        with r9c3:
            st.markdown(
                f"<div class='metric-card'><h3>Avg Booking Count / Month — 2 BHK</h3><p>{fmt_avg_bookings(avg_bpm_2)}</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 10
        r10c1, r10c2, r10c3 = st.columns(3)
        with r10c1:
            st.markdown(f"<div class='metric-card'><h3>Booking % — E & F</h3><p>{ef_pct:.1f}%</p></div>", unsafe_allow_html=True)
        with r10c2:
            st.markdown(f"<div class='metric-card'><h3>Booking % — B & C</h3><p>{bc_pct:.1f}%</p></div>", unsafe_allow_html=True)
        with r10c3:
            st.markdown(f"<div class='metric-card'><h3>Booking % — Phase 1</h3><p>{phase_pct:.1f}%</p></div>", unsafe_allow_html=True)
        
        # Row 11
        r11c1, r11c2 = st.columns(2)
        with r11c1:
            st.markdown(
                f"<div class='metric-card'><h3>E Wing — % Sold</h3><p>{wing_pct_sold('E'):.1f}%</p></div>",
                unsafe_allow_html=True
            )
        with r11c2:
            st.markdown(
                f"<div class='metric-card'><h3>F Wing — % Sold</h3><p>{wing_pct_sold('F'):.1f}%</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 12
        r12c1, r12c2 = st.columns(2)
        with r12c1:
            st.markdown(
                f"<div class='metric-card'><h3>B Wing — % Sold</h3><p>{wing_pct_sold('B'):.1f}%</p></div>",
                unsafe_allow_html=True
            )
        with r12c2:
            st.markdown(
                f"<div class='metric-card'><h3>C Wing — % Sold</h3><p>{wing_pct_sold('C'):.1f}%</p></div>",
                unsafe_allow_html=True
            )
        
        # Row 13 — Appreciation (Lowest Monthly Avg PSF vs Highest Monthly Avg PSF)
        r13c1, r13c2, r13c3 = st.columns(3)
        with r13c1:
            st.markdown(
                f"<div class='metric-card'>"
                f"<h3>1 BHK Appreciation %</h3>"
                f"<p>{('—' if pd.isna(appr_1) else f'{appr_1:.1f}%')}</p>"
                f"<div class='metric-sub'>Lowest Avg Month ({low_month_1 or '—'}): {('—' if pd.isna(low_1) else f'₹{low_1:,.0f}/sqft')} &nbsp;|&nbsp; "
                f"Highest Avg Month ({high_month_1 or '—'}): {('—' if pd.isna(high_1) else f'₹{high_1:,.0f}/sqft')}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with r13c2:
            st.markdown(
                f"<div class='metric-card'>"
                f"<h3>2 BHK Appreciation %</h3>"
                f"<p>{('—' if pd.isna(appr_2) else f'{appr_2:.1f}%')}</p>"
                f"<div class='metric-sub'>Lowest Avg Month ({low_month_2 or '—'}): {('—' if pd.isna(low_2) else f'₹{low_2:,.0f}/sqft')} &nbsp;|&nbsp; "
                f"Highest Avg Month ({high_month_2 or '—'}): {('—' if pd.isna(high_2) else f'₹{high_2:,.0f}/sqft')}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with r13c3:
            st.markdown(
                f"<div class='metric-card'>"
                f"<h3>Overall Appreciation %</h3>"
                f"<p>{('—' if pd.isna(appr_all) else f'{appr_all:.1f}%')}</p>"
                f"<div class='metric-sub'>Lowest Avg Month ({low_month_all or '—'}): {('—' if pd.isna(low_all) else f'₹{low_all:,.0f}/sqft')} &nbsp;|&nbsp; "
                f"Highest Avg Month ({high_month_all or '—'}): {('—' if pd.isna(high_all) else f'₹{high_all:,.0f}/sqft')}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        # ============================================================
        # QUARTERLY DATA
        # ============================================================
        section_heading_card("Quarterly Data")
    
        st.markdown("<div class='section-subtitle'>🗓️ Quarter-wise Booking Count</div>", unsafe_allow_html=True)
        if 'Quarter' in df.columns and ordered_quarters:
            q_count = (
                df.groupby('Quarter').size()
                  .reindex(ordered_quarters, fill_value=0)
                  .reset_index(name='Bookings')
            )
            q_bar = alt.Chart(q_count).mark_bar(color="#7c3aed").encode(
                x=alt.X('Quarter:N', sort=ordered_quarters, title='Quarter',
                        axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                y=alt.Y('Bookings:Q', title='Bookings'),
                tooltip=['Quarter:N', 'Bookings:Q']
            )
            q_text = alt.Chart(q_count).mark_text(
                align='center', baseline='bottom', dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
            ).encode(
                x=alt.X('Quarter:N', sort=ordered_quarters),
                y='Bookings:Q',
                text='Bookings:Q'
            )
            st.altair_chart(
                (q_bar + q_text).properties(
                    title=alt.TitleParams("Quarter-wise Booking Count", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                    height=300, width=alt.Step(110)
                ).configure_title(anchor='start'),
                use_container_width=True
            )
    
        st.markdown("<div class='section-subtitle'>📈 Quarter-wise Avg PSF (₹/sqft)</div>", unsafe_allow_html=True)
        if 'Quarter' in df.columns:
            q_psf = (
                df.dropna(subset=['Quarter'])
                  .groupby('Quarter')
                  .apply(lambda s: avg_psf(s))
                  .reset_index(name='PSF')
            )
            if not q_psf.empty:
                q_psf['Quarter'] = pd.Categorical(q_psf['Quarter'], categories=ordered_quarters, ordered=True)
                qpsf_bar = alt.Chart(q_psf).mark_bar().encode(
                    x=alt.X('Quarter:N', sort=ordered_quarters, title='Quarter',
                            axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                    y=alt.Y('PSF:Q', title='Avg PSF (₹/sqft)'),
                    tooltip=['Quarter:N', alt.Tooltip('PSF:Q', format=',.0f')]
                )
                qpsf_lbl = alt.Chart(q_psf).mark_text(
                    dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    x=alt.X('Quarter:N', sort=ordered_quarters),
                    y='PSF:Q',
                    text=alt.Text('PSF:Q', format=',.0f')
                )
                st.altair_chart(
                    (qpsf_bar + qpsf_lbl).properties(
                        title=alt.TitleParams("Quarter-wise Avg PSF (₹/sqft)", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=280, width=alt.Step(110)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>✅ Quarter-wise Agreement Done (Done only)</div>", unsafe_allow_html=True)
        AGREE_COL = "Agreement Done"
        if AGREE_COL not in df.columns:
            st.info(f"Column '{AGREE_COL}' not found.")
        else:
            df_ad = df.copy()
            if 'Quarter' not in df_ad.columns:
                if 'Date' in df_ad.columns:
                    df_ad['Quarter'] = df_ad['Date'].apply(get_custom_quarter_label)
                else:
                    df_ad = pd.DataFrame()
    
            if not df_ad.empty:
                done_mask = df_ad[AGREE_COL].astype(str).str.strip().str.lower().eq("done")
                df_done = df_ad[done_mask].dropna(subset=['Quarter'])
    
                if df_done.empty:
                    st.info("No rows found where Agreement Done = Done.")
                else:
                    q_domain = ordered_quarters if ordered_quarters else sorted(df_done['Quarter'].unique().tolist())
                    q_done = (
                        df_done.groupby('Quarter').size()
                              .reindex(q_domain, fill_value=0)
                              .reset_index(name='AgreementDone')
                    )
    
                    bar = alt.Chart(q_done).mark_bar().encode(
                        x=alt.X('Quarter:N', sort=q_domain, title='Quarter',
                                axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                        y=alt.Y('AgreementDone:Q', title='Agreements Done'),
                        tooltip=[alt.Tooltip('Quarter:N'), alt.Tooltip('AgreementDone:Q', title='Done')]
                    )
                    labels = alt.Chart(q_done).mark_text(
                        dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(
                        x=alt.X('Quarter:N', sort=q_domain),
                        y='AgreementDone:Q',
                        text=alt.Text('AgreementDone:Q', format='.0f')
                    )
    
                    st.altair_chart(
                        (bar + labels).properties(
                            title=alt.TitleParams("Quarter-wise Agreement Done (Done)", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                            height=280, width=alt.Step(110)
                        ).configure_title(anchor='start'),
                        use_container_width=True
                    )
    
        st.markdown("<div class='section-subtitle'>🏞️ Quarter-wise × Facing-wise Booking Count</div>", unsafe_allow_html=True)
        if {'Carpet Area', 'Quarter'}.issubset(df.columns):
            def classify_facing(area):
                s = nearest_size(area)
                if s is None:
                    return None
                for face, sizes in FACING_MAP.items():
                    if s in sizes:
                        return face
                return None
    
            df_face = df.copy()
            df_face['Facing'] = df_face['Carpet Area'].apply(classify_facing)
            df_face = df_face.dropna(subset=['Facing', 'Quarter'])
    
            if not df_face.empty:
                q_face_count = (
                    df_face.groupby(['Quarter', 'Facing']).size()
                           .reset_index(name='Count')
                )
                q_face_count['Quarter'] = pd.Categorical(q_face_count['Quarter'], categories=ordered_quarters, ordered=True)
    
                bar_qf = alt.Chart(q_face_count).mark_bar().encode(
                    x=alt.X('Quarter:N', sort=ordered_quarters, title='Quarter',
                            axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                    xOffset=alt.X('Facing:N', title='Facing'),
                    y=alt.Y('Count:Q', title='Bookings'),
                    color=alt.Color('Facing:N', scale=alt.Scale(domain=FACING_DOMAIN), title='Facing'),
                    tooltip=['Quarter:N', 'Facing:N', 'Count:Q']
                )
                lbl_qf = alt.Chart(q_face_count).mark_text(
                    dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    x=alt.X('Quarter:N', sort=ordered_quarters),
                    xOffset='Facing:N',
                    y='Count:Q',
                    text='Count:Q'
                )
    
                st.altair_chart(
                    (bar_qf + lbl_qf).properties(
                        title=alt.TitleParams("Quarter-wise × Facing-wise Booking Count", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=320, width=alt.Step(110)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
        # ============================================================
        # MONTHLY DATA
        # ============================================================
        section_heading_card("Monthly Data")
    
        st.markdown("<div class='section-subtitle'>📅 Month-wise Bookings</div>", unsafe_allow_html=True)
        month_chart_data = pd.DataFrame({'Month': month_wise.index, 'Count': month_wise.values})
        month_bar = alt.Chart(month_chart_data).mark_bar(color="#9333ea").encode(
            x=alt.X('Month:N', sort=ordered_months, title='Month',
                    axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
            y=alt.Y('Count:Q', title='Bookings'),
            tooltip=['Month', 'Count']
        )
        month_text = alt.Chart(month_chart_data).mark_text(
            align='center', baseline='bottom', dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
        ).encode(
            x=alt.X('Month:N', sort=ordered_months),
            y='Count:Q',
            text='Count:Q'
        )
        st.altair_chart(
            (month_bar + month_text).properties(
                title=alt.TitleParams("Month-wise Bookings", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                height=260, width=alt.Step(70)
            ).configure_title(anchor='start'),
            use_container_width=True
        )
    
        st.markdown("<div class='section-subtitle'>📈 Month-wise Avg Rate (₹/sqft)</div>", unsafe_allow_html=True)
        if not df.empty:
            monthly_psf = (
                df.dropna(subset=['Month'])
                  .groupby('Month')
                  .apply(lambda s: avg_psf(s))
                  .reindex(ordered_months)
                  .reset_index(name='PSF')
            ).dropna(subset=['PSF'])
    
            if not monthly_psf.empty:
                line_psf = alt.Chart(monthly_psf).mark_line(point=True).encode(
                    x=alt.X('Month:N', sort=ordered_months, title='Month',
                            axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
                    y=alt.Y('PSF:Q', title='Avg PSF (₹/sqft)'),
                    tooltip=['Month:N', alt.Tooltip('PSF:Q', format=',.0f')]
                )
                labels_psf = alt.Chart(monthly_psf).mark_text(
                    dy=-8, fontSize=12, fontWeight='bold'
                ).encode(
                    x=alt.X('Month:N', sort=ordered_months),
                    y='PSF:Q',
                    text=alt.Text('PSF:Q', format=',.0f')
                )
    
                st.altair_chart(
                    (line_psf + labels_psf).properties(
                        title=alt.TitleParams("Month-wise Avg PSF", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=300, width=alt.Step(80)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>📅 Month-wise Carpet Area Sold (sq ft)</div>", unsafe_allow_html=True)
        MONTH_COL = "Month"
        AREA_COL = "Carpet Area"
        missing = [c for c in [MONTH_COL, AREA_COL] if c not in df.columns]
        if missing:
            st.info(f"Missing columns: {', '.join(missing)}")
        else:
            tmp = df[[MONTH_COL, AREA_COL]].copy()
            tmp[MONTH_COL] = tmp[MONTH_COL].astype(str).str.strip()
            tmp[AREA_COL] = pd.to_numeric(tmp[AREA_COL], errors="coerce")
            tmp = tmp.dropna(subset=[MONTH_COL, AREA_COL])
            tmp = tmp[tmp[MONTH_COL] != ""]
    
            if tmp.empty:
                st.info("No Month/Carpet Area data available to plot.")
            else:
                plot_df = (
                    tmp.groupby(MONTH_COL)[AREA_COL]
                       .sum()
                       .reset_index(name="CarpetAreaSold")
                )
    
                if "ordered_months" in locals() and ordered_months:
                    month_order = [m for m in ordered_months if m in set(plot_df[MONTH_COL])]
                    extras = [m for m in plot_df[MONTH_COL].unique().tolist() if m not in set(month_order)]
                    month_order = month_order + extras
                else:
                    month_order = plot_df.sort_values("CarpetAreaSold", ascending=False)[MONTH_COL].tolist()
    
                plot_df[MONTH_COL] = pd.Categorical(plot_df[MONTH_COL], categories=month_order, ordered=True)
                plot_df = plot_df.sort_values(MONTH_COL)
    
                bars = alt.Chart(plot_df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
                    x=alt.X(f"{MONTH_COL}:N", sort=month_order, title="Month",
                            axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                    y=alt.Y("CarpetAreaSold:Q", title="Carpet Area Sold (sq ft)"),
                    tooltip=[
                        alt.Tooltip(f"{MONTH_COL}:N", title="Month"),
                        alt.Tooltip("CarpetAreaSold:Q", title="Carpet Area Sold (sq ft)", format=",.0f")
                    ]
                )
                labels = alt.Chart(plot_df).mark_text(
                    dy=-6, fontSize=12, fontWeight="bold", color="#0f172a"
                ).encode(
                    x=alt.X(f"{MONTH_COL}:N", sort=month_order),
                    y="CarpetAreaSold:Q",
                    text=alt.Text("CarpetAreaSold:Q", format=",.0f")
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Month-wise Carpet Area Sold", anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                        height=300, width=alt.Step(80)
                    ).configure_title(anchor="start"),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>📈 1 BHK & 2 BHK — Month-wise Avg PSF</div>", unsafe_allow_html=True)
        if {'Month', 'Type', 'Carpet Area', 'Agreement Cost'}.issubset(df.columns):
            month_order_local = [m for m in ordered_months if m in df['Month'].unique().tolist()]
            df_m = df.dropna(subset=['Month']).copy()
            df_m['Month'] = pd.Categorical(df_m['Month'], categories=month_order_local, ordered=True)
            tnorm = df_m['Type'].astype(str).str.strip().str.upper()
    
            def _type_month_psf_chart(type_code: str, title: str):
                sub = df_m[tnorm.eq(type_code)].copy()
                if sub.empty:
                    st.info(f"No data for {title}.")
                    return
    
                psf_month = (
                    sub.groupby('Month')
                       .apply(avg_psf)
                       .rename('PSF')
                       .reset_index()
                )
                if psf_month.empty:
                    st.info(f"No data for {title}.")
                    return
    
                base = alt.Chart(psf_month).properties(
                    height=300,
                    width='container',
                    title=alt.TitleParams(title, anchor='start')
                )
                line = base.mark_line(point=True).encode(
                    x=alt.X('Month:N', sort=month_order_local, title='Month',
                            axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                    y=alt.Y('PSF:Q', title='Avg PSF (₹/sqft)'),
                    tooltip=[
                        alt.Tooltip('Month:N', title='Month'),
                        alt.Tooltip('PSF:Q', title='Avg PSF', format=',.0f')
                    ]
                )
                labels = base.mark_text(
                    dy=-8, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    x=alt.X('Month:N', sort=month_order_local),
                    y='PSF:Q',
                    text=alt.Text('PSF:Q', format=',.0f')
                )
                st.altair_chart((line + labels).configure_title(anchor='start'), use_container_width=True)
    
            _type_month_psf_chart('1BHK', "1 BHK — Month-wise Avg PSF")
            _type_month_psf_chart('2BHK', "2 BHK — Month-wise Avg PSF")
        else:
            st.info("Missing columns for monthwise PSF graphs (need Month, Type, Carpet Area, Agreement Cost).")
    
        # ============================================================
        # WING DATA
        # ============================================================
        section_heading_card("Wing Data")
    
        st.markdown("<div class='section-subtitle'>🏢 Wing-wise Avg PSF by Quarter</div>", unsafe_allow_html=True)
        if {'Wing', 'Quarter'}.issubset(df.columns):
            qw_psf = (
                df.dropna(subset=['Quarter', 'Wing'])
                  .groupby(['Quarter', 'Wing'])
                  .apply(lambda s: avg_psf(s))
                  .reset_index(name='PSF')
            )
            if not qw_psf.empty:
                qw_psf['Quarter'] = pd.Categorical(qw_psf['Quarter'], categories=ordered_quarters, ordered=True)
                for w in sorted(qw_psf['Wing'].dropna().unique()):
                    subw = qw_psf[qw_psf['Wing'] == w]
                    bar_wing = alt.Chart(subw).mark_bar().encode(
                        x=alt.X('Quarter:N', sort=ordered_quarters, title='Quarter',
                                axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                        y=alt.Y('PSF:Q', title='Avg PSF (₹/sqft)'),
                        tooltip=['Quarter:N', alt.Tooltip('PSF:Q', format=',.0f')]
                    )
                    lab_wing = alt.Chart(subw).mark_text(
                        dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(
                        x=alt.X('Quarter:N', sort=ordered_quarters),
                        y='PSF:Q',
                        text=alt.Text('PSF:Q', format=',.0f')
                    )
                    st.altair_chart(
                        (bar_wing + lab_wing).properties(
                            title=alt.TitleParams(f"Wing {w} — Avg PSF by Quarter", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                            height=280, width=alt.Step(110)
                        ).configure_title(anchor='start'),
                        use_container_width=True
                    )
    
        st.markdown("<div class='section-subtitle'>🏢 Wing-wise Carpet Area Sold (sq ft)</div>", unsafe_allow_html=True)
        WING_COL = "Wing"
        AREA_COL = "Carpet Area"
        missing = [c for c in [WING_COL, AREA_COL] if c not in df.columns]
        if missing:
            st.info(f"Missing columns: {', '.join(missing)}")
        else:
            tmp = df[[WING_COL, AREA_COL]].copy()
            tmp[WING_COL] = tmp[WING_COL].astype(str).str.strip()
            tmp[AREA_COL] = pd.to_numeric(tmp[AREA_COL], errors="coerce")
            tmp = tmp.dropna(subset=[WING_COL, AREA_COL])
            tmp = tmp[tmp[WING_COL] != ""]
    
            if tmp.empty:
                st.info("No Wing/Carpet Area data available to plot.")
            else:
                plot_df = tmp.groupby(WING_COL)[AREA_COL].sum().reset_index(name="CarpetAreaSold")
                wing_order = plot_df.sort_values("CarpetAreaSold", ascending=False)[WING_COL].tolist()
    
                plot_df[WING_COL] = pd.Categorical(plot_df[WING_COL], categories=wing_order, ordered=True)
                plot_df = plot_df.sort_values(WING_COL)
    
                bars = alt.Chart(plot_df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
                    x=alt.X(f"{WING_COL}:N", sort=wing_order, title="Wing",
                            axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                    y=alt.Y("CarpetAreaSold:Q", title="Carpet Area Sold (sq ft)"),
                    tooltip=[
                        alt.Tooltip(f"{WING_COL}:N", title="Wing"),
                        alt.Tooltip("CarpetAreaSold:Q", title="Carpet Area Sold (sq ft)", format=",.0f")
                    ]
                )
                labels = alt.Chart(plot_df).mark_text(
                    dy=-6, fontSize=12, fontWeight="bold", color="#0f172a"
                ).encode(
                    x=alt.X(f"{WING_COL}:N", sort=wing_order),
                    y="CarpetAreaSold:Q",
                    text=alt.Text("CarpetAreaSold:Q", format=",.0f")
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Wing-wise Carpet Area Sold", anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                        height=300, width=alt.Step(90)
                    ).configure_title(anchor="start"),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>🏢 Wing-wise Bookings by Lead Type</div>", unsafe_allow_html=True)
        WING_COL = "Wing"
        LEAD_COL = "Lead Type"
        missing = [c for c in [WING_COL, LEAD_COL] if c not in df.columns]
        if missing:
            st.info(f"Missing columns: {', '.join(missing)}")
        else:
            tmp = df[[WING_COL, LEAD_COL]].copy()
            tmp[WING_COL] = tmp[WING_COL].astype(str).str.strip()
            tmp[LEAD_COL] = tmp[LEAD_COL].astype(str).str.strip()
            tmp = tmp[(tmp[WING_COL] != "") & (tmp[LEAD_COL] != "")]
    
            if tmp.empty:
                st.info("No Wing/Lead Type data available to plot.")
            else:
                plot_df = (
                    tmp.groupby([WING_COL, LEAD_COL])
                       .size()
                       .reset_index(name="Bookings")
                )
    
                wing_order = sorted(plot_df[WING_COL].unique().tolist())
                lead_order = (
                    plot_df.groupby(LEAD_COL)["Bookings"]
                           .sum()
                           .sort_values(ascending=False)
                           .index.tolist()
                )
    
                plot_df[WING_COL] = pd.Categorical(plot_df[WING_COL], categories=wing_order, ordered=True)
                plot_df[LEAD_COL] = pd.Categorical(plot_df[LEAD_COL], categories=lead_order, ordered=True)
                plot_df = plot_df.sort_values([WING_COL, LEAD_COL])
    
                n_leads = max(1, len(lead_order))
                BAR_SIZE = 9 if n_leads >= 10 else (11 if n_leads >= 6 else 14)
                GROUP_GAP = 0.25
                SUB_GAP = 0.20 if n_leads >= 8 else 0.15
                GROUP_STEP = max(120, int(n_leads * (BAR_SIZE + 7) + 70))
    
                bars = alt.Chart(plot_df).mark_bar(
                    size=BAR_SIZE,
                    cornerRadiusTopLeft=2,
                    cornerRadiusTopRight=2
                ).encode(
                    x=alt.X(f"{WING_COL}:N",
                            sort=wing_order,
                            title="Wing",
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                            axis=alt.Axis(labelAngle=0, labelLimit=200, labelOverlap=True)),
                    xOffset=alt.X(f"{LEAD_COL}:N",
                                  sort=lead_order,
                                  title=None,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y=alt.Y("Bookings:Q", title="Bookings"),
                    color=alt.Color(f"{LEAD_COL}:N",
                                    sort=lead_order,
                                    title="Lead Type",
                                    legend=alt.Legend(orient="top", direction="horizontal", columns=min(6, n_leads))),
                    tooltip=[
                        alt.Tooltip(f"{WING_COL}:N", title="Wing"),
                        alt.Tooltip(f"{LEAD_COL}:N", title="Lead Type"),
                        alt.Tooltip("Bookings:Q", title="Bookings")
                    ]
                )
    
                labels = alt.Chart(plot_df).mark_text(
                    dy=-5, fontSize=11, fontWeight="bold", color="#0f172a"
                ).encode(
                    x=alt.X(f"{WING_COL}:N", sort=wing_order,
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                    xOffset=alt.X(f"{LEAD_COL}:N", sort=lead_order,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y="Bookings:Q",
                    text=alt.Text("Bookings:Q", format=".0f")
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Wing-wise Bookings by Lead Type (Grouped Bars)",
                                              anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                        height=360,
                        width=alt.Step(GROUP_STEP)
                    ).configure_title(anchor="start"),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>🏢 Sales Executive-wise Bookings by Wing (Stacked by Type)</div>", unsafe_allow_html=True)
        SE_COL = "Sales Executive"
        WING_COL = "Wing"
        TYPE_COL = "Type"
        missing = [c for c in [SE_COL, WING_COL, TYPE_COL] if c not in df.columns]
        if missing:
            st.info(f"Missing columns: {', '.join(missing)}")
        else:
            tmp = df[[SE_COL, WING_COL, TYPE_COL]].copy()
            tmp[SE_COL] = tmp[SE_COL].astype(str).str.strip()
            tmp[WING_COL] = tmp[WING_COL].astype(str).str.strip()
            tmp[TYPE_COL] = tmp[TYPE_COL].astype(str).str.strip().str.upper()
            tmp = tmp[(tmp[SE_COL] != "") & (tmp[WING_COL] != "") & (tmp[TYPE_COL] != "")]
    
            if tmp.empty:
                st.info("No Sales Executive / Wing / Type data available to plot.")
            else:
                plot_df = (
                    tmp.groupby([SE_COL, WING_COL, TYPE_COL])
                       .size()
                       .reset_index(name="Bookings")
                )
    
                se_order = (
                    plot_df.groupby(SE_COL)["Bookings"]
                           .sum()
                           .sort_values(ascending=False)
                           .index.tolist()
                )
                wing_order = sorted(plot_df[WING_COL].unique().tolist())
                type_order = (
                    plot_df.groupby(TYPE_COL)["Bookings"]
                           .sum()
                           .sort_values(ascending=False)
                           .index.tolist()
                )
    
                plot_df[SE_COL] = pd.Categorical(plot_df[SE_COL], categories=se_order, ordered=True)
                plot_df[WING_COL] = pd.Categorical(plot_df[WING_COL], categories=wing_order, ordered=True)
                plot_df[TYPE_COL] = pd.Categorical(plot_df[TYPE_COL], categories=type_order, ordered=True)
                plot_df = plot_df.sort_values([SE_COL, WING_COL, TYPE_COL])
    
                totals = (
                    plot_df.groupby([SE_COL, WING_COL], observed=True)["Bookings"]
                           .sum()
                           .reset_index(name="Total")
                )
    
                n_wings = max(1, len(wing_order))
                BAR_SIZE = 10 if n_wings >= 6 else 14
                GROUP_GAP = 0.25
                SUB_GAP = 0.18 if n_wings >= 6 else 0.14
                GROUP_STEP = max(150, int(n_wings * (BAR_SIZE + 12) + 110))
    
                bars = alt.Chart(plot_df).mark_bar(
                    size=BAR_SIZE, cornerRadiusTopLeft=2, cornerRadiusTopRight=2
                ).encode(
                    x=alt.X(f"{SE_COL}:N", sort=se_order, title="Sales Executive",
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                            axis=alt.Axis(labelAngle=0, labelLimit=220, labelOverlap=True)),
                    xOffset=alt.X(f"{WING_COL}:N", sort=wing_order, title=None,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y=alt.Y("Bookings:Q", title="Bookings", stack="zero"),
                    color=alt.Color(f"{TYPE_COL}:N", sort=type_order, title="Type",
                                    legend=alt.Legend(orient="top", direction="horizontal", columns=min(6, len(type_order)))),
                    tooltip=[
                        alt.Tooltip(f"{SE_COL}:N", title="Sales Executive"),
                        alt.Tooltip(f"{WING_COL}:N", title="Wing"),
                        alt.Tooltip(f"{TYPE_COL}:N", title="Type"),
                        alt.Tooltip("Bookings:Q", title="Bookings")
                    ]
                )
    
                total_labels = alt.Chart(totals).mark_text(
                    dy=-6, fontSize=11, fontWeight="bold", color="#0f172a"
                ).encode(
                    x=alt.X(f"{SE_COL}:N", sort=se_order,
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                    xOffset=alt.X(f"{WING_COL}:N", sort=wing_order,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y=alt.Y("Total:Q"),
                    text=alt.Text("Total:Q", format=".0f")
                )
    
                st.altair_chart(
                    (bars + total_labels).properties(
                        title=alt.TitleParams("Sales Executive-wise Bookings by Wing (Stacked by Type)",
                                              anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                        height=420,
                        width=alt.Step(GROUP_STEP)
                    ).configure_title(anchor="start"),
                    use_container_width=True
                )
    
        # ============================================================
        # SALES EXECUTIVE DATA
        # ============================================================
        section_heading_card("Sales Executive Data")
    
        st.markdown("<div class='section-subtitle'>👨‍💼 Sales Executive-wise Bookings</div>", unsafe_allow_html=True)
        exec_chart_data = pd.DataFrame({'Executive': sales_exec_wise.index, 'Count': sales_exec_wise.values})
        exec_bar = alt.Chart(exec_chart_data).mark_bar(color="#10b981").encode(
            x=alt.X('Executive:N', title='Sales Executive',
                    axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
            y=alt.Y('Count:Q', title='Bookings'),
            tooltip=['Executive', 'Count']
        )
        exec_text = alt.Chart(exec_chart_data).mark_text(
            align='center', baseline='bottom', dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
        ).encode(
            x='Executive:N',
            y='Count:Q',
            text='Count:Q'
        )
        st.altair_chart(
            (exec_bar + exec_text).properties(
                title=alt.TitleParams("Sales Executive-wise Bookings", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                height=260, width=alt.Step(60)
            ).configure_title(anchor='start'),
            use_container_width=True
        )
    
        st.markdown("<div class='section-subtitle'>🧑‍💼 Sales Executive — Monthly Booking Count</div>", unsafe_allow_html=True)
        if 'Sales Executive' in df.columns and not df.empty:
            se_month = (
                df.dropna(subset=['Month', 'Sales Executive'])
                  .groupby(['Month', 'Sales Executive'])
                  .size()
                  .reset_index(name='Bookings')
            )
            se_month = se_month[se_month['Bookings'] > 0]
    
            if not se_month.empty:
                exec_order = list(df['Sales Executive'].value_counts().index)
                month_domain = [m for m in ordered_months if m in set(se_month['Month'])]
    
                se_month['Month'] = pd.Categorical(se_month['Month'], categories=month_domain, ordered=True)
                se_month['Sales Executive'] = pd.Categorical(se_month['Sales Executive'], categories=exec_order, ordered=True)
    
                n_months = max(1, len(month_domain))
                BAR_SIZE = 9 if n_months >= 7 else (11 if n_months >= 5 else 14)
                GROUP_GAP = 0.30
                SUB_GAP = 0.25 if n_months >= 6 else 0.20
                GROUP_STEP = max(130, int(n_months * (BAR_SIZE + 8) + 70))
    
                bars = alt.Chart(se_month).mark_bar(
                    size=BAR_SIZE,
                    cornerRadiusTopLeft=2,
                    cornerRadiusTopRight=2
                ).encode(
                    x=alt.X('Sales Executive:N',
                            sort=exec_order,
                            title='Sales Executive',
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                            axis=alt.Axis(labelAngle=0, labelLimit=240, labelOverlap=True)),
                    xOffset=alt.X('Month:N',
                                  sort=month_domain,
                                  title=None,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y=alt.Y('Bookings:Q', title='Bookings'),
                    color=alt.Color('Month:N',
                                    sort=month_domain,
                                    title='Month',
                                    legend=alt.Legend(orient='top', direction='horizontal', columns=min(6, n_months))),
                    tooltip=['Sales Executive:N', 'Month:N', 'Bookings:Q']
                )
    
                labels = alt.Chart(se_month).mark_text(
                    fontSize=11, fontWeight='bold',
                    baseline='bottom', dy=-4, align='center',
                    color='black'
                ).encode(
                    x=alt.X('Sales Executive:N',
                            sort=exec_order,
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                    xOffset=alt.X('Month:N',
                                  sort=month_domain,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y='Bookings:Q',
                    text=alt.Text('Bookings:Q', format='.0f')
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Sales Executive — Monthly Bookings (Grouped Bars)",
                                              anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=380,
                        width=alt.Step(GROUP_STEP)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>👤 Avg Bookings per Month — Sales Executive</div>", unsafe_allow_html=True)
        needed_cols_se = {'Sales Executive', 'MonthYear'}
        missing_cols_se = [c for c in needed_cols_se if c not in df.columns]
        if missing_cols_se:
            st.warning(f"Missing columns for SE avg bookings per month: {', '.join(missing_cols_se)}")
        else:
            dfx = df.dropna(subset=['Sales Executive', 'MonthYear']).copy()
            st.caption(f"SE avg/month diagnostics → unique SE: {dfx['Sales Executive'].nunique()}, unique months: {dfx['MonthYear'].nunique()}, rows: {len(dfx)}")
    
            if dfx.empty:
                st.info("No monthwise data (after dropping blanks) to compute averages.")
            else:
                se_month = (
                    dfx.groupby(['Sales Executive', 'MonthYear'], observed=True)
                       .size()
                       .rename('Bookings')
                       .reset_index()
                )
    
                if se_month.empty:
                    st.info("No per-month booking counts available to average.")
                else:
                    se_avg = (
                        se_month.groupby('Sales Executive', observed=True)['Bookings']
                                .mean()
                                .reset_index(name='AvgBookingsPerMonth')
                    )
    
                    if se_avg['AvgBookingsPerMonth'].sum() == 0:
                        st.info("All SE monthly averages are 0. Showing zero bars for reference.")
    
                    se_avg = se_avg.sort_values('AvgBookingsPerMonth', ascending=True)
    
                    base = alt.Chart(se_avg)
                    bars = base.mark_bar(color="#10b981").encode(
                        y=alt.Y('Sales Executive:N', sort=se_avg['Sales Executive'].tolist(), title='Sales Executive'),
                        x=alt.X('AvgBookingsPerMonth:Q', title='Avg Bookings / Month', axis=alt.Axis(format='.2f')),
                        tooltip=[
                            alt.Tooltip('Sales Executive:N', title='Sales Executive'),
                            alt.Tooltip('AvgBookingsPerMonth:Q', title='Avg / Month', format='.2f')
                        ]
                    )
                    labels = base.mark_text(
                        align='left', baseline='middle', dx=4, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(
                        y=alt.Y('Sales Executive:N', sort=se_avg['Sales Executive'].tolist()),
                        x='AvgBookingsPerMonth:Q',
                        text=alt.Text('AvgBookingsPerMonth:Q', format='.2f')
                    )
    
                    st.altair_chart(
                        (bars + labels).properties(
                            title=alt.TitleParams("Avg Bookings per Month — Sales Executive", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                            height=max(240, 24 * len(se_avg)),
                            width='container'
                        ).configure_axis(
                            labelLimit=220, labelOverlap=True
                        ).configure_title(anchor='start'),
                        use_container_width=True
                    )
    
        st.markdown("<div class='section-subtitle'>⏱️ Sales Executive-wise Overall Average Conversion Period</div>", unsafe_allow_html=True)
        if 'Conversion Period (days)' in df.columns:
            conv_tmp = df.copy()
            conv_tmp['ConvDays'] = pd.to_numeric(conv_tmp['Conversion Period (days)'], errors='coerce')
            conv_tmp = conv_tmp.dropna(subset=['ConvDays', 'Sales Executive'])
    
            if not conv_tmp.empty:
                conv_exec = (
                    conv_tmp.groupby('Sales Executive', dropna=True)['ConvDays']
                            .mean()
                            .reset_index(name='AvgConv')
                )
    
                line = alt.Chart(conv_exec).mark_line(point=True).encode(
                    x=alt.X('Sales Executive:N', title='Sales Executive',
                            axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
                    y=alt.Y('AvgConv:Q', title='Avg Conversion Period (days)'),
                    tooltip=[
                        alt.Tooltip('Sales Executive:N', title='Sales Executive'),
                        alt.Tooltip('AvgConv:Q', title='Avg Days', format=',.1f')
                    ]
                )
                labels = alt.Chart(conv_exec).mark_text(
                    dy=-10, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    x=alt.X('Sales Executive:N'),
                    y=alt.Y('AvgConv:Q'),
                    text=alt.Text('AvgConv:Q', format=',.1f')
                )
    
                st.altair_chart(
                    (line + labels).properties(height=320).configure_title(anchor='start'),
                    use_container_width=True
                )
            else:
                st.info("No conversion-period data available to chart.")
        else:
            st.info("Column 'Conversion Period (days)' not found.")
    
        st.markdown("<div class='section-subtitle'>🧑‍💼 Sales Executive-wise Bookings by Lead Type</div>", unsafe_allow_html=True)
        SE_COL = "Sales Executive"
        LEAD_COL = "Lead Type"
        missing = [c for c in [SE_COL, LEAD_COL] if c not in df.columns]
        if missing:
            st.info(f"Missing columns: {', '.join(missing)}")
        else:
            tmp = df[[SE_COL, LEAD_COL]].copy()
            tmp[SE_COL] = tmp[SE_COL].astype(str).str.strip()
            tmp[LEAD_COL] = tmp[LEAD_COL].astype(str).str.strip()
            tmp = tmp[(tmp[SE_COL] != "") & (tmp[LEAD_COL] != "")]
    
            if tmp.empty:
                st.info("No Sales Executive / Lead Type data available to plot.")
            else:
                plot_df = (
                    tmp.groupby([SE_COL, LEAD_COL])
                       .size()
                       .reset_index(name="Bookings")
                )
    
                se_order = (
                    plot_df.groupby(SE_COL)["Bookings"]
                           .sum()
                           .sort_values(ascending=False)
                           .index.tolist()
                )
                lead_order = (
                    plot_df.groupby(LEAD_COL)["Bookings"]
                           .sum()
                           .sort_values(ascending=False)
                           .index.tolist()
                )
    
                plot_df[SE_COL] = pd.Categorical(plot_df[SE_COL], categories=se_order, ordered=True)
                plot_df[LEAD_COL] = pd.Categorical(plot_df[LEAD_COL], categories=lead_order, ordered=True)
                plot_df = plot_df.sort_values([SE_COL, LEAD_COL])
    
                n_types = max(1, len(lead_order))
                BAR_SIZE = 9 if n_types >= 10 else (11 if n_types >= 6 else 14)
                GROUP_GAP = 0.25
                SUB_GAP = 0.20 if n_types >= 8 else 0.15
                GROUP_STEP = max(140, int(n_types * (BAR_SIZE + 7) + 90))
    
                bars = alt.Chart(plot_df).mark_bar(
                    size=BAR_SIZE, cornerRadiusTopLeft=2, cornerRadiusTopRight=2
                ).encode(
                    x=alt.X(f"{SE_COL}:N",
                            sort=se_order,
                            title="Sales Executive",
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                            axis=alt.Axis(labelAngle=0, labelLimit=220, labelOverlap=True)),
                    xOffset=alt.X(f"{LEAD_COL}:N",
                                  sort=lead_order,
                                  title=None,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y=alt.Y("Bookings:Q", title="Bookings"),
                    color=alt.Color(f"{LEAD_COL}:N",
                                    sort=lead_order,
                                    title="Lead Type",
                                    legend=alt.Legend(orient="top", direction="horizontal", columns=min(6, n_types))),
                    tooltip=[
                        alt.Tooltip(f"{SE_COL}:N", title="Sales Executive"),
                        alt.Tooltip(f"{LEAD_COL}:N", title="Lead Type"),
                        alt.Tooltip("Bookings:Q", title="Bookings")
                    ]
                )
    
                labels = alt.Chart(plot_df).mark_text(
                    dy=-5, fontSize=11, fontWeight="bold", color="#0f172a"
                ).encode(
                    x=alt.X(f"{SE_COL}:N", sort=se_order,
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                    xOffset=alt.X(f"{LEAD_COL}:N", sort=lead_order,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y="Bookings:Q",
                    text=alt.Text("Bookings:Q", format=".0f")
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Sales Executive-wise Bookings by Lead Type (Grouped Bars)",
                                              anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                        height=380,
                        width=alt.Step(GROUP_STEP)
                    ).configure_title(anchor="start"),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>🧑‍💼 Sales Executive-wise Bookings by Visit Count</div>", unsafe_allow_html=True)
        SE_COL = "Sales Executive"
        VISIT_COL = "Visit Count"
        missing = [c for c in [SE_COL, VISIT_COL] if c not in df.columns]
        if missing:
            st.info(f"Missing columns: {', '.join(missing)}")
        else:
            tmp = df[[SE_COL, VISIT_COL]].copy()
            tmp[SE_COL] = tmp[SE_COL].astype(str).str.strip()
            tmp[VISIT_COL] = pd.to_numeric(tmp[VISIT_COL], errors="coerce")
            tmp = tmp[(tmp[SE_COL] != "") & tmp[VISIT_COL].notna()]
            tmp = tmp[tmp[VISIT_COL] > 0]
    
            if tmp.empty:
                st.info("No valid Sales Executive / Visit Count data available to plot.")
            else:
                tmp["VisitBucket"] = tmp[VISIT_COL].round(0).astype(int)
                plot_df = (
                    tmp.groupby([SE_COL, "VisitBucket"])
                       .size()
                       .reset_index(name="Bookings")
                )
    
                se_order = (
                    plot_df.groupby(SE_COL)["Bookings"]
                           .sum()
                           .sort_values(ascending=False)
                           .index.tolist()
                )
                visit_order = sorted(plot_df["VisitBucket"].unique().tolist())
    
                plot_df[SE_COL] = pd.Categorical(plot_df[SE_COL], categories=se_order, ordered=True)
                plot_df["VisitBucket"] = pd.Categorical(plot_df["VisitBucket"], categories=visit_order, ordered=True)
                plot_df = plot_df.sort_values([SE_COL, "VisitBucket"])
    
                n_visits = max(1, len(visit_order))
                BAR_SIZE = 9 if n_visits >= 10 else (11 if n_visits >= 6 else 14)
                GROUP_GAP = 0.25
                SUB_GAP = 0.20 if n_visits >= 8 else 0.15
                GROUP_STEP = max(140, int(n_visits * (BAR_SIZE + 7) + 90))
    
                bars = alt.Chart(plot_df).mark_bar(
                    size=BAR_SIZE, cornerRadiusTopLeft=2, cornerRadiusTopRight=2
                ).encode(
                    x=alt.X(f"{SE_COL}:N",
                            sort=se_order,
                            title="Sales Executive",
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                            axis=alt.Axis(labelAngle=0, labelLimit=220, labelOverlap=True)),
                    xOffset=alt.X("VisitBucket:N",
                                  sort=visit_order,
                                  title=None,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y=alt.Y("Bookings:Q", title="Bookings"),
                    color=alt.Color("VisitBucket:N",
                                    sort=visit_order,
                                    title="Visit Count",
                                    legend=alt.Legend(orient="top", direction="horizontal", columns=min(10, n_visits))),
                    tooltip=[
                        alt.Tooltip(f"{SE_COL}:N", title="Sales Executive"),
                        alt.Tooltip("VisitBucket:N", title="Visit Count"),
                        alt.Tooltip("Bookings:Q", title="Bookings")
                    ]
                )
    
                labels = alt.Chart(plot_df).mark_text(
                    dy=-5, fontSize=11, fontWeight="bold", color="#0f172a"
                ).encode(
                    x=alt.X(f"{SE_COL}:N", sort=se_order,
                            scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                    xOffset=alt.X("VisitBucket:N", sort=visit_order,
                                  scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                    y="Bookings:Q",
                    text=alt.Text("Bookings:Q", format=".0f")
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Sales Executive-wise Bookings by Visit Count (Grouped Bars)",
                                              anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                        height=400,
                        width=alt.Step(GROUP_STEP)
                    ).configure_title(anchor="start"),
                    use_container_width=True
                )
    
        # ============================================================
        # LEAD / CONVERSION / VISIT / LOCATION / TYPE DATA
        # ============================================================
        section_heading_card("Lead, Conversion, Visit & Location Data")
    
        st.markdown("<div class='section-subtitle'>🏠 Type-wise Bookings</div>", unsafe_allow_html=True)
        type_chart_data = pd.DataFrame({'Type': type_wise.index, 'Count': type_wise.values})
        type_bar = alt.Chart(type_chart_data).mark_bar(color="#f59e0b").encode(
            x=alt.X('Type:N', title='Type', axis=alt.Axis(labelAngle=0, labelLimit=140, labelOverlap=True)),
            y=alt.Y('Count:Q', title='Bookings'),
            tooltip=['Type', 'Count']
        )
        type_text = alt.Chart(type_chart_data).mark_text(
            align='center', baseline='bottom', dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
        ).encode(
            x='Type:N',
            y='Count:Q',
            text='Count:Q'
        )
        st.altair_chart(
            (type_bar + type_text).properties(
                title=alt.TitleParams("Type-wise Bookings", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                height=260, width=alt.Step(90)
            ).configure_title(anchor='start'),
            use_container_width=True
        )
    
        st.markdown("<div class='section-subtitle'>🧭 Bookings by Lead Type</div>", unsafe_allow_html=True)
        LEAD_COL = "Lead Type"
        if LEAD_COL not in df.columns:
            st.info(f"Column '{LEAD_COL}' not found.")
        else:
            lead_series = (
                df[LEAD_COL]
                .astype(str).str.strip()
                .replace({'': None})
                .dropna()
            )
            if lead_series.empty:
                st.info("No Lead Type data available.")
            else:
                vc = lead_series.value_counts()
                lead_df = pd.DataFrame({"Lead Type": vc.index, "Bookings": vc.values})
                lead_df = lead_df.sort_values('Bookings', ascending=True)
    
                base = alt.Chart(lead_df)
                bars = base.mark_bar(color="#2563eb").encode(
                    y=alt.Y('Lead Type:N', sort=lead_df['Lead Type'].tolist(), title='Lead Type'),
                    x=alt.X('Bookings:Q', title='Bookings'),
                    tooltip=['Lead Type:N', 'Bookings:Q']
                )
                labels = base.mark_text(
                    align='left', baseline='middle', dx=4, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    y=alt.Y('Lead Type:N', sort=lead_df['Lead Type'].tolist()),
                    x='Bookings:Q',
                    text='Bookings:Q'
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Bookings by Lead Type", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=max(220, 24 * len(lead_df)),
                        width='container'
                    ).configure_axis(
                        labelLimit=220, labelOverlap=True
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>⏱️ Bookings by Conversion Period (Spot & 2-month buckets)</div>", unsafe_allow_html=True)
        CONV_COL = "Conversion Period (days)"
        if CONV_COL not in df.columns:
            st.info(f"Column '{CONV_COL}' not found.")
        else:
            conv_all = pd.to_numeric(df[CONV_COL], errors='coerce')
            conv_all = conv_all[conv_all.notna() & (conv_all >= 0)]
            if conv_all.empty:
                st.info("No valid conversion-day values to compute buckets.")
            else:
                BUCKET_DAYS = 60
                spot_count = int((conv_all == 0).sum())
                nonzero = conv_all[conv_all >= 1]
    
                if len(nonzero) > 0:
                    bidx = ((nonzero - 1) // BUCKET_DAYS).astype(int)
                    max_idx = int(bidx.max())
                    all_idx = list(range(0, max_idx + 1))
    
                    def label_for(i: int) -> str:
                        start = 2 * i
                        end = 2 * (i + 1)
                        return f"{start}–{end} months"
    
                    bucket_counts = (
                        bidx.value_counts()
                            .reindex(all_idx, fill_value=0)
                            .rename_axis('BucketIdx')
                            .reset_index(name='Bookings')
                    )
                    bucket_counts['Bucket'] = bucket_counts['BucketIdx'].map(label_for)
                else:
                    bucket_counts = pd.DataFrame(columns=['BucketIdx', 'Bookings', 'Bucket'])
                    all_idx = []
    
                rows = [{"BucketIdx": -1, "Bucket": "Spot Booking (0 days)", "Bookings": spot_count, "Color": "Blue"}]
                for _, r in bucket_counts.iterrows():
                    color = "Blue" if int(r['BucketIdx']) == 0 else "Red"
                    rows.append({
                        "BucketIdx": int(r['BucketIdx']),
                        "Bucket": str(r['Bucket']),
                        "Bookings": int(r['Bookings']),
                        "Color": color
                    })
    
                plot_df = pd.DataFrame(rows)
                sort_order = ["Spot Booking (0 days)"] + [f"{2*i}–{2*(i+1)} months" for i in all_idx]
                color_domain = ["Blue", "Red"]
                color_range = ["#2563eb", "#ef4444"]
    
                base = alt.Chart(plot_df)
                bars = base.mark_bar().encode(
                    x=alt.X('Bucket:N', sort=sort_order, title='Conversion Period'),
                    y=alt.Y('Bookings:Q', title='Bookings'),
                    color=alt.Color('Color:N', scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
                    tooltip=[alt.Tooltip('Bucket:N', title='Interval'), alt.Tooltip('Bookings:Q', title='Bookings')]
                )
                labels = base.mark_text(
                    dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    x=alt.X('Bucket:N', sort=sort_order),
                    y='Bookings:Q',
                    text='Bookings:Q'
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams(
                            "Bookings by Conversion Period (Spot, 0–2, 2–4, 4–6 months …)",
                            anchor='start', fontSize=16, fontWeight='bold', dy=-5
                        ),
                        height=280, width=alt.Step(90)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>📈 Booking Count by Visit Count</div>", unsafe_allow_html=True)
        VISIT_COL = "Visit Count"
        if VISIT_COL not in df.columns:
            st.info(f"Column '{VISIT_COL}' not found.")
        else:
            tmp = df[[VISIT_COL]].copy()
            tmp[VISIT_COL] = pd.to_numeric(tmp[VISIT_COL], errors="coerce")
            tmp = tmp.dropna(subset=[VISIT_COL])
            tmp = tmp[tmp[VISIT_COL] > 0]
    
            if tmp.empty:
                st.info("No valid Visit Count values available to plot.")
            else:
                plot_df = (
                    tmp.groupby(VISIT_COL)
                       .size()
                       .reset_index(name="Bookings")
                       .sort_values(VISIT_COL)
                )
                plot_df["VisitInt"] = plot_df[VISIT_COL].round(0).astype(int)
                plot_df = (
                    plot_df.groupby("VisitInt")["Bookings"]
                           .sum()
                           .reset_index()
                           .rename(columns={"VisitInt": "Visit Count"})
                )
    
                line = alt.Chart(plot_df).mark_line(point=True).encode(
                    x=alt.X("Visit Count:Q", title="Visit Count", axis=alt.Axis(format="d", tickMinStep=1)),
                    y=alt.Y("Bookings:Q", title="Bookings"),
                    tooltip=[
                        alt.Tooltip("Visit Count:Q", title="Visit Count", format="d"),
                        alt.Tooltip("Bookings:Q", title="Bookings")
                    ]
                )
                labels = alt.Chart(plot_df).mark_text(
                    dy=-10, fontSize=12, fontWeight="bold", color="#0f172a"
                ).encode(
                    x="Visit Count:Q",
                    y="Bookings:Q",
                    text=alt.Text("Bookings:Q", format=".0f")
                )
    
                st.altair_chart(
                    (line + labels).properties(
                        title=alt.TitleParams("Bookings vs Visit Count", anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                        height=320
                    ).configure_title(anchor="start"),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>📍 Location-wise Bookings</div>", unsafe_allow_html=True)
        LOC_COL = "Location"
        if LOC_COL not in df.columns:
            st.info(f"Column '{LOC_COL}' not found.")
        else:
            loc_series = df[LOC_COL].astype(str).str.strip().replace({'': None}).dropna()
    
            if loc_series.empty:
                st.info("No Location data available.")
            else:
                loc_counts = loc_series.value_counts()
                loc_df = pd.DataFrame({"Location": loc_counts.index, "Bookings": loc_counts.values})
                loc_df = loc_df.sort_values("Bookings", ascending=True)
    
                base = alt.Chart(loc_df)
                bars = base.mark_bar(color="#2563eb").encode(
                    y=alt.Y('Location:N', sort=loc_df['Location'].tolist(), title='Location'),
                    x=alt.X('Bookings:Q', title='Bookings'),
                    tooltip=[alt.Tooltip('Location:N'), alt.Tooltip('Bookings:Q')]
                )
                labels = base.mark_text(
                    align='left', baseline='middle', dx=4, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    y=alt.Y('Location:N', sort=loc_df['Location'].tolist()),
                    x='Bookings:Q',
                    text=alt.Text('Bookings:Q', format='.0f')
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Location-wise Booking Count", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=max(240, 24 * len(loc_df)),
                        width='container'
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
        st.markdown("<div class='section-subtitle'>⏳ Time Taken per 50 Bookings</div>", unsafe_allow_html=True)
        DATE_COL = "Date"
        BATCH_SIZE = 50
        if DATE_COL not in df.columns:
            st.info(f"Column '{DATE_COL}' not found.")
        else:
            tmp = df[[DATE_COL]].copy()
            tmp[DATE_COL] = pd.to_datetime(tmp[DATE_COL], errors="coerce")
            tmp = tmp.dropna(subset=[DATE_COL]).sort_values(DATE_COL).reset_index(drop=True)
    
            if tmp.empty:
                st.info("No valid Date values available to compute duration.")
            else:
                tmp["BookingNo"] = tmp.index + 1
                tmp["BatchIdx"] = (tmp["BookingNo"] - 1) // BATCH_SIZE
    
                rows = []
                n_batches = int(tmp["BatchIdx"].max()) + 1
    
                for b in range(n_batches):
                    sub = tmp[tmp["BatchIdx"] == b]
                    if sub.empty:
                        continue
    
                    start_no = b * BATCH_SIZE
                    end_no = min((b + 1) * BATCH_SIZE, len(tmp))
                    bucket_label = f"{start_no}–{end_no}"
    
                    start_dt = sub[DATE_COL].min()
                    end_dt = sub[DATE_COL].max()
    
                    days = int((end_dt - start_dt).days) if pd.notna(start_dt) and pd.notna(end_dt) else 0
                    months = days / 30.0
    
                    rows.append({
                        "Bucket": bucket_label,
                        "Days": days,
                        "MonthsApprox": months,
                        "Label": f"{days} days ({months:.1f} mo)"
                    })
    
                plot_df = pd.DataFrame(rows)
    
                if plot_df.empty:
                    st.info("Not enough data to build 50-booking duration buckets.")
                else:
                    bucket_order = plot_df["Bucket"].tolist()
    
                    bars = alt.Chart(plot_df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
                        x=alt.X("Bucket:N", sort=bucket_order, title="Booking Range"),
                        y=alt.Y("Days:Q", title="Time Taken (days)"),
                        tooltip=[
                            alt.Tooltip("Bucket:N", title="Range"),
                            alt.Tooltip("Days:Q", title="Days"),
                            alt.Tooltip("MonthsApprox:Q", title="Approx Months", format=".1f")
                        ]
                    )
                    labels = alt.Chart(plot_df).mark_text(
                        dy=-6, fontSize=12, fontWeight="bold", color="#0f172a"
                    ).encode(
                        x=alt.X("Bucket:N", sort=bucket_order),
                        y="Days:Q",
                        text="Label:N"
                    )
    
                    st.altair_chart(
                        (bars + labels).properties(
                            title=alt.TitleParams("Time Duration per 50 Bookings", anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                            height=320,
                            width=alt.Step(90)
                        ).configure_title(anchor="start"),
                        use_container_width=True
                    )
    
        # ============================================================
        # PRICING / REVENUE / NEGOTIATION DATA
        # ============================================================
        section_heading_card("Pricing, Revenue & Agreement Data")
    
        df_bd = df.copy()
        df_bd['_NearestSizeBD'] = pd.to_numeric(df_bd.get('Carpet Area', 0), errors='coerce').apply(nearest_size)
        df_bd['_TypeForBD'] = df_bd.get('Type', '').astype(str).str.upper().str.strip()
        _bad = ~df_bd['_TypeForBD'].isin(['1BHK', '2BHK'])
        df_bd.loc[_bad, '_TypeForBD'] = df_bd.loc[_bad, '_NearestSizeBD'].map(SIZE_TYPE_MAP)
    
        if '_FinalPrice_Full' not in df_bd.columns or '_FinalPrice_L' not in df_bd.columns:
            fp_clean_all = (
                df_bd['Final Price'].astype(str)
                     .str.replace(',', '', regex=True)
                     .str.replace('₹', '', regex=False)
                     .str.replace(r'(?i)\s*(rs|inr)\.?\s*', '', regex=True)
                     .str.replace(r'(?i)\s*(lac|lacs|lakh|lakhs)\.?\s*', '', regex=True)
                     .str.strip()
            )
            df_bd['_FinalPrice_L'] = pd.to_numeric(fp_clean_all, errors='coerce')
            df_bd['_FinalPrice_Full'] = (df_bd['_FinalPrice_L'] * 100000).astype('float')
    
        st.markdown("<div class='section-subtitle'>💰 Average Closing Price — 1BHK vs 2BHK (Final Price)</div>", unsafe_allow_html=True)
        df_fp = df_bd.dropna(subset=['_FinalPrice_Full']).copy()
        avg_close_full = (
            df_fp.groupby('_TypeForBD')['_FinalPrice_Full']
                 .mean()
                 .reindex(['1BHK', '2BHK'])
        )
        avg_close_full = avg_close_full.dropna().reset_index().rename(
            columns={'_TypeForBD': 'Type', '_FinalPrice_Full': 'AvgCloseFull'}
        )
    
        if not avg_close_full.empty:
            avg_close_full['Label'] = avg_close_full['AvgCloseFull'].map(lambda v: f"₹{v:,.0f}")
            chart_avg_close = alt.Chart(avg_close_full).mark_bar().encode(
                x=alt.X('Type:N', title='Type'),
                y=alt.Y('AvgCloseFull:Q', title='Average Closing (₹)'),
                tooltip=[
                    alt.Tooltip('Type:N'),
                    alt.Tooltip('AvgCloseFull:Q', format=',.0f', title='Average Closing (₹)')
                ]
            )
            labels_avg_close = alt.Chart(avg_close_full).mark_text(
                dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
            ).encode(
                x='Type:N',
                y='AvgCloseFull:Q',
                text='Label:N'
            )
            st.altair_chart(
                (chart_avg_close + labels_avg_close).properties(height=280).configure_title(anchor='start'),
                use_container_width=True
            )
        else:
            st.info("No Final Price data to compute average closing price.")
    
        COSTSHEET_1BHK_L = 48.50
        COSTSHEET_2BHK_L = 67.50
        COSTSHEET_1BHK_FULL = COSTSHEET_1BHK_L * 100000.0
        COSTSHEET_2BHK_FULL = COSTSHEET_2BHK_L * 100000.0
    
        ef_sub = df_bd[df_bd['Wing'].isin(['E', 'F'])].copy()
        ef_sub = ef_sub.dropna(subset=['_FinalPrice_Full'])
    
        ef_sub['_Negotiated'] = ef_sub.apply(
            lambda r: (COSTSHEET_1BHK_FULL - r['_FinalPrice_Full']) if r['_TypeForBD'] == '1BHK'
            else (COSTSHEET_2BHK_FULL - r['_FinalPrice_Full']) if r['_TypeForBD'] == '2BHK'
            else float('nan'),
            axis=1
        )
    
        nego_avg = (
            ef_sub.dropna(subset=['_Negotiated'])
                  .groupby('_TypeForBD')['_Negotiated']
                  .mean()
                  .reindex(['1BHK', '2BHK'])
        )
        nego_avg = nego_avg.dropna().reset_index().rename(
            columns={'_TypeForBD': 'Type', '_Negotiated': 'AvgNegotiated'}
        )
    
        st.markdown("<div class='section-subtitle'>📉 Average Negotiated Amount — E & F (₹)</div>", unsafe_allow_html=True)
        if not nego_avg.empty:
            nego_avg['Label'] = nego_avg['AvgNegotiated'].map(lambda v: f"₹{v:,.0f}")
            chart_nego_avg = alt.Chart(nego_avg).mark_bar().encode(
                x=alt.X('Type:N', title='Type'),
                y=alt.Y('AvgNegotiated:Q', title='Average Negotiated (₹)'),
                tooltip=[
                    alt.Tooltip('Type:N'),
                    alt.Tooltip('AvgNegotiated:Q', format=',.0f', title='Average Negotiated (₹)')
                ]
            )
            labels_nego_avg = alt.Chart(nego_avg).mark_text(
                dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
            ).encode(
                x='Type:N',
                y='AvgNegotiated:Q',
                text='Label:N'
            )
            st.altair_chart(
                (chart_nego_avg + labels_nego_avg).properties(height=280).configure_title(anchor='start'),
                use_container_width=True
            )
        else:
            st.info("No E & F Final Price data to compute average negotiation.")
    
        import math
    
        def _br_low_high_lakh(v_lakh: float):
            low = math.floor(v_lakh * 2) / 2.0
            high = low + 0.50
            return low, high
    
        def _top5_by_price_brackets(df_in: pd.DataFrame, type_name: str):
            sub = df_in[(df_in['_TypeForBD'] == type_name) & df_in['_FinalPrice_L'].notna()].copy()
            if sub.empty:
                return pd.DataFrame(columns=['Bracket', 'Count', '_hi'])
    
            lows, highs, labels = [], [], []
            for v in sub['_FinalPrice_L']:
                lo, hi = _br_low_high_lakh(float(v))
                lows.append(lo)
                highs.append(hi)
                labels.append(f"{lo:.2f} - {hi:.2f}")
    
            sub['Bracket'] = labels
            sub['_hi'] = highs
    
            counts = (
                sub.groupby(['Bracket', '_hi'])
                   .size()
                   .reset_index(name='Count')
                   .sort_values(['_hi'], ascending=[False])
            )
            return counts.groupby('_hi', as_index=False).first().sort_values('_hi', ascending=False).head(5)
    
        st.markdown("<div class='section-subtitle'>📦 Highest Final-Price Brackets — 1BHK (Dynamic, Lakhs)</div>", unsafe_allow_html=True)
        top1_price = _top5_by_price_brackets(df_bd, '1BHK')
        if not top1_price.empty:
            top_br_1 = top1_price.iloc[0]
            st.markdown(
                f"<div class='chips'>"
                f"<span class='chip ok'><span class='dot'></span> Highest Bracket: {top_br_1['Bracket']}</span>"
                f"<span class='chip ok'><span class='dot'></span> Bookings: {int(top_br_1['Count'])}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            top1_price = top1_price.sort_values('_hi', ascending=False)
            c1 = alt.Chart(top1_price).mark_bar().encode(
                x=alt.X('Bracket:N', title='Final Price (Lakhs)', sort=list(top1_price['Bracket'])),
                y=alt.Y('Count:Q', title='Bookings'),
                tooltip=[
                    alt.Tooltip('Bracket:N', title='Bracket'),
                    alt.Tooltip('Count:Q', title='Count')
                ]
            )
            t1 = alt.Chart(top1_price).mark_text(
                dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
            ).encode(
                x='Bracket:N',
                y='Count:Q',
                text='Count:Q'
            )
            st.altair_chart((c1 + t1).properties(height=280).configure_title(anchor='start'),
                            use_container_width=True)
        else:
            st.info("No 1BHK Final Price data to build dynamic brackets.")
    
        st.markdown("<div class='section-subtitle'>📦 Highest Final-Price Brackets — 2BHK (Dynamic, Lakhs)</div>", unsafe_allow_html=True)
        top2_price = _top5_by_price_brackets(df_bd, '2BHK')
        if not top2_price.empty:
            top_br_2 = top2_price.iloc[0]
            st.markdown(
                f"<div class='chips'>"
                f"<span class='chip ok'><span class='dot'></span> Highest Bracket: {top_br_2['Bracket']}</span>"
                f"<span class='chip ok'><span class='dot'></span> Bookings: {int(top_br_2['Count'])}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            top2_price = top2_price.sort_values('_hi', ascending=False)
            c2 = alt.Chart(top2_price).mark_bar().encode(
                x=alt.X('Bracket:N', title='Final Price (Lakhs)', sort=list(top2_price['Bracket'])),
                y=alt.Y('Count:Q', title='Bookings'),
                tooltip=[
                    alt.Tooltip('Bracket:N', title='Bracket'),
                    alt.Tooltip('Count:Q', title='Count')
                ]
            )
            t2 = alt.Chart(top2_price).mark_text(
                dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
            ).encode(
                x='Bracket:N',
                y='Count:Q',
                text='Count:Q'
            )
            st.altair_chart((c2 + t2).properties(height=280).configure_title(anchor='start'),
                            use_container_width=True)
        else:
            st.info("No 2BHK Final Price data to build dynamic brackets.")
    
        st.markdown("<div class='section-subtitle'>📈 1BHK & 2BHK — Booking-wise Agreement Cost (First → Latest)</div>", unsafe_allow_html=True)
        df_line = df.copy()
    
        if 'Agreement Cost' not in df_line.columns:
            df_line['Agreement Cost'] = 0.0
        df_line['Agreement Cost'] = pd.to_numeric(df_line['Agreement Cost'], errors='coerce')
    
        df_line['_NearestSizeBD'] = pd.to_numeric(df_line.get('Carpet Area', 0), errors='coerce').apply(nearest_size)
        df_line['_TypeForBD'] = df_line.get('Type', '').astype(str).str.upper().str.strip()
        _bad_t = ~df_line['_TypeForBD'].isin(['1BHK', '2BHK'])
        df_line.loc[_bad_t, '_TypeForBD'] = df_line.loc[_bad_t, '_NearestSizeBD'].map(SIZE_TYPE_MAP)
        df_line = df_line.dropna(subset=['Date', 'Agreement Cost']).copy()
    
        def _booking_line_chart(sub_df: pd.DataFrame, title: str):
            if sub_df.empty:
                st.info(f"No data available for {title}.")
                return
    
            sub_df = sub_df.sort_values('Date', kind='mergesort').reset_index(drop=True)
            sub_df['Booking #'] = sub_df.index + 1
    
            tt = [
                alt.Tooltip('Booking #:Q', title='Booking #'),
                alt.Tooltip('Date:T', title='Date'),
                alt.Tooltip('Agreement Cost:Q', title='Agreement Cost (₹)', format=',.0f'),
            ]
            if 'Wing' in sub_df.columns:
                tt.append(alt.Tooltip('Wing:N', title='Wing'))
            if 'Flat Number' in sub_df.columns:
                tt.append(alt.Tooltip('Flat Number:N', title='Flat'))
    
            base = alt.Chart(sub_df)
            line = base.mark_line(point=True).encode(
                x=alt.X('Booking #:Q', title='Booking (sorted by Date)'),
                y=alt.Y('Agreement Cost:Q', title='Agreement Cost (₹)'),
                tooltip=tt
            )
    
            st.altair_chart(
                line.properties(
                    title=alt.TitleParams(title, anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                    height=320
                ).configure_title(anchor='start'),
                use_container_width=True
            )
    
        df_1 = df_line[df_line['_TypeForBD'] == '1BHK'].copy()
        _booking_line_chart(df_1, "1BHK — Booking-wise Agreement Cost")
    
        df_2 = df_line[df_line['_TypeForBD'] == '2BHK'].copy()
        _booking_line_chart(df_2, "2BHK — Booking-wise Agreement Cost")
    
        # ============================================================
        # FINAL TABLES AT END OF BOOKING DASHBOARD (WING-WISE)
        # ============================================================
        section_heading_card("Quarter-wise Wing & Sales Executive Summary Tables")
        
        st.markdown(
            "<div class='section-subtitle'>📋 Quarter-wise Wing-wise & Sales Executive-wise Agreement Cost Sold & Saleable Area Sold</div>",
            unsafe_allow_html=True
        )
        
        required_cols_tbl = {'Quarter', 'Wing', 'Sales Executive', 'Agreement Cost', 'Carpet Area'}
        missing_tbl = [c for c in required_cols_tbl if c not in df.columns]
        
        if missing_tbl:
            st.info(f"Missing columns for final table: {', '.join(missing_tbl)}")
        else:
            tbl_df = df[['Quarter', 'Wing', 'Sales Executive', 'Agreement Cost', 'Carpet Area']].copy()
        
            tbl_df['Quarter'] = tbl_df['Quarter'].astype(str).str.strip()
            tbl_df['Wing'] = tbl_df['Wing'].astype(str).str.strip()
            tbl_df['Sales Executive'] = tbl_df['Sales Executive'].astype(str).str.strip()
        
            ag_clean = (
                tbl_df['Agreement Cost'].astype(str)
                      .str.replace(',', '', regex=True)
                      .str.replace('₹', '', regex=False)
                      .str.replace(r'(?i)\s*(rs|inr)\.?\s*', '', regex=True)
                      .str.strip()
            )
            tbl_df['Agreement Cost'] = pd.to_numeric(ag_clean, errors='coerce')
            tbl_df['Carpet Area'] = pd.to_numeric(tbl_df['Carpet Area'], errors='coerce')
            tbl_df['Saleable Area Sold'] = tbl_df['Carpet Area'] * 1.38
        
            tbl_df = tbl_df[
                (tbl_df['Quarter'] != "") &
                (tbl_df['Wing'] != "") &
                (tbl_df['Sales Executive'] != "")
            ]
            tbl_df = tbl_df.dropna(subset=['Agreement Cost', 'Saleable Area Sold'])
        
            if tbl_df.empty:
                st.info("No data available for quarter-wise wing-wise sales executive-wise agreement/saleable area tables.")
            else:
                final_tbl = (
                    tbl_df.groupby(['Quarter', 'Wing', 'Sales Executive'], as_index=False)
                          .agg({
                              'Agreement Cost': 'sum',
                              'Saleable Area Sold': 'sum'
                          })
                          .rename(columns={
                              'Agreement Cost': 'Agreement Cost Sold (₹)',
                              'Saleable Area Sold': 'Saleable Area Sold (sq ft)'
                          })
                )
        
                q_domain = ordered_quarters if ordered_quarters else sorted(final_tbl['Quarter'].unique().tolist())
                wing_order = sorted(final_tbl['Wing'].unique().tolist())
        
                final_tbl['Quarter'] = pd.Categorical(final_tbl['Quarter'], categories=q_domain, ordered=True)
                final_tbl['Wing'] = pd.Categorical(final_tbl['Wing'], categories=wing_order, ordered=True)
        
                for wing in wing_order:
                    wing_tbl = final_tbl[final_tbl['Wing'] == wing].copy()
        
                    if wing_tbl.empty:
                        continue
        
                    se_order = (
                        wing_tbl.groupby('Sales Executive')['Agreement Cost Sold (₹)']
                                .sum()
                                .sort_values(ascending=False)
                                .index
                                .tolist()
                    )
        
                    wing_tbl['Sales Executive'] = pd.Categorical(
                        wing_tbl['Sales Executive'],
                        categories=se_order,
                        ordered=True
                    )
        
                    wing_tbl = wing_tbl.sort_values(['Quarter', 'Sales Executive']).reset_index(drop=True)
        
                    wing_tbl_display = wing_tbl.copy()
                    wing_tbl_display['Agreement Cost Sold (₹)'] = wing_tbl_display['Agreement Cost Sold (₹)'].map(lambda x: f"₹{x:,.0f}")
                    wing_tbl_display['Saleable Area Sold (sq ft)'] = wing_tbl_display['Saleable Area Sold (sq ft)'].map(lambda x: f"{x:,.0f}")
        
                    st.markdown(
                        f"<div class='section-subtitle'>🏢 Wing {wing}</div>",
                        unsafe_allow_html=True
                    )
                    st.dataframe(
                        wing_tbl_display[['Quarter', 'Wing', 'Sales Executive', 'Agreement Cost Sold (₹)', 'Saleable Area Sold (sq ft)']],
                        use_container_width=True,
                        hide_index=True
                    )
    # ------------------------------------------------------------
    # TAB_AGREEMENT: Agreement Done Dashboard
    # ------------------------------------------------------------
    with TAB_AGREEMENT:
        st.header("📑 Agreement Done Dashboard")
    
        # ============================================================
        # SECTION HEADING CARD STYLE
        # ============================================================
        st.markdown("""
        <style>
        .section-kpi-card {
            width: 100%;
            background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 45%, #3b82f6 100%);
            border: 1px solid rgba(37, 99, 235, 0.35);
            border-radius: 18px;
            padding: 20px 24px;
            margin: 26px 0 16px 0;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 82px;
        }
        .section-kpi-card h2 {
            margin: 0;
            font-size: 28px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 0.4px;
            text-align: center;
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)
    
        def section_heading_card(title: str):
            st.markdown(
                f"""
                <div class="section-kpi-card">
                    <h2>{title}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
    
        # ============================================================
        # Base filtered dataframe: only rows where Agreement Done = Done
        # ============================================================
        AGREE_COL = "Agreement Done"
    
        if AGREE_COL not in df.columns:
            st.warning(f"Column '{AGREE_COL}' not found. Agreement dashboard cannot be created.")
        else:
            df_ag = df.copy()
            df_ag = df_ag[
                df_ag[AGREE_COL].astype(str).str.strip().str.lower().eq("done")
            ].copy()
    
            if df_ag.empty:
                st.info("No bookings found where Agreement Done = Done.")
            else:
                # ============================================================
                # HELPERS
                # ============================================================
                def _fiscal_qidx(m: int) -> int:
                    if 4 <= m <= 6:
                        return 1
                    if 7 <= m <= 9:
                        return 2
                    if 10 <= m <= 12:
                        return 3
                    return 4
    
                def _pct(booked, total):
                    return (booked / total * 100.0) if total > 0 else 0.0
    
                def fmt_visits(x):
                    return f"{x:.2f}" if pd.notna(x) else "—"
    
                def fmt_avg_bookings(x):
                    return f"{x:.2f}" if pd.notna(x) else "—"
    
                def fmt_rate(x):
                    return f"₹{x:,.0f}/sqft" if pd.notna(x) and x > 0 else "—"
    
                def wing_pct_sold_ag(wing_code: str) -> float:
                    booked = int(booked_by_wing_counts_ag.get(wing_code, 0))
                    total = int(WING_TOTALS.get(wing_code, 0))
                    return (booked / total * 100.0) if total > 0 else 0.0
    
                # Ensure Quarter exists
                if 'Quarter' not in df_ag.columns and 'Date' in df_ag.columns:
                    df_ag['Quarter'] = df_ag['Date'].apply(get_custom_quarter_label)
    
                # Ordered quarters
                ordered_quarters_ag = []
                if {'Date', 'Quarter'}.issubset(df_ag.columns):
                    qorder_df_ag = (
                        df_ag.dropna(subset=['Date', 'Quarter'])
                             .assign(
                                 _FY=lambda d: d['Date'].dt.year - (d['Date'].dt.month < 4),
                                 _QIDX=lambda d: d['Date'].dt.month.apply(_fiscal_qidx)
                             )
                             .groupby('Quarter', as_index=False)[['_FY', '_QIDX']].median()
                    )
                    ordered_quarters_ag = (
                        qorder_df_ag.sort_values(['_FY', '_QIDX'])['Quarter'].tolist()
                        if not qorder_df_ag.empty else df_ag['Quarter'].dropna().unique().tolist()
                    )
    
                # Ordered months
                ordered_months_ag = [m for m in ordered_months if 'Month' in df_ag.columns and m in df_ag['Month'].dropna().unique().tolist()]
    
                # ============================================================
                # RECOMPUTED METRICS / BASES
                # ============================================================
                total_bookings_ag = len(df_ag)
                total_agreements_ag = total_bookings_ag
                agreement_done_count_ag = total_bookings_ag
                agreement_pending_count_ag = 0
    
                total_carpet_area_ag = pd.to_numeric(df_ag.get('Carpet Area', 0), errors='coerce').fillna(0).sum()
                total_agreement_cost_ag = sum_rev(df_ag)
    
                # Avg conversion days
                if 'Conversion Period (days)' in df_ag.columns:
                    conv_days_ag = pd.to_numeric(df_ag['Conversion Period (days)'], errors='coerce')
                    conv_days_ag = conv_days_ag[conv_days_ag.notna() & (conv_days_ag >= 0)]
                    avg_conv_days_ag = conv_days_ag.mean() if len(conv_days_ag) else float("nan")
                    avg_conv_days_display_ag = f"{avg_conv_days_ag:.1f}" if pd.notna(avg_conv_days_ag) else "—"
                else:
                    avg_conv_days_display_ag = "—"
    
                # Avg visits
                VISIT_COL = "Visit Count"
                if VISIT_COL in df_ag.columns:
                    visit_vals_ag = pd.to_numeric(df_ag[VISIT_COL], errors="coerce")
                    visit_vals_ag = visit_vals_ag[visit_vals_ag.notna() & (visit_vals_ag > 0)]
                    avg_visits_for_booking_ag = float(visit_vals_ag.mean()) if len(visit_vals_ag) else float("nan")
                else:
                    avg_visits_for_booking_ag = float("nan")
    
                # Avg bookings per month
                MONTH_KEY_AG = "MonthYear" if "MonthYear" in df_ag.columns else ("Month" if "Month" in df_ag.columns else None)
                if MONTH_KEY_AG is None or df_ag.empty:
                    avg_bookings_per_month_ag = float("nan")
                else:
                    m_ag = df_ag[MONTH_KEY_AG].astype(str).str.strip()
                    m_ag = m_ag[m_ag != ""]
                    n_months_ag = int(m_ag.nunique()) if len(m_ag) else 0
                    avg_bookings_per_month_ag = (len(m_ag) / n_months_ag) if n_months_ag > 0 else float("nan")
    
                # PSF cards
                if 'Type' in df_ag.columns:
                    type_norm_ag = df_ag['Type'].astype(str).str.strip().str.upper()
                else:
                    type_norm_ag = pd.Series(index=df_ag.index, dtype=str)
    
                avg_psf_1_ag = avg_psf(df_ag[type_norm_ag.eq('1BHK')]) if 'Type' in df_ag.columns else float('nan')
                avg_psf_2_ag = avg_psf(df_ag[type_norm_ag.eq('2BHK')]) if 'Type' in df_ag.columns else float('nan')
                avg_psf_all_ag = avg_psf(df_ag)
    
                # Counts
                month_wise_ag = df_ag['Month'].value_counts().reindex(ordered_months, fill_value=0) if 'Month' in df_ag.columns else pd.Series(dtype=int)
                type_wise_ag = df_ag['Type'].value_counts() if 'Type' in df_ag.columns else pd.Series(dtype=int)
                sales_exec_wise_ag = df_ag['Sales Executive'].value_counts() if 'Sales Executive' in df_ag.columns else pd.Series(dtype=int)
                wing_wise_ag = df_ag['Wing'].astype(str).str.strip().value_counts() if 'Wing' in df_ag.columns else pd.Series(dtype=int)
    
                booked_by_wing_counts_ag = wing_wise_ag.to_dict()
    
                ef_total_units_ag = int(WING_TOTALS.get('E', 0) + WING_TOTALS.get('F', 0))
                ef_booked_ag = int(booked_by_wing_counts_ag.get('E', 0) + booked_by_wing_counts_ag.get('F', 0))
                ef_pct_ag = _pct(ef_booked_ag, ef_total_units_ag)
    
                bc_total_units_ag = int(WING_TOTALS.get('B', 0) + WING_TOTALS.get('C', 0))
                bc_booked_ag = int(booked_by_wing_counts_ag.get('B', 0) + booked_by_wing_counts_ag.get('C', 0))
                bc_pct_ag = _pct(bc_booked_ag, bc_total_units_ag)
    
                phase_total_units_ag = int(sum(WING_TOTALS.get(w, 0) for w in ['E', 'F', 'B', 'C']))
                phase_booked_ag = int(sum(booked_by_wing_counts_ag.get(w, 0) for w in ['E', 'F', 'B', 'C']))
                phase_pct_ag = _pct(phase_booked_ag, phase_total_units_ag)
    
                # Appreciation KPIs
                BASE_MONTH_LABEL = "April 25"
    
                def _avg_psf_for_ag(month_label: str, type_code: str | None):
                    if month_label is None or 'Month' not in df_ag.columns:
                        return float('nan')
                    sub = df_ag[df_ag['Month'] == month_label]
                    if type_code is not None and 'Type' in sub.columns:
                        sub = sub[sub['Type'].astype(str).str.strip().str.upper() == type_code]
                    val = avg_psf(sub)
                    return float(val) if pd.notna(val) else float('nan')
    
                def _appr_pct(base_val, curr_val):
                    if pd.isna(base_val) or pd.isna(curr_val) or base_val == 0:
                        return float('nan')
                    return ((curr_val - base_val) / base_val) * 100.0
    
                latest_month_label_ag = ordered_months_ag[-1] if ordered_months_ag else None
    
                base_1_ag = _avg_psf_for_ag(BASE_MONTH_LABEL, '1BHK')
                curr_1_ag = _avg_psf_for_ag(latest_month_label_ag, '1BHK')
                appr_1_ag = _appr_pct(base_1_ag, curr_1_ag)
    
                base_2_ag = _avg_psf_for_ag(BASE_MONTH_LABEL, '2BHK')
                curr_2_ag = _avg_psf_for_ag(latest_month_label_ag, '2BHK')
                appr_2_ag = _appr_pct(base_2_ag, curr_2_ag)
    
                base_all_ag = _avg_psf_for_ag(BASE_MONTH_LABEL, None)
                curr_all_ag = _avg_psf_for_ag(latest_month_label_ag, None)
                appr_all_ag = _appr_pct(base_all_ag, curr_all_ag)
    
                # ============================================================
                # SUMMARY
                # ============================================================
                section_heading_card("Summary")
                
                def _pct(booked, total):
                    return (booked / total * 100.0) if total > 0 else 0.0
                
                def fmt_avg_bookings(x):
                    return f"{x:.2f}" if pd.notna(x) else "—"
                
                def _fmt_1_dec_ag(x):
                    return f"{x:.1f}" if pd.notna(x) else "—"
                
                def _fmt_0_dec_ag(x):
                    return f"{x:.0f}" if pd.notna(x) else "—"
                
                def _subset_by_type_ag(dataframe, type_code=None):
                    if type_code is None or 'Type' not in dataframe.columns:
                        return dataframe.copy()
                    tnorm = dataframe['Type'].astype(str).str.strip().str.upper()
                    return dataframe[tnorm.eq(type_code)].copy()
                
                def _avg_conversion_ag(dataframe, type_code=None):
                    if 'Conversion Period (days)' not in dataframe.columns:
                        return float("nan")
                    sub = _subset_by_type_ag(dataframe, type_code)
                    vals = pd.to_numeric(sub['Conversion Period (days)'], errors='coerce')
                    vals = vals[vals.notna() & (vals >= 0)]
                    return float(vals.mean()) if len(vals) else float("nan")
                
                def _avg_visits_ag(dataframe, type_code=None):
                    if 'Visit Count' not in dataframe.columns:
                        return float("nan")
                    sub = _subset_by_type_ag(dataframe, type_code)
                    vals = pd.to_numeric(sub['Visit Count'], errors='coerce')
                    vals = vals[vals.notna() & (vals > 0)]
                    return float(vals.mean()) if len(vals) else float("nan")
                
                def _avg_bookings_per_month_ag(dataframe, type_code=None):
                    sub = _subset_by_type_ag(dataframe, type_code)
                    month_key = "MonthYear" if "MonthYear" in sub.columns else ("Month" if "Month" in sub.columns else None)
                    if month_key is None or sub.empty:
                        return float("nan")
                    m = sub[month_key].astype(str).str.strip()
                    m = m[m != ""]
                    n_months = int(m.nunique()) if len(m) else 0
                    return (len(m) / n_months) if n_months > 0 else float("nan")
                
                def _monthly_weighted_psf_stats_ag(dataframe, type_code=None):
                    sub = _subset_by_type_ag(dataframe, type_code)
                
                    if sub.empty or 'Month' not in sub.columns or 'Agreement Cost' not in sub.columns or 'Carpet Area' not in sub.columns:
                        return float("nan"), float("nan"), float("nan"), None, None
                
                    temp = sub.copy()
                    temp['_AgreementCostNum'] = pd.to_numeric(temp['Agreement Cost'], errors='coerce')
                    temp['_CarpetAreaNum'] = pd.to_numeric(temp['Carpet Area'], errors='coerce')
                    temp['_SaleableArea'] = temp['_CarpetAreaNum'] * 1.38
                
                    temp = temp[
                        temp['Month'].notna() &
                        temp['_AgreementCostNum'].notna() &
                        temp['_SaleableArea'].notna() &
                        (temp['_SaleableArea'] > 0)
                    ].copy()
                
                    if temp.empty:
                        return float("nan"), float("nan"), float("nan"), None, None
                
                    month_tbl = (
                        temp.groupby('Month', as_index=False)
                            .agg(
                                TotalAgreementCost=('_AgreementCostNum', 'sum'),
                                TotalSaleableArea=('_SaleableArea', 'sum')
                            )
                    )
                
                    month_tbl['WeightedAvgPSF'] = month_tbl['TotalAgreementCost'] / month_tbl['TotalSaleableArea']
                
                    month_order_local = ordered_months_ag if 'ordered_months_ag' in locals() and ordered_months_ag else (ordered_months if 'ordered_months' in locals() else [])
                    if month_order_local:
                        month_tbl['Month'] = pd.Categorical(month_tbl['Month'], categories=month_order_local, ordered=True)
                        month_tbl = month_tbl.sort_values('Month')
                
                    if month_tbl.empty:
                        return float("nan"), float("nan"), float("nan"), None, None
                
                    low_row = month_tbl.loc[month_tbl['WeightedAvgPSF'].idxmin()]
                    high_row = month_tbl.loc[month_tbl['WeightedAvgPSF'].idxmax()]
                
                    low_psf = float(low_row['WeightedAvgPSF']) if pd.notna(low_row['WeightedAvgPSF']) else float("nan")
                    high_psf = float(high_row['WeightedAvgPSF']) if pd.notna(high_row['WeightedAvgPSF']) else float("nan")
                    appr_pct = ((high_psf - low_psf) / low_psf * 100.0) if pd.notna(low_psf) and pd.notna(high_psf) and low_psf > 0 else float("nan")
                
                    low_month = str(low_row['Month']) if pd.notna(low_row['Month']) else None
                    high_month = str(high_row['Month']) if pd.notna(high_row['Month']) else None
                
                    return low_psf, high_psf, appr_pct, low_month, high_month
                
                # Base summary values
                total_carpet_area_ag_summary = pd.to_numeric(df_ag.get('Carpet Area', 0), errors='coerce').fillna(0).sum()
                total_agreement_cost_ag_summary = sum_rev(df_ag)
                
                # Booking % calculations
                booked_by_wing_counts_ag = wing_wise_ag.to_dict()
                
                ef_total_units_ag = int(WING_TOTALS.get('E', 0) + WING_TOTALS.get('F', 0))
                ef_booked_ag = int(booked_by_wing_counts_ag.get('E', 0) + booked_by_wing_counts_ag.get('F', 0))
                ef_pct_ag = _pct(ef_booked_ag, ef_total_units_ag)
                
                bc_total_units_ag = int(WING_TOTALS.get('B', 0) + WING_TOTALS.get('C', 0))
                bc_booked_ag = int(booked_by_wing_counts_ag.get('B', 0) + booked_by_wing_counts_ag.get('C', 0))
                bc_pct_ag = _pct(bc_booked_ag, bc_total_units_ag)
                
                phase_total_units_ag = int(sum(WING_TOTALS.get(w, 0) for w in ['E', 'F', 'B', 'C']))
                phase_booked_ag = int(sum(booked_by_wing_counts_ag.get(w, 0) for w in ['E', 'F', 'B', 'C']))
                phase_pct_ag = _pct(phase_booked_ag, phase_total_units_ag)
                
                def wing_pct_sold_ag(wing_code: str) -> float:
                    booked = int(booked_by_wing_counts_ag.get(wing_code, 0))
                    total = int(WING_TOTALS.get(wing_code, 0))
                    return (booked / total * 100.0) if total > 0 else 0.0
                
                # Appreciation based on lowest avg month vs highest avg month
                low_1_ag, high_1_ag, appr_1_ag, low_month_1_ag, high_month_1_ag = _monthly_weighted_psf_stats_ag(df_ag, '1BHK')
                low_2_ag, high_2_ag, appr_2_ag, low_month_2_ag, high_month_2_ag = _monthly_weighted_psf_stats_ag(df_ag, '2BHK')
                low_all_ag, high_all_ag, appr_all_ag, low_month_all_ag, high_month_all_ag = _monthly_weighted_psf_stats_ag(df_ag, None)
                
                # Row 1
                r1 = st.columns(1)
                with r1[0]:
                    st.markdown(
                        f"<div class='metric-card'><h3>Total Bookings</h3><p>{total_bookings_ag}</p></div>",
                        unsafe_allow_html=True
                    )
                
                # Stamp duty row removed for Agreement Done tab
                
                # Row 2
                r2c1, r2c2 = st.columns(2)
                with r2c1:
                    st.markdown(
                        f"<div class='metric-card'><h3>Total Carpet Area Sold</h3><p>{total_carpet_area_ag_summary:,.0f} sq ft</p></div>",
                        unsafe_allow_html=True
                    )
                with r2c2:
                    st.markdown(
                        f"<div class='metric-card'><h3>Total Agreement Cost Sold (₹)</h3><p>{total_agreement_cost_ag_summary:,.0f}</p></div>",
                        unsafe_allow_html=True
                    )
                
                # Row 3
                avg_conv_all_ag = _avg_conversion_ag(df_ag, None)
                avg_conv_1_ag = _avg_conversion_ag(df_ag, '1BHK')
                avg_conv_2_ag = _avg_conversion_ag(df_ag, '2BHK')
                
                r3c1, r3c2, r3c3 = st.columns(3)
                with r3c1:
                    st.markdown(
                        f"<div class='metric-card'><h3>Average Conversion Period</h3><p>{_fmt_1_dec_ag(avg_conv_all_ag)} days</p></div>",
                        unsafe_allow_html=True
                    )
                with r3c2:
                    st.markdown(
                        f"<div class='metric-card'><h3>Average Conversion Period — 1 BHK</h3><p>{_fmt_1_dec_ag(avg_conv_1_ag)} days</p></div>",
                        unsafe_allow_html=True
                    )
                with r3c3:
                    st.markdown(
                        f"<div class='metric-card'><h3>Average Conversion Period — 2 BHK</h3><p>{_fmt_1_dec_ag(avg_conv_2_ag)} days</p></div>",
                        unsafe_allow_html=True
                    )
                
                # Row 4
                avg_visits_all_ag = _avg_visits_ag(df_ag, None)
                avg_visits_1_ag = _avg_visits_ag(df_ag, '1BHK')
                avg_visits_2_ag = _avg_visits_ag(df_ag, '2BHK')
                
                r4c1, r4c2, r4c3 = st.columns(3)
                with r4c1:
                    st.markdown(
                        f"<div class='metric-card'><h3>Average Visits for Booking</h3><p>{_fmt_0_dec_ag(avg_visits_all_ag)}</p></div>",
                        unsafe_allow_html=True
                    )
                with r4c2:
                    st.markdown(
                        f"<div class='metric-card'><h3>Average Visits for Booking — 1 BHK</h3><p>{_fmt_0_dec_ag(avg_visits_1_ag)}</p></div>",
                        unsafe_allow_html=True
                    )
                with r4c3:
                    st.markdown(
                        f"<div class='metric-card'><h3>Average Visits for Booking — 2 BHK</h3><p>{_fmt_0_dec_ag(avg_visits_2_ag)}</p></div>",
                        unsafe_allow_html=True
                    )
                
                # Row 5
                avg_bpm_all_ag = _avg_bookings_per_month_ag(df_ag, None)
                avg_bpm_1_ag = _avg_bookings_per_month_ag(df_ag, '1BHK')
                avg_bpm_2_ag = _avg_bookings_per_month_ag(df_ag, '2BHK')
                
                r5c1, r5c2, r5c3 = st.columns(3)
                with r5c1:
                    st.markdown(
                        f"<div class='metric-card'><h3>Avg Booking Count / Month</h3><p>{fmt_avg_bookings(avg_bpm_all_ag)}</p></div>",
                        unsafe_allow_html=True
                    )
                with r5c2:
                    st.markdown(
                        f"<div class='metric-card'><h3>Avg Booking Count / Month — 1 BHK</h3><p>{fmt_avg_bookings(avg_bpm_1_ag)}</p></div>",
                        unsafe_allow_html=True
                    )
                with r5c3:
                    st.markdown(
                        f"<div class='metric-card'><h3>Avg Booking Count / Month — 2 BHK</h3><p>{fmt_avg_bookings(avg_bpm_2_ag)}</p></div>",
                        unsafe_allow_html=True
                    )
                
                # Row 6
                r6c1, r6c2, r6c3 = st.columns(3)
                with r6c1:
                    st.markdown(f"<div class='metric-card'><h3>Booking % — E & F</h3><p>{ef_pct_ag:.1f}%</p></div>", unsafe_allow_html=True)
                with r6c2:
                    st.markdown(f"<div class='metric-card'><h3>Booking % — B & C</h3><p>{bc_pct_ag:.1f}%</p></div>", unsafe_allow_html=True)
                with r6c3:
                    st.markdown(f"<div class='metric-card'><h3>Booking % — Phase 1</h3><p>{phase_pct_ag:.1f}%</p></div>", unsafe_allow_html=True)
                
                # Row 7
                r7c1, r7c2 = st.columns(2)
                with r7c1:
                    st.markdown(
                        f"<div class='metric-card'><h3>E Wing — % Sold</h3><p>{wing_pct_sold_ag('E'):.1f}%</p></div>",
                        unsafe_allow_html=True
                    )
                with r7c2:
                    st.markdown(
                        f"<div class='metric-card'><h3>F Wing — % Sold</h3><p>{wing_pct_sold_ag('F'):.1f}%</p></div>",
                        unsafe_allow_html=True
                    )
                
                # Row 8
                r8c1, r8c2 = st.columns(2)
                with r8c1:
                    st.markdown(
                        f"<div class='metric-card'><h3>B Wing — % Sold</h3><p>{wing_pct_sold_ag('B'):.1f}%</p></div>",
                        unsafe_allow_html=True
                    )
                with r8c2:
                    st.markdown(
                        f"<div class='metric-card'><h3>C Wing — % Sold</h3><p>{wing_pct_sold_ag('C'):.1f}%</p></div>",
                        unsafe_allow_html=True
                    )
                
                # Row 9
                r9c1, r9c2, r9c3 = st.columns(3)
                with r9c1:
                    st.markdown(
                        f"<div class='metric-card'>"
                        f"<h3>1 BHK Appreciation %</h3>"
                        f"<p>{('—' if pd.isna(appr_1_ag) else f'{appr_1_ag:.1f}%')}</p>"
                        f"<div class='metric-sub'>Lowest Avg Month ({low_month_1_ag or '—'}): {('—' if pd.isna(low_1_ag) else f'₹{low_1_ag:,.0f}/sqft')} &nbsp;|&nbsp; "
                        f"Highest Avg Month ({high_month_1_ag or '—'}): {('—' if pd.isna(high_1_ag) else f'₹{high_1_ag:,.0f}/sqft')}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with r9c2:
                    st.markdown(
                        f"<div class='metric-card'>"
                        f"<h3>2 BHK Appreciation %</h3>"
                        f"<p>{('—' if pd.isna(appr_2_ag) else f'{appr_2_ag:.1f}%')}</p>"
                        f"<div class='metric-sub'>Lowest Avg Month ({low_month_2_ag or '—'}): {('—' if pd.isna(low_2_ag) else f'₹{low_2_ag:,.0f}/sqft')} &nbsp;|&nbsp; "
                        f"Highest Avg Month ({high_month_2_ag or '—'}): {('—' if pd.isna(high_2_ag) else f'₹{high_2_ag:,.0f}/sqft')}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with r9c3:
                    st.markdown(
                        f"<div class='metric-card'>"
                        f"<h3>Overall Appreciation %</h3>"
                        f"<p>{('—' if pd.isna(appr_all_ag) else f'{appr_all_ag:.1f}%')}</p>"
                        f"<div class='metric-sub'>Lowest Avg Month ({low_month_all_ag or '—'}): {('—' if pd.isna(low_all_ag) else f'₹{low_all_ag:,.0f}/sqft')} &nbsp;|&nbsp; "
                        f"Highest Avg Month ({high_month_all_ag or '—'}): {('—' if pd.isna(high_all_ag) else f'₹{high_all_ag:,.0f}/sqft')}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                # ============================================================
                # QUARTERLY DATA
                # ============================================================
                section_heading_card("Quarterly Data")
    
                st.markdown("<div class='section-subtitle'>🗓️ Quarter-wise Booking Count</div>", unsafe_allow_html=True)
                if 'Quarter' in df_ag.columns and ordered_quarters_ag:
                    q_count = (
                        df_ag.groupby('Quarter').size()
                             .reindex(ordered_quarters_ag, fill_value=0)
                             .reset_index(name='Bookings')
                    )
                    q_bar = alt.Chart(q_count).mark_bar(color="#7c3aed").encode(
                        x=alt.X('Quarter:N', sort=ordered_quarters_ag, title='Quarter',
                                axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                        y=alt.Y('Bookings:Q', title='Bookings'),
                        tooltip=['Quarter:N', 'Bookings:Q']
                    )
                    q_text = alt.Chart(q_count).mark_text(
                        align='center', baseline='bottom', dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(
                        x=alt.X('Quarter:N', sort=ordered_quarters_ag),
                        y='Bookings:Q',
                        text='Bookings:Q'
                    )
                    st.altair_chart(
                        (q_bar + q_text).properties(
                            title=alt.TitleParams("Quarter-wise Booking Count", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                            height=300, width=alt.Step(110)
                        ).configure_title(anchor='start'),
                        use_container_width=True
                    )
    
                st.markdown("<div class='section-subtitle'>📈 Quarter-wise Avg PSF (₹/sqft)</div>", unsafe_allow_html=True)
                if 'Quarter' in df_ag.columns:
                    q_psf = (
                        df_ag.dropna(subset=['Quarter'])
                             .groupby('Quarter')
                             .apply(lambda s: avg_psf(s))
                             .reset_index(name='PSF')
                    )
                    if not q_psf.empty:
                        q_psf['Quarter'] = pd.Categorical(q_psf['Quarter'], categories=ordered_quarters_ag, ordered=True)
                        qpsf_bar = alt.Chart(q_psf).mark_bar().encode(
                            x=alt.X('Quarter:N', sort=ordered_quarters_ag, title='Quarter',
                                    axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                            y=alt.Y('PSF:Q', title='Avg PSF (₹/sqft)'),
                            tooltip=['Quarter:N', alt.Tooltip('PSF:Q', format=',.0f')]
                        )
                        qpsf_lbl = alt.Chart(q_psf).mark_text(
                            dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                        ).encode(
                            x=alt.X('Quarter:N', sort=ordered_quarters_ag),
                            y='PSF:Q',
                            text=alt.Text('PSF:Q', format=',.0f')
                        )
                        st.altair_chart(
                            (qpsf_bar + qpsf_lbl).properties(
                                title=alt.TitleParams("Quarter-wise Avg PSF (₹/sqft)", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                height=280, width=alt.Step(110)
                            ).configure_title(anchor='start'),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>✅ Quarter-wise Agreement Done (Done only)</div>", unsafe_allow_html=True)
                if 'Quarter' in df_ag.columns:
                    q_domain = ordered_quarters_ag if ordered_quarters_ag else sorted(df_ag['Quarter'].dropna().unique().tolist())
                    q_done = (
                        df_ag.dropna(subset=['Quarter'])
                             .groupby('Quarter')
                             .size()
                             .reindex(q_domain, fill_value=0)
                             .reset_index(name='AgreementDone')
                    )
                    bar = alt.Chart(q_done).mark_bar().encode(
                        x=alt.X('Quarter:N', sort=q_domain, title='Quarter',
                                axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                        y=alt.Y('AgreementDone:Q', title='Agreements Done'),
                        tooltip=[alt.Tooltip('Quarter:N'), alt.Tooltip('AgreementDone:Q', title='Done')]
                    )
                    labels = alt.Chart(q_done).mark_text(
                        dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(
                        x=alt.X('Quarter:N', sort=q_domain),
                        y='AgreementDone:Q',
                        text=alt.Text('AgreementDone:Q', format='.0f')
                    )
                    st.altair_chart(
                        (bar + labels).properties(
                            title=alt.TitleParams("Quarter-wise Agreement Done (Done)", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                            height=280, width=alt.Step(110)
                        ).configure_title(anchor='start'),
                        use_container_width=True
                    )
    
                st.markdown("<div class='section-subtitle'>🏞️ Quarter-wise × Facing-wise Booking Count</div>", unsafe_allow_html=True)
                if {'Carpet Area', 'Quarter'}.issubset(df_ag.columns):
                    def classify_facing(area):
                        s = nearest_size(area)
                        if s is None:
                            return None
                        for face, sizes in FACING_MAP.items():
                            if s in sizes:
                                return face
                        return None
    
                    df_face = df_ag.copy()
                    df_face['Facing'] = df_face['Carpet Area'].apply(classify_facing)
                    df_face = df_face.dropna(subset=['Facing', 'Quarter'])
                    if not df_face.empty:
                        q_face_count = (
                            df_face.groupby(['Quarter', 'Facing']).size()
                                   .reset_index(name='Count')
                        )
                        q_face_count['Quarter'] = pd.Categorical(q_face_count['Quarter'], categories=ordered_quarters_ag, ordered=True)
                        bar_qf = alt.Chart(q_face_count).mark_bar().encode(
                            x=alt.X('Quarter:N', sort=ordered_quarters_ag, title='Quarter',
                                    axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                            xOffset=alt.X('Facing:N', title='Facing'),
                            y=alt.Y('Count:Q', title='Bookings'),
                            color=alt.Color('Facing:N', scale=alt.Scale(domain=FACING_DOMAIN), title='Facing'),
                            tooltip=['Quarter:N', 'Facing:N', 'Count:Q']
                        )
                        lbl_qf = alt.Chart(q_face_count).mark_text(
                            dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                        ).encode(
                            x=alt.X('Quarter:N', sort=ordered_quarters_ag),
                            xOffset='Facing:N',
                            y='Count:Q',
                            text='Count:Q'
                        )
                        st.altair_chart(
                            (bar_qf + lbl_qf).properties(
                                title=alt.TitleParams("Quarter-wise × Facing-wise Booking Count", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                height=320, width=alt.Step(110)
                            ).configure_title(anchor='start'),
                            use_container_width=True
                        )
    
                # ============================================================
                # MONTHLY DATA
                # ============================================================
                section_heading_card("Monthly Data")
    
                st.markdown("<div class='section-subtitle'>📅 Month-wise Bookings</div>", unsafe_allow_html=True)
                month_chart_data = pd.DataFrame({'Month': month_wise_ag.index, 'Count': month_wise_ag.values})
                month_bar = alt.Chart(month_chart_data).mark_bar(color="#9333ea").encode(
                    x=alt.X('Month:N', sort=ordered_months, title='Month',
                            axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
                    y=alt.Y('Count:Q', title='Bookings'),
                    tooltip=['Month', 'Count']
                )
                month_text = alt.Chart(month_chart_data).mark_text(
                    align='center', baseline='bottom', dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(x=alt.X('Month:N', sort=ordered_months), y='Count:Q', text='Count:Q')
                st.altair_chart(
                    (month_bar + month_text).properties(
                        title=alt.TitleParams("Month-wise Bookings", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=260, width=alt.Step(70)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
                st.markdown("<div class='section-subtitle'>📈 Month-wise Avg Rate (₹/sqft)</div>", unsafe_allow_html=True)
                if not df_ag.empty:
                    monthly_psf_ag = (
                        df_ag.dropna(subset=['Month'])
                             .groupby('Month')
                             .apply(lambda s: avg_psf(s))
                             .reindex(ordered_months)
                             .reset_index(name='PSF')
                    ).dropna(subset=['PSF'])
    
                    if not monthly_psf_ag.empty:
                        line_psf = alt.Chart(monthly_psf_ag).mark_line(point=True).encode(
                            x=alt.X('Month:N', sort=ordered_months, title='Month',
                                    axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
                            y=alt.Y('PSF:Q', title='Avg PSF (₹/sqft)'),
                            tooltip=['Month:N', alt.Tooltip('PSF:Q', format=',.0f')]
                        )
                        labels_psf = alt.Chart(monthly_psf_ag).mark_text(
                            dy=-8, fontSize=12, fontWeight='bold'
                        ).encode(
                            x=alt.X('Month:N', sort=ordered_months),
                            y='PSF:Q',
                            text=alt.Text('PSF:Q', format=',.0f')
                        )
                        st.altair_chart(
                            (line_psf + labels_psf).properties(
                                title=alt.TitleParams("Month-wise Avg PSF", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                height=300, width=alt.Step(80)
                            ).configure_title(anchor='start'),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>📅 Month-wise Carpet Area Sold (sq ft)</div>", unsafe_allow_html=True)
                MONTH_COL = "Month"
                AREA_COL = "Carpet Area"
                missing = [c for c in [MONTH_COL, AREA_COL] if c not in df_ag.columns]
                if missing:
                    st.info(f"Missing columns: {', '.join(missing)}")
                else:
                    tmp = df_ag[[MONTH_COL, AREA_COL]].copy()
                    tmp[MONTH_COL] = tmp[MONTH_COL].astype(str).str.strip()
                    tmp[AREA_COL] = pd.to_numeric(tmp[AREA_COL], errors="coerce")
                    tmp = tmp.dropna(subset=[MONTH_COL, AREA_COL])
                    tmp = tmp[tmp[MONTH_COL] != ""]
    
                    if tmp.empty:
                        st.info("No Month/Carpet Area data available to plot.")
                    else:
                        plot_df = (
                            tmp.groupby(MONTH_COL)[AREA_COL]
                               .sum()
                               .reset_index(name="CarpetAreaSold")
                        )
    
                        if "ordered_months" in locals() and ordered_months:
                            month_order = [m for m in ordered_months if m in set(plot_df[MONTH_COL])]
                            extras = [m for m in plot_df[MONTH_COL].unique().tolist() if m not in set(month_order)]
                            month_order = month_order + extras
                        else:
                            month_order = plot_df.sort_values("CarpetAreaSold", ascending=False)[MONTH_COL].tolist()
    
                        plot_df[MONTH_COL] = pd.Categorical(plot_df[MONTH_COL], categories=month_order, ordered=True)
                        plot_df = plot_df.sort_values(MONTH_COL)
    
                        bars = alt.Chart(plot_df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
                            x=alt.X(f"{MONTH_COL}:N", sort=month_order, title="Month",
                                    axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                            y=alt.Y("CarpetAreaSold:Q", title="Carpet Area Sold (sq ft)"),
                            tooltip=[
                                alt.Tooltip(f"{MONTH_COL}:N", title="Month"),
                                alt.Tooltip("CarpetAreaSold:Q", title="Carpet Area Sold (sq ft)", format=",.0f")
                            ]
                        )
                        labels = alt.Chart(plot_df).mark_text(
                            dy=-6, fontSize=12, fontWeight="bold", color="#0f172a"
                        ).encode(
                            x=alt.X(f"{MONTH_COL}:N", sort=month_order),
                            y="CarpetAreaSold:Q",
                            text=alt.Text("CarpetAreaSold:Q", format=",.0f")
                        )
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams("Month-wise Carpet Area Sold", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                height=300,
                                width=alt.Step(80)
                            ).configure_title(anchor='start'),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>📈 1 BHK & 2 BHK — Monthwise Avg PSF</div>", unsafe_allow_html=True)
                if {'Month', 'Type', 'Carpet Area', 'Agreement Cost'}.issubset(df_ag.columns):
                    month_order_local = [m for m in ordered_months if m in df_ag['Month'].unique().tolist()]
                    df_m = df_ag.dropna(subset=['Month']).copy()
                    df_m['Month'] = pd.Categorical(df_m['Month'], categories=month_order_local, ordered=True)
                    tnorm = df_m['Type'].astype(str).str.strip().str.upper()
    
                    def _type_month_psf_chart(type_code: str, title: str):
                        sub = df_m[tnorm.eq(type_code)].copy()
                        if sub.empty:
                            st.info(f"No data for {title}.")
                            return
                        psf_month = (
                            sub.groupby('Month')
                               .apply(avg_psf)
                               .rename('PSF')
                               .reset_index()
                        )
                        if psf_month.empty:
                            st.info(f"No data for {title}.")
                            return
    
                        base = alt.Chart(psf_month).properties(
                            height=300,
                            width='container',
                            title=alt.TitleParams(title, anchor='start')
                        )
                        line = base.mark_line(point=True).encode(
                            x=alt.X('Month:N', sort=month_order_local, title='Month',
                                    axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                            y=alt.Y('PSF:Q', title='Avg PSF (₹/sqft)'),
                            tooltip=[alt.Tooltip('Month:N', title='Month'),
                                     alt.Tooltip('PSF:Q', title='Avg PSF', format=',.0f')]
                        )
                        labels = base.mark_text(
                            dy=-8, fontSize=12, fontWeight='bold', color='#0f172a'
                        ).encode(
                            x=alt.X('Month:N', sort=month_order_local),
                            y='PSF:Q',
                            text=alt.Text('PSF:Q', format=',.0f')
                        )
                        st.altair_chart((line + labels).configure_title(anchor='start'), use_container_width=True)
    
                    _type_month_psf_chart('1BHK', "1 BHK — Monthwise Avg PSF")
                    _type_month_psf_chart('2BHK', "2 BHK — Monthwise Avg PSF")
                else:
                    st.info("Missing columns for monthwise PSF graphs (need Month, Type, Carpet Area, Agreement Cost).")
    
                # ============================================================
                # WING DATA
                # ============================================================
                section_heading_card("Wing Data")
    
                st.markdown("<div class='section-subtitle'>🏢 Wing-wise Avg PSF by Quarter</div>", unsafe_allow_html=True)
                if {'Wing', 'Quarter'}.issubset(df_ag.columns):
                    qw_psf = (
                        df_ag.dropna(subset=['Quarter', 'Wing'])
                             .groupby(['Quarter', 'Wing'])
                             .apply(lambda s: avg_psf(s))
                             .reset_index(name='PSF')
                    )
                    if not qw_psf.empty:
                        qw_psf['Quarter'] = pd.Categorical(qw_psf['Quarter'], categories=ordered_quarters_ag, ordered=True)
                        for w in sorted(qw_psf['Wing'].dropna().unique()):
                            subw = qw_psf[qw_psf['Wing'] == w]
                            bar_wing = alt.Chart(subw).mark_bar().encode(
                                x=alt.X('Quarter:N', sort=ordered_quarters_ag, title='Quarter',
                                        axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                                y=alt.Y('PSF:Q', title='Avg PSF (₹/sqft)'),
                                tooltip=['Quarter:N', alt.Tooltip('PSF:Q', format=',.0f')]
                            )
                            lab_wing = alt.Chart(subw).mark_text(
                                dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                            ).encode(
                                x=alt.X('Quarter:N', sort=ordered_quarters_ag),
                                y='PSF:Q',
                                text=alt.Text('PSF:Q', format=',.0f')
                            )
                            st.altair_chart(
                                (bar_wing + lab_wing).properties(
                                    title=alt.TitleParams(f"Wing {w} — Avg PSF by Quarter", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                    height=280, width=alt.Step(110)
                                ).configure_title(anchor='start'),
                                use_container_width=True
                            )
    
                st.markdown("<div class='section-subtitle'>🏢 Wing-wise Carpet Area Sold (sq ft)</div>", unsafe_allow_html=True)
                WING_COL = "Wing"
                AREA_COL = "Carpet Area"
                missing = [c for c in [WING_COL, AREA_COL] if c not in df_ag.columns]
                if missing:
                    st.info(f"Missing columns: {', '.join(missing)}")
                else:
                    tmp = df_ag[[WING_COL, AREA_COL]].copy()
                    tmp[WING_COL] = tmp[WING_COL].astype(str).str.strip()
                    tmp[AREA_COL] = pd.to_numeric(tmp[AREA_COL], errors="coerce")
                    tmp = tmp.dropna(subset=[WING_COL, AREA_COL])
                    tmp = tmp[tmp[WING_COL] != ""]
    
                    if tmp.empty:
                        st.info("No Wing/Carpet Area data available to plot.")
                    else:
                        plot_df = tmp.groupby(WING_COL)[AREA_COL].sum().reset_index(name="CarpetAreaSold")
                        wing_order = plot_df.sort_values("CarpetAreaSold", ascending=False)[WING_COL].tolist()
    
                        plot_df[WING_COL] = pd.Categorical(plot_df[WING_COL], categories=wing_order, ordered=True)
                        plot_df = plot_df.sort_values(WING_COL)
    
                        bars = alt.Chart(plot_df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
                            x=alt.X(f"{WING_COL}:N", sort=wing_order, title="Wing",
                                    axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True)),
                            y=alt.Y("CarpetAreaSold:Q", title="Carpet Area Sold (sq ft)"),
                            tooltip=[
                                alt.Tooltip(f"{WING_COL}:N", title="Wing"),
                                alt.Tooltip("CarpetAreaSold:Q", title="Carpet Area Sold (sq ft)", format=",.0f")
                            ]
                        )
                        labels = alt.Chart(plot_df).mark_text(
                            dy=-6, fontSize=12, fontWeight="bold", color="#0f172a"
                        ).encode(
                            x=alt.X(f"{WING_COL}:N", sort=wing_order),
                            y="CarpetAreaSold:Q",
                            text=alt.Text("CarpetAreaSold:Q", format=",.0f")
                        )
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams("Wing-wise Carpet Area Sold", anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                                height=300,
                                width=alt.Step(90)
                            ).configure_title(anchor="start"),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>🏢 Wing-wise Bookings by Lead Type</div>", unsafe_allow_html=True)
                WING_COL = "Wing"
                LEAD_COL = "Lead Type"
                missing = [c for c in [WING_COL, LEAD_COL] if c not in df_ag.columns]
                if missing:
                    st.info(f"Missing columns: {', '.join(missing)}")
                else:
                    tmp = df_ag[[WING_COL, LEAD_COL]].copy()
                    tmp[WING_COL] = tmp[WING_COL].astype(str).str.strip()
                    tmp[LEAD_COL] = tmp[LEAD_COL].astype(str).str.strip()
                    tmp = tmp[(tmp[WING_COL] != "") & (tmp[LEAD_COL] != "")]
    
                    if tmp.empty:
                        st.info("No Wing/Lead Type data available to plot.")
                    else:
                        plot_df = (
                            tmp.groupby([WING_COL, LEAD_COL])
                               .size()
                               .reset_index(name="Bookings")
                        )
    
                        wing_order = sorted(plot_df[WING_COL].unique().tolist())
                        lead_order = (
                            plot_df.groupby(LEAD_COL)["Bookings"]
                                   .sum()
                                   .sort_values(ascending=False)
                                   .index.tolist()
                        )
    
                        plot_df[WING_COL] = pd.Categorical(plot_df[WING_COL], categories=wing_order, ordered=True)
                        plot_df[LEAD_COL] = pd.Categorical(plot_df[LEAD_COL], categories=lead_order, ordered=True)
                        plot_df = plot_df.sort_values([WING_COL, LEAD_COL])
    
                        n_leads = max(1, len(lead_order))
                        BAR_SIZE = 9 if n_leads >= 10 else (11 if n_leads >= 6 else 14)
                        GROUP_GAP = 0.25
                        SUB_GAP = 0.20 if n_leads >= 8 else 0.15
                        GROUP_STEP = max(120, int(n_leads * (BAR_SIZE + 7) + 70))
    
                        bars = alt.Chart(plot_df).mark_bar(
                            size=BAR_SIZE,
                            cornerRadiusTopLeft=2,
                            cornerRadiusTopRight=2
                        ).encode(
                            x=alt.X(f"{WING_COL}:N",
                                    sort=wing_order,
                                    title="Wing",
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                                    axis=alt.Axis(labelAngle=0, labelLimit=200, labelOverlap=True)),
                            xOffset=alt.X(f"{LEAD_COL}:N",
                                          sort=lead_order,
                                          title=None,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y=alt.Y("Bookings:Q", title="Bookings"),
                            color=alt.Color(f"{LEAD_COL}:N",
                                            sort=lead_order,
                                            title="Lead Type",
                                            legend=alt.Legend(orient="top", direction="horizontal", columns=min(6, n_leads))),
                            tooltip=[
                                alt.Tooltip(f"{WING_COL}:N", title="Wing"),
                                alt.Tooltip(f"{LEAD_COL}:N", title="Lead Type"),
                                alt.Tooltip("Bookings:Q", title="Bookings")
                            ]
                        )
    
                        labels = alt.Chart(plot_df).mark_text(
                            dy=-5, fontSize=11, fontWeight="bold", color="#0f172a"
                        ).encode(
                            x=alt.X(f"{WING_COL}:N", sort=wing_order,
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                            xOffset=alt.X(f"{LEAD_COL}:N", sort=lead_order,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y="Bookings:Q",
                            text=alt.Text("Bookings:Q", format=".0f")
                        )
    
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams("Wing-wise Bookings by Lead Type (Grouped Bars)",
                                                      anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                                height=360,
                                width=alt.Step(GROUP_STEP)
                            ).configure_title(anchor="start"),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>🏢 Sales Executive-wise Bookings by Wing (Stacked by Type)</div>", unsafe_allow_html=True)
                SE_COL = "Sales Executive"
                WING_COL = "Wing"
                TYPE_COL = "Type"
                missing = [c for c in [SE_COL, WING_COL, TYPE_COL] if c not in df_ag.columns]
                if missing:
                    st.info(f"Missing columns: {', '.join(missing)}")
                else:
                    tmp = df_ag[[SE_COL, WING_COL, TYPE_COL]].copy()
                    tmp[SE_COL] = tmp[SE_COL].astype(str).str.strip()
                    tmp[WING_COL] = tmp[WING_COL].astype(str).str.strip()
                    tmp[TYPE_COL] = tmp[TYPE_COL].astype(str).str.strip().str.upper()
                    tmp = tmp[(tmp[SE_COL] != "") & (tmp[WING_COL] != "") & (tmp[TYPE_COL] != "")]
    
                    if tmp.empty:
                        st.info("No Sales Executive / Wing / Type data available to plot.")
                    else:
                        plot_df = (
                            tmp.groupby([SE_COL, WING_COL, TYPE_COL])
                               .size()
                               .reset_index(name="Bookings")
                        )
    
                        se_order = (
                            plot_df.groupby(SE_COL)["Bookings"]
                                   .sum()
                                   .sort_values(ascending=False)
                                   .index.tolist()
                        )
                        wing_order = sorted(plot_df[WING_COL].unique().tolist())
                        type_order = (
                            plot_df.groupby(TYPE_COL)["Bookings"]
                                   .sum()
                                   .sort_values(ascending=False)
                                   .index.tolist()
                        )
    
                        plot_df[SE_COL] = pd.Categorical(plot_df[SE_COL], categories=se_order, ordered=True)
                        plot_df[WING_COL] = pd.Categorical(plot_df[WING_COL], categories=wing_order, ordered=True)
                        plot_df[TYPE_COL] = pd.Categorical(plot_df[TYPE_COL], categories=type_order, ordered=True)
                        plot_df = plot_df.sort_values([SE_COL, WING_COL, TYPE_COL])
    
                        totals = (
                            plot_df.groupby([SE_COL, WING_COL], observed=True)["Bookings"]
                                   .sum()
                                   .reset_index(name="Total")
                        )
    
                        n_wings = max(1, len(wing_order))
                        BAR_SIZE = 10 if n_wings >= 6 else 14
                        GROUP_GAP = 0.25
                        SUB_GAP = 0.18 if n_wings >= 6 else 0.14
                        GROUP_STEP = max(150, int(n_wings * (BAR_SIZE + 12) + 110))
    
                        bars = alt.Chart(plot_df).mark_bar(
                            size=BAR_SIZE, cornerRadiusTopLeft=2, cornerRadiusTopRight=2
                        ).encode(
                            x=alt.X(f"{SE_COL}:N", sort=se_order, title="Sales Executive",
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                                    axis=alt.Axis(labelAngle=0, labelLimit=220, labelOverlap=True)),
                            xOffset=alt.X(f"{WING_COL}:N", sort=wing_order, title=None,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y=alt.Y("Bookings:Q", title="Bookings", stack="zero"),
                            color=alt.Color(f"{TYPE_COL}:N", sort=type_order, title="Type",
                                            legend=alt.Legend(orient="top", direction="horizontal", columns=min(6, len(type_order)))),
                            tooltip=[
                                alt.Tooltip(f"{SE_COL}:N", title="Sales Executive"),
                                alt.Tooltip(f"{WING_COL}:N", title="Wing"),
                                alt.Tooltip(f"{TYPE_COL}:N", title="Type"),
                                alt.Tooltip("Bookings:Q", title="Bookings")
                            ]
                        )
    
                        total_labels = alt.Chart(totals).mark_text(
                            dy=-6, fontSize=11, fontWeight="bold", color="#0f172a"
                        ).encode(
                            x=alt.X(f"{SE_COL}:N", sort=se_order,
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                            xOffset=alt.X(f"{WING_COL}:N", sort=wing_order,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y=alt.Y("Total:Q"),
                            text=alt.Text("Total:Q", format=".0f")
                        )
    
                        st.altair_chart(
                            (bars + total_labels).properties(
                                title=alt.TitleParams("Sales Executive-wise Bookings by Wing (Stacked by Type)",
                                                      anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                                height=420,
                                width=alt.Step(GROUP_STEP)
                            ).configure_title(anchor="start"),
                            use_container_width=True
                        )
    
                # ============================================================
                # SALES EXECUTIVE DATA
                # ============================================================
                section_heading_card("Sales Executive Data")
    
                st.markdown("<div class='section-subtitle'>👨‍💼 Sales Executive Wise</div>", unsafe_allow_html=True)
                exec_chart_data = pd.DataFrame({'Executive': sales_exec_wise_ag.index, 'Count': sales_exec_wise_ag.values})
                exec_bar = alt.Chart(exec_chart_data).mark_bar(color="#10b981").encode(
                    x=alt.X('Executive:N', title='Sales Executive', axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
                    y=alt.Y('Count:Q', title='Bookings'),
                    tooltip=['Executive', 'Count']
                )
                exec_text = alt.Chart(exec_chart_data).mark_text(
                    align='center', baseline='bottom', dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(x='Executive:N', y='Count:Q', text='Count:Q')
                st.altair_chart(
                    (exec_bar + exec_text).properties(
                        title=alt.TitleParams("Sales Executive-wise Bookings", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=260, width=alt.Step(60)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
                st.markdown("<div class='section-subtitle'>🧑‍💼 Sales Executive — Monthly Booking Count</div>", unsafe_allow_html=True)
                if 'Sales Executive' in df_ag.columns and not df_ag.empty:
                    se_month = (
                        df_ag.dropna(subset=['Month', 'Sales Executive'])
                             .groupby(['Month', 'Sales Executive'])
                             .size()
                             .reset_index(name='Bookings')
                    )
                    se_month = se_month[se_month['Bookings'] > 0]
                    if not se_month.empty:
                        exec_order = list(df_ag['Sales Executive'].value_counts().index)
                        month_domain = [m for m in ordered_months if m in set(se_month['Month'])]
    
                        se_month['Month'] = pd.Categorical(se_month['Month'], categories=month_domain, ordered=True)
                        se_month['Sales Executive'] = pd.Categorical(se_month['Sales Executive'], categories=exec_order, ordered=True)
    
                        n_months = max(1, len(month_domain))
                        BAR_SIZE = 9 if n_months >= 7 else (11 if n_months >= 5 else 14)
                        GROUP_GAP = 0.30
                        SUB_GAP = 0.25 if n_months >= 6 else 0.20
                        GROUP_STEP = max(130, int(n_months * (BAR_SIZE + 8) + 70))
    
                        bars = alt.Chart(se_month).mark_bar(
                            size=BAR_SIZE,
                            cornerRadiusTopLeft=2,
                            cornerRadiusTopRight=2
                        ).encode(
                            x=alt.X('Sales Executive:N',
                                    sort=exec_order,
                                    title='Sales Executive',
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                                    axis=alt.Axis(labelAngle=0, labelLimit=240, labelOverlap=True)),
                            xOffset=alt.X('Month:N',
                                          sort=month_domain,
                                          title=None,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y=alt.Y('Bookings:Q', title='Bookings'),
                            color=alt.Color('Month:N',
                                            sort=month_domain,
                                            title='Month',
                                            legend=alt.Legend(orient='top', direction='horizontal', columns=min(6, n_months))),
                            tooltip=['Sales Executive:N', 'Month:N', 'Bookings:Q']
                        )
    
                        labels = alt.Chart(se_month).mark_text(
                            fontSize=11, fontWeight='bold',
                            baseline='bottom', dy=-4, align='center',
                            color='black'
                        ).encode(
                            x=alt.X('Sales Executive:N',
                                    sort=exec_order,
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                            xOffset=alt.X('Month:N',
                                          sort=month_domain,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y='Bookings:Q',
                            text=alt.Text('Bookings:Q', format='.0f')
                        )
    
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams("Sales Executive — Monthly Bookings (Grouped Bars)",
                                                      anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                height=380,
                                width=alt.Step(GROUP_STEP)
                            ).configure_title(anchor='start'),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>👤 Avg Bookings per Month — Sales Executive</div>", unsafe_allow_html=True)
                needed_cols_se = {'Sales Executive', 'MonthYear'}
                missing_cols_se = [c for c in needed_cols_se if c not in df_ag.columns]
                if missing_cols_se:
                    st.warning(f"Missing columns for SE avg bookings per month: {', '.join(missing_cols_se)}")
                else:
                    dfx = df_ag.dropna(subset=['Sales Executive', 'MonthYear']).copy()
                    st.caption(f"SE avg/month diagnostics → unique SE: {dfx['Sales Executive'].nunique()}, unique months: {dfx['MonthYear'].nunique()}, rows: {len(dfx)}")
    
                    if dfx.empty:
                        st.info("No monthwise data (after dropping blanks) to compute averages.")
                    else:
                        se_month = (
                            dfx.groupby(['Sales Executive', 'MonthYear'], observed=True)
                               .size()
                               .rename('Bookings')
                               .reset_index()
                        )
    
                        if se_month.empty:
                            st.info("No per-month booking counts available to average.")
                        else:
                            se_avg = (
                                se_month.groupby('Sales Executive', observed=True)['Bookings']
                                        .mean()
                                        .reset_index(name='AvgBookingsPerMonth')
                            )
    
                            if se_avg['AvgBookingsPerMonth'].sum() == 0:
                                st.info("All SE monthly averages are 0. Showing zero bars for reference.")
    
                            se_avg = se_avg.sort_values('AvgBookingsPerMonth', ascending=True)
    
                            base = alt.Chart(se_avg)
                            bars = base.mark_bar(color="#10b981").encode(
                                y=alt.Y('Sales Executive:N', sort=se_avg['Sales Executive'].tolist(), title='Sales Executive'),
                                x=alt.X('AvgBookingsPerMonth:Q', title='Avg Bookings / Month', axis=alt.Axis(format='.2f')),
                                tooltip=[
                                    alt.Tooltip('Sales Executive:N', title='Sales Executive'),
                                    alt.Tooltip('AvgBookingsPerMonth:Q', title='Avg / Month', format='.2f')
                                ]
                            )
                            labels = base.mark_text(
                                align='left', baseline='middle', dx=4, fontSize=12, fontWeight='bold', color='#0f172a'
                            ).encode(
                                y=alt.Y('Sales Executive:N', sort=se_avg['Sales Executive'].tolist()),
                                x='AvgBookingsPerMonth:Q',
                                text=alt.Text('AvgBookingsPerMonth:Q', format='.2f')
                            )
    
                            st.altair_chart(
                                (bars + labels).properties(
                                    title=alt.TitleParams("Avg Bookings per Month — Sales Executive", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                    height=max(240, 24 * len(se_avg)),
                                    width='container'
                                ).configure_axis(
                                    labelLimit=220, labelOverlap=True
                                ).configure_title(anchor='start'),
                                use_container_width=True
                            )
    
                st.markdown("<div class='section-subtitle'>⏱️ Sales Executive-wise Overall Average Conversion Period</div>", unsafe_allow_html=True)
                if 'Conversion Period (days)' in df_ag.columns:
                    conv_tmp = df_ag.copy()
                    conv_tmp['ConvDays'] = pd.to_numeric(conv_tmp['Conversion Period (days)'], errors='coerce')
                    conv_tmp = conv_tmp.dropna(subset=['ConvDays', 'Sales Executive'])
    
                    if not conv_tmp.empty:
                        conv_exec = (
                            conv_tmp.groupby('Sales Executive', dropna=True)['ConvDays']
                                    .mean()
                                    .reset_index(name='AvgConv')
                        )
    
                        line = alt.Chart(conv_exec).mark_line(point=True).encode(
                            x=alt.X('Sales Executive:N', title='Sales Executive',
                                    axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
                            y=alt.Y('AvgConv:Q', title='Avg Conversion Period (days)'),
                            tooltip=[
                                alt.Tooltip('Sales Executive:N', title='Sales Executive'),
                                alt.Tooltip('AvgConv:Q', title='Avg Days', format=',.1f')
                            ]
                        )
    
                        labels = alt.Chart(conv_exec).mark_text(
                            dy=-10, fontSize=12, fontWeight='bold', color='#0f172a'
                        ).encode(
                            x=alt.X('Sales Executive:N'),
                            y=alt.Y('AvgConv:Q'),
                            text=alt.Text('AvgConv:Q', format=',.1f')
                        )
    
                        st.altair_chart(
                            (line + labels).properties(height=320).configure_title(anchor='start'),
                            use_container_width=True
                        )
                    else:
                        st.info("No conversion-period data available to chart.")
                else:
                    st.info("Column 'Conversion Period (days)' not found.")
    
                st.markdown("<div class='section-subtitle'>🧑‍💼 Sales Executive-wise Bookings by Lead Type</div>", unsafe_allow_html=True)
                SE_COL = "Sales Executive"
                LEAD_COL = "Lead Type"
                missing = [c for c in [SE_COL, LEAD_COL] if c not in df_ag.columns]
                if missing:
                    st.info(f"Missing columns: {', '.join(missing)}")
                else:
                    tmp = df_ag[[SE_COL, LEAD_COL]].copy()
                    tmp[SE_COL] = tmp[SE_COL].astype(str).str.strip()
                    tmp[LEAD_COL] = tmp[LEAD_COL].astype(str).str.strip()
                    tmp = tmp[(tmp[SE_COL] != "") & (tmp[LEAD_COL] != "")]
    
                    if tmp.empty:
                        st.info("No Sales Executive / Lead Type data available to plot.")
                    else:
                        plot_df = (
                            tmp.groupby([SE_COL, LEAD_COL])
                               .size()
                               .reset_index(name="Bookings")
                        )
    
                        se_order = (
                            plot_df.groupby(SE_COL)["Bookings"]
                                   .sum()
                                   .sort_values(ascending=False)
                                   .index.tolist()
                        )
    
                        lead_order = (
                            plot_df.groupby(LEAD_COL)["Bookings"]
                                   .sum()
                                   .sort_values(ascending=False)
                                   .index.tolist()
                        )
    
                        plot_df[SE_COL] = pd.Categorical(plot_df[SE_COL], categories=se_order, ordered=True)
                        plot_df[LEAD_COL] = pd.Categorical(plot_df[LEAD_COL], categories=lead_order, ordered=True)
                        plot_df = plot_df.sort_values([SE_COL, LEAD_COL])
    
                        n_types = max(1, len(lead_order))
                        BAR_SIZE = 9 if n_types >= 10 else (11 if n_types >= 6 else 14)
                        GROUP_GAP = 0.25
                        SUB_GAP = 0.20 if n_types >= 8 else 0.15
                        GROUP_STEP = max(140, int(n_types * (BAR_SIZE + 7) + 90))
    
                        bars = alt.Chart(plot_df).mark_bar(
                            size=BAR_SIZE, cornerRadiusTopLeft=2, cornerRadiusTopRight=2
                        ).encode(
                            x=alt.X(f"{SE_COL}:N",
                                    sort=se_order,
                                    title="Sales Executive",
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                                    axis=alt.Axis(labelAngle=0, labelLimit=220, labelOverlap=True)),
                            xOffset=alt.X(f"{LEAD_COL}:N",
                                          sort=lead_order,
                                          title=None,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y=alt.Y("Bookings:Q", title="Bookings"),
                            color=alt.Color(f"{LEAD_COL}:N",
                                            sort=lead_order,
                                            title="Lead Type",
                                            legend=alt.Legend(orient="top", direction="horizontal", columns=min(6, n_types))),
                            tooltip=[
                                alt.Tooltip(f"{SE_COL}:N", title="Sales Executive"),
                                alt.Tooltip(f"{LEAD_COL}:N", title="Lead Type"),
                                alt.Tooltip("Bookings:Q", title="Bookings")
                            ]
                        )
    
                        labels = alt.Chart(plot_df).mark_text(
                            dy=-5, fontSize=11, fontWeight="bold", color="#0f172a"
                        ).encode(
                            x=alt.X(f"{SE_COL}:N", sort=se_order,
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                            xOffset=alt.X(f"{LEAD_COL}:N", sort=lead_order,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y="Bookings:Q",
                            text=alt.Text("Bookings:Q", format=".0f")
                        )
    
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams("Sales Executive-wise Bookings by Lead Type (Grouped Bars)",
                                                      anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                                height=380,
                                width=alt.Step(GROUP_STEP)
                            ).configure_title(anchor="start"),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>🧑‍💼 Sales Executive-wise Bookings by Visit Count</div>", unsafe_allow_html=True)
                SE_COL = "Sales Executive"
                VISIT_COL = "Visit Count"
                missing = [c for c in [SE_COL, VISIT_COL] if c not in df_ag.columns]
                if missing:
                    st.info(f"Missing columns: {', '.join(missing)}")
                else:
                    tmp = df_ag[[SE_COL, VISIT_COL]].copy()
                    tmp[SE_COL] = tmp[SE_COL].astype(str).str.strip()
                    tmp[VISIT_COL] = pd.to_numeric(tmp[VISIT_COL], errors="coerce")
                    tmp = tmp[(tmp[SE_COL] != "") & tmp[VISIT_COL].notna()]
                    tmp = tmp[tmp[VISIT_COL] > 0]
    
                    if tmp.empty:
                        st.info("No valid Sales Executive / Visit Count data available to plot.")
                    else:
                        tmp["VisitBucket"] = tmp[VISIT_COL].round(0).astype(int)
                        plot_df = (
                            tmp.groupby([SE_COL, "VisitBucket"])
                               .size()
                               .reset_index(name="Bookings")
                        )
    
                        se_order = (
                            plot_df.groupby(SE_COL)["Bookings"]
                                   .sum()
                                   .sort_values(ascending=False)
                                   .index.tolist()
                        )
                        visit_order = sorted(plot_df["VisitBucket"].unique().tolist())
    
                        plot_df[SE_COL] = pd.Categorical(plot_df[SE_COL], categories=se_order, ordered=True)
                        plot_df["VisitBucket"] = pd.Categorical(plot_df["VisitBucket"], categories=visit_order, ordered=True)
                        plot_df = plot_df.sort_values([SE_COL, "VisitBucket"])
    
                        n_visits = max(1, len(visit_order))
                        BAR_SIZE = 9 if n_visits >= 10 else (11 if n_visits >= 6 else 14)
                        GROUP_GAP = 0.25
                        SUB_GAP = 0.20 if n_visits >= 8 else 0.15
                        GROUP_STEP = max(140, int(n_visits * (BAR_SIZE + 7) + 90))
    
                        bars = alt.Chart(plot_df).mark_bar(
                            size=BAR_SIZE, cornerRadiusTopLeft=2, cornerRadiusTopRight=2
                        ).encode(
                            x=alt.X(f"{SE_COL}:N",
                                    sort=se_order,
                                    title="Sales Executive",
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP),
                                    axis=alt.Axis(labelAngle=0, labelLimit=220, labelOverlap=True)),
                            xOffset=alt.X("VisitBucket:N",
                                          sort=visit_order,
                                          title=None,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y=alt.Y("Bookings:Q", title="Bookings"),
                            color=alt.Color("VisitBucket:N",
                                            sort=visit_order,
                                            title="Visit Count",
                                            legend=alt.Legend(orient="top", direction="horizontal", columns=min(10, n_visits))),
                            tooltip=[
                                alt.Tooltip(f"{SE_COL}:N", title="Sales Executive"),
                                alt.Tooltip("VisitBucket:N", title="Visit Count"),
                                alt.Tooltip("Bookings:Q", title="Bookings")
                            ]
                        )
    
                        labels = alt.Chart(plot_df).mark_text(
                            dy=-5, fontSize=11, fontWeight="bold", color="#0f172a"
                        ).encode(
                            x=alt.X(f"{SE_COL}:N", sort=se_order,
                                    scale=alt.Scale(paddingInner=GROUP_GAP, paddingOuter=GROUP_GAP)),
                            xOffset=alt.X("VisitBucket:N", sort=visit_order,
                                          scale=alt.Scale(paddingInner=SUB_GAP, paddingOuter=SUB_GAP)),
                            y="Bookings:Q",
                            text=alt.Text("Bookings:Q", format=".0f")
                        )
    
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams(
                                    "Sales Executive-wise Bookings by Visit Count (Grouped Bars)",
                                    anchor="start", fontSize=16, fontWeight="bold", dy=-5
                                ),
                                height=400,
                                width=alt.Step(GROUP_STEP)
                            ).configure_title(anchor="start"),
                            use_container_width=True
                        )
    
                # ============================================================
                # LEAD / CONVERSION / VISIT / LOCATION / TYPE DATA
                # ============================================================
                section_heading_card("Lead, Conversion, Visit & Location Data")
    
                st.markdown("<div class='section-subtitle'>🏠 Type Wise</div>", unsafe_allow_html=True)
                type_chart_data = pd.DataFrame({'Type': type_wise_ag.index, 'Count': type_wise_ag.values})
                type_bar = alt.Chart(type_chart_data).mark_bar(color="#f59e0b").encode(
                    x=alt.X('Type:N', title='Type', axis=alt.Axis(labelAngle=0, labelLimit=140, labelOverlap=True)),
                    y=alt.Y('Count:Q', title='Bookings'),
                    tooltip=['Type', 'Count']
                )
                type_text = alt.Chart(type_chart_data).mark_text(
                    align='center', baseline='bottom', dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(x='Type:N', y='Count:Q', text='Count:Q')
                st.altair_chart(
                    (type_bar + type_text).properties(
                        title=alt.TitleParams("Type-wise Bookings", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=260, width=alt.Step(90)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
    
                st.markdown("<div class='section-subtitle'>🧭 Bookings by Lead Type</div>", unsafe_allow_html=True)
                LEAD_COL = "Lead Type"
                if LEAD_COL not in df_ag.columns:
                    st.info(f"Column '{LEAD_COL}' not found.")
                else:
                    lead_series = (
                        df_ag[LEAD_COL]
                        .astype(str).str.strip()
                        .replace({'': None})
                        .dropna()
                    )
                    if lead_series.empty:
                        st.info("No Lead Type data available.")
                    else:
                        vc = lead_series.value_counts()
                        lead_df = pd.DataFrame({"Lead Type": vc.index, "Bookings": vc.values})
                        lead_df = lead_df.sort_values('Bookings', ascending=True)
    
                        base = alt.Chart(lead_df)
                        bars = base.mark_bar(color="#2563eb").encode(
                            y=alt.Y('Lead Type:N', sort=lead_df['Lead Type'].tolist(), title='Lead Type'),
                            x=alt.X('Bookings:Q', title='Bookings'),
                            tooltip=['Lead Type:N', 'Bookings:Q']
                        )
                        labels = base.mark_text(
                            align='left', baseline='middle', dx=4, fontSize=12, fontWeight='bold', color='#0f172a'
                        ).encode(
                            y=alt.Y('Lead Type:N', sort=lead_df['Lead Type'].tolist()),
                            x='Bookings:Q',
                            text='Bookings:Q'
                        )
    
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams("Bookings by Lead Type", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                height=max(220, 24 * len(lead_df)),
                                width='container'
                            ).configure_axis(
                                labelLimit=220, labelOverlap=True
                            ).configure_title(anchor='start'),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>⏱️ Bookings by Conversion Period (Spot & 2-month buckets)</div>", unsafe_allow_html=True)
                CONV_COL = "Conversion Period (days)"
                if CONV_COL not in df_ag.columns:
                    st.info(f"Column '{CONV_COL}' not found.")
                else:
                    conv_all = pd.to_numeric(df_ag[CONV_COL], errors='coerce')
                    conv_all = conv_all[conv_all.notna() & (conv_all >= 0)]
                    if conv_all.empty:
                        st.info("No valid conversion-day values to compute buckets.")
                    else:
                        BUCKET_DAYS = 60
                        spot_count = int((conv_all == 0).sum())
                        nonzero = conv_all[conv_all >= 1]
    
                        if len(nonzero) > 0:
                            bidx = ((nonzero - 1) // BUCKET_DAYS).astype(int)
                            max_idx = int(bidx.max())
                            all_idx = list(range(0, max_idx + 1))
    
                            def label_for(i: int) -> str:
                                start = 2 * i
                                end = 2 * (i + 1)
                                return f"{start}–{end} months"
    
                            bucket_counts = (
                                bidx.value_counts()
                                    .reindex(all_idx, fill_value=0)
                                    .rename_axis('BucketIdx')
                                    .reset_index(name='Bookings')
                            )
                            bucket_counts['Bucket'] = bucket_counts['BucketIdx'].map(label_for)
                        else:
                            bucket_counts = pd.DataFrame(columns=['BucketIdx', 'Bookings', 'Bucket'])
                            all_idx = []
    
                        rows = [{"BucketIdx": -1, "Bucket": "Spot Booking (0 days)", "Bookings": spot_count, "Color": "Blue"}]
                        for _, r in bucket_counts.iterrows():
                            color = "Blue" if int(r['BucketIdx']) == 0 else "Red"
                            rows.append({
                                "BucketIdx": int(r['BucketIdx']),
                                "Bucket": str(r['Bucket']),
                                "Bookings": int(r['Bookings']),
                                "Color": color
                            })
    
                        plot_df = pd.DataFrame(rows)
                        sort_order = ["Spot Booking (0 days)"] + [f"{2*i}–{2*(i+1)} months" for i in all_idx]
                        color_domain = ["Blue", "Red"]
                        color_range = ["#2563eb", "#ef4444"]
    
                        base = alt.Chart(plot_df)
                        bars = base.mark_bar().encode(
                            x=alt.X('Bucket:N', sort=sort_order, title='Conversion Period'),
                            y=alt.Y('Bookings:Q', title='Bookings'),
                            color=alt.Color('Color:N', scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
                            tooltip=[alt.Tooltip('Bucket:N', title='Interval'), alt.Tooltip('Bookings:Q', title='Bookings')]
                        )
                        labels = base.mark_text(
                            dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                        ).encode(
                            x=alt.X('Bucket:N', sort=sort_order),
                            y='Bookings:Q',
                            text='Bookings:Q'
                        )
    
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams(
                                    "Bookings by Conversion Period (Spot, 0–2, 2–4, 4–6 months …)",
                                    anchor='start', fontSize=16, fontWeight='bold', dy=-5
                                ),
                                height=280, width=alt.Step(90)
                            ).configure_title(anchor='start'),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>📈 Booking Count by Visit Count</div>", unsafe_allow_html=True)
                VISIT_COL = "Visit Count"
                if VISIT_COL not in df_ag.columns:
                    st.info(f"Column '{VISIT_COL}' not found.")
                else:
                    tmp = df_ag[[VISIT_COL]].copy()
                    tmp[VISIT_COL] = pd.to_numeric(tmp[VISIT_COL], errors="coerce")
                    tmp = tmp.dropna(subset=[VISIT_COL])
                    tmp = tmp[tmp[VISIT_COL] > 0]
    
                    if tmp.empty:
                        st.info("No valid Visit Count values available to plot.")
                    else:
                        plot_df = (
                            tmp.groupby(VISIT_COL)
                               .size()
                               .reset_index(name="Bookings")
                               .sort_values(VISIT_COL)
                        )
    
                        plot_df["VisitInt"] = plot_df[VISIT_COL].round(0).astype(int)
                        plot_df = (
                            plot_df.groupby("VisitInt")["Bookings"]
                                   .sum()
                                   .reset_index()
                                   .rename(columns={"VisitInt": "Visit Count"})
                        )
    
                        line = alt.Chart(plot_df).mark_line(point=True).encode(
                            x=alt.X("Visit Count:Q",
                                    title="Visit Count",
                                    axis=alt.Axis(format="d", tickMinStep=1)),
                            y=alt.Y("Bookings:Q", title="Bookings"),
                            tooltip=[
                                alt.Tooltip("Visit Count:Q", title="Visit Count", format="d"),
                                alt.Tooltip("Bookings:Q", title="Bookings")
                            ]
                        )
    
                        labels = alt.Chart(plot_df).mark_text(
                            dy=-10, fontSize=12, fontWeight="bold", color="#0f172a"
                        ).encode(
                            x="Visit Count:Q",
                            y="Bookings:Q",
                            text=alt.Text("Bookings:Q", format=".0f")
                        )
    
                        st.altair_chart(
                            (line + labels).properties(
                                title=alt.TitleParams("Bookings vs Visit Count", anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                                height=320
                            ).configure_title(anchor="start"),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>📍 Location-wise Bookings</div>", unsafe_allow_html=True)
                LOC_COL = "Location"
                if LOC_COL not in df_ag.columns:
                    st.info(f"Column '{LOC_COL}' not found.")
                else:
                    loc_series = df_ag[LOC_COL].astype(str).str.strip().replace({'': None}).dropna()
    
                    if loc_series.empty:
                        st.info("No Location data available.")
                    else:
                        loc_counts = loc_series.value_counts()
                        loc_df = pd.DataFrame({"Location": loc_counts.index, "Bookings": loc_counts.values})
                        loc_df = loc_df.sort_values("Bookings", ascending=True)
    
                        base = alt.Chart(loc_df)
                        bars = base.mark_bar(color="#2563eb").encode(
                            y=alt.Y('Location:N', sort=loc_df['Location'].tolist(), title='Location'),
                            x=alt.X('Bookings:Q', title='Bookings'),
                            tooltip=[alt.Tooltip('Location:N'), alt.Tooltip('Bookings:Q')]
                        )
                        labels = base.mark_text(
                            align='left', baseline='middle', dx=4, fontSize=12, fontWeight='bold', color='#0f172a'
                        ).encode(
                            y=alt.Y('Location:N', sort=loc_df['Location'].tolist()),
                            x='Bookings:Q',
                            text=alt.Text('Bookings:Q', format='.0f')
                        )
    
                        st.altair_chart(
                            (bars + labels).properties(
                                title=alt.TitleParams("Location-wise Booking Count", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                                height=max(240, 24 * len(loc_df)),
                                width='container'
                            ).configure_title(anchor='start'),
                            use_container_width=True
                        )
    
                st.markdown("<div class='section-subtitle'>⏳ Time Taken per 50 Bookings</div>", unsafe_allow_html=True)
                DATE_COL = "Date"
                BATCH_SIZE = 50
                if DATE_COL not in df_ag.columns:
                    st.info(f"Column '{DATE_COL}' not found.")
                else:
                    tmp = df_ag[[DATE_COL]].copy()
                    tmp[DATE_COL] = pd.to_datetime(tmp[DATE_COL], errors="coerce")
                    tmp = tmp.dropna(subset=[DATE_COL]).sort_values(DATE_COL).reset_index(drop=True)
    
                    if tmp.empty:
                        st.info("No valid Date values available to compute duration.")
                    else:
                        tmp["BookingNo"] = tmp.index + 1
                        tmp["BatchIdx"] = (tmp["BookingNo"] - 1) // BATCH_SIZE
    
                        rows = []
                        n_batches = int(tmp["BatchIdx"].max()) + 1
    
                        for b in range(n_batches):
                            sub = tmp[tmp["BatchIdx"] == b]
                            if sub.empty:
                                continue
    
                            start_no = b * BATCH_SIZE
                            end_no = min((b + 1) * BATCH_SIZE, len(tmp))
                            bucket_label = f"{start_no}–{end_no}"
    
                            start_dt = sub[DATE_COL].min()
                            end_dt = sub[DATE_COL].max()
    
                            days = int((end_dt - start_dt).days) if pd.notna(start_dt) and pd.notna(end_dt) else 0
                            months = days / 30.0
    
                            rows.append({
                                "Bucket": bucket_label,
                                "Days": days,
                                "MonthsApprox": months,
                                "Label": f"{days} days ({months:.1f} mo)"
                            })
    
                        plot_df = pd.DataFrame(rows)
    
                        if plot_df.empty:
                            st.info("Not enough data to build 50-booking duration buckets.")
                        else:
                            bucket_order = plot_df["Bucket"].tolist()
    
                            bars = alt.Chart(plot_df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
                                x=alt.X("Bucket:N", sort=bucket_order, title="Booking Range"),
                                y=alt.Y("Days:Q", title="Time Taken (days)"),
                                tooltip=[
                                    alt.Tooltip("Bucket:N", title="Range"),
                                    alt.Tooltip("Days:Q", title="Days"),
                                    alt.Tooltip("MonthsApprox:Q", title="Approx Months", format=".1f")
                                ]
                            )
    
                            labels = alt.Chart(plot_df).mark_text(
                                dy=-6, fontSize=12, fontWeight="bold", color="#0f172a"
                            ).encode(
                                x=alt.X("Bucket:N", sort=bucket_order),
                                y="Days:Q",
                                text="Label:N"
                            )
    
                            st.altair_chart(
                                (bars + labels).properties(
                                    title=alt.TitleParams("Time Duration per 50 Bookings", anchor="start", fontSize=16, fontWeight="bold", dy=-5),
                                    height=320,
                                    width=alt.Step(90)
                                ).configure_title(anchor="start"),
                                use_container_width=True
                            )
    
                # ============================================================
                # PRICING / REVENUE / NEGOTIATION DATA
                # ============================================================
                section_heading_card("Pricing, Revenue & Agreement Data")
    
                df_bd = df_ag.copy()
                df_bd['_NearestSizeBD'] = pd.to_numeric(df_bd.get('Carpet Area', 0), errors='coerce').apply(nearest_size)
                df_bd['_TypeForBD'] = df_bd.get('Type', '').astype(str).str.upper().str.strip()
                _bad = ~df_bd['_TypeForBD'].isin(['1BHK', '2BHK'])
                df_bd.loc[_bad, '_TypeForBD'] = df_bd.loc[_bad, '_NearestSizeBD'].map(SIZE_TYPE_MAP)
    
                if '_FinalPrice_Full' not in df_bd.columns or '_FinalPrice_L' not in df_bd.columns:
                    fp_clean_all = (
                        df_bd['Final Price'].astype(str)
                             .str.replace(',', '', regex=True)
                             .str.replace('₹', '', regex=False)
                             .str.replace(r'(?i)\s*(rs|inr)\.?\s*', '', regex=True)
                             .str.replace(r'(?i)\s*(lac|lacs|lakh|lakhs)\.?\s*', '', regex=True)
                             .str.strip()
                    )
                    df_bd['_FinalPrice_L'] = pd.to_numeric(fp_clean_all, errors='coerce')
                    df_bd['_FinalPrice_Full'] = (df_bd['_FinalPrice_L'] * 100000).astype('float')
    
                st.markdown("<div class='section-subtitle'>💰 Average Closing Price — 1BHK vs 2BHK (Final Price)</div>", unsafe_allow_html=True)
                df_fp = df_bd.dropna(subset=['_FinalPrice_Full']).copy()
                avg_close_full = (
                    df_fp.groupby('_TypeForBD')['_FinalPrice_Full']
                         .mean()
                         .reindex(['1BHK', '2BHK'])
                )
                avg_close_full = avg_close_full.dropna().reset_index().rename(
                    columns={'_TypeForBD': 'Type', '_FinalPrice_Full': 'AvgCloseFull'}
                )
    
                if not avg_close_full.empty:
                    avg_close_full['Label'] = avg_close_full['AvgCloseFull'].map(lambda v: f"₹{v:,.0f}")
                    chart_avg_close = alt.Chart(avg_close_full).mark_bar().encode(
                        x=alt.X('Type:N', title='Type'),
                        y=alt.Y('AvgCloseFull:Q', title='Average Closing (₹)'),
                        tooltip=[
                            alt.Tooltip('Type:N'),
                            alt.Tooltip('AvgCloseFull:Q', format=',.0f', title='Average Closing (₹)')
                        ]
                    )
                    labels_avg_close = alt.Chart(avg_close_full).mark_text(
                        dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(
                        x='Type:N',
                        y='AvgCloseFull:Q',
                        text='Label:N'
                    )
                    st.altair_chart(
                        (chart_avg_close + labels_avg_close).properties(height=280).configure_title(anchor='start'),
                        use_container_width=True
                    )
                else:
                    st.info("No Final Price data to compute average closing price.")
    
                COSTSHEET_1BHK_L = 48.50
                COSTSHEET_2BHK_L = 67.50
                COSTSHEET_1BHK_FULL = COSTSHEET_1BHK_L * 100000.0
                COSTSHEET_2BHK_FULL = COSTSHEET_2BHK_L * 100000.0
    
                ef_sub = df_bd[df_bd['Wing'].isin(['E', 'F'])].copy()
                ef_sub = ef_sub.dropna(subset=['_FinalPrice_Full'])
    
                ef_sub['_Negotiated'] = ef_sub.apply(
                    lambda r: (COSTSHEET_1BHK_FULL - r['_FinalPrice_Full']) if r['_TypeForBD'] == '1BHK'
                    else (COSTSHEET_2BHK_FULL - r['_FinalPrice_Full']) if r['_TypeForBD'] == '2BHK'
                    else float('nan'),
                    axis=1
                )
    
                nego_avg = (
                    ef_sub.dropna(subset=['_Negotiated'])
                          .groupby('_TypeForBD')['_Negotiated']
                          .mean()
                          .reindex(['1BHK', '2BHK'])
                )
                nego_avg = nego_avg.dropna().reset_index().rename(
                    columns={'_TypeForBD': 'Type', '_Negotiated': 'AvgNegotiated'}
                )
    
                st.markdown("<div class='section-subtitle'>📉 Average Negotiated Amount — E & F (₹)</div>", unsafe_allow_html=True)
                if not nego_avg.empty:
                    nego_avg['Label'] = nego_avg['AvgNegotiated'].map(lambda v: f"₹{v:,.0f}")
                    chart_nego_avg = alt.Chart(nego_avg).mark_bar().encode(
                        x=alt.X('Type:N', title='Type'),
                        y=alt.Y('AvgNegotiated:Q', title='Average Negotiated (₹)'),
                        tooltip=[
                            alt.Tooltip('Type:N'),
                            alt.Tooltip('AvgNegotiated:Q', format=',.0f', title='Average Negotiated (₹)')
                        ]
                    )
                    labels_nego_avg = alt.Chart(nego_avg).mark_text(
                        dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(
                        x='Type:N',
                        y='AvgNegotiated:Q',
                        text='Label:N'
                    )
                    st.altair_chart(
                        (chart_nego_avg + labels_nego_avg).properties(height=280).configure_title(anchor='start'),
                        use_container_width=True
                    )
                else:
                    st.info("No E & F Final Price data to compute average negotiation.")
    
                import math
    
                def _br_low_high_lakh(v_lakh: float):
                    low = math.floor(v_lakh * 2) / 2.0
                    high = low + 0.50
                    return low, high
    
                def _top5_by_price_brackets(df_in: pd.DataFrame, type_name: str):
                    sub = df_in[(df_in['_TypeForBD'] == type_name) & df_in['_FinalPrice_L'].notna()].copy()
                    if sub.empty:
                        return pd.DataFrame(columns=['Bracket', 'Count', '_hi'])
    
                    lows, highs, labels = [], [], []
                    for v in sub['_FinalPrice_L']:
                        lo, hi = _br_low_high_lakh(float(v))
                        lows.append(lo)
                        highs.append(hi)
                        labels.append(f"{lo:.2f} - {hi:.2f}")
    
                    sub['Bracket'] = labels
                    sub['_hi'] = highs
    
                    counts = (
                        sub.groupby(['Bracket', '_hi'])
                           .size()
                           .reset_index(name='Count')
                           .sort_values(['_hi'], ascending=[False])
                    )
                    return counts.groupby('_hi', as_index=False).first().sort_values('_hi', ascending=False).head(5)
    
                st.markdown("<div class='section-subtitle'>📦 Highest Final-Price Brackets — 1BHK (Dynamic, Lakhs)</div>", unsafe_allow_html=True)
                top1_price = _top5_by_price_brackets(df_bd, '1BHK')
                if not top1_price.empty:
                    top_br_1 = top1_price.iloc[0]
                    st.markdown(
                        f"<div class='chips'>"
                        f"<span class='chip ok'><span class='dot'></span> Highest Bracket: {top_br_1['Bracket']}</span>"
                        f"<span class='chip ok'><span class='dot'></span> Bookings: {int(top_br_1['Count'])}</span>"
                        f"</div>", unsafe_allow_html=True
                    )
                    top1_price = top1_price.sort_values('_hi', ascending=False)
                    c1 = alt.Chart(top1_price).mark_bar().encode(
                        x=alt.X('Bracket:N', title='Final Price (Lakhs)', sort=list(top1_price['Bracket'])),
                        y=alt.Y('Count:Q', title='Bookings'),
                        tooltip=[alt.Tooltip('Bracket:N', title='Bracket'),
                                 alt.Tooltip('Count:Q', title='Count')]
                    )
                    t1 = alt.Chart(top1_price).mark_text(
                        dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(x='Bracket:N', y='Count:Q', text='Count:Q')
                    st.altair_chart((c1 + t1).properties(height=280).configure_title(anchor='start'),
                                    use_container_width=True)
                else:
                    st.info("No 1BHK Final Price data to build dynamic brackets.")
    
                st.markdown("<div class='section-subtitle'>📦 Highest Final-Price Brackets — 2BHK (Dynamic, Lakhs)</div>", unsafe_allow_html=True)
                top2_price = _top5_by_price_brackets(df_bd, '2BHK')
                if not top2_price.empty:
                    top_br_2 = top2_price.iloc[0]
                    st.markdown(
                        f"<div class='chips'>"
                        f"<span class='chip ok'><span class='dot'></span> Highest Bracket: {top_br_2['Bracket']}</span>"
                        f"<span class='chip ok'><span class='dot'></span> Bookings: {int(top_br_2['Count'])}</span>"
                        f"</div>", unsafe_allow_html=True
                    )
                    top2_price = top2_price.sort_values('_hi', ascending=False)
                    c2 = alt.Chart(top2_price).mark_bar().encode(
                        x=alt.X('Bracket:N', title='Final Price (Lakhs)', sort=list(top2_price['Bracket'])),
                        y=alt.Y('Count:Q', title='Bookings'),
                        tooltip=[alt.Tooltip('Bracket:N', title='Bracket'),
                                 alt.Tooltip('Count:Q', title='Count')]
                    )
                    t2 = alt.Chart(top2_price).mark_text(
                        dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                    ).encode(x='Bracket:N', y='Count:Q', text='Count:Q')
                    st.altair_chart((c2 + t2).properties(height=280).configure_title(anchor='start'),
                                    use_container_width=True)
                else:
                    st.info("No 2BHK Final Price data to build dynamic brackets.")
    
                st.markdown("<div class='section-subtitle'>📈 1BHK & 2BHK — Booking-wise Agreement Cost (First → Latest)</div>", unsafe_allow_html=True)
                df_line = df_ag.copy()
    
                if 'Agreement Cost' not in df_line.columns:
                    df_line['Agreement Cost'] = 0.0
                df_line['Agreement Cost'] = pd.to_numeric(df_line['Agreement Cost'], errors='coerce')
    
                df_line['_NearestSizeBD'] = pd.to_numeric(df_line.get('Carpet Area', 0), errors='coerce').apply(nearest_size)
                df_line['_TypeForBD'] = df_line.get('Type', '').astype(str).str.upper().str.strip()
                _bad_t = ~df_line['_TypeForBD'].isin(['1BHK', '2BHK'])
                df_line.loc[_bad_t, '_TypeForBD'] = df_line.loc[_bad_t, '_NearestSizeBD'].map(SIZE_TYPE_MAP)
                df_line = df_line.dropna(subset=['Date', 'Agreement Cost']).copy()
    
                def _booking_line_chart(sub_df: pd.DataFrame, title: str):
                    if sub_df.empty:
                        st.info(f"No data available for {title}.")
                        return
    
                    sub_df = sub_df.sort_values('Date', kind='mergesort').reset_index(drop=True)
                    sub_df['Booking #'] = sub_df.index + 1
    
                    tt = [
                        alt.Tooltip('Booking #:Q', title='Booking #'),
                        alt.Tooltip('Date:T', title='Date'),
                        alt.Tooltip('Agreement Cost:Q', title='Agreement Cost (₹)', format=',.0f'),
                    ]
                    if 'Wing' in sub_df.columns:
                        tt.append(alt.Tooltip('Wing:N', title='Wing'))
                    if 'Flat Number' in sub_df.columns:
                        tt.append(alt.Tooltip('Flat Number:N', title='Flat'))
    
                    base = alt.Chart(sub_df)
                    line = base.mark_line(point=True).encode(
                        x=alt.X('Booking #:Q', title='Booking (sorted by Date)'),
                        y=alt.Y('Agreement Cost:Q', title='Agreement Cost (₹)'),
                        tooltip=tt
                    )
    
                    st.altair_chart(
                        line.properties(
                            title=alt.TitleParams(title, anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                            height=320
                        ).configure_title(anchor='start'),
                        use_container_width=True
                    )
    
                df_1 = df_line[df_line['_TypeForBD'] == '1BHK'].copy()
                _booking_line_chart(df_1, "1BHK — Booking-wise Agreement Cost")
    
                df_2 = df_line[df_line['_TypeForBD'] == '2BHK'].copy()
                _booking_line_chart(df_2, "2BHK — Booking-wise Agreement Cost")
    
                # ============================================================
                # FINAL TABLES AT END OF AGREEMENT DONE DASHBOARD (WING-WISE)
                # ============================================================
                section_heading_card("Quarter-wise Wing & Sales Executive Summary Tables")
                
                st.markdown(
                    "<div class='section-subtitle'>📋 Quarter-wise Wing-wise & Sales Executive-wise Agreement Cost Sold & Saleable Area Sold</div>",
                    unsafe_allow_html=True
                )
                
                required_cols_tbl = {'Quarter', 'Wing', 'Sales Executive', 'Agreement Cost', 'Carpet Area'}
                missing_tbl = [c for c in required_cols_tbl if c not in df_ag.columns]
                
                if missing_tbl:
                    st.info(f"Missing columns for final table: {', '.join(missing_tbl)}")
                else:
                    tbl_df = df_ag[['Quarter', 'Wing', 'Sales Executive', 'Agreement Cost', 'Carpet Area']].copy()
                
                    tbl_df['Quarter'] = tbl_df['Quarter'].astype(str).str.strip()
                    tbl_df['Wing'] = tbl_df['Wing'].astype(str).str.strip()
                    tbl_df['Sales Executive'] = tbl_df['Sales Executive'].astype(str).str.strip()
                
                    ag_clean = (
                        tbl_df['Agreement Cost'].astype(str)
                              .str.replace(',', '', regex=True)
                              .str.replace('₹', '', regex=False)
                              .str.replace(r'(?i)\s*(rs|inr)\.?\s*', '', regex=True)
                              .str.strip()
                    )
                    tbl_df['Agreement Cost'] = pd.to_numeric(ag_clean, errors='coerce')
                    tbl_df['Carpet Area'] = pd.to_numeric(tbl_df['Carpet Area'], errors='coerce')
                    tbl_df['Saleable Area Sold'] = tbl_df['Carpet Area'] * 1.38
                
                    tbl_df = tbl_df[
                        (tbl_df['Quarter'] != "") &
                        (tbl_df['Wing'] != "") &
                        (tbl_df['Sales Executive'] != "")
                    ]
                    tbl_df = tbl_df.dropna(subset=['Agreement Cost', 'Saleable Area Sold'])
                
                    if tbl_df.empty:
                        st.info("No data available for quarter-wise wing-wise sales executive-wise agreement/saleable area tables.")
                    else:
                        final_tbl = (
                            tbl_df.groupby(['Quarter', 'Wing', 'Sales Executive'], as_index=False)
                                  .agg({
                                      'Agreement Cost': 'sum',
                                      'Saleable Area Sold': 'sum'
                                  })
                                  .rename(columns={
                                      'Agreement Cost': 'Agreement Cost Sold (₹)',
                                      'Saleable Area Sold': 'Saleable Area Sold (sq ft)'
                                  })
                        )
                
                        q_domain = ordered_quarters_ag if ordered_quarters_ag else sorted(final_tbl['Quarter'].unique().tolist())
                        wing_order = sorted(final_tbl['Wing'].unique().tolist())
                
                        final_tbl['Quarter'] = pd.Categorical(final_tbl['Quarter'], categories=q_domain, ordered=True)
                        final_tbl['Wing'] = pd.Categorical(final_tbl['Wing'], categories=wing_order, ordered=True)
                
                        for wing in wing_order:
                            wing_tbl = final_tbl[final_tbl['Wing'] == wing].copy()
                
                            if wing_tbl.empty:
                                continue
                
                            se_order = (
                                wing_tbl.groupby('Sales Executive')['Agreement Cost Sold (₹)']
                                        .sum()
                                        .sort_values(ascending=False)
                                        .index
                                        .tolist()
                            )
                
                            wing_tbl['Sales Executive'] = pd.Categorical(
                                wing_tbl['Sales Executive'],
                                categories=se_order,
                                ordered=True
                            )
                
                            wing_tbl = wing_tbl.sort_values(['Quarter', 'Sales Executive']).reset_index(drop=True)
                
                            wing_tbl_display = wing_tbl.copy()
                            wing_tbl_display['Agreement Cost Sold (₹)'] = wing_tbl_display['Agreement Cost Sold (₹)'].map(lambda x: f"₹{x:,.0f}")
                            wing_tbl_display['Saleable Area Sold (sq ft)'] = wing_tbl_display['Saleable Area Sold (sq ft)'].map(lambda x: f"{x:,.0f}")
                
                            st.markdown(
                                f"<div class='section-subtitle'>🏢 Wing {wing}</div>",
                                unsafe_allow_html=True
                            )
                            st.dataframe(
                                wing_tbl_display[['Quarter', 'Wing', 'Sales Executive', 'Agreement Cost Sold (₹)', 'Saleable Area Sold (sq ft)']],
                                use_container_width=True,
                                hide_index=True
                            )
    with TAB_INVENTORY:
            st.header("🏢 Inventory Dashboard")
        
            # Wing Inventory vs Bookings (clustered)
            st.markdown("<div class='section-subtitle'>🏢 Wing Inventory vs Bookings</div>", unsafe_allow_html=True)
            booked_by_wing = wing_wise.to_dict()
            rows = []
            all_wings = sorted(set(list(booked_by_wing.keys()) + list(WING_TOTALS.keys())))
            for wing in all_wings:
                booked = int(booked_by_wing.get(wing, 0))
                total = int(WING_TOTALS.get(wing, booked))
                available = max(total - booked, 0)
                rows += [
                    {"Wing": wing, "Metric": "Booked", "Count": booked},
                    {"Wing": wing, "Metric": "Available", "Count": available},
                    {"Wing": wing, "Metric": "Total", "Count": total},
                ]
            wing_inv_df = pd.DataFrame(rows)
            wing_cluster = alt.Chart(wing_inv_df).mark_bar(size=12).encode(
                x=alt.X('Wing:N', title='Wing', scale=alt.Scale(paddingInner=0.35, paddingOuter=0.35),
                        axis=alt.Axis(labelAngle=0, labelLimit=120, labelOverlap=True)),
                xOffset=alt.X('Metric:N'),
                y=alt.Y('Count:Q', title='Units'),
                color=alt.Color('Metric:N', scale=alt.Scale(domain=METRICS, range=METRIC_COLORS), legend=alt.Legend(title="", orient='top')),
                tooltip=['Wing:N', 'Metric:N', 'Count:Q']
            )
            wing_labels = alt.Chart(wing_inv_df).mark_text(
                dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
            ).encode(
                x=alt.X('Wing:N'),
                xOffset='Metric:N',
                y='Count:Q',
                text='Count:Q'
            )
            st.altair_chart(
                (wing_cluster + wing_labels).properties(
                    title=alt.TitleParams("Wing Inventory vs Bookings", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                    height=300, width=alt.Step(80)
                ).configure_title(anchor='start'),
                use_container_width=True
            )
        
            # Inventory by Type — separate charts for each wing
            for wing in WINGS:
                st.markdown(f"<div class='section-subtitle'>🏢 Wing {wing} — Inventory by Type</div>", unsafe_allow_html=True)
        
                def build_wing_type_inventory_df(df_in: pd.DataFrame, wing_: str) -> pd.DataFrame:
                    booked_counts = (
                        df_in[df_in['Wing'].astype(str).str.strip() == wing_]
                        .groupby('Type').size().reindex(TYPE_DOMAIN, fill_value=0).to_dict()
                    )
                    rows2 = []
                    for t in TYPE_DOMAIN:
                        booked = int(booked_counts.get(t, 0))
                        total = int(WING_TYPE_TOTALS.get((wing_, t), booked))
                        available = max(total - booked, 0)
                        rows2 += [
                            {"Wing": wing_, "Type": t, "Metric": "Booked", "Count": booked},
                            {"Wing": wing_, "Type": t, "Metric": "Available", "Count": available},
                            {"Wing": wing_, "Type": t, "Metric": "Total", "Count": total},
                        ]
                    return pd.DataFrame(rows2)
        
                wing_df = build_wing_type_inventory_df(df, wing)
                st.altair_chart(wing_type_chart(wing_df, wing), use_container_width=True)
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        
            # Podium by Type (Wing-wise)
            st.markdown("<div class='section-subtitle'>🪟 Podium Inventory by Type (Wing-wise)</div>", unsafe_allow_html=True)
        
            def podium_inventory_by_type(wing: str) -> pd.DataFrame:
                rows3 = []
                for t in TYPE_DOMAIN:
                    sizes_t = [s for s in PODIUM_SIZES if SIZE_TYPE_MAP.get(s) == t]
                    total = sum(int(CARPET_TOTALS.get((wing, s), 0)) for s in sizes_t)
                    booked = sum(int(size_booked.get((wing, s), 0)) for s in sizes_t)
                    available = max(total - booked, 0)
                    rows3 += [
                        {"Wing": wing, "Type": t, "Metric": "Booked", "Count": booked},
                        {"Wing": wing, "Type": t, "Metric": "Available", "Count": available},
                        {"Wing": wing, "Type": t, "Metric": "Total", "Count": total},
                    ]
                return pd.DataFrame(rows3)
        
            for wing in WINGS:
                dfp = podium_inventory_by_type(wing)
                chart_podium = grouped_bar_with_gaps(dfp, x_field="Type", x_domain=TYPE_DOMAIN, title=f"Wing {wing} — Podium Flats by Type")
                st.altair_chart(chart_podium, use_container_width=True)
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        
            # Inventory by Facing (Wing-wise)
            st.markdown("<div class='section-subtitle'>🏞️ Inventory by Facing (Wing-wise)</div>", unsafe_allow_html=True)
            for wing in WINGS:
                df_face = pd.DataFrame([
                    {"Wing": wing, "Facing": face, "Metric": metric, "Count": (
                        sum(int(CARPET_TOTALS.get((wing, s), 0)) for s in FACING_MAP[face]) if metric == "Total" else
                        sum(int(size_booked.get((wing, s), 0)) for s in FACING_MAP[face]) if metric == "Booked" else
                        max(
                            sum(int(CARPET_TOTALS.get((wing, s), 0)) for s in FACING_MAP[face]) -
                            sum(int(size_booked.get((wing, s), 0)) for s in FACING_MAP[face]), 0
                        )
                    )}
                    for face in FACING_DOMAIN
                    for metric in METRICS
                ])
                chart_face = grouped_bar_with_gaps(df_face, x_field="Facing", x_domain=FACING_DOMAIN, title=f"Wing {wing} — Facing (Garden vs Road)")
                st.altair_chart(chart_face, use_container_width=True)
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        
            # Inventory by Carpet Area (Wing-wise)
            st.markdown("<div class='section-subtitle'>📐 Inventory by Carpet Area (Wing-wise)</div>", unsafe_allow_html=True)
            for wing in WINGS:
                rows = []
                for s in CARPET_SIZES:
                    total = int(CARPET_TOTALS.get((wing, s), 0))
                    booked = int(size_booked.get((wing, s), 0))
                    available = max(total - booked, 0)
                    rows += [
                        {"Wing": wing, "Size": f"{s:.2f}", "Metric": "Booked", "Count": booked},
                        {"Wing": wing, "Size": f"{s:.2f}", "Metric": "Available", "Count": available},
                        {"Wing": wing, "Size": f"{s:.2f}", "Metric": "Total", "Count": total},
                    ]
                df_size = pd.DataFrame(rows)
                chart_size = grouped_bar_with_gaps(df_size, x_field="Size", x_domain=CARPET_LABELS, title=f"Wing {wing} — Carpet Sizes")
                st.altair_chart(chart_size, use_container_width=True)
                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        
            # Merged Units Sold
            st.markdown("<div class='section-subtitle'>🔗 Merged Units Sold</div>", unsafe_allow_html=True)
        
            MERGED_DOMAIN = ["1+1", "2+1", "2+2"]
            MERGED_COL = "Merged Units"
        
            if MERGED_COL in df.columns:
                mu = df[MERGED_COL].dropna().astype(str).str.strip()
                mu = mu[mu.isin(MERGED_DOMAIN)]
        
                merged_counts = mu.value_counts().reindex(MERGED_DOMAIN, fill_value=0)
                merged_df = (
                    (merged_counts / 2.0)
                    .rename("Merged Units Sold")
                    .reset_index()
                    .rename(columns={"index": MERGED_COL})
                )
        
                chart_merged = alt.Chart(merged_df).mark_bar(size=28).encode(
                    x=alt.X(f'{MERGED_COL}:N', sort=MERGED_DOMAIN, title="Merged Combination",
                            axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('Merged Units Sold:Q', title="Merged Units Sold"),
                    tooltip=[
                        alt.Tooltip(f'{MERGED_COL}:N', title="Merged Units"),
                        alt.Tooltip('Merged Units Sold:Q', format='.2f')
                    ]
                ).properties(
                    title=alt.TitleParams("Merged Units Sold", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                    height=280
                )
        
                merged_labels = alt.Chart(merged_df).mark_text(
                    dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    x=alt.X(f'{MERGED_COL}:N', sort=MERGED_DOMAIN),
                    y=alt.Y('Merged Units Sold:Q'),
                    text=alt.Text('Merged Units Sold:Q', format='.0f')
                )
        
                st.altair_chart((chart_merged + merged_labels).configure_title(anchor='start'),
                                use_container_width=True)
            else:
                st.info('Column "Merged Units" not found in df, so Merged Units Sold chart was skipped.')
        
            # Wing-wise Merged Units Sold
            st.markdown("<div class='section-subtitle'>🔗 Wing-wise Merged Units Sold</div>", unsafe_allow_html=True)
        
            if ("Wing" in df.columns) and (MERGED_COL in df.columns):
                df_mu = df[["Wing", MERGED_COL]].dropna().copy()
                df_mu["Wing"] = df_mu["Wing"].astype(str).str.strip()
                df_mu[MERGED_COL] = df_mu[MERGED_COL].astype(str).str.strip()
                df_mu = df_mu[df_mu[MERGED_COL].isin(MERGED_DOMAIN)]
        
                wing_domain = WINGS if "WINGS" in locals() else sorted(df_mu["Wing"].unique())
        
                rows_mu = []
                for w in wing_domain:
                    for m in MERGED_DOMAIN:
                        c = int(((df_mu["Wing"] == w) & (df_mu[MERGED_COL] == m)).sum())
                        rows_mu.append({
                            "Wing": w,
                            MERGED_COL: m,
                            "Merged Units Sold": c / 2.0
                        })
                merged_wing_df = pd.DataFrame(rows_mu)
        
                merged_wing_chart = alt.Chart(merged_wing_df).mark_bar(size=12).encode(
                    x=alt.X('Wing:N', title='Wing',
                            sort=wing_domain,
                            scale=alt.Scale(paddingInner=0.35, paddingOuter=0.35),
                            axis=alt.Axis(labelAngle=0, labelLimit=120, labelOverlap=True)),
                    xOffset=alt.X(f'{MERGED_COL}:N', sort=MERGED_DOMAIN),
                    y=alt.Y('Merged Units Sold:Q', title='Merged Units Sold'),
                    color=alt.Color(f'{MERGED_COL}:N', legend=alt.Legend(title="", orient='top')),
                    tooltip=[
                        alt.Tooltip('Wing:N'),
                        alt.Tooltip(f'{MERGED_COL}:N', title="Merged Units"),
                        alt.Tooltip('Merged Units Sold:Q', format='.2f')
                    ]
                )
        
                merged_wing_labels = alt.Chart(merged_wing_df).mark_text(
                    dy=-5, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    x=alt.X('Wing:N', sort=wing_domain),
                    xOffset=alt.X(f'{MERGED_COL}:N', sort=MERGED_DOMAIN),
                    y=alt.Y('Merged Units Sold:Q'),
                    text=alt.Text('Merged Units Sold:Q', format='.0f')
                )
        
                st.altair_chart(
                    (merged_wing_chart + merged_wing_labels).properties(
                        title=alt.TitleParams("Wing-wise Merged Units Sold", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=300, width=alt.Step(80)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
            else:
                st.info('Required columns ("Wing" and "Merged Units") not found in df, so Wing-wise Merged chart was skipped.')
    with TAB_MONTHLY:
        st.header("🧾 Monthly Stamp Duty & Agreement Status")
        st.markdown("<div class='section-subtitle'>📅 Monthly Stamp Duty & Agreement Status</div>", unsafe_allow_html=True)

        if 'MonthYear' in df.columns and not df.empty:
            month_options = sorted(df['MonthYear'].dropna().unique().tolist())
            if month_options:
                selected_month = st.selectbox("Select Month", month_options)
                monthly_df = df[df['MonthYear'] == selected_month]
                if monthly_df.empty:
                    st.info("No records for the selected month.")
                    st.stop()

                executives_list = sorted(
                    [
                        str(x).strip()
                        for x in df["Sales Executive"].dropna().unique().tolist()
                        if str(x).strip() != "" and str(x).strip().upper() != "NAN"
                    ]
                )

                # --- Table summary ---
                summary_stats = []
                for exec_name in executives_list:
                    exec_data = monthly_df[monthly_df['Sales Executive'] == exec_name]
                    stamp_duty_received_cnt = (exec_data['Stamp Duty'].str.lower() == 'received').sum()
                    stamp_duty_pending_cnt = len(exec_data) - stamp_duty_received_cnt
                    agreement_done_cnt = (exec_data['Agreement Done'].str.lower() == 'done').sum()
                    agreement_pending_cnt = len(exec_data) - agreement_done_cnt
                    summary_stats.append({
                        "Sales Executive": exec_name,
                        "Stamp Duty Received": stamp_duty_received_cnt,
                        "Stamp Duty Pending": stamp_duty_pending_cnt,
                        "Agreement Done": agreement_done_cnt,
                        "Agreement Pending": agreement_pending_cnt
                    })
                monthly_summary_df = pd.DataFrame(summary_stats)
                st.markdown(monthly_summary_df.to_html(index=False, classes="styled-table"), unsafe_allow_html=True)

                # ---- Charts ----
                stats_df = monthly_summary_df.copy()
                stats_df["Stamp Duty Total"] = stats_df["Stamp Duty Received"] + stats_df["Stamp Duty Pending"]
                stats_df["Agreement Total"]  = stats_df["Agreement Done"] + stats_df["Agreement Pending"]

                st.markdown("<div class='section-subtitle'>📦 Stamp Duty Status by Sales Executive</div>", unsafe_allow_html=True)
                stamp_long = stats_df.melt(
                    id_vars="Sales Executive",
                    value_vars=["Stamp Duty Total", "Stamp Duty Received", "Stamp Duty Pending"],
                    var_name="Metric",
                    value_name="Count"
                ).replace({"Metric": {
                    "Stamp Duty Total": "Total", "Stamp Duty Received": "Received", "Stamp Duty Pending": "Pending"
                }})
                stamp_bar = alt.Chart(stamp_long).mark_bar().encode(
                    x=alt.X('Sales Executive:N', title='Sales Executive',
                            axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True),
                            scale=alt.Scale(paddingInner=0.35, paddingOuter=0.35)),
                    xOffset='Metric:N',
                    y=alt.Y('Count:Q', title='Units'),
                    color=alt.Color('Metric:N',
                                    scale=alt.Scale(domain=["Total","Received","Pending"], range=["#6366f1","#10b981","#f59e0b"]),
                                    legend=alt.Legend(title="", orient='top')),
                    tooltip=['Sales Executive:N', 'Metric:N', 'Count:Q']
                )
                stamp_text = alt.Chart(stamp_long).mark_text(
                    dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(x='Sales Executive:N', xOffset='Metric:N', y='Count:Q', text='Count:Q')
                st.altair_chart(
                    (stamp_bar + stamp_text).properties(
                        title=alt.TitleParams("Stamp Duty Status by Sales Executive", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=340, width=alt.Step(80)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )

                st.markdown("<div class='section-subtitle'>📝 Agreement Status by Sales Executive</div>", unsafe_allow_html=True)
                agree_long = stats_df.melt(
                    id_vars="Sales Executive",
                    value_vars=["Agreement Total", "Agreement Done", "Agreement Pending"],
                    var_name="Metric",
                    value_name="Count"
                ).replace({"Metric": {
                    "Agreement Total": "Total", "Agreement Done": "Done", "Agreement Pending": "Pending"
                }})
                agree_bar = alt.Chart(agree_long).mark_bar().encode(
                    x=alt.X('Sales Executive:N', title='Sales Executive',
                            axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True),
                            scale=alt.Scale(paddingInner=0.35, paddingOuter=0.35)),
                    xOffset='Metric:N',
                    y=alt.Y('Count:Q', title='Units'),
                    color=alt.Color('Metric:N',
                                    scale=alt.Scale(domain=["Total","Done","Pending"], range=["#6366f1","#10b981","#f59e0b"]),
                                    legend=alt.Legend(title="", orient='top')),
                    tooltip=['Sales Executive:N', 'Metric:N', 'Count:Q']
                )
                agree_text = alt.Chart(agree_long).mark_text(
                    dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(x='Sales Executive:N', xOffset='Metric:N', y='Count:Q', text='Count:Q')
                st.altair_chart(
                    (agree_bar + agree_text).properties(
                        title=alt.TitleParams("Agreement Status by Sales Executive", anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=340, width=alt.Step(80)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )
            else:
                st.info("No valid months available for selection.")
        else:
            st.warning("Month data is missing or empty.")

        # ---- NEW: Overall Funding Source chart (Insider / Outsider / Self Funded) ----
        st.markdown("<div class='section-subtitle'>🏦 Funding Source by Sales Executive — Overall</div>", unsafe_allow_html=True)
    
        req_cols = ['Sales Executive', 'Insider Banker', 'Outsider Banker']
        missing_funding_cols = [c for c in req_cols if c not in df.columns]
        if missing_funding_cols:
            st.warning(f"Missing columns for funding chart: {', '.join(missing_funding_cols)}")
        else:
            def _funding_overall(row):
                ib = str(row.get('Insider Banker', '')).strip().lower()
                ob = str(row.get('Outsider Banker', '')).strip().lower()
                if ib == 'yes':
                    return 'Insider Banker'
                elif ob == 'yes':
                    return 'Outsider Banker'
                else:
                    return 'Self Funded'
    
            fdf_all = df.copy()
            fdf_all['Sales Executive'] = fdf_all['Sales Executive'].astype(str).str.strip()
            fdf_all = fdf_all[fdf_all['Sales Executive'].ne('')]
    
            if fdf_all.empty:
                st.info("No Sales Executive entries to chart funding.")
            else:
                fdf_all['Funding'] = fdf_all.apply(_funding_overall, axis=1)
    
                FUNDING_DOMAIN = ['Insider Banker', 'Outsider Banker', 'Self Funded']
                funding_counts_all = (fdf_all
                                      .groupby(['Sales Executive','Funding'])
                                      .size()
                                      .reset_index(name='Count'))
                funding_counts_all['Funding'] = pd.Categorical(
                    funding_counts_all['Funding'], categories=FUNDING_DOMAIN, ordered=True
                )
    
                base = alt.Chart(funding_counts_all)
                bars = base.mark_bar(size=16).encode(
                    x=alt.X('Sales Executive:N', title='Sales Executive',
                            axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True),
                            scale=alt.Scale(paddingInner=0.35, paddingOuter=0.35)),
                    xOffset=alt.X('Funding:N', sort=FUNDING_DOMAIN, title=None),
                    y=alt.Y('Count:Q', title='Bookings'),
                    color=alt.Color('Funding:N',
                                    scale=alt.Scale(domain=FUNDING_DOMAIN,
                                                    range=['#2563eb', '#f59e0b', '#10b981']),
                                    legend=alt.Legend(title='Funding')),
                    tooltip=[
                        alt.Tooltip('Sales Executive:N', title='Sales Executive'),
                        alt.Tooltip('Funding:N'),
                        alt.Tooltip('Count:Q', title='Count')
                    ]
                )
                labels = base.mark_text(
                    dy=-6, fontSize=12, fontWeight='bold', color='#0f172a'
                ).encode(
                    x=alt.X('Sales Executive:N',
                            axis=alt.Axis(labelAngle=0, labelLimit=160, labelOverlap=True)),
                    xOffset=alt.X('Funding:N', sort=FUNDING_DOMAIN),
                    y='Count:Q',
                    text='Count:Q'
                )
    
                st.altair_chart(
                    (bars + labels).properties(
                        title=alt.TitleParams("Funding Source by Sales Executive — Overall",
                                              anchor='start', fontSize=16, fontWeight='bold', dy=-5),
                        height=340, width=alt.Step(80)
                    ).configure_title(anchor='start'),
                    use_container_width=True
                )

        # === Monthwise: Bookings vs Stamp Duty Received vs Agreement Done (single chart) ===
        st.markdown("<div class='section-subtitle'>📊 Monthwise: Bookings, Stamp Duty Received, Agreement Done</div>", unsafe_allow_html=True)
        
        needed_cols = {'MonthYear', 'Stamp Duty', 'Agreement Done'}
        if not needed_cols.issubset(df.columns):
            st.info("Missing columns for monthwise combined graph (need MonthYear, Stamp Duty, Agreement Done).")
        else:
            # Ensure ordering matches the rest of the app
            month_order_local = [m for m in ordered_months if m in df['MonthYear'].unique().tolist()]
            if not month_order_local:
                # Fallback if ordered_months isn't populated
                month_order_local = sorted(
                    df['MonthYear'].dropna().unique().tolist(),
                    key=lambda x: pd.to_datetime(x, format="%B %y", errors='coerce')
                )
        
            dfx = df.dropna(subset=['MonthYear']).copy()
            dfx['MonthYear'] = pd.Categorical(dfx['MonthYear'], categories=month_order_local, ordered=True)
        
            # Aggregations per month
            grp = dfx.groupby('MonthYear', observed=True)
        
            month_bookings = grp.size().rename('Bookings').reset_index()
        
            month_sd = grp['Stamp Duty'].apply(
                lambda s: int((s.astype(str).str.lower().str.strip() == 'received').sum())
            ).rename('Stamp Duty Received').reset_index()
        
            month_ag = grp['Agreement Done'].apply(
                lambda s: int((s.astype(str).str.lower().str.strip() == 'done').sum())
            ).rename('Agreement Done').reset_index()
        
            # Merge and ONLY fill numeric columns
            m_all = (month_bookings
                     .merge(month_sd, on='MonthYear', how='outer')
                     .merge(month_ag, on='MonthYear', how='outer'))
        
            num_cols = ['Bookings', 'Stamp Duty Received', 'Agreement Done']
            for c in num_cols:
                m_all[c] = pd.to_numeric(m_all[c], errors='coerce').fillna(0).astype(int)
        
            # Long format for grouped bars
            m_long = m_all.melt(
                id_vars='MonthYear',
                value_vars=num_cols,
                var_name='Metric',
                value_name='Count'
            )
        
            base = alt.Chart(m_long)
            bars = base.mark_bar().encode(
                x=alt.X('MonthYear:N', sort=month_order_local, title='Month',
                        axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=True),
                        scale=alt.Scale(paddingInner=0.35, paddingOuter=0.35)),
                xOffset=alt.X('Metric:N'),
                y=alt.Y('Count:Q', title='Count'),
                color=alt.Color('Metric:N',
                                scale=alt.Scale(
                                    domain=['Bookings','Stamp Duty Received','Agreement Done'],
                                    range=['#6366f1','#10b981','#f59e0b']
                                ),
                                legend=alt.Legend(title="", orient='top')),
                tooltip=['MonthYear:N','Metric:N','Count:Q']
            )
            labels = base.mark_text(dy=-6, fontSize=12, fontWeight='bold', color='#0f172a').encode(
                x=alt.X('MonthYear:N', sort=month_order_local),
                xOffset='Metric:N',
                y='Count:Q',
                text='Count:Q'
            )
        
            st.altair_chart(
                (bars + labels).properties(
                    title=alt.TitleParams(
                        "Monthwise: Bookings vs Stamp Duty Received vs Agreement Done",
                        anchor='start', fontSize=16, fontWeight='bold', dy=-5
                    ),
                    height=340, width=alt.Step(90)
                ).configure_title(anchor='start'),
                use_container_width=True
            )
    with TAB_OFFERS_DASH:
        st.header("📈 Offers Dashboard")
    
        base_df = df.copy()
    
        required_off_cols = [
            'Offer 1', 'Offer 2', 'Offer 1 Rewarded', 'Offer 2 Rewarded',
            'month', 'Wing', 'Floor', 'Flat Number'
        ]
    
        for col in required_off_cols:
            if col not in base_df.columns:
                base_df[col] = ""
    
        def _norm(x):
            if pd.isna(x):
                return ""
            return str(x).strip()
    
        tall_rows = []
        for _, r in base_df.iterrows():
            o1 = _norm(r.get('Offer 1'))
            o2 = _norm(r.get('Offer 2'))
            o1r = _norm(r.get('Offer 1 Rewarded')).lower()
            o2r = _norm(r.get('Offer 2 Rewarded')).lower()
    
            if o1:
                tall_rows.append({"offer": o1, "rewarded": o1r in ["rewarded 1", "true", "yes", "1"]})
            if o2:
                tall_rows.append({"offer": o2, "rewarded": o2r in ["rewarded 2", "true", "yes", "1"]})
    
        tall = pd.DataFrame(tall_rows) if tall_rows else pd.DataFrame(columns=["offer", "rewarded"])
    
        OFFERS_LIST = [
            "1 Gram Gold Coin",
            "2 Gram Gold Coin",
            "200 Gram Silver",
            "Kitchen Trolley",
            "25000 Electronic Voucher"
        ]
    
        def stats_for(name: str):
            if tall.empty:
                return 0, 0, 0
            sub = tall[tall['offer'].astype(str).str.strip().str.casefold() == name.strip().casefold()]
            tot = int(len(sub))
            rwd = int(sub['rewarded'].sum())
            pend = max(tot - rwd, 0)
            return tot, rwd, pend
    
        REF_LEAD_COL = "Lead Type"
        REF_GIVEN_COL = "Referral Given"
        AGREEMENT_COL = "Agreement Done"
    
        for col in [REF_LEAD_COL, REF_GIVEN_COL, AGREEMENT_COL]:
            if col not in base_df.columns:
                base_df[col] = ""
    
        ref_total_done = 0
        ref_pending = 0
        ref_rewarded = 0
    
        df_ref = base_df.copy()
    
        lead_norm = df_ref[REF_LEAD_COL].astype(str).str.strip().str.casefold()
        is_referral = lead_norm.str.contains("ref", na=False)
        df_ref = df_ref[is_referral]
    
        agr_done_mask = df_ref[AGREEMENT_COL].astype(str).str.lower().str.strip() == 'done'
        df_ref_done = df_ref[agr_done_mask].copy()
    
        ref_total_done = int(len(df_ref_done))
    
        given_norm = df_ref_done[REF_GIVEN_COL].astype(str).str.strip().str.casefold()
        given_referrals = int(given_norm.str.contains("given|true|yes|1", regex=True, na=False).sum())
        ref_pending = max(ref_total_done - given_referrals, 0)
        ref_rewarded = max(ref_total_done - ref_pending, 0)
    
        total_offers_count = int(len(tall)) + int(ref_total_done)
    
        st.markdown(
            f"<div class='metric-card'><h3>Total Offers Given</h3><p>{total_offers_count}</p></div>",
            unsafe_allow_html=True
        )
    
        r7c1, r7c2, r7c3 = st.columns(3)
        with r7c1:
            st.markdown(
                f"<div class='metric-card'><h3>Total Referrals</h3><p>{ref_total_done}</p></div>",
                unsafe_allow_html=True
            )
        with r7c2:
            st.markdown(
                f"<div class='metric-card'><h3>Pending Referrals</h3><p>{ref_pending}</p></div>",
                unsafe_allow_html=True
            )
        with r7c3:
            st.markdown(
                f"<div class='metric-card'><h3>Rewarded Referrals</h3><p>{ref_rewarded}</p></div>",
                unsafe_allow_html=True
            )
    
        def render_offer_row(offer_name: str):
            t, r, p = stats_for(offer_name)
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='metric-card'><h3>{offer_name} — Total</h3><p>{t}</p></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-card'><h3>{offer_name} — Pending</h3><p>{p}</p></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='metric-card'><h3>{offer_name} — Rewarded</h3><p>{r}</p></div>", unsafe_allow_html=True)
    
        for offer_nm in OFFERS_LIST:
            render_offer_row(offer_nm)
    
        st.markdown("<div class='section-subtitle'>🎁 Offers Lookup</div>", unsafe_allow_html=True)
    
        def canon_month2(s: str) -> str:
            return str(s).strip().replace(" ", "").replace("-", "").upper() if pd.notna(s) else ""
    
        base_df['__MonthCanon'] = base_df['month'].map(canon_month2)
    
        months_o = ['All'] + sorted([m for m in base_df['__MonthCanon'].dropna().unique() if str(m).strip()], key=str)
    
        wings_o = ['All'] + sorted(
            [
                str(x).strip()
                for x in base_df['Wing'].dropna().unique()
                if str(x).strip() != "" and str(x).strip().upper() != "NAN"
            ]
        )
    
        floors_o = ['All'] + sorted(
            [
                str(x).strip()
                for x in base_df['Floor'].dropna().unique()
                if str(x).strip() != "" and str(x).strip().upper() != "NAN"
            ],
            key=lambda x: str(x)
        )
    
        lc1, lc2, lc3 = st.columns(3)
        sel_wing = lc1.selectbox("Select Wing", wings_o, key="tab1_off_wing")
        sel_floor = lc2.selectbox("Select Floor", floors_o, key="tab1_off_floor")
        sel_month = lc3.selectbox("Select Month", months_o, key="tab1_off_month")
    
        fdf = base_df.copy()
    
        if sel_wing != "All":
            fdf = fdf[fdf['Wing'].astype(str).str.strip() == sel_wing]
    
        if sel_floor != "All":
            fdf = fdf[fdf['Floor'].astype(str).str.strip() == sel_floor]
    
        if sel_month != "All":
            fdf = fdf[fdf['__MonthCanon'] == sel_month]
    
        has_offer = (
            fdf['Offer 1'].astype(str).str.strip().ne('') |
            fdf['Offer 2'].astype(str).str.strip().ne('')
        )
        fdf = fdf[has_offer]
    
        st.markdown(
            f"<div class='chips'>"
            f"<span class='chip'><span class='dot'></span> Wing: {sel_wing}</span>"
            f"<span class='chip'><span class='dot'></span> Floor: {sel_floor}</span>"
            f"<span class='chip'><span class='dot'></span> Month: {sel_month}</span>"
            f"<span class='chip ok'><span class='dot'></span> Matches: {len(fdf)}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
    
        if fdf.empty:
            st.warning("No Offer data available for selected criteria.")
        else:
            show = fdf[['Flat Number', 'Offer 1', 'Offer 2']].copy()
            st.markdown(show.to_html(index=False, classes="styled-table"), unsafe_allow_html=True)
    with TAB_SE_PERFORMANCE:
        st.header("📈 Sales Performance Command Center")
        st.caption("Unified view of calls, visits, revisits, cancellations, conversion, and sales executive performance.")
    
        # =========================================================
        # Guards
        # =========================================================
        if not ordered_months:
            st.info("No month data available to filter.")
            st.stop()
    
        if df is None or df.empty:
            st.info("Sales executive booking data is not available.")
            st.stop()
    
        daily_visits_available = sheets_connected and daily_visits_df is not None and not daily_visits_df.empty
    
        # =========================================================
        # CSS
        # =========================================================
        st.markdown(
            """
            <style>
            .spcc-filter-shell{
              background: rgba(255,255,255,0.96);
              border: 1px solid rgba(49,51,63,0.12);
              border-radius: 18px;
              padding: 14px 16px 10px 16px;
              box-shadow: 0 8px 22px rgba(0,0,0,0.06);
              margin-bottom: 12px;
            }
            .section-shell{
              background: rgba(255,255,255,0.96);
              border: 1px solid rgba(49,51,63,0.10);
              border-radius: 18px;
              padding: 16px 16px 12px 16px;
              box-shadow: 0 8px 22px rgba(0,0,0,0.05);
              margin-bottom: 16px;
            }
            .section-banner{
              text-align: center;
              font-weight: 900;
              font-size: 20px;
              line-height: 1.2;
              padding: 12px 14px;
              border-radius: 16px;
              color: #ffffff;
              background: linear-gradient(90deg, #2563eb, #7c3aed);
              box-shadow: 0 8px 20px rgba(37,99,235,0.18);
              margin-bottom: 8px;
            }
            .section-sub{
              text-align: center;
              font-size: 0.92rem;
              font-weight: 600;
              color: rgba(49,51,63,0.72);
              margin-bottom: 12px;
            }
            .metric-card{
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
            }
            .metric-card h3{
              margin: 0 0 8px 0;
              font-size: 12.5px;
              line-height: 1.2;
              font-weight: 800;
              color: rgba(49,51,63,0.78);
              text-align: center;
            }
            .metric-card p{
              margin: 0;
              font-size: 28px;
              line-height: 1.05;
              font-weight: 900;
              color: #111827;
              text-align: center;
            }
            .metric-card span{
              display: block;
              margin-top: 8px;
              font-size: 12px;
              line-height: 1.2;
              font-weight: 700;
              color: rgba(49,51,63,0.65);
              text-align: center;
            }
            .chips{
              display: flex;
              gap: 8px;
              flex-wrap: wrap;
              margin: 6px 0 14px 0;
            }
            .chip{
              display: inline-flex;
              align-items: center;
              gap: 7px;
              background: rgba(255,255,255,0.96);
              border: 1px solid rgba(49,51,63,0.12);
              border-radius: 999px;
              padding: 6px 10px;
              font-size: 12.5px;
              font-weight: 700;
              color: #111827;
            }
            .chip.ok{
              background: rgba(236,253,245,0.95);
              border-color: rgba(16,185,129,0.20);
            }
            .dot{
              width: 8px;
              height: 8px;
              border-radius: 999px;
              background: #2563eb;
              display: inline-block;
            }
            .chip.ok .dot{
              background: #10b981;
            }
            div[data-testid="stDateInput"] input,
            .stSelectbox div[data-baseweb="select"]{
              border-radius: 12px !important;
            }
            button[kind="primary"]{
              border-radius: 14px !important;
              font-weight: 800 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    
        # =========================================================
        # Helpers
        # =========================================================
        BOOK_COL = "Today's Booking"
        CANC_COL = "Today's Cancellation"
    
        EXEC_CONFIG = [
            {
                "name": "Tejas P",
                "revisits": "Tejas P Revisits",
                "attended": "Tejas P Attended",
                "answered": "Tejas P Calls Answered",
                "unanswered": "Tejas P Calls Unanswered",
            },
            {
                "name": "Komal K",
                "revisits": "Komal K Revisits",
                "attended": "Komal K Attended",
                "answered": "Komal K Calls Answered",
                "unanswered": "Komal K Calls Unanswered",
            },
            {
                "name": "Ashutosh S",
                "revisits": "Ashutosh S Revisits",
                "attended": "Ashutosh S Attended",
                "answered": "Ashutosh S Calls Answered",
                "unanswered": "Ashutosh S Calls Unanswered",
            },
            {
                "name": "Sailee D",
                "revisits": "Sailee D Revisits",
                "attended": "Sailee D Attended",
                "answered": "Sailee D Calls Answered",
                "unanswered": "Sailee D Calls Unanswered",
            },
        ]
    
        def _to_int(x):
            try:
                return int(float(str(x).strip() or 0))
            except Exception:
                return 0
    
        def _strip_apostrophe(s: str) -> str:
            s = str(s or "").strip()
            return s[1:] if s.startswith("'") else s
    
        def parse_date_text(s):
            t = _strip_apostrophe(s)
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%m/%d/%Y"):
                try:
                    return datetime.datetime.strptime(t, fmt).date()
                except Exception:
                    pass
            try:
                ts = pd.to_datetime(t, dayfirst=True, errors="coerce")
                if pd.isna(ts):
                    return None
                return ts.date()
            except Exception:
                return None
    
        def month_label_to_key(s: str) -> str:
            raw = _strip_apostrophe(s)
            raw = str(raw or "").replace("-", " ").replace("_", " ").strip()
            raw = " ".join(raw.split())
            if not raw:
                return ""
    
            candidates = [raw, raw.title(), raw.upper()]
            formats = ("%B %y", "%B %Y", "%b %y", "%b %Y", "%Y-%m", "%m/%Y")
    
            for cand in candidates:
                for fmt in formats:
                    try:
                        return datetime.datetime.strptime(cand, fmt).strftime("%Y-%m")
                    except Exception:
                        pass
    
            try:
                ts = pd.to_datetime(raw, dayfirst=True, errors="coerce")
                if pd.isna(ts):
                    return ""
                return ts.strftime("%Y-%m")
            except Exception:
                return ""
    
        def _pct(num, den):
            den = den if den not in (0, None) else 0
            if den == 0:
                return None
            return (num / den) * 100.0
    
        def _fmt_pct(x):
            return "—" if (x is None or pd.isna(x)) else f"{x:.1f}%"
    
        def _fmt_days(x):
            return "—" if (x is None or pd.isna(x)) else f"{x:.1f} days"
    
        def line_chart_with_values(df_in, x_col, y_col, title, x_sort=None):
            if df_in.empty:
                st.info(f"No data for: {title}")
                return
            base = alt.Chart(df_in).encode(
                x=alt.X(f"{x_col}:N", sort=x_sort, title=x_col),
                y=alt.Y(f"{y_col}:Q", title=y_col)
            )
            line = base.mark_line(point=True).encode(
                tooltip=[
                    alt.Tooltip(f"{x_col}:N"),
                    alt.Tooltip(f"{y_col}:Q", format=",.0f")
                ]
            )
            labels = base.mark_text(dy=-10, fontSize=11, fontWeight="bold").encode(
                text=alt.Text(f"{y_col}:Q", format=",.0f")
            )
            st.altair_chart(
                (line + labels).properties(title=title, height=360),
                use_container_width=True
            )
    
        def bar_chart_with_values(df_in, x_col, y_col, title, x_sort=None, color_col=None):
            if df_in.empty:
                st.info(f"No data for: {title}")
                return
    
            enc = {
                "x": alt.X(f"{x_col}:N", sort=x_sort, title=x_col),
                "y": alt.Y(f"{y_col}:Q", title=y_col),
                "tooltip": [
                    alt.Tooltip(f"{x_col}:N"),
                    alt.Tooltip(f"{y_col}:Q", format=",.0f")
                ],
            }
            if color_col:
                enc["color"] = alt.Color(f"{color_col}:N", title=color_col)
    
            base = alt.Chart(df_in).encode(**enc)
            bars = base.mark_bar()
            labels = base.mark_text(dy=-7, fontSize=11, fontWeight="bold").encode(
                text=alt.Text(f"{y_col}:Q", format=",.0f")
            )
            st.altair_chart(
                (bars + labels).properties(title=title, height=360),
                use_container_width=True
            )
    
        def grouped_bar_chart_with_values(df_in, x_col, series_col, value_col, title, x_sort=None, series_sort=None):
            if df_in.empty:
                st.info(f"No data for: {title}")
                return
            base = alt.Chart(df_in).encode(
                x=alt.X(f"{x_col}:N", sort=x_sort, title=x_col),
                xOffset=alt.XOffset(f"{series_col}:N", sort=series_sort),
                y=alt.Y(f"{value_col}:Q", title=value_col),
                color=alt.Color(f"{series_col}:N", title=series_col),
                tooltip=[
                    alt.Tooltip(f"{x_col}:N"),
                    alt.Tooltip(f"{series_col}:N"),
                    alt.Tooltip(f"{value_col}:Q", format=",.0f"),
                ],
            )
            bars = base.mark_bar()
            labels = base.mark_text(dy=-6, fontSize=11, fontWeight="bold").encode(
                text=alt.Text(f"{value_col}:Q", format=",.0f")
            )
            st.altair_chart(
                (bars + labels).properties(title=title, height=390),
                use_container_width=True
            )
    
        # =========================================================
        # Month filter
        # =========================================================
        fcol1, fcol2 = st.columns(2)
        start_month = fcol1.selectbox("From Month", ordered_months, index=0, key="spcc_start_month")
        end_month = fcol2.selectbox("To Month", ordered_months, index=len(ordered_months) - 1, key="spcc_end_month")
    
        try:
            si = ordered_months.index(start_month)
            ei = ordered_months.index(end_month)
        except ValueError:
            st.warning("Please select valid months.")
            st.stop()
    
        if si > ei:
            si, ei = ei, si
            start_month, end_month = ordered_months[si], ordered_months[ei]
    
        selected_months = ordered_months[si:ei + 1]
        selected_month_norms = {str(_strip_apostrophe(m)).strip().upper() for m in selected_months}
        selected_month_keys = {month_label_to_key(m) for m in selected_months if month_label_to_key(m)}
    
        # =========================================================
        # Booking dataframe
        # =========================================================
        df_all = df.copy()
        if "Month" not in df_all.columns:
            df_all["Month"] = ""
        
        df_all["Month"] = df_all["Month"].astype("object").where(pd.notna(df_all["Month"]), "").astype(str)
        df_all["_MonthNorm"] = df_all["Month"].apply(lambda x: str(_strip_apostrophe(x)).strip().upper())
        df_all["_MonthKey"] = df_all["Month"].apply(month_label_to_key)
    
        df_period = df_all[
            (df_all["_MonthNorm"].isin(selected_month_norms)) |
            (df_all["_MonthKey"].isin(selected_month_keys))
        ].copy()
    
        # =========================================================
        # Daily visits dataframe
        # =========================================================
        dv_period = pd.DataFrame()
    
        if daily_visits_available:
            dv = daily_visits_df.copy()
        
            supabase_daily_visits_cols = {
                "visit_date": "Date",
                "date": "Date",
                "month": "Month",
                "day": "Day",
                "cp_visits": "CP Visits",
                "direct_walk_in": "Direct Walk-in",
                "references": "References",
                "digital": "Digital",
                "newspaper": "Newspaper",
                "todays_cancellation": "Today's Cancellation",
                "todays_booking": "Today's Booking",
                "total_revisits": "Total Revisits",
                "tejas_p_revisits": "Tejas P Revisits",
                "komal_k_revisits": "Komal K Revisits",
                "ashutosh_s_revisits": "Ashutosh S Revisits",
                "sailee_d_revisits": "Sailee D Revisits",
                "total_attended": "Total Attended",
                "tejas_p_attended": "Tejas P Attended",
                "komal_k_attended": "Komal K Attended",
                "ashutosh_s_attended": "Ashutosh S Attended",
                "sailee_d_attended": "Sailee D Attended",
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
        
            dv = dv.rename(columns=supabase_daily_visits_cols)
    
            if not dv.empty:
                for c in ["Date", "Month", "Festival 1", "Festival 2", "Festival 3"]:
                    if c not in dv.columns:
                        dv[c] = ""
    
                required_dv_num_cols = [
                    "CP Visits",
                    "Direct Walk-in",
                    "References",
                    "Digital",
                    "Newspaper",
                    BOOK_COL,
                    CANC_COL,
                    "Total Visits",
                    "Total Revisits",
                    "Total Attended",
                    "Total Calls Answered",
                    "Total Calls Unanswered",
                    "Revisit",
                ]
                for ex in EXEC_CONFIG:
                    required_dv_num_cols.extend([
                        ex["revisits"],
                        ex["attended"],
                        ex["answered"],
                        ex["unanswered"],
                    ])
    
                for c in required_dv_num_cols:
                    if c not in dv.columns:
                        dv[c] = 0
    
                for c in required_dv_num_cols:
                    dv[c] = dv[c].apply(_to_int)
    
                dv["Date_obj"] = dv["Date"].apply(parse_date_text)
                dv = dv.dropna(subset=["Date_obj"]).copy()
    
                if not dv.empty:
                    exec_revisit_cols = [ex["revisits"] for ex in EXEC_CONFIG]
                    exec_attended_cols = [ex["attended"] for ex in EXEC_CONFIG]
                    exec_answered_cols = [ex["answered"] for ex in EXEC_CONFIG]
                    exec_unanswered_cols = [ex["unanswered"] for ex in EXEC_CONFIG]
    
                    zero_mask = dv["Total Revisits"].fillna(0).astype(int) == 0
                    if "Revisit" in dv.columns:
                        dv.loc[zero_mask, "Total Revisits"] = dv.loc[zero_mask, "Revisit"]
                    dv.loc[dv["Total Revisits"].fillna(0).astype(int) == 0, "Total Revisits"] = dv[exec_revisit_cols].sum(axis=1)
                    dv["Total Revisits"] = dv["Total Revisits"].astype(int)
    
                    zero_mask = dv["Total Attended"].fillna(0).astype(int) == 0
                    dv.loc[zero_mask, "Total Attended"] = dv.loc[zero_mask, exec_attended_cols].sum(axis=1)
                    dv["Total Attended"] = dv["Total Attended"].astype(int)
    
                    zero_mask = dv["Total Calls Answered"].fillna(0).astype(int) == 0
                    dv.loc[zero_mask, "Total Calls Answered"] = dv.loc[zero_mask, exec_answered_cols].sum(axis=1)
                    dv["Total Calls Answered"] = dv["Total Calls Answered"].astype(int)
    
                    zero_mask = dv["Total Calls Unanswered"].fillna(0).astype(int) == 0
                    dv.loc[zero_mask, "Total Calls Unanswered"] = dv.loc[zero_mask, exec_unanswered_cols].sum(axis=1)
                    dv["Total Calls Unanswered"] = dv["Total Calls Unanswered"].astype(int)
    
                    source_cols = ["CP Visits", "Direct Walk-in", "References", "Digital", "Newspaper"]
                    zero_mask_vis = dv["Total Visits"].fillna(0).astype(int) == 0
                    dv.loc[zero_mask_vis, "Total Visits"] = (
                        dv.loc[zero_mask_vis, source_cols].sum(axis=1) + dv.loc[zero_mask_vis, "Total Revisits"]
                    )
                    dv["Total Visits"] = dv["Total Visits"].astype(int)
    
                    dv["_MonthNorm"] = dv["Month"].apply(lambda x: str(_strip_apostrophe(x)).strip().upper())
                    dv["_MonthKey"] = dv["Month"].apply(month_label_to_key)
    
                    missing_month_mask = dv["_MonthKey"].eq("") | dv["_MonthKey"].isna()
                    dv.loc[missing_month_mask, "_MonthKey"] = dv.loc[missing_month_mask, "Date_obj"].apply(
                        lambda d: d.strftime("%Y-%m")
                    )
                    dv.loc[dv["_MonthNorm"].eq("") | dv["_MonthNorm"].isna(), "_MonthNorm"] = dv["Date_obj"].apply(
                        lambda d: d.strftime("%B %y").upper()
                    )
    
                    dv_period = dv[
                        (dv["_MonthNorm"].isin(selected_month_norms)) |
                        (dv["_MonthKey"].isin(selected_month_keys))
                    ].copy()
    
        # =========================================================
        # Availability check
        # =========================================================
        st.markdown(
            f"<div class='chips'>"
            f"<span class='chip'><span class='dot'></span> From: {start_month}</span>"
            f"<span class='chip'><span class='dot'></span> To: {end_month}</span>"
            f"<span class='chip ok'><span class='dot'></span> Booking Records: {len(df_period)}</span>"
            f"<span class='chip ok'><span class='dot'></span> Daily Visit Rows: {len(dv_period) if not dv_period.empty else 0}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
    
        if df_period.empty and dv_period.empty:
            st.warning("No data available for the selected month range.")
            st.stop()
    
        # =========================================================
        # Normalize booking dataset
        # =========================================================
        if not df_period.empty:
            if "_DerivedType" in df_period.columns:
                type_col = df_period["_DerivedType"].astype(str).str.upper().str.strip()
            else:
                type_col = df_period.get("Type", pd.Series(index=df_period.index, dtype="object")).astype(str).str.upper().str.strip()
            df_period["_DerivedType2"] = type_col
    
            if "Lead Type" in df_period.columns:
                df_period["_LeadType2"] = (
                    df_period["Lead Type"]
                    .fillna("Unknown")
                    .astype(str)
                    .str.strip()
                    .replace("", "Unknown")
                    .str.title()
                )
            else:
                df_period["_LeadType2"] = "Unknown"
    
            df_period["_ConvDays"] = pd.to_numeric(
                df_period.get("Conversion Period (days)", pd.Series(index=df_period.index, dtype="float")),
                errors="coerce"
            )
    
            df_period["_MonthDisplay"] = df_period["Month"].astype(str).replace("", "Unknown")
            booking_execs = sorted(df_period["Sales Executive"].dropna().astype(str).unique())
        else:
            booking_execs = []
    
        active_exec_count = len(booking_execs) if booking_execs else len(EXEC_CONFIG)
    
        # =========================================================
        # Overall KPIs
        # =========================================================
        avg_conv_overall = df_period["_ConvDays"].mean() if (not df_period.empty and df_period["_ConvDays"].notna().any()) else float("nan")
    
        total_visits = int(dv_period["Total Visits"].sum()) if not dv_period.empty else 0
        total_revisits = int(dv_period["Total Revisits"].sum()) if not dv_period.empty else 0
        total_calls_answered = int(dv_period["Total Calls Answered"].sum()) if not dv_period.empty else 0
        total_calls_unanswered = int(dv_period["Total Calls Unanswered"].sum()) if not dv_period.empty else 0
        total_calls = total_calls_answered + total_calls_unanswered
        total_cancellations = int(dv_period[CANC_COL].sum()) if not dv_period.empty else 0
        call_answer_rate = _pct(total_calls_answered, total_calls)
        revisit_rate = _pct(total_revisits, total_visits)
    
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        st.markdown("<div class='section-banner'>📌 Overall Performance Snapshot</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Top level summary for the selected month range.</div>", unsafe_allow_html=True)
    
        ov1, ov2, ov3, ov4 = st.columns(4)
        ov1.markdown(
            f"<div class='metric-card'><h3>Total Visits</h3><p>{total_visits:,}</p><span>Daily visits sheet</span></div>",
            unsafe_allow_html=True
        )
        ov2.markdown(
            f"<div class='metric-card'><h3>Total Calls</h3><p>{total_calls:,}</p><span>Answered + unanswered</span></div>",
            unsafe_allow_html=True
        )
        ov3.markdown(
            f"<div class='metric-card'><h3>Call Answer Rate</h3><p>{_fmt_pct(call_answer_rate)}</p><span>Answered / Total Calls</span></div>",
            unsafe_allow_html=True
        )
        ov4.markdown(
            f"<div class='metric-card'><h3>Total Revisits</h3><p>{total_revisits:,}</p><span>Across selected period</span></div>",
            unsafe_allow_html=True
        )
    
        ov5, ov6, ov7, ov8 = st.columns(4)
        ov5.markdown(
            f"<div class='metric-card'><h3>Revisit Rate</h3><p>{_fmt_pct(revisit_rate)}</p><span>Revisits / Total Visits</span></div>",
            unsafe_allow_html=True
        )
        ov6.markdown(
            f"<div class='metric-card'><h3>Avg Conversion Period</h3><p>{_fmt_days(avg_conv_overall)}</p><span>Booking dataset</span></div>",
            unsafe_allow_html=True
        )
        ov7.markdown(
            f"<div class='metric-card'><h3>Total Cancellations</h3><p>{total_cancellations:,}</p><span>Selected period</span></div>",
            unsafe_allow_html=True
        )
        ov8.markdown(
            f"<div class='metric-card'><h3>Active Executives</h3><p>{active_exec_count:,}</p><span>Across selected range</span></div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
        # =========================================================
        # Calls Dashboard
        # =========================================================
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        st.markdown("<div class='section-banner'>📞 Calls Dashboard</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Call volume, answered/unanswered split, and executive-wise call-to-visit performance.</div>", unsafe_allow_html=True)
    
        if dv_period.empty:
            st.info("Daily visits / calls data is not available for the selected month range.")
        else:
            calls_exec_rows = []
            for ex in EXEC_CONFIG:
                ans = int(dv_period[ex["answered"]].sum()) if ex["answered"] in dv_period.columns else 0
                unans = int(dv_period[ex["unanswered"]].sum()) if ex["unanswered"] in dv_period.columns else 0
                total = ans + unans
                att = int(dv_period[ex["attended"]].sum()) if ex["attended"] in dv_period.columns else 0
                rev = int(dv_period[ex["revisits"]].sum()) if ex["revisits"] in dv_period.columns else 0
    
                calls_exec_rows.append({
                    "Sales Executive": ex["name"],
                    "Total Calls": total,
                    "Calls Answered": ans,
                    "Calls Unanswered": unans,
                    "Answer Rate %": _pct(ans, total),
                    "Attended Visits": att,
                    "Revisits": rev,
                    "Calls → Visits %": _pct(att, total),
                    "Calls → Revisits %": _pct(rev, total),
                    "Visits → Revisits %": _pct(rev, att),
                })
    
            calls_exec_df = pd.DataFrame(calls_exec_rows).sort_values(
                ["Total Calls", "Calls Answered"], ascending=[False, False]
            ).reset_index(drop=True)
    
            best_answer_exec = "—"
            best_answer_exec_sub = ""
            answer_non_null = calls_exec_df.dropna(subset=["Answer Rate %"])
            answer_non_null = answer_non_null[answer_non_null["Total Calls"] > 0]
            if not answer_non_null.empty:
                rr = answer_non_null.sort_values("Answer Rate %", ascending=False).iloc[0]
                best_answer_exec = rr["Sales Executive"]
                best_answer_exec_sub = _fmt_pct(rr["Answer Rate %"])
    
            best_visit_conv_exec = "—"
            best_visit_conv_sub = ""
            visit_non_null = calls_exec_df.dropna(subset=["Calls → Visits %"])
            visit_non_null = visit_non_null[visit_non_null["Total Calls"] > 0]
            if not visit_non_null.empty:
                rr = visit_non_null.sort_values("Calls → Visits %", ascending=False).iloc[0]
                best_visit_conv_exec = rr["Sales Executive"]
                best_visit_conv_sub = _fmt_pct(rr["Calls → Visits %"])
    
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f"<div class='metric-card'><h3>Total Calls</h3><p>{total_calls:,}</p><span>All executives combined</span></div>",
                unsafe_allow_html=True
            )
            c2.markdown(
                f"<div class='metric-card'><h3>Calls Answered</h3><p>{total_calls_answered:,}</p><span>{_fmt_pct(call_answer_rate)} answer rate</span></div>",
                unsafe_allow_html=True
            )
            c3.markdown(
                f"<div class='metric-card'><h3>Calls Unanswered</h3><p>{total_calls_unanswered:,}</p><span>{_fmt_pct(_pct(total_calls_unanswered, total_calls))} of total calls</span></div>",
                unsafe_allow_html=True
            )
            c4.markdown(
                f"<div class='metric-card'><h3>Best Answer Rate</h3><p>{best_answer_exec}</p><span>{best_answer_exec_sub}</span></div>",
                unsafe_allow_html=True
            )
    
            c5, c6, c7, c8 = st.columns(4)
            c5.markdown(
                f"<div class='metric-card'><h3>Visit Conversion from Calls</h3><p>{_fmt_pct(_pct(int(dv_period['Total Attended'].sum()), total_calls))}</p><span>Attended / Total Calls</span></div>",
                unsafe_allow_html=True
            )
            c6.markdown(
                f"<div class='metric-card'><h3>Revisit Conversion from Calls</h3><p>{_fmt_pct(_pct(total_revisits, total_calls))}</p><span>Revisits / Total Calls</span></div>",
                unsafe_allow_html=True
            )
            c7.markdown(
                f"<div class='metric-card'><h3>Best Call→Visit</h3><p>{best_visit_conv_exec}</p><span>{best_visit_conv_sub}</span></div>",
                unsafe_allow_html=True
            )
            c8.markdown(
                f"<div class='metric-card'><h3>Avg Calls / Active SE</h3><p>{int(round(total_calls / max(len(EXEC_CONFIG), 1), 0)):,}</p><span>Across selected period</span></div>",
                unsafe_allow_html=True
            )
    
            calls_exec_display = calls_exec_df.copy()
            for pc in ["Answer Rate %", "Calls → Visits %", "Calls → Revisits %", "Visits → Revisits %"]:
                calls_exec_display[pc] = calls_exec_display[pc].apply(_fmt_pct)
    
            st.markdown("#### Executive-wise Call Performance")
            st.dataframe(calls_exec_display, use_container_width=True, hide_index=True)
    
            calls_long = pd.concat(
                [
                    calls_exec_df[["Sales Executive", "Calls Answered"]].rename(columns={"Calls Answered": "Count"}).assign(Type="Calls Answered"),
                    calls_exec_df[["Sales Executive", "Calls Unanswered"]].rename(columns={"Calls Unanswered": "Count"}).assign(Type="Calls Unanswered"),
                ],
                ignore_index=True
            )
    
            calls_conv_long = pd.concat(
                [
                    calls_exec_df[["Sales Executive", "Total Calls"]].rename(columns={"Total Calls": "Count"}).assign(Type="Total Calls"),
                    calls_exec_df[["Sales Executive", "Attended Visits"]].rename(columns={"Attended Visits": "Count"}).assign(Type="Attended Visits"),
                    calls_exec_df[["Sales Executive", "Revisits"]].rename(columns={"Revisits": "Count"}).assign(Type="Revisits"),
                ],
                ignore_index=True
            )
    
            ch1, ch2 = st.columns(2)
            with ch1:
                grouped_bar_chart_with_values(
                    calls_long,
                    x_col="Sales Executive",
                    series_col="Type",
                    value_col="Count",
                    title="Answered vs Unanswered Calls",
                    x_sort=calls_exec_df["Sales Executive"].tolist(),
                    series_sort=["Calls Answered", "Calls Unanswered"],
                )
            with ch2:
                grouped_bar_chart_with_values(
                    calls_conv_long,
                    x_col="Sales Executive",
                    series_col="Type",
                    value_col="Count",
                    title="Calls vs Attended Visits vs Revisits",
                    x_sort=calls_exec_df["Sales Executive"].tolist(),
                    series_sort=["Total Calls", "Attended Visits", "Revisits"],
                )
    
        st.markdown("</div>", unsafe_allow_html=True)
    
        # =========================================================
        # Daily Visits Dashboard
        # =========================================================
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        st.markdown("<div class='section-banner'>🚶 Daily Visits Dashboard</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Visits, revisits, sources, calls, cancellations, and weekday trends.</div>", unsafe_allow_html=True)
    
        if dv_period.empty:
            st.info("Daily visits data is not available for the selected month range.")
        else:
            source_summary = pd.DataFrame({
                "Source": ["CP Visits", "Direct Walk-in", "References", "Digital", "Newspaper"],
                "Count": [
                    int(dv_period["CP Visits"].sum()),
                    int(dv_period["Direct Walk-in"].sum()),
                    int(dv_period["References"].sum()),
                    int(dv_period["Digital"].sum()),
                    int(dv_period["Newspaper"].sum()),
                ]
            }).sort_values("Count", ascending=False).reset_index(drop=True)
    
            top_source = "—"
            top_source_sub = ""
            if not source_summary.empty and int(source_summary["Count"].max()) > 0:
                sr = source_summary.iloc[0]
                top_source = sr["Source"]
                top_source_sub = f"{int(sr['Count']):,} visits"
    
            avg_visits_per_day = (dv_period["Total Visits"].mean() if len(dv_period) > 0 else float("nan"))
    
            d1, d2, d3, d4 = st.columns(4)
            d1.markdown(
                f"<div class='metric-card'><h3>Total Visits</h3><p>{total_visits:,}</p><span>All visit sources + revisits</span></div>",
                unsafe_allow_html=True
            )
            d2.markdown(
                f"<div class='metric-card'><h3>Total Revisits</h3><p>{total_revisits:,}</p><span>{_fmt_pct(revisit_rate)} of total visits</span></div>",
                unsafe_allow_html=True
            )
            d3.markdown(
                f"<div class='metric-card'><h3>Total Cancellations</h3><p>{total_cancellations:,}</p><span>Selected period</span></div>",
                unsafe_allow_html=True
            )
            d4.markdown(
                f"<div class='metric-card'><h3>Top Source</h3><p>{top_source}</p><span>{top_source_sub}</span></div>",
                unsafe_allow_html=True
            )
    
            d5, d6, d7, d8 = st.columns(4)
            d5.markdown(
                f"<div class='metric-card'><h3>Total Attended</h3><p>{int(dv_period['Total Attended'].sum()):,}</p><span>Executive attended visits</span></div>",
                unsafe_allow_html=True
            )
            d6.markdown(
                f"<div class='metric-card'><h3>Calls Answered</h3><p>{total_calls_answered:,}</p><span>Selected period</span></div>",
                unsafe_allow_html=True
            )
            d7.markdown(
                f"<div class='metric-card'><h3>Calls Unanswered</h3><p>{total_calls_unanswered:,}</p><span>Selected period</span></div>",
                unsafe_allow_html=True
            )
            d8.markdown(
                f"<div class='metric-card'><h3>Avg Visits / Day</h3><p>{0 if pd.isna(avg_visits_per_day) else int(round(avg_visits_per_day, 0)):,}</p><span>Average daily throughput</span></div>",
                unsafe_allow_html=True
            )
    
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dv_period["DayName"] = dv_period["Date_obj"].apply(lambda d: d.strftime("%A"))
            dv_period["DayName"] = pd.Categorical(dv_period["DayName"], categories=day_order, ordered=True)
    
            daily_trend = (
                dv_period.groupby("Date_obj", as_index=False)
                .agg({
                    BOOK_COL: "sum",
                    CANC_COL: "sum",
                    "Total Calls Answered": "sum",
                    "Total Calls Unanswered": "sum",
                })
                .sort_values("Date_obj")
            )
            daily_trend["DateLabel"] = daily_trend["Date_obj"].apply(lambda d: d.strftime("%d %b"))
            daily_trend["Total Calls"] = daily_trend["Total Calls Answered"] + daily_trend["Total Calls Unanswered"]
    
            weekday_summary = (
                dv_period.groupby("DayName", as_index=False)
                .agg({
                    "Total Visits": "sum",
                    BOOK_COL: "sum",
                    CANC_COL: "sum",
                    "Total Revisits": "sum",
                })
                .rename(columns={
                    "Total Visits": "Visits",
                    BOOK_COL: "Bookings",
                    CANC_COL: "Cancellations",
                    "Total Revisits": "Revisits",
                })
                .sort_values("DayName")
            )
    
            exec_visits_rows = []
            for ex in EXEC_CONFIG:
                exec_visits_rows.append({
                    "Sales Executive": ex["name"],
                    "Attended Visits": int(dv_period[ex["attended"]].sum()),
                    "Revisits": int(dv_period[ex["revisits"]].sum()),
                })
            exec_visits_df = pd.DataFrame(exec_visits_rows)
            exec_visits_long = pd.concat(
                [
                    exec_visits_df[["Sales Executive", "Attended Visits"]].rename(columns={"Attended Visits": "Count"}).assign(Type="Attended Visits"),
                    exec_visits_df[["Sales Executive", "Revisits"]].rename(columns={"Revisits": "Count"}).assign(Type="Revisits"),
                ],
                ignore_index=True
            )
    
            vch1, vch2 = st.columns(2)
            with vch1:
                line_chart_with_values(daily_trend, "DateLabel", BOOK_COL, "Daily Booking Trend")
            with vch2:
                line_chart_with_values(daily_trend, "DateLabel", "Total Calls", "Daily Total Calls Trend")
    
            vch3, vch4 = st.columns(2)
            with vch3:
                bar_chart_with_values(source_summary, "Source", "Count", "Lead Source Mix")
            with vch4:
                grouped_bar_chart_with_values(
                    exec_visits_long,
                    x_col="Sales Executive",
                    series_col="Type",
                    value_col="Count",
                    title="Executive-wise Attended Visits vs Revisits",
                    x_sort=exec_visits_df["Sales Executive"].tolist(),
                    series_sort=["Attended Visits", "Revisits"],
                )
    
            vch5, vch6 = st.columns(2)
            with vch5:
                grouped_bar_chart_with_values(
                    weekday_summary.melt(
                        id_vars=["DayName"],
                        value_vars=["Visits", "Bookings", "Cancellations"],
                        var_name="Type",
                        value_name="Count"
                    ),
                    x_col="DayName",
                    series_col="Type",
                    value_col="Count",
                    title="Weekday-wise Visits, Bookings, Cancellations",
                    x_sort=day_order,
                    series_sort=["Visits", "Bookings", "Cancellations"],
                )
            with vch6:
                line_chart_with_values(weekday_summary, "DayName", "Revisits", "Weekday-wise Revisits", x_sort=day_order)
    
        st.markdown("</div>", unsafe_allow_html=True)
    
        # =========================================================
        # Sales Executive Conversion Dashboard
        # =========================================================
        st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
        st.markdown("<div class='section-banner'>💼 Sales Executive Conversion Dashboard</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Executive-wise conversion speed, lead mix, unit mix, and supporting performance table.</div>", unsafe_allow_html=True)
    
        if df_period.empty:
            st.info("Booking / conversion data is not available for the selected month range.")
        else:
            se_rows = []
            executives = sorted(df_period["Sales Executive"].dropna().astype(str).unique())
    
            for se in executives:
                sub = df_period[df_period["Sales Executive"].astype(str) == se].copy()
    
                bookings = len(sub)
                avg_conv = sub["_ConvDays"].mean() if sub["_ConvDays"].notna().any() else float("nan")
                psf_val = avg_psf(sub) if bookings > 0 else float("nan")
    
                tseries = sub["_DerivedType2"]
                sold_1 = int((tseries == "1BHK").sum())
                sold_2 = int((tseries == "2BHK").sum())
    
                lead_counts = (
                    sub["_LeadType2"]
                    .value_counts()
                    .reset_index()
                )
                if lead_counts.empty:
                    top_lead = "—"
                else:
                    top_lead = str(lead_counts.iloc[0, 0])
    
                se_rows.append({
                    "Sales Executive": se,
                    "Bookings": bookings,
                    "Avg Conversion Days": avg_conv,
                    "Overall PSF": psf_val,
                    "1 BHK Sold": sold_1,
                    "2 BHK Sold": sold_2,
                    "Top Lead Type": top_lead,
                })
    
            se_summary_df = pd.DataFrame(se_rows).sort_values("Bookings", ascending=False).reset_index(drop=True)
    
            total_1bhk = int((df_period["_DerivedType2"] == "1BHK").sum())
            total_2bhk = int((df_period["_DerivedType2"] == "2BHK").sum())
    
            best_exec_by_conv = "—"
            best_exec_by_conv_sub = ""
            conv_rank = se_summary_df.dropna(subset=["Avg Conversion Days"])
            conv_rank = conv_rank[conv_rank["Bookings"] > 0]
            if not conv_rank.empty:
                rr = conv_rank.sort_values("Avg Conversion Days", ascending=True).iloc[0]
                best_exec_by_conv = rr["Sales Executive"]
                best_exec_by_conv_sub = _fmt_days(rr["Avg Conversion Days"])
    
            lead_type_summary = (
                df_period.groupby("_LeadType2", as_index=False)
                .size()
                .rename(columns={"size": "Bookings"})
                .sort_values("Bookings", ascending=False)
            )
            dominant_lead_type = "—"
            dominant_lead_sub = ""
            if not lead_type_summary.empty and int(lead_type_summary["Bookings"].max()) > 0:
                lr = lead_type_summary.iloc[0]
                dominant_lead_type = str(lr["_LeadType2"])
                dominant_lead_sub = f"{int(lr['Bookings']):,} records"
    
            best_1bhk_exec = "—"
            best_1bhk_sub = ""
            best_1bhk_df = se_summary_df.sort_values("1 BHK Sold", ascending=False)
            if not best_1bhk_df.empty and int(best_1bhk_df.iloc[0]["1 BHK Sold"]) > 0:
                rr = best_1bhk_df.iloc[0]
                best_1bhk_exec = rr["Sales Executive"]
                best_1bhk_sub = f"{int(rr['1 BHK Sold']):,} sold"
    
            best_2bhk_exec = "—"
            best_2bhk_sub = ""
            best_2bhk_df = se_summary_df.sort_values("2 BHK Sold", ascending=False)
            if not best_2bhk_df.empty and int(best_2bhk_df.iloc[0]["2 BHK Sold"]) > 0:
                rr = best_2bhk_df.iloc[0]
                best_2bhk_exec = rr["Sales Executive"]
                best_2bhk_sub = f"{int(rr['2 BHK Sold']):,} sold"
    
            b1, b2, b3, b4 = st.columns(4)
            b1.markdown(
                f"<div class='metric-card'><h3>Avg Conversion Period</h3><p>{_fmt_days(avg_conv_overall)}</p><span>Lower is better</span></div>",
                unsafe_allow_html=True
            )
            b2.markdown(
                f"<div class='metric-card'><h3>Fastest Conversion Executive</h3><p>{best_exec_by_conv}</p><span>{best_exec_by_conv_sub}</span></div>",
                unsafe_allow_html=True
            )
            b3.markdown(
                f"<div class='metric-card'><h3>1 BHK Sold</h3><p>{total_1bhk:,}</p><span>{_fmt_pct(_pct(total_1bhk, total_1bhk + total_2bhk))} of unit mix</span></div>",
                unsafe_allow_html=True
            )
            b4.markdown(
                f"<div class='metric-card'><h3>2 BHK Sold</h3><p>{total_2bhk:,}</p><span>{_fmt_pct(_pct(total_2bhk, total_1bhk + total_2bhk))} of unit mix</span></div>",
                unsafe_allow_html=True
            )
    
            b5, b6, b7, b8 = st.columns(4)
            b5.markdown(
                f"<div class='metric-card'><h3>Active Executives</h3><p>{len(executives):,}</p><span>In selected range</span></div>",
                unsafe_allow_html=True
            )
            b6.markdown(
                f"<div class='metric-card'><h3>Dominant Lead Type</h3><p>{dominant_lead_type}</p><span>{dominant_lead_sub}</span></div>",
                unsafe_allow_html=True
            )
            b7.markdown(
                f"<div class='metric-card'><h3>Best 1 BHK Seller</h3><p>{best_1bhk_exec}</p><span>{best_1bhk_sub}</span></div>",
                unsafe_allow_html=True
            )
            b8.markdown(
                f"<div class='metric-card'><h3>Best 2 BHK Seller</h3><p>{best_2bhk_exec}</p><span>{best_2bhk_sub}</span></div>",
                unsafe_allow_html=True
            )
    
            se_display = se_summary_df.copy()
            se_display["Avg Conversion Days"] = se_display["Avg Conversion Days"].apply(_fmt_days)
            se_display["Overall PSF"] = se_display["Overall PSF"].apply(fmt_psf)
    
            st.markdown("#### Executive-wise Conversion Summary")
            st.dataframe(se_display, use_container_width=True, hide_index=True)
    
            lead_type_summary = lead_type_summary.rename(columns={"_LeadType2": "Lead Type"})
    
            month_booking_summary = (
                df_period.groupby("_MonthDisplay", as_index=False)
                .size()
                .rename(columns={"size": "Bookings"})
            )
            month_booking_summary["_Sort"] = month_booking_summary["_MonthDisplay"].apply(
                lambda x: ordered_months.index(x) if x in ordered_months else 9999
            )
            month_booking_summary = month_booking_summary.sort_values("_Sort").drop(columns=["_Sort"])
    
            bhk_long = pd.concat(
                [
                    se_summary_df[["Sales Executive", "1 BHK Sold"]].rename(columns={"1 BHK Sold": "Count"}).assign(Type="1 BHK"),
                    se_summary_df[["Sales Executive", "2 BHK Sold"]].rename(columns={"2 BHK Sold": "Count"}).assign(Type="2 BHK"),
                ],
                ignore_index=True
            )
    
            chb1, chb2 = st.columns(2)
            with chb1:
                bar_chart_with_values(
                    se_summary_df.sort_values("Avg Conversion Days", ascending=True),
                    "Sales Executive",
                    "Avg Conversion Days",
                    "Executive-wise Avg Conversion Days",
                    x_sort=se_summary_df.sort_values("Avg Conversion Days", ascending=True)["Sales Executive"].tolist(),
                )
            with chb2:
                bar_chart_with_values(
                    lead_type_summary,
                    "Lead Type",
                    "Bookings",
                    "Lead Type-wise Records",
                    x_sort=lead_type_summary["Lead Type"].tolist(),
                )
    
            chb3, chb4 = st.columns(2)
            with chb3:
                grouped_bar_chart_with_values(
                    bhk_long,
                    x_col="Sales Executive",
                    series_col="Type",
                    value_col="Count",
                    title="1 BHK vs 2 BHK Sold by Executive",
                    x_sort=se_summary_df["Sales Executive"].tolist(),
                    series_sort=["1 BHK", "2 BHK"],
                )
            with chb4:
                line_chart_with_values(
                    month_booking_summary.rename(columns={"_MonthDisplay": "Month"}),
                    "Month",
                    "Bookings",
                    "Booking Trend Across Selected Months",
                    x_sort=month_booking_summary["_MonthDisplay"].tolist(),
                )
    
            with st.expander("Open detailed executive cards"):
                for _, row in se_summary_df.iterrows():
                    st.markdown(f"### {row['Sales Executive']}")
                    st.caption(f"Bookings: {int(row['Bookings']):,} | Overall PSF: {fmt_psf(row['Overall PSF'])}")
    
                    dc1, dc2, dc3, dc4 = st.columns(4)
                    dc1.markdown(
                        f"<div class='metric-card'><h3>Avg Conversion</h3><p>{_fmt_days(row['Avg Conversion Days'])}</p><span>Average conversion days</span></div>",
                        unsafe_allow_html=True
                    )
                    dc2.markdown(
                        f"<div class='metric-card'><h3>Top Lead Type</h3><p>{row['Top Lead Type']}</p><span>Most frequent source</span></div>",
                        unsafe_allow_html=True
                    )
                    dc3.markdown(
                        f"<div class='metric-card'><h3>1 BHK Sold</h3><p>{int(row['1 BHK Sold']):,}</p><span>{_fmt_pct(_pct(int(row['1 BHK Sold']), int(row['Bookings'])))}</span></div>",
                        unsafe_allow_html=True
                    )
                    dc4.markdown(
                        f"<div class='metric-card'><h3>2 BHK Sold</h3><p>{int(row['2 BHK Sold']):,}</p><span>{_fmt_pct(_pct(int(row['2 BHK Sold']), int(row['Bookings'])))}</span></div>",
                        unsafe_allow_html=True
                    )
                    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    
        st.markdown("</div>", unsafe_allow_html=True)
    with TAB_PROJECTED:
            import datetime as dt
            import math
            import pandas as pd
            import altair as alt
            import streamlit as st
        
            st.subheader("📌 Projected Sales Dashboard (FY Apr–Mar)")
        
            # ----------------------------
            # CONFIG (as per your requirement)
            # ----------------------------
            TOTAL_FLATS_TARGET = 588
            PROJECT_START = dt.date(2025, 4, 1)             # Project starts 1 Apr 2025
            PROJECT_END   = dt.date(2028, 3, 31)            # 3 FY years ending 31 Mar 2028
        
            GOOD_DAY_WEIGHT   = 1.25
            NORMAL_DAY_WEIGHT = 1.00
            BAD_DAY_WEIGHT    = 0.00
        
            # ----------------------------
            # UI: Colored KPI Cards
            # ----------------------------
            st.markdown(
                """
                <style>
                .psd-card{
                    padding:18px;
                    border-radius:14px;
                    text-align:center;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    margin:8px 0;
                    border:1px solid #e5e7eb;
                }
                .psd-title{font-size:13px;font-weight:700;color:#111827;margin-bottom:6px;}
                .psd-value{font-size:26px;font-weight:900;color:#111827;line-height:1.1;}
                .psd-blue{background:#eff6ff;border-color:#93c5fd;}
                .psd-green{background:#ecfdf5;border-color:#6ee7b7;}
                .psd-red{background:#fef2f2;border-color:#fca5a5;}
                .psd-amber{background:#fffbeb;border-color:#fcd34d;}
                .psd-gray{background:#ffffff;border-color:#e5e7eb;}
                </style>
                """,
                unsafe_allow_html=True
            )
        
            def psd_kpi(title: str, value, theme: str = "psd-gray"):
                st.markdown(
                    f"""
                    <div class="psd-card {theme}">
                        <div class="psd-title">{title}</div>
                        <div class="psd-value">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
            # ----------------------------
            # Helpers: dates / months / FY / quarters
            # ----------------------------
            def month_start(d: dt.date) -> dt.date:
                return dt.date(d.year, d.month, 1)
        
            def add_months(d: dt.date, months: int) -> dt.date:
                y = d.year + (d.month - 1 + months) // 12
                m = (d.month - 1 + months) % 12 + 1
                return dt.date(y, m, 1)
        
            def month_end(d: dt.date) -> dt.date:
                return add_months(month_start(d), 1) - dt.timedelta(days=1)
        
            def iter_days(start: dt.date, end: dt.date):
                cur = start
                while cur <= end:
                    yield cur
                    cur += dt.timedelta(days=1)
        
            def fy_start(d: dt.date) -> dt.date:
                # FY starts on Apr 1
                return dt.date(d.year if d.month >= 4 else d.year - 1, 4, 1)
        
            def fy_label(fy_s: dt.date) -> str:
                # "APR 25 - MAR 26"
                return f"APR {str(fy_s.year)[-2:]} - MAR {str(fy_s.year + 1)[-2:]}"
        
            def quarter_start(d: dt.date) -> dt.date:
                # FY quarters: Q1 Apr-Jun, Q2 Jul-Sep, Q3 Oct-Dec, Q4 Jan-Mar
                if 4 <= d.month <= 6:
                    return dt.date(d.year, 4, 1)
                if 7 <= d.month <= 9:
                    return dt.date(d.year, 7, 1)
                if 10 <= d.month <= 12:
                    return dt.date(d.year, 10, 1)
                return dt.date(d.year, 1, 1)
        
            def quarter_num(qs: dt.date) -> int:
                return {4: 1, 7: 2, 10: 3, 1: 4}[qs.month]
        
            def quarter_end(qs: dt.date) -> dt.date:
                return add_months(qs, 3) - dt.timedelta(days=1)
        
            def quarter_label(qs: dt.date) -> str:
                qe = quarter_end(qs)
                qn = quarter_num(qs)
                return f"Q{qn} {qs.strftime('%b %y').upper()} - {qe.strftime('%b %y').upper()}"
        
            # ----------------------------
            # Build day-type map from good_bad_df (Auspicious sheet) if available
            # - Uses previous-year same-date fallback for future years
            # ----------------------------
            gb = globals().get("good_bad_df", None)
        
            def _pick_type_col(df_in: pd.DataFrame):
                if df_in is None or df_in.empty:
                    return None
                candidates = [
                    "Type", "type", "DayType", "Day Type", "CATEGORY", "Category",
                    "Status", "GOOD/BAD", "Good/Bad", "GoodBad", "Nature"
                ]
                for c in candidates:
                    if c in df_in.columns:
                        return c
                # fallback: first non-Date column
                for c in df_in.columns:
                    if c != "Date":
                        return c
                return None
        
            def _normalize_day_type(x: object) -> str:
                s = str(x).strip().upper()
                if "HOLIDAY" in s:
                    return "HOLIDAY"
                if "BAD" in s:
                    return "BAD"
                if "FEST" in s:
                    return "FESTIVAL"
                if "GOOD" in s:
                    return "GOOD"
                if "NEUT" in s:
                    return "NEUTRAL"
                # common short forms
                if s in {"H", "HD"}:
                    return "HOLIDAY"
                if s in {"B"}:
                    return "BAD"
                if s in {"G"}:
                    return "GOOD"
                return "NEUTRAL"
        
            # priority: BAD/HOLIDAY overrides GOOD/FESTIVAL
            _priority = {"NEUTRAL": 1, "GOOD": 2, "FESTIVAL": 2, "BAD": 3, "HOLIDAY": 3}
        
            day_type_by_date = {}
            if gb is not None and isinstance(gb, pd.DataFrame) and (not gb.empty) and ("Date" in gb.columns):
                gb2 = gb.copy()
                gb2["Date"] = pd.to_datetime(gb2["Date"], errors="coerce")
                gb2 = gb2.dropna(subset=["Date"])
                tcol = _pick_type_col(gb2)
        
                if tcol is not None:
                    for _, r in gb2.iterrows():
                        d = r["Date"].date()
                        t = _normalize_day_type(r[tcol])
                        if d not in day_type_by_date or _priority[t] > _priority[day_type_by_date[d]]:
                            day_type_by_date[d] = t
        
            def day_type_for(d: dt.date) -> str:
                # exact date
                if d in day_type_by_date:
                    return day_type_by_date[d]
                # previous-year fallback (so FY 26-27 uses FY 25-26 pattern)
                for back in (1, 2, 3):
                    try:
                        d2 = dt.date(d.year - back, d.month, d.day)
                    except ValueError:
                        continue
                    if d2 in day_type_by_date:
                        return day_type_by_date[d2]
                return "NEUTRAL"
        
            def day_weight(d: dt.date) -> float:
                t = day_type_for(d)
                if t in ("BAD", "HOLIDAY"):
                    return BAD_DAY_WEIGHT
                if t in ("GOOD", "FESTIVAL"):
                    return GOOD_DAY_WEIGHT
                return NORMAL_DAY_WEIGHT
        
            # ----------------------------
            # Booking data (df is your Booking sheet df already in Tab1)
            # ----------------------------
            if df is None or df.empty or ("Date" not in df.columns):
                st.warning("Booking data not available (missing df or Date column).")
            else:
                today = dt.date.today()
                effective_today = max(today, PROJECT_START)
                if today > PROJECT_END:
                    st.info("Project period is over (today is after project end).")
        
                dfb = df.copy()
                dfb["Date"] = pd.to_datetime(dfb["Date"], errors="coerce")
                dfb = dfb.dropna(subset=["Date"])
                dfb["DateOnly"] = dfb["Date"].dt.date
        
                # Achieved bookings only inside project window up to today
                dfb_proj = dfb[
                    (dfb["DateOnly"] >= PROJECT_START)
                    & (dfb["DateOnly"] <= min(today, PROJECT_END))
                ].copy()
        
                dfb_proj["MonthStart"] = dfb_proj["Date"].dt.to_period("M").dt.to_timestamp().dt.date
                achieved_by_month = dfb_proj.groupby("MonthStart").size().to_dict()
        
                total_booked = int(len(dfb_proj))
                remaining_flats = max(0, TOTAL_FLATS_TARGET - total_booked)
        
                # average monthly bookings so far (used for realistic multiplier)
                months_with_data = sorted(achieved_by_month.keys())
                avg_monthly_bookings = (total_booked / len(months_with_data)) if months_with_data else (TOTAL_FLATS_TARGET / 36.0)
        
                def clamp(x: float, lo: float, hi: float) -> float:
                    return max(lo, min(hi, x))
        
                # ----------------------------
                # Build all project months (Apr 2025 ... Mar 2028) and compute weights
                # ----------------------------
                project_months = []
                cur_ms = month_start(PROJECT_START)
                end_ms = month_start(PROJECT_END)
        
                while cur_ms <= end_ms:
                    full_ms = cur_ms
                    full_me = month_end(full_ms)
        
                    # clamp month range to project window
                    rng_start = max(full_ms, PROJECT_START)
                    rng_end = min(full_me, PROJECT_END)
        
                    # day weights from Good/Bad/Festival (or neutral if not present)
                    w = 0.0
                    for d in iter_days(rng_start, rng_end):
                        w += day_weight(d)
        
                    # previous-year same month bookings multiplier (Mar 2027 uses Mar 2026)
                    prev_year_ms = dt.date(full_ms.year - 1, full_ms.month, 1)
                    prev_year_count = achieved_by_month.get(prev_year_ms, None)
                    if prev_year_count is None:
                        booking_factor = 1.0
                    else:
                        booking_factor = (prev_year_count + 1.0) / (avg_monthly_bookings + 1.0)
                        booking_factor = clamp(booking_factor, 0.80, 1.20)  # keep realistic
        
                    eff_w = max(0.01, w * booking_factor)
        
                    project_months.append(
                        {
                            "MonthStart": full_ms,
                            "MonthEnd": full_me,
                            "Weight": w,
                            "BookingFactor": booking_factor,
                            "EffWeight": eff_w,
                        }
                    )
                    cur_ms = add_months(cur_ms, 1)
        
                # ----------------------------
                # Allocate monthly targets across ALL 36 months so SUM = 588
                # ----------------------------
                total_eff = sum(m["EffWeight"] for m in project_months)
                if total_eff <= 0:
                    # fallback: equal distribution
                    float_targets = [TOTAL_FLATS_TARGET / len(project_months)] * len(project_months)
                else:
                    float_targets = [(m["EffWeight"] / total_eff) * TOTAL_FLATS_TARGET for m in project_months]
        
                floors = [int(math.floor(x)) for x in float_targets]
                rem = TOTAL_FLATS_TARGET - sum(floors)
        
                fracs = sorted(
                    [(float_targets[i] - floors[i], i) for i in range(len(project_months))],
                    reverse=True
                )
                for k in range(rem):
                    floors[fracs[k][1]] += 1
        
                target_by_month = {project_months[i]["MonthStart"]: int(floors[i]) for i in range(len(project_months))}
        
                # ----------------------------
                # Current month KPIs
                # ----------------------------
                this_month_ms = month_start(effective_today)
                this_month_me = month_end(this_month_ms)
        
                # targets / achieved for this month
                this_month_target = int(target_by_month.get(this_month_ms, 0))
                achieved_this_month = int(achieved_by_month.get(this_month_ms, 0))
                gap_this_month = this_month_target - achieved_this_month
        
                # selling days left (this month)
                selling_days_left_this_month = 0
                for d in iter_days(max(effective_today, this_month_ms), min(this_month_me, PROJECT_END)):
                    if day_weight(d) > 0:
                        selling_days_left_this_month += 1
        
                # selling days left (project)
                selling_days_left_project = 0
                for d in iter_days(effective_today, PROJECT_END):
                    if day_weight(d) > 0:
                        selling_days_left_project += 1
        
                # needed per selling day (this month)
                need_this_month = max(0, gap_this_month)
                needed_per_selling_day = (need_this_month / selling_days_left_this_month) if selling_days_left_this_month > 0 else 0.0
        
                # Good/Bad counts this month (based on available good_bad_df + fallback)
                bad_days_this_month = 0
                good_days_this_month = 0
                for d in iter_days(this_month_ms, min(this_month_me, PROJECT_END)):
                    t = day_type_for(d)
                    if t in ("BAD", "HOLIDAY"):
                        bad_days_this_month += 1
                    elif t in ("GOOD", "FESTIVAL"):
                        good_days_this_month += 1
        
                project_ends_in_days = max(0, (PROJECT_END - today).days)
        
                # ----------------------------
                # KPI rows (colored)
                # ----------------------------
                r1 = st.columns(3)
                with r1[0]: psd_kpi("Flats Target (3 Years)", TOTAL_FLATS_TARGET, "psd-blue")
                with r1[1]: psd_kpi("Total Bookings (From 1 Apr 2025)", total_booked, "psd-green")
                with r1[2]: psd_kpi("Remaining Flats", remaining_flats, "psd-red")
        
                r2 = st.columns(3)
                with r2[0]: psd_kpi("This Month Target", this_month_target, "psd-blue")
                with r2[1]: psd_kpi("Achieved (This Month)", achieved_this_month, "psd-green")
                with r2[2]:
                    theme = "psd-green" if gap_this_month <= 0 else "psd-red"
                    psd_kpi("Gap (Target - Achieved)", gap_this_month, theme)
        
                r3 = st.columns(3)
                with r3[0]: psd_kpi("Selling Days Left (Project)", selling_days_left_project, "psd-gray")
                with r3[1]: psd_kpi("Selling Days Left (This Month)", selling_days_left_this_month, "psd-gray")
                with r3[2]: psd_kpi("Needed / Selling Day (This Month)", f"{needed_per_selling_day:.1f}", "psd-amber")
        
                r4 = st.columns(3)
                with r4[0]: psd_kpi("Bad Days (This Month)", bad_days_this_month, "psd-red")
                with r4[1]: psd_kpi("Good/Festival Days (This Month)", good_days_this_month, "psd-green")
                with r4[2]: psd_kpi("Project Ends In (Days)", project_ends_in_days, "psd-gray")
        
                # ----------------------------
                # Current quarter + next 2 quarters
                # ----------------------------
                st.markdown("### 🗓️ Current Quarter + Next 2 Quarters (FY Quarters)")
                q0 = quarter_start(effective_today)
        
                q_cols = st.columns(3)
                for i in range(3):
                    qs = add_months(q0, 3 * i)
                    qe = quarter_end(qs)
        
                    # quarter target = sum of month targets inside quarter
                    q_target = 0
                    cur = month_start(qs)
                    while cur <= month_start(qe):
                        q_target += int(target_by_month.get(cur, 0))
                        cur = add_months(cur, 1)
        
                    # achieved in quarter (up to today, inside project)
                    if qs > today:
                        q_ach = 0
                    else:
                        q_ach = int(
                            dfb_proj[
                                (dfb_proj["DateOnly"] >= max(qs, PROJECT_START))
                                & (dfb_proj["DateOnly"] <= min(today, qe, PROJECT_END))
                            ].shape[0]
                        )
        
                    with q_cols[i]:
                        st.markdown(
                            f"""
                            <div class="psd-card psd-gray">
                                <div class="psd-title">{quarter_label(qs)}</div>
                                <div class="psd-value">{q_ach} / {q_target}</div>
                                <div style="font-size:12px;color:#6b7280;margin-top:4px;">Achieved / Target</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        
                # ----------------------------
                # FY targets: current FY + next 2 FY (Apr–Mar)
                # ----------------------------
                st.markdown("### 📅 Yearly Targets (FY Apr–Mar)")
                fy0 = fy_start(effective_today)
        
                fy_cols = st.columns(3)
                for i in range(3):
                    fys = dt.date(fy0.year + i, 4, 1)
                    fye = dt.date(fy0.year + i + 1, 3, 31)
        
                    # FY target = sum of month targets inside FY
                    fy_target = 0
                    cur = month_start(fys)
                    while cur <= month_start(fye):
                        # only count months inside the project window
                        if PROJECT_START <= cur <= PROJECT_END:
                            fy_target += int(target_by_month.get(cur, 0))
                        cur = add_months(cur, 1)
        
                    # Achieved in FY (up to today)
                    if fys > today:
                        fy_ach = 0
                    else:
                        fy_ach = int(
                            dfb_proj[
                                (dfb_proj["DateOnly"] >= max(fys, PROJECT_START))
                                & (dfb_proj["DateOnly"] <= min(today, fye, PROJECT_END))
                            ].shape[0]
                        )
        
                    with fy_cols[i]:
                        st.markdown(
                            f"""
                            <div class="psd-card psd-gray">
                                <div class="psd-title">{fy_label(fys)}</div>
                                <div class="psd-value">{fy_ach} / {fy_target}</div>
                                <div style="font-size:12px;color:#6b7280;margin-top:4px;">Achieved / Target</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        
                # ----------------------------
                # 6-month projection chart (chronological)
                # ----------------------------
                st.markdown("### 📈 6‑Month Projection (Targets)")
        
                next6 = []
                cur = month_start(effective_today)
                for i in range(6):
                    ms = add_months(cur, i)
                    if ms > PROJECT_END:
                        break
                    next6.append(
                        {
                            "MonthStart": pd.to_datetime(ms),
                            "Month": ms.strftime("%b %y").upper(),
                            "Target": int(target_by_month.get(ms, 0)),
                        }
                    )
        
                if next6:
                    proj_df = pd.DataFrame(next6)
        
                    line = (
                        alt.Chart(proj_df)
                        .mark_line(point=True, strokeDash=[4, 4])
                        .encode(
                            x=alt.X("MonthStart:T", title="Month", axis=alt.Axis(format="%b %y")),
                            y=alt.Y("Target:Q", title="Units"),
                            tooltip=["Month:N", "Target:Q"],
                        )
                    )
                    labels = (
                        alt.Chart(proj_df)
                        .mark_text(dy=-10)
                        .encode(x="MonthStart:T", y="Target:Q", text="Target:Q")
                    )
        
                    st.altair_chart(line + labels, use_container_width=True)
                else:
                    st.info("No upcoming months available inside project window.")
with tab2:
    # ============================
    # 🧩 Combined Tools in Sub-Tabs (UI-only wrapping)
    # ============================

    ST_RATE, ST_REVERSE, ST_CP, ST_INCENTIVE, ST_INCENTIVE_STATUS = st.tabs([
        "Rate Calculator",
        "Reverse Rate Calculator",
        "CP Payout Calculator",
        "Incentive Calculator",
        "Incentive Status"
    ])

    # ------------------------------------------------------------------
    # SUBTAB 1 — 🧮 RATE CALCULATOR (FORM + Remarks)
    # ------------------------------------------------------------------
    with ST_RATE:
        # ---------- THEME / STYLES ----------
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

        # Common carpet list
        ALL_CARPETS = [480.94, 482.12, 655.10, 665.65, 666.29]

        st.markdown('<div class="tool-wrap"><div class="tool-title">🧮 Rate Calculator</div>'
                    '<div class="subtext">Computes per-sqft rates with & without Channel Partner deduction.</div>',
                    unsafe_allow_html=True)

        saleable_area = rate_excl_cp = rate_incl_cp = None
        with st.form("rate_calc_form", clear_on_submit=False):
            rc_col1, rc_col2 = st.columns(2)
            with rc_col1:
                cost_lakhs = st.number_input("Enter Cost (in Lakhs)", min_value=0.0, step=0.1, key="rc_cost_lakhs")
            with rc_col2:
                carpet_area = st.selectbox("Select Carpet Area", options=ALL_CARPETS, key="rc_carpet_area")

            cp_percentage = st.number_input("Channel Partner %", min_value=0.0, step=0.1, key="rc_cp_percentage")
            rc_submit = st.form_submit_button("Calculate Rate")

        if rc_submit and (cost_lakhs is not None) and (cp_percentage is not None) and (carpet_area is not None):
            saleable_area = round(carpet_area * 1.38, 2)
            adjusted_cost = (cost_lakhs * 100000) - 30000  # infra/other adj removed

            # GST divisor by saleable slab
            gst_divisor = 1.0
            if 662 <= saleable_area <= 667:
                gst_divisor = 1.08
            elif 903 <= saleable_area <= 920:
                gst_divisor = 1.12

            pre_cp_value = adjusted_cost / gst_divisor
            rate_excl_cp = round(pre_cp_value / saleable_area)

            # CP deduction applied only on basic above 4L
            after_cp_deduction = ((pre_cp_value - 400000) * (1 - cp_percentage / 100)) + 400000
            rate_incl_cp = round(after_cp_deduction / saleable_area)

            # Remark on Per Sqft Rate (Excl. CP)
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
        st.markdown('</div>', unsafe_allow_html=True)  # close tool-wrap

    # ------------------------------------------------------------------
    # SUBTAB 2 — 🔄 REVERSE RATE CALCULATOR (FORM)
    # ------------------------------------------------------------------
    with ST_REVERSE:
        # ---------- THEME / STYLES ----------
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

        st.markdown('<div class="tool-wrap"><div class="tool-title">🔄 Reverse Rate Calculator</div>'
                    '<div class="subtext">Back-calculates total package from a given PSF rate.</div>',
                    unsafe_allow_html=True)

        with st.form("reverse_rate_form", clear_on_submit=False):
            psf_rate = st.number_input("Enter Per Square Feet Rate", min_value=0.0, step=10.0, format="%.2f", key="rev_psf_rate")
            rev_submit = st.form_submit_button("Calculate Total Cost")

        if rev_submit and psf_rate > 0:
            for carpet in [480.94, 482.12, 655.1, 665.65, 666.29, 678, 689, 790, 545, 756]:
                saleable_area = carpet * 1.38
                base_cost = saleable_area * psf_rate

                stamp_duty = base_cost * 0.07
                gst_rate = 0.01 if carpet in [480.94, 482.12] else 0.05
                gst = base_cost * gst_rate
                registration = 30000
                legal = 12000
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
    # SUBTAB 3 — 💰 CP PAYOUT CALCULATOR (FORM)
    # ------------------------------------------------------------------
    with ST_CP:
        # ---------- THEME / STYLES ----------
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

        st.markdown('<div class="tool-wrap"><div class="tool-title">💰 CP Payout Calculator</div>'
                    '<div class="subtext">Computes CP payout on final cost after adjustments.</div>',
                    unsafe_allow_html=True)

        with st.form("cp_payout_form", clear_on_submit=False):
            final_cost_lakhs = st.number_input("Enter Final Cost (in lakhs)", min_value=0.0, step=0.1, key="cp_final_cost")
            cp_percent = st.number_input("Enter Channel Partner %", min_value=0.0, step=0.1, key="cp_percent")
            cp_submit = st.form_submit_button("Calculate CP Payout")

        if cp_submit and (final_cost_lakhs > 0) and (cp_percent > 0):
            final_cost = final_cost_lakhs * 1_00_000
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

        st.markdown('</div>', unsafe_allow_html=True)  # close tool-wrap

    # ------------------------------------------------------------------
    # SUBTAB 4 — 💸 INCENTIVE CALCULATOR (Agreement Done = "Done")
    # ------------------------------------------------------------------
    with ST_INCENTIVE:
        st.header("💸 Incentive Calculator")
    
        # ---------- Theme CSS ----------
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
    
        # ---------- Logic ----------
        import numpy as np
        import pandas as pd
        import re
    
        # ============================
        # Filter form – Quarter + Executive
        # ============================
        df['Lead'] = df['Lead Type'].astype(str).str.strip().str.title()
    
        quarter_options = sorted(df['Quarter'].dropna().unique())
        exec_names = ['Harshal S', 'Tejas P', 'Sagar B', 'Alok R', 'Ashutosh S', 'Komal K']
    
        if not quarter_options:
            st.warning("No quarters found in data.")
        else:
            default_quarter = st.session_state.get("ic_selected_quarter_val", quarter_options[0])
            default_exec    = st.session_state.get("ic_selected_exec_val", exec_names[0])
    
            try:
                default_q_index = quarter_options.index(default_quarter)
            except:
                default_q_index = 0
    
            try:
                default_e_index = exec_names.index(default_exec)
            except:
                default_e_index = 0
    
            with st.form("incentive_filter"):
                selected_quarter = st.selectbox("Select Quarter", quarter_options, index=default_q_index)
                selected_exec = st.selectbox("Select Sales Executive", exec_names, index=default_e_index)
                submitted = st.form_submit_button("Show Incentive")
    
            if submitted:
                st.session_state["ic_selected_quarter_val"] = selected_quarter
                st.session_state["ic_selected_exec_val"] = selected_exec
    
            active_quarter = st.session_state.get("ic_selected_quarter_val")
            active_exec    = st.session_state.get("ic_selected_exec_val")
    
            if active_quarter is None or active_exec is None:
                st.info("Please select Quarter and Sales Executive, then click **Show Incentive**.")
            else:
                exec_df = df[(df['Quarter'] == active_quarter) & (df['Sales Executive'] == active_exec)].copy()
    
                # ============================
                # Helpers
                # ============================
                def _to_num(x):
                    if pd.isna(x):
                        return np.nan
                    s = str(x).replace('₹', '').replace('Rs', '').replace('rs', '').replace(',', '').strip()
                    try:
                        return float(s)
                    except:
                        return np.nan
    
                def _avg_rate_for_mask(sub_df):
                    if sub_df.empty or ('Agreement Cost' not in sub_df.columns) or ('Carpet Area' not in sub_df.columns):
                        return np.nan
                    ac_sum = sub_df['Agreement Cost'].apply(_to_num).sum(min_count=1)
                    ca_sum = sub_df['Carpet Area'].apply(_to_num).sum(min_count=1)
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
    
                # Keep old slab only for OTHER wings if needed
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
    
                # E+F slab
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
    
                # C Wing slab (NON-PODIUM)
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
    
                # Podium slab
                def podium_payout_percent_from_rate(r):
                    if pd.isna(r):
                        return 0.0
                    if r >= 5800:
                        return 1.0
                    elif 5700 <= r < 5800:
                        return 0.7
                    return 0.0
    
                # ============================
                # Identify Podium Units
                # ============================
                if 'Floor' in exec_df.columns:
                    floor_norm = exec_df['Floor'].astype(str).str.strip().str.lower()
                    podium_mask = (
                        floor_norm.eq('1')
                        | floor_norm.eq('1.0')
                        | floor_norm.str.contains(r'\b1st\b|\bfirst\b|podium|garden', case=False, na=False)
                    )
                else:
                    podium_mask = pd.Series(False, index=exec_df.index)
    
                exec_df['PodiumFlag'] = podium_mask
    
                # ============================
                # Avg PSF (overall bookings)
                # ============================
                if 'Agreement Cost' in exec_df.columns and 'Carpet Area' in exec_df.columns:
                    agreement_cost_sum = exec_df['Agreement Cost'].apply(_to_num).sum(min_count=1)
                    carpet_area_sum = exec_df['Carpet Area'].apply(_to_num).sum(min_count=1)
                    denom = (carpet_area_sum * 1.38) if pd.notna(carpet_area_sum) else np.nan
                    avg_rate = (agreement_cost_sum / denom) if (pd.notna(agreement_cost_sum) and pd.notna(denom) and denom > 0) else np.nan
                else:
                    avg_rate = exec_df['Rate'].mean() if 'Rate' in exec_df.columns else np.nan
    
                unit_count = len(exec_df)
    
                # ---- Wing helpers (E / F / C) — EXCLUDE Podium from wing counts/PSF
                if 'Wing' in exec_df.columns:
                    exec_df['WingNorm'] = exec_df['Wing'].astype(str).str.strip().str.upper()
                else:
                    exec_df['WingNorm'] = ""
    
                mask_non_podium = ~exec_df['PodiumFlag']
                mask_E  = exec_df['WingNorm'].eq('E') & mask_non_podium
                mask_F  = exec_df['WingNorm'].eq('F') & mask_non_podium
                mask_C  = exec_df['WingNorm'].eq('C') & mask_non_podium
                mask_EF = mask_E | mask_F
                mask_EFC = mask_EF | mask_C
                mask_POD = exec_df['PodiumFlag']
    
                e_units = int(mask_E.sum())
                f_units = int(mask_F.sum())
                c_units = int(mask_C.sum())
                ef_units = e_units + f_units
                pod_units = int(mask_POD.sum())
                efc_units_no_podium = ef_units + c_units
    
                avg_rate_EF  = _avg_rate_for_mask(exec_df[mask_EF]) if ef_units > 0 else np.nan
                avg_rate_C   = _avg_rate_for_mask(exec_df[mask_C]) if c_units > 0 else np.nan
                avg_rate_E   = _avg_rate_for_mask(exec_df[mask_E]) if e_units > 0 else np.nan
                avg_rate_F   = _avg_rate_for_mask(exec_df[mask_F]) if f_units > 0 else np.nan
                avg_rate_POD = _avg_rate_for_mask(exec_df[mask_POD]) if pod_units > 0 else np.nan
    
                # ---------- Per-unit rate ----------
                if unit_count >= 18:
                    direct_rate = 6000
                    cp_like_rate = 6000
                else:
                    direct_rate = 5000
                    cp_like_rate = 5000
    
                def per_unit_rate(lead):
                    lead = str(lead).strip().title()
                    if lead == 'Direct':
                        return direct_rate
                    if lead in {'Cp', 'CP', 'Referral', 'Digital', 'Hoarding'}:
                        return cp_like_rate
                    return 0
    
                exec_df['Per Unit Rate Applied'] = exec_df['Lead'].map(per_unit_rate)
    
                # ---------- Payout % ----------
                # FORCE wing-wise logic directly; no quarter-based fallback for C/E/F
                def wing_payout(row):
                    if row['PodiumFlag']:
                        return podium_payout_percent_from_rate(avg_rate_POD)
    
                    w = str(row['WingNorm']).strip().upper()
    
                    if w in {'E', 'F'}:
                        return ef_wing_payout_percent_from_rate(avg_rate_EF)
    
                    if w == 'C':
                        return c_wing_payout_percent_from_rate(avg_rate_C)
    
                    return old_global_payout_percent_from_rate(avg_rate)
    
                exec_df['Payout % Applied'] = exec_df.apply(wing_payout, axis=1)
                pod_pct = podium_payout_percent_from_rate(avg_rate_POD)
    
                # ---------- Per-unit incentive ----------
                exec_df['Per Unit Incentive'] = exec_df['Per Unit Rate Applied'] * exec_df['Payout % Applied']
                base_incentive_all = float(exec_df['Per Unit Incentive'].sum())
    
                # ---------- IDs & flags ----------
                wing_col = 'Wing' if 'Wing' in exec_df.columns else None
                flatno_col = 'Flat Number' if 'Flat Number' in exec_df.columns else ('Flat' if 'Flat' in exec_df.columns else None)
    
                if wing_col or flatno_col:
                    left = exec_df[wing_col].astype(str).str.strip() if wing_col else ""
                    right = exec_df[flatno_col].apply(_fmt_flat_number) if flatno_col else ""
                    exec_df['Flat ID'] = (left + (" " if wing_col and flatno_col else "") + right).astype(str).str.strip()
                    exec_df['Flat ID'] = exec_df['Flat ID'].replace({"nan": "", "None": ""}, regex=True).str.strip()
                else:
                    exec_df['Flat ID'] = ""
    
                exec_df['Is Given'] = (
                    exec_df['Incentive'].astype(str).str.contains('given', case=False, na=False)
                    if 'Incentive' in exec_df.columns else False
                )
                exec_df['Agreement Done Flag'] = (
                    exec_df['Agreement Done'].astype(str).str.strip().str.lower().eq('done')
                    if 'Agreement Done' in exec_df.columns else False
                )
    
                # ---------- Applicable ----------
                applicable_mask = exec_df['Agreement Done Flag']
                applicable_df = exec_df[applicable_mask].copy()
                applicable_count = len(applicable_df)
                applicable_flats = [f for f in applicable_df['Flat ID'].fillna("").tolist() if f]
                applicable_incentive_base = float(applicable_df['Per Unit Incentive'].sum())
    
                # ---------- ON-SCREEN BONUSES (BOOKINGS basis) ----------
                top_seller_amount_screen = unit_count * 1000 if unit_count >= 20 else 0
    
                q_df = df[df['Quarter'] == active_quarter].copy()
                team_units_screen = len(q_df)
                elig_counts_screen = q_df.groupby('Sales Executive').size() if not q_df.empty else pd.Series(dtype=int)
                elig_names_screen = elig_counts_screen[elig_counts_screen >= 12].index.tolist()
    
                team_bonus_amount_screen = 0
                if team_units_screen >= 60 and len(elig_names_screen) > 0 and active_exec in elig_names_screen:
                    team_bonus_amount_screen = 50000 / len(elig_names_screen)
    
                cond_ef_screen = (ef_units == 0) or (pd.notna(avg_rate_EF) and avg_rate_EF >= 6000)
                cond_c_screen  = (c_units == 0) or (pd.notna(avg_rate_C) and avg_rate_C >= 6000)
                high_rate_amount_screen = 100000 if (efc_units_no_podium >= 18 and cond_ef_screen and cond_c_screen) else 0
    
                bonus_total_screen = int(round(top_seller_amount_screen + team_bonus_amount_screen + high_rate_amount_screen))
    
                # ---------- Stamp Duty ----------
                if 'Stamp Duty' in exec_df.columns:
                    sd_norm = exec_df['Stamp Duty'].astype(str).str.strip().str.lower()
                    stamp_duty_mask = sd_norm.str.contains('receiv') | sd_norm.isin(['yes', 'y', 'received', 'recieved', 'done'])
                else:
                    stamp_duty_mask = pd.Series(False, index=exec_df.index)
    
                stamp_duty_count = int(stamp_duty_mask.sum())
                stamp_duty_incentive = float(exec_df.loc[stamp_duty_mask, 'Per Unit Incentive'].sum())
    
                # ---------- KPI CARDS ----------
                applicable_ratio_pct = 0 if unit_count == 0 else int((applicable_count / unit_count) * 100)
    
                # IMPORTANT: slab labels also forced directly from wing avg PSF
                ef_pct = ef_wing_payout_percent_from_rate(avg_rate_EF)
                c_pct  = c_wing_payout_percent_from_rate(avg_rate_C)
                pod_pct = podium_payout_percent_from_rate(avg_rate_POD)
    
                ef_label = _pct_label(ef_pct)
                c_label  = _pct_label(c_pct)
                pod_label = _pct_label(pod_pct)
    
                ef_bar = max(0, min(int(ef_pct * 100), 100))
                c_bar  = max(0, min(int(c_pct * 100), 100))
                pod_bar = max(0, min(int(pod_pct * 100), 100))
    
                # Row 1: E+F
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1:
                    st.markdown(f"""
                    <div class="kpi"><h6>E+F Total Bookings</h6>
                      <p>{ef_units}</p>
                      <div class="bar"><span style="width:{min(ef_units,20)/20*100}%"></span></div>
                    </div>""", unsafe_allow_html=True)
                with r1c2:
                    st.markdown(f"""
                    <div class="kpi blue"><h6>E+F Avg PSF</h6>
                      <p>₹ {0 if pd.isna(avg_rate_EF) else round(avg_rate_EF,2):,}</p>
                      <div class="bar"><span style="width:{min(max(((0 if pd.isna(avg_rate_EF) else avg_rate_EF)-5400)/8,0),100)}%"></span></div>
                    </div>""", unsafe_allow_html=True)
                with r1c3:
                    st.markdown(f"""
                    <div class="kpi amb"><h6>E+F Payout Slab</h6>
                      <p>{ef_label}</p>
                      <div class="bar"><span style="width:{ef_bar}%"></span></div>
                    </div>""", unsafe_allow_html=True)
    
                # Row 2: C
                r2c1, r2c2, r2c3 = st.columns(3)
                with r2c1:
                    st.markdown(f"""
                    <div class="kpi"><h6>C Total Bookings</h6>
                      <p>{c_units}</p>
                      <div class="bar"><span style="width:{min(c_units,20)/20*100}%"></span></div>
                    </div>""", unsafe_allow_html=True)
                with r2c2:
                    st.markdown(f"""
                    <div class="kpi blue"><h6>C Avg PSF</h6>
                      <p>₹ {0 if pd.isna(avg_rate_C) else round(avg_rate_C,2):,}</p>
                      <div class="bar"><span style="width:{min(max(((0 if pd.isna(avg_rate_C) else avg_rate_C)-5400)/8,0),100)}%"></span></div>
                    </div>""", unsafe_allow_html=True)
                with r2c3:
                    st.markdown(f"""
                    <div class="kpi amb"><h6>C Payout Slab</h6>
                      <p>{c_label}</p>
                      <div class="bar"><span style="width:{c_bar}%"></span></div>
                    </div>""", unsafe_allow_html=True)
    
                # Row 3: Podium
                r3c1, r3c2, r3c3 = st.columns(3)
                with r3c1:
                    st.markdown(f"""
                    <div class="kpi"><h6>Podium Units Total Bookings</h6>
                      <p>{pod_units}</p>
                      <div class="bar"><span style="width:{min(pod_units,20)/20*100}%"></span></div>
                    </div>""", unsafe_allow_html=True)
                with r3c2:
                    st.markdown(f"""
                    <div class="kpi blue"><h6>Podium Units Avg PSF</h6>
                      <p>₹ {0 if pd.isna(avg_rate_POD) else round(avg_rate_POD,2):,}</p>
                      <div class="bar"><span style="width:{min(max(((0 if pd.isna(avg_rate_POD) else avg_rate_POD)-5400)/8,0),100)}%"></span></div>
                    </div>""", unsafe_allow_html=True)
                with r3c3:
                    st.markdown(f"""
                    <div class="kpi amb"><h6>Podium Units Payout Slab</h6>
                      <p>{pod_label}</p>
                      <div class="bar"><span style="width:{pod_bar}%"></span></div>
                    </div>""", unsafe_allow_html=True)
    
                # Row 4: Totals
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
    
                # Row 5: Overall / Stamp Duty
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
    
                # ---------- SUMMARY TABLE ----------
                def _fmt_rate(r):
                    return "—" if pd.isna(r) else f"₹{round(r,2):,}"
    
                flats_E = [f for f in exec_df.loc[mask_E, 'Flat ID'].fillna("").tolist() if f]
                flats_F = [f for f in exec_df.loc[mask_F, 'Flat ID'].fillna("").tolist() if f]
                flats_C = [f for f in exec_df.loc[mask_C, 'Flat ID'].fillna("").tolist() if f]
                flats_POD = [f for f in exec_df.loc[mask_POD, 'Flat ID'].fillna("").tolist() if f]
    
                mask_other = ~(mask_EFC | mask_POD)
                other_units = int(mask_other.sum())
                flats_other = [f for f in exec_df.loc[mask_other, 'Flat ID'].fillna("").tolist() if f]
    
                base_incentive_E = int(exec_df.loc[mask_E, 'Per Unit Incentive'].sum())
                base_incentive_F = int(exec_df.loc[mask_F, 'Per Unit Incentive'].sum())
                base_incentive_C = int(exec_df.loc[mask_C, 'Per Unit Incentive'].sum())
                base_incentive_POD = int(exec_df.loc[mask_POD, 'Per Unit Incentive'].sum())
                base_incentive_other = int(exec_df.loc[mask_other, 'Per Unit Incentive'].sum())
    
                released_amount_base_all = int(exec_df.loc[exec_df['Is Given'], 'Per Unit Incentive'].sum())
    
                summary_rows = [
                    ("Total Flats (Bookings)", "—", "—", unit_count),
                    ("Applicable Flats (Agreement Done)", "—", "—", f"{applicable_count}"),
                    ("Applicable Flats — Flat Numbers", "—", "—", applicable_flats),
    
                    ("E Wing (non-Podium)", _fmt_rate(avg_rate_E), f"{int((exec_df.loc[mask_E, 'Payout % Applied'].mean() if mask_E.any() else 0)*100)}%", flats_E),
                    ("F Wing (non-Podium)", _fmt_rate(avg_rate_F), f"{int((exec_df.loc[mask_F, 'Payout % Applied'].mean() if mask_F.any() else 0)*100)}%", flats_F),
                    ("C Wing (non-Podium)", _fmt_rate(avg_rate_C), f"{int((exec_df.loc[mask_C, 'Payout % Applied'].mean() if mask_C.any() else 0)*100)}%", flats_C),
                    ("Podium Units", _fmt_rate(avg_rate_POD), f"{int((pod_pct if not pd.isna(pod_pct) else 0)*100)}%", flats_POD),
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
                        chips = ''.join(f'<span class="chip">{f}</span>' for f in amt) or '—'
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
                from fpdf import FPDF
                import base64
    
                # --- Applicable-only aggregates for bonuses in PDF ---
                is_given_mask = exec_df['Is Given'].astype(bool)
                given_flats_list = [f for f in exec_df.loc[applicable_mask & is_given_mask, 'Flat ID'].fillna("").tolist() if f]
                balance_flats_list = [f for f in exec_df.loc[applicable_mask & (~is_given_mask), 'Flat ID'].fillna("").tolist() if f]
    
                total_app_amt = float(exec_df.loc[applicable_mask, 'Per Unit Incentive'].sum())
                given_app_amt = float(exec_df.loc[applicable_mask & is_given_mask, 'Per Unit Incentive'].sum())
                balance_app_amt = float(exec_df.loc[applicable_mask & (~is_given_mask), 'Per Unit Incentive'].sum())
    
                def _avg(col, mask):
                    if col not in exec_df.columns:
                        return 0.0
                    s = exec_df.loc[mask, col]
                    if s.empty:
                        return 0.0
                    return float(np.nanmean(pd.to_numeric(s, errors='coerce')))
    
                avg_payout_total = _avg('Payout % Applied', applicable_mask)
                avg_amt_per_flat = _avg('Per Unit Incentive', applicable_mask)
                avg_payout_given = _avg('Payout % Applied', applicable_mask & is_given_mask)
                avg_amt_per_given = _avg('Per Unit Incentive', applicable_mask & is_given_mask)
                avg_payout_balance = _avg('Payout % Applied', applicable_mask & (~is_given_mask))
                avg_amt_per_balance = _avg('Per Unit Incentive', applicable_mask & (~is_given_mask))
    
                count_all = int(len(exec_df))
                count_non_app = int((~applicable_mask).sum())
                count_app = int(applicable_mask.sum())
                count_given = int((applicable_mask & is_given_mask).sum())
                count_balance = int((applicable_mask & (~is_given_mask)).sum())
    
                # ---- Bonuses for PDF (APPLICABLE basis) ----
                app_mask_non_pod = applicable_mask & (~exec_df['PodiumFlag'])
                e_app_units = int((exec_df['WingNorm'].eq('E') & app_mask_non_pod).sum())
                f_app_units = int((exec_df['WingNorm'].eq('F') & app_mask_non_pod).sum())
                c_app_units = int((exec_df['WingNorm'].eq('C') & app_mask_non_pod).sum())
                efc_app_units = e_app_units + f_app_units + c_app_units
    
                def _avg_rate_app(mask_bool):
                    sub = exec_df[mask_bool]
                    if sub.empty or ('Agreement Cost' not in sub.columns) or ('Carpet Area' not in sub.columns):
                        return np.nan
                    ac_sum = sub['Agreement Cost'].apply(_to_num).sum(min_count=1)
                    ca_sum = sub['Carpet Area'].apply(_to_num).sum(min_count=1)
                    denom = (ca_sum * 1.38) if pd.notna(ca_sum) else np.nan
                    return (ac_sum / denom) if (pd.notna(ac_sum) and pd.notna(denom) and denom > 0) else np.nan
    
                avg_rate_EF_app = _avg_rate_app(exec_df['WingNorm'].isin(['E', 'F']) & app_mask_non_pod)
                avg_rate_C_app = _avg_rate_app(exec_df['WingNorm'].eq('C') & app_mask_non_pod)
    
                top_seller_amount_pdf = count_app * 1000 if count_app >= 20 else 0
    
                q_df_app = df[df['Quarter'] == active_quarter].copy()
                q_df_app['AgDone'] = q_df_app['Agreement Done'].astype(str).str.strip().str.lower().eq('done')
                team_units_app = int(q_df_app['AgDone'].sum())
                elig_counts_app = q_df_app[q_df_app['AgDone']].groupby('Sales Executive').size() if not q_df_app[q_df_app['AgDone']].empty else pd.Series(dtype=int)
                elig_names_app = elig_counts_app[elig_counts_app >= 0].index.tolist()
    
                team_bonus_amount_pdf = 0
                if team_units_app >= 60 and len(elig_names_app) > 0 and active_exec in elig_names_app:
                    team_bonus_amount_pdf = 50000 / len(elig_names_app)
    
                cond_ef_pdf = (e_app_units + f_app_units == 0) or (pd.notna(avg_rate_EF_app) and avg_rate_EF_app >= 6000)
                cond_c_pdf  = (c_app_units == 0) or (pd.notna(avg_rate_C_app) and avg_rate_C_app >= 6000)
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
    
                # ---------------- PDF helpers ----------------
                def ascii_only(s: str) -> str:
                    return str(s).replace("₹", "Rs ").replace("—", "-").replace("–", "-")
    
                def fmt_money(v):
                    try:
                        return f"Rs {int(round(float(v))):,}"
                    except:
                        return "Rs 0"
    
                def fmt_pct(p):
                    try:
                        return f"{int(round(float(p) * 100))}%"
                    except:
                        return "0%"
    
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.set_margins(10, 10, 10)
                pdf.set_auto_page_break(auto=True, margin=12)
                pdf.add_page()
    
                page_w = pdf.w - pdf.l_margin - pdf.r_margin
                page_h = pdf.h
                b_margin = getattr(pdf, 'b_margin', 12)
    
                def ensure_space(h):
                    if pdf.get_y() + h > (page_h - b_margin):
                        pdf.add_page()
    
                def section_title(txt, size=12, top=2, bottom=1):
                    ensure_space(10)
                    pdf.ln(top)
                    pdf.set_font("Arial", 'B', size)
                    pdf.cell(0, 8, ascii_only(txt), ln=True, align='C')
                    pdf.ln(bottom)
    
                def wrap_by_spaces(text, inner_w, font=("Arial", "", 9)):
                    pdf.set_font(font[0], font[1], font[2])
                    s = ascii_only(str(text)) or "-"
                    words = s.split()
                    lines, cur = [], ""
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
                    lines, cur = [], ""
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
                    pdf.set_font("Arial", 'B', size)
                    for h, w in zip(headers, widths):
                        pdf.cell(w, 7.2, ascii_only(h), border=1, align='C')
                    pdf.ln()
    
                def table_row_exact(values, widths, aligns, size=9, lh=5.8, hpad=1.8, vpad=2.0, comma_cols=None):
                    comma_cols = set(comma_cols or {})
                    pdf.set_font("Arial", '', size)
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
                    for idx, (cell_lines, w, iw, alg) in enumerate(zip(wrapped, widths, inner_ws, aligns)):
                        ix = cx + hpad
                        iy = y0 + vpad
                        for line_idx, line in enumerate(cell_lines):
                            pdf.set_xy(ix, iy + line_idx * lh)
                            pdf.cell(iw, lh, ascii_only(line), border=0, ln=0, align=alg)
                        cx += w
    
                    pdf.set_xy(pdf.l_margin, y0 + row_h + 0.6)
    
                # ---------- Title ----------
                pdf.set_font("Arial", 'B', 13)
                pdf.cell(0, 9, ascii_only(f"Incentive Invoice - {active_exec} ({active_quarter})"), ln=True, align='C')
                pdf.ln(2)
    
                # ---------- Overview ----------
                all_flats = [f for f in exec_df['Flat ID'].fillna("").tolist() if f]
                non_app_flats = [f for f in exec_df.loc[~applicable_mask, 'Flat ID'].fillna("").tolist() if f]
                app_flats = [f for f in exec_df.loc[applicable_mask, 'Flat ID'].fillna("").tolist() if f]
    
                ov_w_cat, ov_w_count, ov_w_vals = page_w * 0.28, page_w * 0.12, page_w * 0.60
                ov_widths, ov_aligns = [ov_w_cat, ov_w_count, ov_w_vals], ['L', 'C', 'L']
                table_header(["Category", "Count", "Flat Numbers"], ov_widths)
                table_row_exact(["TOTAL FLATS", count_all, ", ".join(all_flats) if all_flats else "-"], ov_widths, ov_aligns, size=9, comma_cols=[2])
                table_row_exact(["AGREEMENT NOT DONE (NON-APPLICABLE)", count_non_app, ", ".join(non_app_flats) if non_app_flats else "-"], ov_widths, ov_aligns, size=9, comma_cols=[2])
                table_row_exact(["AGREEMENT DONE (APPLICABLE)", count_app, ", ".join(app_flats) if app_flats else "-"], ov_widths, ov_aligns, size=9, comma_cols=[2])
    
                # ---------- Incentive Summary ----------
                section_title("Incentive Summary")
                sum_w_cat, sum_w_cnt, sum_w_pct, sum_w_each, sum_w_amt = page_w * 0.32, page_w * 0.12, page_w * 0.16, page_w * 0.18, page_w * 0.22
                sum_widths, sum_aligns = [sum_w_cat, sum_w_cnt, sum_w_pct, sum_w_each, sum_w_amt], ['L', 'C', 'C', 'R', 'R']
                table_header(["Category", "Flat Count", "Payout % (Avg)", "Amount / Flat (Avg)", "Total Amount"], sum_widths)
                table_row_exact(["TOTAL INCENTIVE (Applicable Base)", count_app, fmt_pct(avg_payout_total), fmt_money(avg_amt_per_flat), fmt_money(total_app_amt)], sum_widths, sum_aligns, size=10)
                table_row_exact(["INCENTIVE GIVEN", count_given, fmt_pct(avg_payout_given), fmt_money(avg_amt_per_given), fmt_money(given_app_amt)], sum_widths, sum_aligns, size=10)
                table_row_exact(["INCENTIVE BALANCE", count_balance, fmt_pct(avg_payout_balance), fmt_money(avg_amt_per_balance), fmt_money(balance_app_amt)], sum_widths, sum_aligns, size=10)
    
                table_row_exact(["TOP SELLER BONUS (Applicable units)", "—", "—", "—", fmt_money(top_seller_amount_pdf)], sum_widths, sum_aligns, size=10)
                table_row_exact(["TEAM BONUS (your share; Applicable basis)", "—", "—", "—", fmt_money(team_bonus_amount_pdf)], sum_widths, sum_aligns, size=10)
                table_row_exact(["HIGH RATE BONUS (Applicable basis)", "—", "—", "—", fmt_money(high_rate_amount_pdf)], sum_widths, sum_aligns, size=10)
                table_row_exact(["BONUS TOTAL", "—", "—", "—", fmt_money(bonus_total_pdf)], sum_widths, sum_aligns, size=10)
    
                # ---------- Grouped Ledger ----------
                section_title("Applicable Flats — Grouped Ledger")
                led_w_status, led_w_count, led_w_flats, led_w_amt = page_w * 0.20, page_w * 0.12, page_w * 0.46, page_w * 0.22
                led_widths, led_aligns = [led_w_status, led_w_count, led_w_flats, led_w_amt], ['C', 'C', 'L', 'R']
                table_header(["Remark", "Flats", "Flat Numbers / Notes", "Amount"], led_widths)
                table_row_exact(["Given", str(count_given), ", ".join(given_flats_list) if given_flats_list else "-", fmt_money(given_app_amt)], led_widths, led_aligns, size=9, comma_cols=[2])
                table_row_exact(["Balance Amount", str(count_balance), ", ".join(balance_flats_list) if balance_flats_list else "-", fmt_money(balance_amount_with_bonus_pdf)], led_widths, led_aligns, size=9, comma_cols=[2])
    
                # ---------- Signatures ----------
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
                pdf.cell(block_w, 7, ascii_only("Developer Signature"), ln=False, align='L')
    
                pdf.set_xy(x_right, y_sig + 4)
                pdf.set_font("Arial", size=10)
                pdf.cell(block_w, 7, ascii_only(f"{active_exec} Signature"), ln=False, align='R')
    
                pdf.set_xy(pdf.l_margin, y_sig + sig_h)
                pdf.set_auto_page_break(auto=orig_apb_state, margin=orig_bmargin)
    
                # ---------- Download ----------
                pdf_bytes = pdf.output(dest="S").encode("latin1", "ignore")
                b64 = base64.b64encode(pdf_bytes).decode()
                st.markdown(
                    f'<a href="data:application/octet-stream;base64,{b64}" download="incentive_invoice.pdf" '
                    f'style="display:inline-block;margin-top:10px;padding:10px 14px;border-radius:10px;'
                    f'background:linear-gradient(135deg,#06b6d4 0%,#6366f1 100%);color:#fff;text-decoration:none;'
                    f'font-weight:800">⬇️ Download Incentive Invoice (PDF)</a>',
                    unsafe_allow_html=True
                )
    with ST_INCENTIVE_STATUS:
        st.header("📊 Incentive Status")
    
        import re
        import numpy as np
        import pandas as _pd
    
        # ================= Quarter helpers =================
        MONTHS = {
            'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,
            'apr':4,'april':4,'may':5,'jun':6,'june':6,
            'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,
            'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12
        }
    
        def _parse_yq(qtxt):
            s = str(qtxt).strip().lower()
    
            # Handles "Q1 2025", "q2-2026", etc.
            m = re.search(r'\bq\s*(\d)\b.*?(\d{4})', s)
            if m:
                return (int(m.group(2)), int(m.group(1)))
    
            # Handles "April-June 2025", "July-September 2025", etc.
            my = re.search(r'(\d{4})', s)
            if my:
                y = int(my.group(1))
                m1 = re.search(
                    r'(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|'
                    r'january|february|march|april|june|july|august|september|october|november|december)',
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
    
        quarters = sorted(list(df['Quarter'].dropna().unique()), key=_quarter_sort_key)
    
        # ============ Quarter-specific rules ============
        # IMPORTANT: Your sheet has:
        #   Apr–Jun 2025  -> calendar 2025-Q2  (your "Q1")
        #   Jul–Sep 2025  -> calendar 2025-Q3  (your "Q2")
        #   Oct–Dec 2025  -> calendar 2025-Q4  (your "Q3")
        #   Jan–Mar 2026  -> calendar 2026-Q1
        #
        # Payout slabs are 100% / 70% / 40% (NOT 30%).
        QUARTER_RULES = {
            # Apr–Jun 2025 (your Q1): fixed per booking by exec
            "2025-Q2": {
                "mode": "FIXED_PER_EXEC",
                "fixed_rates": {"Harshal S": 5000, "Tejas P": 3500, "Alok R": 4000}
            },
    
            # Jul–Sep 2025 (your Q2): GLOBAL slabs 5800/5700/5600 with 100/70/40
            "2025-Q3": {
                "mode": "GLOBAL",
                "global_t": {"t100": 5800, "t70": 5700, "t40": 5600}
            },
    
            # Oct–Dec 2025 (your Q3): WING-WISE slabs (E+F combined, C separate), 100/70/40
            "2025-Q4": {
                "mode": "WING_WISE",
                "ef_t": {"t100": 5950, "t70": 5900, "t40": 5850},
                "c_t":  {"t100": 6325, "t70": 6300, "t40": 6275}
            },
    
            # Jan–Mar 2026: WING-WISE with updated EF thresholds, 100/70/40
            "2026-Q1": {
                "mode": "WING_WISE",
                "ef_t": {"t100": 6000, "t70": 5950, "t40": 5900},
                "c_t":  {"t100": 6325, "t70": 6300, "t40": 6275}
            },
        }
    
        DEFAULT_RULE_KEY = "2026-Q1"
    
        # From Apr–Jun 2026 (calendar 2026-Q2) onwards → staged payout policy applies
        CUTOFF_YEAR, CUTOFF_Q = 2026, 2
        def use_three_term_for(qtxt):
            y, q = _parse_yq(qtxt)
            return (y, q) >= (CUTOFF_YEAR, CUTOFF_Q)
    
        # ============ Normalize base data ============
        data = df.copy()
    
        if 'Quarter' in data.columns:
            data['Quarter'] = data['Quarter'].astype(str).str.strip()
    
        data['Sales Executive'] = data['Sales Executive'].astype(str).str.strip()
        data['Lead'] = data['Lead Type'].astype(str).str.strip().str.title() if 'Lead Type' in data.columns else ""
    
        # Exclude Advait M
        executives = sorted(
            [
                str(e).strip()
                for e in data["Sales Executive"].dropna().unique()
                if str(e).strip() != "" and str(e).strip().upper() != "NAN" and str(e).strip() != "Advait M"
            ]
        )
    
        # Wing + Podium detection
        data['WingNorm'] = data['Wing'].astype(str).str.strip().str.upper() if 'Wing' in data.columns else ""
    
        if 'Floor' in data.columns:
            floor_norm = data['Floor'].astype(str).str.strip().str.lower()
            data['PodiumFlag'] = (
                floor_norm.eq('1') | floor_norm.eq('1.0') |
                floor_norm.str.contains(r'\b1st\b|\bfirst\b|podium|garden', case=False, na=False)
            )
        else:
            data['PodiumFlag'] = False
    
        # Stage flags
        data['Agreement Done Flag'] = (
            data['Agreement Done'].astype(str).str.strip().str.lower().eq('done')
            if 'Agreement Done' in data.columns else False
        )
    
        if 'RCC' in data.columns:
            rcc_s = data['RCC'].astype(str).str.strip().str.lower()
            data['RCC Flag'] = rcc_s.str.contains('complet', na=False)  # "COMPLETED"
        else:
            data['RCC Flag'] = False
    
        if 'POSSESSION HANDOVER' in data.columns:
            pos_s = data['POSSESSION HANDOVER'].astype(str).str.strip().str.lower()
            data['Possession Flag'] = pos_s.str.contains('handover', na=False)  # "HANDOVER"
        else:
            data['Possession Flag'] = False
    
        data['Is Given'] = (
            data['Incentive'].astype(str).str.contains('given', case=False, na=False)
            if 'Incentive' in data.columns else False
        )
    
        # Stamp Duty
        def stamp_duty_mask(df_local):
            if 'Stamp Duty' not in df_local.columns:
                return _pd.Series(False, index=df_local.index)
            s = df_local['Stamp Duty'].astype(str).str.strip().str.lower()
            return s.str.contains('receiv', na=False) | s.isin(['yes','y','received','recieved','done'])
    
        # Numeric helpers
        def _to_num(x):
            if _pd.isna(x):
                return np.nan
            s = str(x).replace('₹', '').replace('Rs', '').replace('rs', '').replace(',', '').strip()
            try:
                return float(s)
            except:
                return np.nan
    
        def avg_rate_subset(df_local):
            # Avg PSF = (Σ Agreement Cost) / (Σ Carpet Area * 1.38)
            if df_local.empty or ('Agreement Cost' not in df_local.columns) or ('Carpet Area' not in df_local.columns):
                return np.nan
            ac_sum = df_local['Agreement Cost'].apply(_to_num).sum(min_count=1)
            ca_sum = df_local['Carpet Area'].apply(_to_num).sum(min_count=1)
            denom = (ca_sum * 1.38) if _pd.notna(ca_sum) else np.nan
            return (ac_sum / denom) if (_pd.notna(ac_sum) and _pd.notna(denom) and denom > 0) else np.nan
    
        # Base per-unit rate rule (except FIXED_PER_EXEC quarter)
        def per_unit_rate_from_count(qdf_len: int):
            # same as Incentive Calculator: >=18 bookings => 6000 else 5000
            return (6000, 6000) if qdf_len >= 18 else (5000, 5000)
    
        def unit_rate_map(lead, dr, cr):
            lead = str(lead).strip().title()
            if lead == 'Direct':
                return dr
            if lead in {'Cp', 'CP', 'Referral', 'Digital', 'Hoarding'}:
                return cr
            return 0
    
        # ============ Quarter-aware payout engine ============
        def get_rule_for_quarter(qtxt):
            key = _canonical_quarter(qtxt)
            return QUARTER_RULES.get(key, QUARTER_RULES[DEFAULT_RULE_KEY])
    
        def _pct_from_thresholds(rate_value, tdict):
            """
            tdict keys: t100, t70, t40
            """
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
            mask_np = ~q_df['PodiumFlag']     # non-podium
            mask_p  = q_df['PodiumFlag']      # podium
    
            mE  = q_df['WingNorm'].eq('E') & mask_np
            mF  = q_df['WingNorm'].eq('F') & mask_np
            mC  = q_df['WingNorm'].eq('C') & mask_np
            mEF = mE | mF
    
            rule = get_rule_for_quarter(q)
    
            # ---------- Mode 1: FIXED PER EXEC (Apr–Jun 2025 in your sheet) ----------
            if rule["mode"] == "FIXED_PER_EXEC":
                fixed = rule.get("fixed_rates", {})
                flat_rate = float(fixed.get(exec_name, 0))
                q_df['Per Unit Rate Applied'] = flat_rate
                q_df['Payout % Applied'] = 1.0
    
                # DO NOT apply podium override here (this quarter was fixed scheme)
                q_df['Per Unit Incentive'] = q_df['Per Unit Rate Applied'] * q_df['Payout % Applied']
                return q_df
    
            # ---------- Mode 2/3: PSF slabs ----------
            # Per-unit rate based on this exec's booking count (same as incentive calculator)
            dr, cr = per_unit_rate_from_count(len(q_df))
            q_df['Per Unit Rate Applied'] = q_df['Lead'].map(lambda L: unit_rate_map(L, dr, cr))
    
            # Averages (non-podium only for wing/global slabs)
            avg_all_np = avg_rate_subset(q_df[mask_np])
            avgEF = avg_rate_subset(q_df[mEF]) if mEF.any() else np.nan
            avgC  = avg_rate_subset(q_df[mC])  if mC.any()  else np.nan
    
            # Global fallback thresholds (used in GLOBAL mode and for "Other Wings" fallback)
            GLOBAL_FALLBACK = {"t100": 5800, "t70": 5700, "t40": 5600}
    
            if rule["mode"] == "GLOBAL":
                t = rule["global_t"]
                base_pct = _pct_from_thresholds(avg_all_np, t)
                q_df['Payout % Applied'] = base_pct
    
            elif rule["mode"] == "WING_WISE":
                tef, tc = rule["ef_t"], rule["c_t"]
    
                def wing_pct_row(row):
                    # We'll override podium later
                    if row['PodiumFlag']:
                        return 0.0
    
                    w = row['WingNorm']
                    if w in {'E', 'F'}:
                        return _pct_from_thresholds(avgEF, tef)
                    if w == 'C':
                        return _pct_from_thresholds(avgC, tc)
    
                    # Other wings => global fallback on non-podium average
                    return _pct_from_thresholds(avg_all_np, GLOBAL_FALLBACK)
    
                q_df['Payout % Applied'] = q_df.apply(wing_pct_row, axis=1)
    
            else:
                # safety fallback
                q_df['Payout % Applied'] = _pct_from_thresholds(avg_all_np, GLOBAL_FALLBACK)
    
            # ---------- Podium override (by PODIUM AVG PSF, like Incentive Calculator) ----------
            # Rule: >=6000 => 100%, 5800–5999 => 70%, else 0%
            if mask_p.any():
                avg_pod = avg_rate_subset(q_df[mask_p])
                if _pd.isna(avg_pod):
                    pod_pct = 0.0
                elif avg_pod >= 5800:
                    pod_pct = 1.0
                elif 5700 <= avg_pod < 5799:
                    pod_pct = 0.7
                else:
                    pod_pct = 0.0
                q_df.loc[mask_p, 'Payout % Applied'] = pod_pct
    
            # Final per-flat incentive (includes slab %)
            q_df['Per Unit Incentive'] = q_df['Per Unit Rate Applied'] * q_df['Payout % Applied']
            return q_df
    
        # Split (from 2026-Q2): RCC=1000, POS=1000, AG=remainder (bonuses never split)
        def split_fixed_1000(amount):
            A = 0.0 if _pd.isna(amount) else float(amount)
            if A <= 0:
                return (0.0, 0.0, 0.0)
            rcc = min(1000.0, A)
            rem = A - rcc
            pos = min(1000.0, rem)
            ag  = max(A - rcc - pos, 0.0)
            return (ag, rcc, pos)
    
        # Bonuses (Applicable basis; non-podium for EF/C PSF checks; 6000 thresholds; 18+ combined)
        def bonuses_applicable(q_df_all, q, exec_name):
            q_app = q_df_all[q_df_all['Agreement Done Flag']].copy()
            q_app_np = q_app[~q_app['PodiumFlag']]
    
            e_cnt = int((q_app_np['WingNorm'] == 'E').sum())
            f_cnt = int((q_app_np['WingNorm'] == 'F').sum())
            c_cnt = int((q_app_np['WingNorm'] == 'C').sum())
            efc_cnt = e_cnt + f_cnt + c_cnt
    
            avgEF = avg_rate_subset(q_app_np[q_app_np['WingNorm'].isin(['E', 'F'])])
            avgC  = avg_rate_subset(q_app_np[q_app_np['WingNorm'] == 'C'])
    
            # Top seller: 20+ applicable units => 1000 per unit
            top_seller = (len(q_app) * 1000) if len(q_app) >= 20 else 0
    
            # Team bonus: if team applicable units in the quarter >= 60, share 50k among execs with 12+ applicable
            all_q = data[data['Quarter'] == q].copy()
            all_q['Agreement Done Flag'] = (
                all_q['Agreement Done'].astype(str).str.strip().str.lower().eq('done')
                if 'Agreement Done' in all_q.columns else False
            )
            team_units_app = int(all_q['Agreement Done Flag'].sum())
            elig_counts = (
                all_q[all_q['Agreement Done Flag']].groupby('Sales Executive').size()
                if not all_q[all_q['Agreement Done Flag']].empty else _pd.Series(dtype=int)
            )
            elig_names = elig_counts[elig_counts >= 1].index.tolist()
            team_share = (50000 / len(elig_names)) if (team_units_app >= 60 and len(elig_names) > 0 and exec_name in elig_names) else 0
    
            # High rate bonus: 18+ applicable (non-podium) E/F/C, EF avg >=6000, C avg >=6000
            high_rate = 100000 if (
                efc_cnt >= 18 and
                ((e_cnt + f_cnt == 0) or (_pd.notna(avgEF) and avgEF >= 6000)) and
                ((c_cnt == 0)         or (_pd.notna(avgC)  and avgC  >= 6000))
            ) else 0
    
            return int(round(top_seller + team_share + high_rate))
    
        def fmt_inr(x):
            try:
                return f"₹ {int(round(float(x))):,}"
            except:
                return "₹ 0"
    
        # ================= Build per-executive sections =================
        overall_rows = []       # Overall Total Balance (Agreement basis)
        overall_paid_rows = []  # Overall Total Paid to Date (Agreement basis)
    
        for exec_name in executives:
            st.subheader(f"👤 {exec_name}")
    
            # -------- Agreement Done basis --------
            rows_ag = []
    
            for q in quarters:
                q_df = data[(data['Quarter'] == q) & (data['Sales Executive'] == exec_name)].copy()
    
                if q_df.empty:
                    rows_ag.append({
                        "Quarter": q,
                        "AG": "₹ 0", "RCC": "₹ 0", "POS": "₹ 0",
                        "AG Paid": "₹ 0", "RCC Paid": "₹ 0", "POS Paid": "₹ 0",
                        "Total Paid": "₹ 0", "Bonus": "₹ 0", "Balance": "₹ 0"
                    })
                    continue
    
                # Apply correct quarter logic => this is where your 70%/40% payouts get applied
                q_df = apply_payouts_for_exec_quarter(q_df, q, exec_name)
    
                ag_mask  = q_df['Agreement Done Flag']
                rcc_mask = ag_mask & q_df['RCC Flag']
                pos_mask = ag_mask & q_df['Possession Flag']
    
                # Due (base) — Per Unit Incentive already includes slab payout (100/70/40)
                base_series = (q_df['Per Unit Incentive'] * ag_mask).fillna(0.0).astype(float)
    
                # Term-wise due
                if use_three_term_for(q):
                    splits = base_series.apply(split_fixed_1000)
                    t1 = splits.apply(lambda t: t[0])
                    t2 = splits.apply(lambda t: t[1])
                    t3 = splits.apply(lambda t: t[2])
                    ag_due  = float(t1.loc[ag_mask].sum())
                    rcc_due = float(t2.loc[rcc_mask].sum())
                    pos_due = float(t3.loc[pos_mask].sum())
                else:
                    ag_due, rcc_due, pos_due = float(base_series.sum()), 0.0, 0.0
    
                # Paid per-quarter policy:
                # legacy (till 2026-Q1): "Given" means full base incentive for those Agreement Done units
                # staged (2026-Q2+): "Given" pays AG tranche, RCC completion pays RCC tranche, Possession pays POS tranche
                if not use_three_term_for(q):
                    ag_paid  = float(q_df.loc[ag_mask & q_df['Is Given'], 'Per Unit Incentive'].sum())
                    rcc_paid = 0.0
                    pos_paid = 0.0
                else:
                    splits_all = q_df['Per Unit Incentive'].fillna(0.0).astype(float).apply(split_fixed_1000)
                    ag_share  = splits_all.apply(lambda t: t[0])
                    rcc_share = splits_all.apply(lambda t: t[1])
                    pos_share = splits_all.apply(lambda t: t[2])
    
                    ag_paid  = float(ag_share.loc[ag_mask & q_df['Is Given']].sum())
                    rcc_paid = float(rcc_share.loc[rcc_mask].sum())
                    pos_paid = float(pos_share.loc[pos_mask].sum())
    
                total_paid = ag_paid + rcc_paid + pos_paid
    
                # Bonuses (Applicable basis; not split; not auto-counted as paid)
                bonus_amt = bonuses_applicable(q_df, q, exec_name)
    
                # Balance = (due base) + bonus - paid
                bal_base = max((ag_due + rcc_due + pos_due) - total_paid, 0.0)
                balance  = int(round(bal_base + bonus_amt))
    
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
    
            df_ag = _pd.DataFrame(rows_ag, columns=[
                "Quarter","AG","RCC","POS","AG Paid","RCC Paid","POS Paid","Total Paid","Bonus","Balance"
            ])
            df_ag["__key"] = df_ag["Quarter"].map(_quarter_sort_key)
            df_ag = df_ag.sort_values("__key").drop(columns="__key").reset_index(drop=True)
    
            st.markdown("**Status by Quarter (Agreement Done basis)**")
            st.dataframe(df_ag, use_container_width=True)
    
            # -------- Stamp Duty basis --------
            rows_sd = []
            for q in quarters:
                q_df = data[(data['Quarter'] == q) & (data['Sales Executive'] == exec_name)].copy()
    
                if q_df.empty:
                    rows_sd.append({
                        "Quarter": q,
                        "AG": "₹ 0", "RCC": "₹ 0", "POS": "₹ 0",
                        "AG Paid": "₹ 0", "RCC Paid": "₹ 0", "POS Paid": "₹ 0",
                        "Total Paid": "₹ 0", "Bonus": "₹ 0", "Balance": "₹ 0"
                    })
                    continue
    
                q_df = apply_payouts_for_exec_quarter(q_df, q, exec_name)
    
                sd_mask  = stamp_duty_mask(q_df)
                rcc_mask = sd_mask & q_df['RCC Flag']
                pos_mask = sd_mask & q_df['Possession Flag']
    
                base_series = (q_df['Per Unit Incentive'] * sd_mask).fillna(0.0).astype(float)
    
                if use_three_term_for(q):
                    splits = base_series.apply(split_fixed_1000)
                    t1 = splits.apply(lambda t: t[0])
                    t2 = splits.apply(lambda t: t[1])
                    t3 = splits.apply(lambda t: t[2])
                    ag_due  = float(t1.loc[sd_mask].sum())
                    rcc_due = float(t2.loc[rcc_mask].sum())
                    pos_due = float(t3.loc[pos_mask].sum())
                else:
                    ag_due, rcc_due, pos_due = float(base_series.sum()), 0.0, 0.0
    
                if not use_three_term_for(q):
                    ag_paid  = float(q_df.loc[sd_mask & q_df['Is Given'], 'Per Unit Incentive'].sum())
                    rcc_paid = 0.0
                    pos_paid = 0.0
                else:
                    splits_all = q_df['Per Unit Incentive'].fillna(0.0).astype(float).apply(split_fixed_1000)
                    ag_share  = splits_all.apply(lambda t: t[0])
                    rcc_share = splits_all.apply(lambda t: t[1])
                    pos_share = splits_all.apply(lambda t: t[2])
                    ag_paid  = float(ag_share.loc[sd_mask & q_df['Is Given']].sum())
                    rcc_paid = float(rcc_share.loc[rcc_mask].sum())
                    pos_paid = float(pos_share.loc[pos_mask].sum())
    
                # Bonuses on SD subset (same eligibility style, SD-only counts)
                q_sd = q_df[sd_mask].copy()
                q_sd_np = q_sd[~q_sd['PodiumFlag']]
                e_cnt = int((q_sd_np['WingNorm'] == 'E').sum())
                f_cnt = int((q_sd_np['WingNorm'] == 'F').sum())
                c_cnt = int((q_sd_np['WingNorm'] == 'C').sum())
                efc_cnt = e_cnt + f_cnt + c_cnt
                avgEF_sd = avg_rate_subset(q_sd_np[q_sd_np['WingNorm'].isin(['E','F'])])
                avgC_sd  = avg_rate_subset(q_sd_np[q_sd_np['WingNorm'] == 'C'])
    
                top_seller_sd = (len(q_sd) * 1000) if len(q_sd) >= 20 else 0
    
                all_q_sd = data[stamp_duty_mask(data) & (data['Quarter'] == q)]
                elig_counts_sd = all_q_sd.groupby('Sales Executive').size() if not all_q_sd.empty else _pd.Series(dtype=int)
                elig_names_sd  = elig_counts_sd[elig_counts_sd >= 12].index.tolist()
                team_sd = (50000 / len(elig_names_sd)) if (len(all_q_sd) >= 60 and len(elig_names_sd) > 0 and exec_name in elig_names_sd) else 0
    
                high_rate_sd = 100000 if (
                    efc_cnt >= 18 and
                    ((e_cnt + f_cnt == 0) or (_pd.notna(avgEF_sd) and avgEF_sd >= 6000)) and
                    ((c_cnt == 0)         or (_pd.notna(avgC_sd)  and avgC_sd  >= 6000))
                ) else 0
    
                bonus_sd = int(round(top_seller_sd + team_sd + high_rate_sd))
    
                total_paid = ag_paid + rcc_paid + pos_paid
                bal_base = max((ag_due + rcc_due + pos_due) - total_paid, 0.0)
                balance  = int(round(bal_base + bonus_sd))
    
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
    
            df_sd = _pd.DataFrame(rows_sd, columns=[
                "Quarter","AG","RCC","POS","AG Paid","RCC Paid","POS Paid","Total Paid","Bonus","Balance"
            ])
            df_sd["__key"] = df_sd["Quarter"].map(_quarter_sort_key)
            df_sd = df_sd.sort_values("__key").drop(columns="__key").reset_index(drop=True)
    
            st.markdown("**Status by Quarter (Stamp Duty Received basis)**")
            st.dataframe(df_sd, use_container_width=True)
    
            # Collect for overall tables (Agreement basis)
            def _to_int_series(col):
                return _pd.to_numeric(
                    col.astype(str).str.replace('₹', '', regex=False).str.replace(',', '', regex=False).str.strip(),
                    errors='coerce'
                ).fillna(0).astype(int)
    
            overall_rows.append({
                "Sales Executive": exec_name,
                "Amount": int(_to_int_series(df_ag["Balance"]).sum())
            })
            overall_paid_rows.append({
                "Sales Executive": exec_name,
                "Amount": int(_to_int_series(df_ag["Total Paid"]).sum())
            })
    
            st.markdown("---")
    
        # ===== Overall Totals (Agreement basis) =====
        df_overall = _pd.DataFrame(overall_rows, columns=["Sales Executive","Amount"])
        total_sum_bal = int(df_overall["Amount"].sum()) if not df_overall.empty else 0
        df_overall = _pd.concat(
            [df_overall, _pd.DataFrame([{"Sales Executive":"TOTAL", "Amount": total_sum_bal}])],
            ignore_index=True
        )
        st.markdown("**Overall Total Balance (Agreement basis)**")
        st.dataframe(df_overall, use_container_width=True)
    
        df_paid = _pd.DataFrame(overall_paid_rows, columns=["Sales Executive","Amount"])
        total_sum_paid = int(df_paid["Amount"].sum()) if not df_paid.empty else 0
        df_paid = _pd.concat(
            [df_paid, _pd.DataFrame([{"Sales Executive":"TOTAL", "Amount": total_sum_paid}])],
            ignore_index=True
        )
        st.markdown("**Overall Total Paid to Date (Agreement basis)**")
        st.dataframe(df_paid, use_container_width=True)
with tab3:
    st.header("📝 Booking Punch")

    if not sheets_connected:
        st.warning("📋 Please connect to Supabase to submit bookings.")
        st.stop()

    def clean_text(v):
        v = "" if v is None else str(v).strip()
        return "" if v == "" else v

    # ---- session defaults ----
    st.session_state.setdefault("inputs_locked", False)
    st.session_state.setdefault("calculated", False)
    st.session_state.setdefault("booking_selected_rate", None)
    st.session_state.setdefault("agreement_cost", None)
    st.session_state.setdefault("stamp_duty_percent", 7)
    st.session_state.setdefault("parkings", [{"type": "Stilt", "number": ""}])
    st.session_state.setdefault("offer_1", "")
    st.session_state.setdefault("offer_2", "")
    st.session_state.setdefault("floor", 1)
    st.session_state.setdefault("wing", "E")
    st.session_state.setdefault("booking_carpet_area_main", None)
    st.session_state.setdefault("merged_units", "")
    st.session_state.setdefault("location", "")
    st.session_state.setdefault("visit_count", "")

    location_options = [
        "",
        "Dhayari",
        "Dhayari Gaon",
        "Dhayari Phata",
        "Chavan Baug",
        "Benkar Nagar",
        "Ganesh Nagar (Dhayari)",
        "Shree Nagar (Dhayari)",
        "Raykar Mala",
        "Garmal",
        "Morya Nagar (Dhayari)",
        "Saikrupa Nagar",
        "Siddharth Nagar (Dhayari side)",
        "Laxmi Nagar (Dhayari)",
        "Nanded",
        "Nanded Gaon",
        "Nanded Fata",
        "Nanded City",
        "Deshmukh Nagar",
        "Pandurang Industrial Area",
        "Vadgaon Budruk",
        "Santosh Nagar (Vadgaon)",
        "Kirloskar Colony",
        "Anand Nagar (Sinhagad Road)",
        "Manik Baug",
        "Suncity",
        "Narhe",
        "Narhe Gaon",
        "Khadewadi",
        "Kirkatwadi",
        "Kirkatwadi Gaon",
        "Kolhewadi",
        "Donje",
        "Donje Gaon",
        "Mukai Nagar",
        "Shivane",
        "Uttam Nagar",
        "Warje",
        "Warje Malwadi",
        "Ram Nagar (Warje)",
        "Gokul Nagar (Warje)",
        "Hingne Budruk",
        "Hingne Khurd",
        "Karve Nagar",
        "Kothrud",
        "Swargate"
    ]

    def _ensure_parking_keys():
        for i, p in enumerate(st.session_state.parkings):
            st.session_state.setdefault(f"parking_type_{i}", p.get("type", "Stilt"))
            st.session_state.setdefault(f"parking_number_{i}", p.get("number", ""))

    def _sync_parkings_from_keys():
        new_list = []
        for i in range(len(st.session_state.parkings)):
            p_type = st.session_state.get(f"parking_type_{i}", "Stilt")
            p_num = (st.session_state.get(f"parking_number_{i}", "") or "").strip()
            new_list.append({"type": p_type, "number": p_num})
        st.session_state.parkings = new_list

    def _has_at_least_one_parking():
        for p in st.session_state.get("parkings", []):
            p_type = (p.get("type") or "").strip()
            p_num = (p.get("number") or "").strip()
            if p_type and p_num:
                return True
        return False

    _ensure_parking_keys()

    if not st.session_state.inputs_locked:
        st.session_state.calculated = False

    all_carpets = [480.94, 482.12, 655.10, 665.65, 666.29, 678, 689, 790, 545, 756]

    offer_options = [
        "",
        "1 Gram Gold Coin",
        "2 Gram Gold Coin",
        "200 Gram Silver",
        "Kitchen Trolley",
        "25000 Electronic Voucher"
    ]

    def offer_label(opt):
        return "— No Offer —" if opt == "" else opt

    visit_count_options = [""] + list(range(1, 11))

    def _visit_label(x):
        return "Select" if x == "" else str(x)

    with st.form("booking_inputs_form", clear_on_submit=False):
        st.caption("Fill all details. Use ➕ in Parking if needed. Then Lock Inputs to calculate.")

        with st.container(border=True):
            st.subheader("🗓️ Dates", divider="gray")
            c1, c2, c3 = st.columns(3)

            with c1:
                st.date_input(
                    "Date of Booking *",
                    format="DD/MM/YYYY",
                    key="booking_date",
                    disabled=st.session_state.inputs_locked
                )

            with c2:
                st.date_input(
                    "Date of First Visit *",
                    format="DD/MM/YYYY",
                    key="first_visit_date",
                    disabled=st.session_state.inputs_locked
                )

            with c3:
                st.selectbox(
                    "Visit Count *",
                    options=visit_count_options,
                    format_func=_visit_label,
                    key="visit_count",
                    disabled=st.session_state.inputs_locked
                )

        st.divider()

        with st.container(border=True):
            st.subheader("👤 Basic Details", divider="gray")
            b1, b2, b3 = st.columns(3)

            with b1:
                st.text_input(
                    "Customer Name *",
                    key="cust_name",
                    placeholder="e.g., Rohan Sharma",
                    disabled=st.session_state.inputs_locked
                )

            with b2:
                st.selectbox(
                    "Wing *",
                    ["E", "F", "C"],
                    key="wing",
                    disabled=st.session_state.inputs_locked
                )

            with b3:
                st.selectbox(
                    "Floor *",
                    list(range(1, 14)),
                    key="floor",
                    disabled=st.session_state.inputs_locked
                )

            u1, u2 = st.columns(2)

            with u1:
                st.text_input(
                    "Flat Number *",
                    key="flat_number",
                    placeholder="e.g., 1004",
                    disabled=st.session_state.inputs_locked
                )

            with u2:
                st.selectbox(
                    "Type *",
                    ["1BHK", "2BHK"],
                    key="unit_type",
                    disabled=st.session_state.inputs_locked
                )

            l1, l2 = st.columns(2)

            with l1:
                st.selectbox(
                    "Location *",
                    options=location_options,
                    key="location",
                    disabled=st.session_state.inputs_locked
                )

            with l2:
                st.selectbox(
                    "Merged Units",
                    options=["", "1+1", "2+1", "2+2"],
                    key="merged_units",
                    disabled=st.session_state.inputs_locked
                )

        st.divider()

        with st.container(border=True):
            st.subheader("📐 Carpet Area", divider="gray")
            st.selectbox(
                "Booking: Carpet Area *",
                options=all_carpets,
                key="booking_carpet_area_main",
                disabled=st.session_state.inputs_locked
            )

        st.divider()

        with st.container(border=True):
            st.subheader("🚗 Parking", divider="gray")
            st.caption("Saved as Type-Number. Example: Basement-121 , Basement-122")

            parking_types = ["Stilt", "Ground", "Basement", "Tandum S", "Tandum B"]

            add_row_cols = st.columns([3, 1])
            with add_row_cols[1]:
                add_parking_clicked = st.form_submit_button(
                    "➕ Add",
                    use_container_width=True,
                    disabled=st.session_state.inputs_locked
                )

            if add_parking_clicked:
                _sync_parkings_from_keys()
                st.session_state.parkings.append({"type": "Stilt", "number": ""})
                _ensure_parking_keys()

            for i in range(len(st.session_state.parkings)):
                r1, r2 = st.columns([1, 1])

                with r1:
                    st.selectbox(
                        f"Parking Type {i+1}",
                        parking_types,
                        key=f"parking_type_{i}",
                        disabled=st.session_state.inputs_locked
                    )

                with r2:
                    st.text_input(
                        f"Parking Number {i+1} *",
                        key=f"parking_number_{i}",
                        placeholder="e.g., 121 or 121A",
                        disabled=st.session_state.inputs_locked
                    )

        st.divider()

        with st.container(border=True):
            st.subheader("💰 Commercials", divider="gray")
            m1, m2 = st.columns([1, 1])

            with m1:
                st.number_input(
                    "Final Price (in Lakhs) *",
                    value=st.session_state.get("final_price_lakhs")
                    if st.session_state.get("final_price_lakhs") is not None else 0.0,
                    key="final_price_lakhs",
                    disabled=st.session_state.inputs_locked
                )

            with m2:
                st.selectbox(
                    "Stamp Duty (for calc only) *",
                    options=[6, 7],
                    format_func=lambda x: f"{x}%",
                    key="stamp_duty_percent",
                    disabled=st.session_state.inputs_locked
                )

        st.divider()

        with st.container(border=True):
            st.subheader("🎁 Offers & Remarks", divider="gray")
            o1, o2 = st.columns(2)

            with o1:
                st.selectbox(
                    "Offer 1",
                    offer_options,
                    key="offer_1",
                    format_func=offer_label,
                    disabled=st.session_state.inputs_locked
                )

            with o2:
                st.selectbox(
                    "Offer 2",
                    offer_options,
                    key="offer_2",
                    format_func=offer_label,
                    disabled=st.session_state.inputs_locked
                )

            st.text_input(
                "Civil Changes (if any)",
                key="civil_changes",
                placeholder="e.g., Kitchen platform shift, extra electrical points",
                disabled=st.session_state.inputs_locked
            )

        st.divider()

        with st.container(border=True):
            st.subheader("👥 Lead & Executive", divider="gray")
            le1, le2 = st.columns(2)

            with le1:
                st.selectbox(
                    "Lead Type *",
                    ["Direct", "CP", "Digital", "Referral", "Hoarding"],
                    key="lead_type",
                    disabled=st.session_state.inputs_locked
                )

            with le2:
                st.selectbox(
                    "Sales Executive *",
                    ["Komal K", "Tejas P", "Ashutosh S", "Sailee D"],
                    key="sales_exec",
                    disabled=st.session_state.inputs_locked
                )

        lock_clicked = st.form_submit_button(
            "🔒 Lock Inputs & Calculate",
            use_container_width=True,
            disabled=st.session_state.inputs_locked
        )

    if lock_clicked:
        _sync_parkings_from_keys()
        valid = True

        if not st.session_state.get("booking_date") or not st.session_state.get("first_visit_date"):
            st.error("❌ Please fill both dates.")
            valid = False

        if st.session_state.get("visit_count") == "" or st.session_state.get("visit_count") is None:
            st.error("❌ Visit Count is compulsory.")
            valid = False

        if not (st.session_state.get("cust_name") or "").strip():
            st.error("❌ Customer Name is compulsory.")
            valid = False

        if not (st.session_state.get("flat_number") or "").strip():
            st.error("❌ Flat Number is compulsory.")
            valid = False

        if not (st.session_state.get("location") or "").strip():
            st.error("❌ Location is compulsory.")
            valid = False

        if st.session_state.get("booking_carpet_area_main") is None:
            st.error("❌ Carpet Area is compulsory.")
            valid = False

        if not _has_at_least_one_parking():
            st.error("❌ Parking is compulsory.")
            valid = False

        fp = st.session_state.get("final_price_lakhs")
        if fp is None or fp <= 0:
            st.error("❌ Please enter valid Final Price.")
            valid = False

        if valid:
            gap = (st.session_state.booking_date - st.session_state.first_visit_date).days
            if gap < 0:
                st.error("❌ First Visit Date cannot be after Date of Booking.")
                valid = False

        if valid:
            booking_carpet_area = st.session_state.booking_carpet_area_main
            booking_saleable = round(booking_carpet_area * 1.38, 2)

            registration = 30000
            total_package = fp * 100000
            booking_adjusted_cost = total_package - registration

            gst_percent = 1 if total_package <= 4889999 else 5
            stamp = st.session_state.stamp_duty_percent

            booking_divisor = 1 + ((stamp + gst_percent) / 100)

            agreement_cost = round(booking_adjusted_cost / booking_divisor)
            booking_selected_rate = round(agreement_cost / booking_saleable)

            st.session_state.booking_selected_rate = booking_selected_rate
            st.session_state.agreement_cost = agreement_cost
            st.session_state.inputs_locked = True
            st.session_state.calculated = True

            st.success("Inputs locked and calculation done. You can now submit booking.")

    if st.session_state.get("first_visit_date") and st.session_state.get("booking_date"):
        conversion_days = (st.session_state.booking_date - st.session_state.first_visit_date).days
        if conversion_days >= 0:
            st.info(f"🕒 Conversion Period: {conversion_days} days")
        else:
            st.warning("⚠️ First Visit Date is after Date of Booking.")

    st.text_input(
        "Rate Per Sqft (Auto)",
        value=st.session_state.get("booking_selected_rate"),
        disabled=True
    )

    st.text_input(
        "Agreement Cost (Auto)",
        value=st.session_state.get("agreement_cost"),
        disabled=True
    )

    can_submit = st.session_state.inputs_locked and st.session_state.calculated

    if st.button("✅ Submit Booking", disabled=not can_submit):
        try:
            _sync_parkings_from_keys()

            if not st.session_state.get("booking_date") or not st.session_state.get("first_visit_date"):
                st.error("❌ Both dates are compulsory.")
                st.stop()

            if st.session_state.get("visit_count") == "" or st.session_state.get("visit_count") is None:
                st.error("❌ Visit Count is compulsory.")
                st.stop()

            if not (st.session_state.get("cust_name") or "").strip():
                st.error("❌ Customer Name is compulsory.")
                st.stop()

            if not (st.session_state.get("flat_number") or "").strip():
                st.error("❌ Flat Number is compulsory.")
                st.stop()

            if not (st.session_state.get("location") or "").strip():
                st.error("❌ Location is compulsory.")
                st.stop()

            if st.session_state.get("booking_carpet_area_main") is None:
                st.error("❌ Carpet Area is compulsory.")
                st.stop()

            if not _has_at_least_one_parking():
                st.error("❌ Parking is compulsory.")
                st.stop()

            _days_gap = (st.session_state.booking_date - st.session_state.first_visit_date).days
            if _days_gap < 0:
                st.error("❌ First Visit Date cannot be after Date of Booking.")
                st.stop()

            parking_parts = []
            for p in st.session_state.get("parkings", []):
                p_type = (p.get("type") or "").strip()
                p_num = (p.get("number") or "").strip()
                if p_type and p_num:
                    parking_parts.append(f"{p_type}-{p_num}")

            parking_string = " , ".join(parking_parts)

            month_label = st.session_state.booking_date.strftime("%B %y").upper()
            agreement_cost = st.session_state.agreement_cost

            booking_amount = round(agreement_cost * 0.05)
            agreement = round(agreement_cost * 0.10)
            plinth = round(agreement_cost * 0.15)
            third_floor = round(agreement_cost * 0.075)
            seventh_floor = round(agreement_cost * 0.075)
            tenth_floor = round(agreement_cost * 0.075)
            thirteenth_floor = round(agreement_cost * 0.075)
            flooring = round(agreement_cost * 0.075)
            plastering = round(agreement_cost * 0.075)
            plumbing = round(agreement_cost * 0.075)
            electrical = round(agreement_cost * 0.075)
            sanitary_lift = round(agreement_cost * 0.05)
            possession = round(agreement_cost * 0.05)

            booking_row = {
                "booking_date": st.session_state.booking_date.isoformat(),
                "customer_name": clean_text(st.session_state.cust_name),
                "wing": clean_text(st.session_state.wing),
                "floor": int(st.session_state.floor),
                "flat_number": clean_text(st.session_state.flat_number),
                "type": clean_text(st.session_state.unit_type),

                "final_price": float(st.session_state.final_price_lakhs),
                "rate": int(st.session_state.booking_selected_rate),
                "agreement_cost": int(st.session_state.agreement_cost),

                "lead_type": clean_text(st.session_state.lead_type),
                "sales_executive": clean_text(st.session_state.sales_exec),
                "month": clean_text(month_label),

                "civil_changes": clean_text(st.session_state.get("civil_changes")),
                "offer_1": clean_text(st.session_state.get("offer_1")),
                "offer_2": clean_text(st.session_state.get("offer_2")),

                "offer_1_rewarded": "",
                "offer_2_rewarded": "",
                "referral_given": "",
                "stamp_duty": "",
                "agreement_done": "",
                "incentive": "",
                "rcc": "",
                "possession_handover": "",
                "insider_banker": "",
                "outsider_banker": "",

                "carpet_area": float(st.session_state.booking_carpet_area_main),

                "booking_amount": booking_amount,
                "agreement": agreement,
                "plinth": plinth,
                "third_floor": third_floor,
                "seventh_floor": seventh_floor,
                "tenth_floor": tenth_floor,
                "thirteenth_floor": thirteenth_floor,
                "flooring": flooring,
                "plastering": plastering,
                "plumbing": plumbing,
                "electrical": electrical,
                "sanitary_lift": sanitary_lift,
                "possession": possession,

                "first_visit_date": st.session_state.first_visit_date.isoformat(),
                "conversion_period_days": int(_days_gap),

                "parking_number": clean_text(parking_string),
                "merged_units": clean_text(st.session_state.get("merged_units")),
                "location": clean_text(st.session_state.get("location")),
                "visit_count": int(st.session_state.get("visit_count")),

                "received_amount": None,
                "stamp_duty_percent": int(st.session_state.stamp_duty_percent),
            }

            supabase.table("bookings").insert(booking_row).execute()

            st.success("🎉 Booking submitted successfully!")

            st.session_state.calculated = False
            st.session_state.inputs_locked = False
            st.session_state.booking_selected_rate = None
            st.session_state.agreement_cost = None

            st.session_state.pop("merged_units", None)
            st.session_state.pop("location", None)
            st.session_state.pop("visit_count", None)

            for i in range(len(st.session_state.get("parkings", []))):
                st.session_state.pop(f"parking_type_{i}", None)
                st.session_state.pop(f"parking_number_{i}", None)

            st.session_state.parkings = [{"type": "Stilt", "number": ""}]
            _ensure_parking_keys()

        except Exception as e:
            st.error(f"❌ Error submitting to Supabase: {e}")
