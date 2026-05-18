# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.


import streamlit as st
import pandas as pd

# =========================
#  PRATHAM VIHAR – SIDEBAR
# =========================

# --- Header ---
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
           padding: 2rem; border-radius: 15px; margin-bottom: 1.5rem; 
           box-shadow: 0 8px 16px rgba(0,0,0,0.15); text-align: center;">
    <h2 style="color: white; margin: 0; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
        🏢 PRATHAM VIHAR
    </h2>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
        Quick Reference Guide
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# Carpet Area ↔ Series Mapping
# -------------------------------
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
           padding: 1.5rem; border-radius: 12px; margin-bottom: 1.2rem; 
           box-shadow: 0 6px 12px rgba(0,0,0,0.1); text-align: center;">
    <h3 style="color: white; margin: 0; font-weight: 700; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
        🏠 Carpet Area ↔ Series Mapping
    </h3>
</div>
""", unsafe_allow_html=True)

series_data = [
    {"🏠 Carpet Area (sq ft)": "480.94", "🏗️ Series": "4 and 7", "🏢 Type": "1BHK"},
    {"🏠 Carpet Area (sq ft)": "482.12", "🏗️ Series": "5 and 6", "🏢 Type": "1BHK"},
    {"🏠 Carpet Area (sq ft)": "655.10", "🏗️ Series": "1 and 10", "🏢 Type": "2BHK"},
    {"🏠 Carpet Area (sq ft)": "665.65", "🏗️ Series": "3 and 8", "🏢 Type": "2BHK"},
    {"🏠 Carpet Area (sq ft)": "666.29", "🏗️ Series": "2 and 9", "🏢 Type": "2BHK"}
]
st.sidebar.dataframe(pd.DataFrame(series_data), use_container_width=True, hide_index=True)

# -----------------------------------------
# Sales Effectiveness %
# -----------------------------------------
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #4f46e5 0%, #8b5cf6 100%);
           padding: 1.2rem; border-radius: 12px; margin: 1.2rem 0 .6rem 0;
           box-shadow: 0 6px 12px rgba(0,0,0,0.15); text-align:center;">
  <h3 style="color:#fff; margin:0; font-weight:800;">📐 Sales Effectiveness %</h3>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
           padding: 1rem; border-radius: 12px;
           border: 2px solid #4f46e5; box-shadow: 0 4px 10px rgba(0,0,0,.06);">

  <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:.6rem;">
    <span style="background:#eef2ff; color:#3730a3; padding:.25rem .6rem; border-radius:999px; font-weight:800;">Bookings 40%</span>
    <span style="background:#ecfeff; color:#155e75; padding:.25rem .6rem; border-radius:999px; font-weight:800;">Rate 30%</span>
    <span style="background:#f0fdf4; color:#166534; padding:.25rem .6rem; border-radius:999px; font-weight:800;">Mix 30%</span>
  </div>

  <table style="width:100%; border-collapse:collapse; text-align:left; font-size:.92rem;">
    <tr>
      <th colspan="2" style="background:#4f46e5; color:#fff; padding:.55rem; border-radius:8px;">How it’s calculated</th>
    </tr>
    <tr>
      <td style="padding:.55rem; border-bottom:1px solid #e5e7eb; width:36%; font-weight:700;">Bookings %</td>
      <td style="padding:.55rem; border-bottom:1px solid #e5e7eb;">(Bookings ÷ 12) × 100 <span style="color:#64748b;">(cap 100)</span></td>
    </tr>
    <tr>
      <td style="padding:.55rem; border-bottom:1px solid #e5e7eb; font-weight:700;">Rate %</td>
      <td style="padding:.55rem; border-bottom:1px solid #e5e7eb;">(Avg Rate ÷ ₹5850) × 100</td>
    </tr>
    <tr>
      <td style="padding:.55rem; font-weight:700;">Mix %</td>
      <td style="padding:.55rem;">Type weights: Premium 1.2×, Standard 1.0×, Low 0.8×</td>
    </tr>
  </table>

  <div style="margin:.75rem 0 0 0; font-weight:800;">Final Score</div>
  <div style="font-family:ui-monospace, SFMono-Regular, Menlo, monospace; background:#f3f4f6; padding:.45rem .6rem; border-radius:8px; display:inline-block; margin-top:.2rem;">
    0.40×Bookings % + 0.30×Rate % + 0.30×Mix %
  </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar.expander("Area Mapping & Weights"):
    mapping_df = pd.DataFrame({
        "Category": ["Premium", "Standard", "Low"],
        "Carpet Area (sq ft)": [
            "655.10, 678, 545, 689, 790, 756",  # Premium
            "666.29",                           # Standard
            "482.12, 480.94, 665.65"            # Low
        ],
        "Weight": ["1.2×", "1.0×", "0.8×"],
        "Tolerance": ["±0.25 sqft", "±0.25 sqft", "±0.25 sqft"]
    })
    st.dataframe(mapping_df, use_container_width=True, hide_index=True)


# -----------------------
# Incentive Structure
# -----------------------
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #fd7e14 0%, #e63946 100%); 
           padding: 1.5rem; border-radius: 12px; margin: 1.2rem 0; 
           box-shadow: 0 6px 12px rgba(220, 53, 69, 0.3); text-align: center;">
    <h3 style="color: white; margin: 0; font-weight: 700; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
        💰 INCENTIVE STRUCTURE
    </h3>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
        E & F Wing - Your Path to Success
    </p>
</div>
""", unsafe_allow_html=True)

