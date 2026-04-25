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
