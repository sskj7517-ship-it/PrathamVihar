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

    if 'tab5_filters_active' not in st.session_state:
        st.session_state.tab5_filters_active = False
    if 'tab5_customer' not in st.session_state:
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

    if not sheets_connected:
        st.warning("📋 Please connect to Supabase to use this feature.")
    else:
        data = load_all_data()
        df = data["sheet_df"].copy()

        if df.empty:
            st.warning("No data available in Supabase.")
        else:
            rename_map = {
                "customer_name": "Customer Name",
                "wing": "Wing",
                "flat_number": "Flat Number",
                "sales_executive": "Sales Executive",
                "lead_type": "Lead Type",
                "stamp_duty": "Stamp Duty",
                "agreement_done": "Agreement Done",
                "incentive": "Incentive",
                "rcc": "RCC",
                "possession_handover": "POSSESSION HANDOVER",
                "referral_given": "Referral Given",
                "insider_banker": "Insider Banker",
                "outsider_banker": "Outsider Banker",
                "offer_1": "Offer 1",
                "offer_2": "Offer 2",
                "offer_1_rewarded": "Offer 1 Rewarded",
                "offer_2_rewarded": "Offer 2 Rewarded",
                "month": "month",
            }

            df = df.rename(columns=rename_map)

            required_cols = [
                "id", "month", "Customer Name", "Sales Executive",
                "Wing", "Flat Number",
                "Agreement Done", "Stamp Duty", "Incentive",
                "RCC", "POSSESSION HANDOVER",
                "Lead Type", "Referral Given",
                "Insider Banker", "Outsider Banker",
                "Offer 1", "Offer 2", "Offer 1 Rewarded", "Offer 2 Rewarded"
            ]

            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""

            df["Flat Address"] = (
                df["Wing"].fillna("").astype(str).str.strip()
                + " "
                + df["Flat Number"].fillna("").astype(str).str.strip()
            ).str.strip()

            def _norm(s):
                return str(s or "").strip().lower()

            def _bool_to_status(value, true_word):
                if value is True:
                    return true_word
                if value is False:
                    return ""
                return str(value or "")

            df["Agreement Done"] = df["Agreement Done"].apply(lambda x: _bool_to_status(x, "Done"))
            df["POSSESSION HANDOVER"] = df["POSSESSION HANDOVER"].apply(lambda x: _bool_to_status(x, "Handover"))
            df["Referral Given"] = df["Referral Given"].apply(lambda x: _bool_to_status(x, "Given"))
            df["Offer 1 Rewarded"] = df["Offer 1 Rewarded"].apply(lambda x: _bool_to_status(x, "Rewarded 1"))
            df["Offer 2 Rewarded"] = df["Offer 2 Rewarded"].apply(lambda x: _bool_to_status(x, "Rewarded 2"))

            def make_label(row):
                wf = str(row.get("Flat Address", "")).strip()
                nm = str(row.get("Customer Name", "")).strip()
                return f"{wf} - {nm}" if wf else nm

            base_preview = df.copy()
            pre_month = st.session_state.get("tab5_month", "ALL")
            pre_exec = st.session_state.get("tab5_exec", "ALL")
            pre_wing = st.session_state.get("tab5_wing", "ALL")

            if pre_month != "ALL":
                base_preview = base_preview[base_preview["month"] == pre_month]
            if pre_exec != "ALL":
                base_preview = base_preview[base_preview["Sales Executive"].astype(str) == pre_exec]
            if pre_wing != "ALL":
                base_preview = base_preview[base_preview["Wing"].astype(str).str.strip() == pre_wing]

            label_map_preview = {idx: make_label(r) for idx, r in base_preview.iterrows()}
            customer_options = ["ALL"] + [label_map_preview[i] for i in base_preview.index]
            cust_default_idx = (
                customer_options.index(st.session_state.tab5_customer)
                if st.session_state.tab5_customer in customer_options else 0
            )

            with st.form("agreement_filter_form"):
                month_values = sorted(df["month"].dropna().unique(), reverse=True)
                month_options = ["ALL"] + list(month_values)
                st.selectbox("Month (fixed)", month_options, key="tab5_month")

                exec_values = sorted(df["Sales Executive"].dropna().astype(str).unique())
                exec_options = ["ALL"] + list(exec_values)
                st.selectbox("Sales Executive (fixed)", exec_options, key="tab5_exec")

                wing_values = df["Wing"].dropna().astype(str).str.strip().unique().tolist()
                wing_values = sorted([w for w in wing_values if w != ""])
                wing_options = ["ALL"] + wing_values
                st.selectbox("Wing (fixed)", wing_options, key="tab5_wing")

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
                    if st.session_state.tab5_filter_field in var_fields else 0,
                    key="tab5_filter_field"
                )

                ff = st.session_state.tab5_filter_field
                if ff == "Customer":
                    st.selectbox("Customer (Wing Flat – Name)", options=customer_options, index=cust_default_idx, key="tab5_customer")
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
                    st.selectbox("Offer 1 Filter", ["Has Offer", "No Offer", "Rewarded", "Not Rewarded"], key="tab5_o1_choice")
                elif ff == "Offer 2 (Has/Rewarded)":
                    st.selectbox("Offer 2 Filter", ["Has Offer", "No Offer", "Rewarded", "Not Rewarded"], key="tab5_o2_choice")

                c1, c2 = st.columns(2)
                with c1:
                    st.form_submit_button("Find", on_click=_tab5_apply_filters)
                with c2:
                    st.form_submit_button("Reset", on_click=_tab5_reset_filters)

            if not st.session_state.tab5_filters_active:
                st.info("Set Month, Sales Executive & Wing (fixed), choose one additional filter, then click **Find**.")
            else:
                post_df = df.copy()

                if st.session_state.tab5_month != "ALL":
                    post_df = post_df[post_df["month"] == st.session_state.tab5_month]
                if st.session_state.tab5_exec != "ALL":
                    post_df = post_df[post_df["Sales Executive"].astype(str) == st.session_state.tab5_exec]
                if st.session_state.tab5_wing != "ALL":
                    post_df = post_df[post_df["Wing"].astype(str).str.strip() == st.session_state.tab5_wing]

                ff = st.session_state.tab5_filter_field

                if ff == "Customer" and st.session_state.tab5_customer != "ALL":
                    label_map = {idx: make_label(r) for idx, r in post_df.iterrows()}
                    chosen = [i for i, lab in label_map.items() if lab == st.session_state.tab5_customer]
                    post_df = post_df.loc[chosen]

                elif ff == "Flat Address (contains)":
                    q = st.session_state.tab5_addr_contains.strip().lower()
                    if q:
                        post_df = post_df[post_df["Flat Address"].astype(str).str.lower().str.contains(q, na=False)]

                elif ff == "Customer Name (contains)":
                    q = st.session_state.tab5_name_contains.strip().lower()
                    if q:
                        post_df = post_df[post_df["Customer Name"].astype(str).str.lower().str.contains(q, na=False)]

                elif ff == "Stamp Duty":
                    want_received = (st.session_state.tab5_stamp_choice == "Received")
                    post_df = post_df[post_df["Stamp Duty"].apply(lambda v: _norm(v) == "received") == want_received]

                elif ff == "Agreement Done":
                    want_done = (st.session_state.tab5_agree_choice == "Done")
                    post_df = post_df[post_df["Agreement Done"].apply(lambda v: _norm(v) == "done") == want_done]

                elif ff == "Incentive":
                    want_given = (st.session_state.tab5_incentive_choice == "Given")
                    post_df = post_df[post_df["Incentive"].apply(lambda v: _norm(v) == "given") == want_given]

                elif ff == "Insider Banker":
                    want_yes = (st.session_state.tab5_insider_choice == "Yes")
                    post_df = post_df[post_df["Insider Banker"].apply(lambda v: _norm(v) == "yes") == want_yes]

                elif ff == "Outsider Banker":
                    want_yes = (st.session_state.tab5_outsider_choice == "Yes")
                    post_df = post_df[post_df["Outsider Banker"].apply(lambda v: _norm(v) == "yes") == want_yes]

                elif ff == "Offer 1 (Has/Rewarded)":
                    choice = st.session_state.tab5_o1_choice
                    if choice == "Has Offer":
                        post_df = post_df[post_df["Offer 1"].astype(str).str.strip() != ""]
                    elif choice == "No Offer":
                        post_df = post_df[post_df["Offer 1"].astype(str).str.strip() == ""]
                    elif choice == "Rewarded":
                        post_df = post_df[post_df["Offer 1 Rewarded"].apply(lambda x: _norm(x) in ("rewarded 1", "true", "yes", "1", "y", "✓"))]
                    elif choice == "Not Rewarded":
                        post_df = post_df[~post_df["Offer 1 Rewarded"].apply(lambda x: _norm(x) in ("rewarded 1", "true", "yes", "1", "y", "✓"))]

                elif ff == "Offer 2 (Has/Rewarded)":
                    choice = st.session_state.tab5_o2_choice
                    if choice == "Has Offer":
                        post_df = post_df[post_df["Offer 2"].astype(str).str.strip() != ""]
                    elif choice == "No Offer":
                        post_df = post_df[post_df["Offer 2"].astype(str).str.strip() == ""]
                    elif choice == "Rewarded":
                        post_df = post_df[post_df["Offer 2 Rewarded"].apply(lambda x: _norm(x) in ("rewarded 2", "true", "yes", "1", "y", "✓"))]
                    elif choice == "Not Rewarded":
                        post_df = post_df[~post_df["Offer 2 Rewarded"].apply(lambda x: _norm(x) in ("rewarded 2", "true", "yes", "1", "y", "✓"))]

                month_label = st.session_state.tab5_month if st.session_state.tab5_month != "ALL" else "All Months"
                exec_label = st.session_state.tab5_exec if st.session_state.tab5_exec != "ALL" else "All Executives"
                wing_label = st.session_state.tab5_wing if st.session_state.tab5_wing != "ALL" else "All Wings"

                extra = st.session_state.tab5_filter_field
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
                        row_id = row.get("id")
                        flat_addr = row.get("Flat Address", "")
                        cust_name = row.get("Customer Name", "")

                        is_agreement_done = _norm(row.get("Agreement Done", "")) == "done"
                        is_stamp_received = _norm(row.get("Stamp Duty", "")) == "received"
                        is_incentive_given = _norm(row.get("Incentive", "")) == "given"
                        is_referral_given = _norm(row.get("Referral Given", "")) == "given"
                        is_rcc_completed = _norm(row.get("RCC", "")) == "completed"
                        is_poss_handover = _norm(row.get("POSSESSION HANDOVER", "")) == "handover"
                        is_referral_lead = _norm(row.get("Lead Type", "")) == "referral"
                        is_insider = _norm(row.get("Insider Banker", "")) == "yes"
                        is_outsider = _norm(row.get("Outsider Banker", "")) == "yes"

                        offer1_text = str(row.get("Offer 1", "") or "").strip()
                        offer2_text = str(row.get("Offer 2", "") or "").strip()
                        has_offer1 = offer1_text != ""
                        has_offer2 = offer2_text != ""

                        is_o1_rewarded = _norm(row.get("Offer 1 Rewarded", "")) in ("rewarded 1", "true", "yes", "1", "y", "✓")
                        is_o2_rewarded = _norm(row.get("Offer 2 Rewarded", "")) in ("rewarded 2", "true", "yes", "1", "y", "✓")

                        col0, col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(
                            [2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3]
                        )

                        col0.write(flat_addr)
                        col1.write(cust_name)

                        stamp_checked = col2.checkbox("Received", value=is_stamp_received, key=f"tab5_stamp_{row_id}")
                        agreement_checked = col3.checkbox("Done", value=is_agreement_done, key=f"tab5_agree_{row_id}")
                        incentive_checked = col4.checkbox("Given", value=is_incentive_given, key=f"tab5_incentive_{row_id}")
                        rcc_checked = col5.checkbox("Completed", value=is_rcc_completed, key=f"tab5_rcc_{row_id}")
                        pos_checked = col6.checkbox("Handover", value=is_poss_handover, key=f"tab5_pos_{row_id}")

                        if is_referral_lead:
                            referral_checked = col7.checkbox("Given", value=is_referral_given, key=f"tab5_referral_{row_id}")
                        else:
                            col7.write("Given" if is_referral_given else "—")
                            referral_checked = is_referral_given

                        insider_checked = col8.checkbox("Yes", value=is_insider, key=f"tab5_insider_{row_id}")
                        outsider_checked = col9.checkbox("Yes", value=is_outsider, key=f"tab5_outsider_{row_id}")

                        if has_offer1:
                            o1_checked = col10.checkbox(offer1_text, value=is_o1_rewarded, key=f"tab5_offer1_{row_id}")
                        else:
                            col10.write("—")
                            o1_checked = is_o1_rewarded

                        if has_offer2:
                            o2_checked = col11.checkbox(offer2_text, value=is_o2_rewarded, key=f"tab5_offer2_{row_id}")
                        else:
                            col11.write("—")
                            o2_checked = is_o2_rewarded

                        update_data = {}

                        if stamp_checked and not is_stamp_received:
                            update_data["stamp_duty"] = "Received"

                        if agreement_checked and not is_agreement_done:
                            update_data["agreement_done"] = True
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
                                unsafe_allow_html=True
                            )

                        if incentive_checked and not is_incentive_given:
                            update_data["incentive"] = "Given"

                        if rcc_checked and not is_rcc_completed:
                            update_data["rcc"] = "Completed"

                        if pos_checked and not is_poss_handover:
                            update_data["possession_handover"] = True

                        if is_referral_lead and referral_checked and not is_referral_given:
                            update_data["referral_given"] = True

                        if insider_checked and not is_insider:
                            update_data["insider_banker"] = "Yes"

                        if outsider_checked and not is_outsider:
                            update_data["outsider_banker"] = "Yes"

                        if has_offer1:
                            new_o1_val = True if o1_checked else False
                            if new_o1_val != is_o1_rewarded:
                                update_data["offer_1_rewarded"] = new_o1_val

                        if has_offer2:
                            new_o2_val = True if o2_checked else False
                            if new_o2_val != is_o2_rewarded:
                                update_data["offer_2_rewarded"] = new_o2_val

                        if update_data:
                            update_row("bookings", row_id, update_data)
                            st.success("✅ Status updated in Supabase.")

                st.caption("**Note:** Month, Sales Executive & Wing are fixed filters (always applied). Exactly one additional filter from the form is applied at a time. Checkboxes update Supabase immediately.")