# --- Booking Incentives (single-call HTML with 5 lead types) ---
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
           padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;
           border: 2px solid #667eea; text-align: center;">
  <h4 style="color: #667eea; margin: 0 0 1rem 0; font-weight: 700;">🎯 Booking Incentives</h4>
  <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    <table style="width: 100%; text-align: center; border-collapse: collapse;">
      <tr style="background: #667eea; color: white;">
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">Type</th>
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">12 Units</th>
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">18+ Units</th>
      </tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f8f9fa; font-weight:600;">Direct</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#28a745; font-weight:700;">₹5,000</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#28a745; font-weight:700;">₹6,000</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f8f9fa; font-weight:600;">CP</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#fd7e14; font-weight:700;">₹5,000</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#fd7e14; font-weight:700;">₹6,000</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f8f9fa; font-weight:600;">Referral</td>
          <td style="padding:.8rem; border:1px solid #ddd; font-weight:700;">₹5,000</td>
          <td style="padding:.8rem; border:1px solid #ddd; font-weight:700;">₹6,000</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f8f9fa; font-weight:600;">Digital</td>
          <td style="padding:.8rem; border:1px solid #ddd; font-weight:700;">₹5,000</td>
          <td style="padding:.8rem; border:1px solid #ddd; font-weight:700;">₹6,000</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f8f9fa; font-weight:600;">Hoarding</td>
          <td style="padding:.8rem; border:1px solid #ddd; font-weight:700;">₹5,000</td>
          <td style="padding:.8rem; border:1px solid #ddd; font-weight:700;">₹6,000</td></tr>
    </table>
  </div>
  <p style="color: #6c757d; margin: 1rem 0 0 0; font-size: .85rem; font-style: italic;">
    *For bookings at ₹5850/sq.ft. and above*
  </p>
