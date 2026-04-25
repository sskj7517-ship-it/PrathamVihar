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
with tab1:
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
