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