</div>
""", unsafe_allow_html=True)

# --- Rate-Based Payout ---
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
           padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;
           border: 2px solid #20c997; text-align: center;">
  <h4 style="color: #20c997; margin: 0 0 1rem 0; font-weight: 700;">📊 Rate-Based Payout E and F</h4>
  <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    <table style="width: 100%; text-align: center; border-collapse: collapse;">
      <tr style="background: #20c997; color: white;">
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">Rate Slab</th>
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">Payout %</th>
      </tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#d4edda; font-weight:600;">₹5950+</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#28a745; font-weight:700; font-size:1.1rem;">100%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#fff3cd; font-weight:600;">₹5900–₹5949</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#fd7e14; font-weight:700;">70%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f8d7da; font-weight:600;">₹5850–₹5899</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#dc3545; font-weight:700;">40%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f1f3f4; font-weight:600;">Below ₹5850</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#6c757d; font-weight:700;">0%</td></tr>
    </table>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Rate-Based Payout ---
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
           padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;
           border: 2px solid #20c997; text-align: center;">
  <h4 style="color: #20c997; margin: 0 0 1rem 0; font-weight: 700;">📊 Rate-Based Payout C</h4>
  <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    <table style="width: 100%; text-align: center; border-collapse: collapse;">
      <tr style="background: #20c997; color: white;">
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">Rate Slab</th>
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">Payout %</th>
      </tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#d4edda; font-weight:600;">₹6325+</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#28a745; font-weight:700; font-size:1.1rem;">100%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#fff3cd; font-weight:600;">₹6300–₹6324</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#fd7e14; font-weight:700;">70%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f8d7da; font-weight:600;">₹6275–₹6299</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#dc3545; font-weight:700;">40%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f1f3f4; font-weight:600;">Below ₹6275</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#6c757d; font-weight:700;">0%</td></tr>
    </table>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Count-Based Payout ---
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
           padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;
           border: 2px solid #6f42c1; text-align: center;">
  <h4 style="color: #6f42c1; margin: 0 0 1rem 0; font-weight: 700;">📈 Count-Based Payout</h4>
  <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    <table style="width: 100%; text-align: center; border-collapse: collapse;">
      <tr style="background: #6f42c1; color: white;">
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">Units Sold</th>
        <th style="padding: .8rem; border: 1px solid #ddd; font-weight: 600;">Payout %</th>
      </tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#d4edda; font-weight:600;">12+ Units</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#28a745; font-weight:700; font-size:1.1rem;">100%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#fff3cd; font-weight:600;">10–11 Units</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#fd7e14; font-weight:700;">70%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f8d7da; font-weight:600;">8–9 Units</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#dc3545; font-weight:700;">40%</td></tr>
      <tr><td style="padding:.8rem; border:1px solid #ddd; background:#f1f3f4; font-weight:600;">Below 8</td>
          <td style="padding:.8rem; border:1px solid #ddd; color:#6c757d; font-weight:700;">0%</td></tr>
    </table>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------
# Bonus Incentives
# -----------------------
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); 
           padding: 1.5rem; border-radius: 12px; margin: 1.2rem 0 1rem 0; 
           box-shadow: 0 6px 12px rgba(220, 53, 69, 0.3); text-align: center;">
    <h3 style="color: white; margin: 0; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
        🏆 BONUS INCENTIVES 🎯
    </h3>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
        Extra Rewards for High Performers!
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
           padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;
           box-shadow: 0 4px 8px rgba(40, 167, 69, 0.2); text-align: center;">
  <h4 style="color: white; margin: 0 0 0.8rem 0; font-weight: 700;">🥇 TOP SELLER BONUS</h4>
  <div style="background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 8px;">
    <p style="color: #28a745; font-weight: 700; font-size: 1.05rem; margin: 0;">
      Book 20+ units → Extra ₹1,000 per unit
    </p>
    <p style="color: #6c757d; font-size: 0.85rem; margin: 0.5rem 0 0 0; font-style: italic;">
      Applied to your total booking count
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #007bff 0%, #6610f2 100%); 
           padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;
           box-shadow: 0 4px 8px rgba(0, 123, 255, 0.2); text-align: center;">
  <h4 style="color: white; margin: 0 0 0.8rem 0; font-weight: 700;">👥 TEAM ACHIEVEMENT BONUS</h4>
  <div style="background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 8px;">
    <p style="color: #007bff; font-weight: 700; font-size: 1.05rem; margin: 0;">
      Team crosses 60 units → ₹50,000 shared
    </p>
    <p style="color: #6c757d; font-size: 0.85rem; margin: 0.5rem 0 0 0; font-style: italic;">
      Divided among executives with 12+ bookings
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #fd7e14 0%, #e63946 100%); 
           padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;
           box-shadow: 0 4px 8px rgba(253, 126, 20, 0.2); text-align: center;">
  <h4 style="color: white; margin: 0 0 0.8rem 0; font-weight: 700;">⭐ HIGH RATE BONUS</h4>
  <div style="background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 8px;">
    <p style="color: #fd7e14; font-weight: 700; font-size: 1.05rem; margin: 0;">
      Avg rate > ₹6000/sq.ft. for E and F and Avg rate > ₹6325/sq.ft. for C + 18 units
    </p>
    <p style="color: #e63946; font-weight: 800; font-size: 1.15rem; margin: 0.5rem 0;">
      → ₹1,00,000 BONUS!
    </p>
    <p style="color: #6c757d; font-size: 0.85rem; margin: 0.5rem 0 0 0; font-style: italic;">
      The ultimate achievement
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Footer ---
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%); 
           padding: 1.5rem; border-radius: 12px; margin: 1rem 0; 
           box-shadow: 0 6px 12px rgba(111, 66, 193, 0.3); text-align: center;">
  <h4 style="color: white; margin: 0 0 0.5rem 0; font-weight: 800; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
    💫 UNLOCK YOUR POTENTIAL! 💫
  </h4>
  <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem; font-style: italic;">
    Every booking brings you closer to your goals!
  </p>
</div>
""", unsafe_allow_html=True)

# ================= TAB 6 — CP Payout Expenditure (Supabase version) =================
