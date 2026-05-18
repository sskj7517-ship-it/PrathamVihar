# This file was moved out of main.py to keep the app lighter.
# It is executed by main.py with the same app globals, so existing logic stays unchanged.

import pandas as pd
from fpdf import FPDF

BOOKING_TABLE = "bookings"  # change this only if your Supabase booking table has another name

# ---------- THEME ----------
st.markdown("""
<style>
  :root{
    --ink:#0f172a; --muted:#475569; --border:#e2e8f0; --bg:#ffffff; --soft:#f8fafc;
    --card:#ffffff; --accent:#2563eb; --accent2:#6366f1; --ok:#10b981; --warn:#f59e0b;
  }
  .pane{
    border:1px solid var(--border);
    background:var(--card);
    border-radius:16px;
    padding:16px;
    margin:14px 0;
    box-shadow:0 8px 18px rgba(15,23,42,.06);
  }
  .title{
    display:flex;
    align-items:center;
    gap:8px;
    font-weight:900;
    font-size:20px;
    color:var(--ink);
    margin-bottom:6px;
  }
  .sub{
    color:var(--muted);
    font-size:13px;
    margin-top:-4px;
    margin-bottom:10px;
  }
  .chips{
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    margin:8px 0 2px 0;
  }
  .chip{
    display:inline-flex;
    align-items:center;
    gap:6px;
    padding:6px 10px;
    border:1px solid var(--border);
    border-radius:999px;
    background:var(--soft);
    font-size:12px;
    font-weight:700;
    color:var(--ink);
  }
  .chip .dot{
    width:8px;
    height:8px;
    border-radius:999px;
    background:var(--accent2);
  }
  .chip.ok .dot{background:var(--ok);}
  .chip.warn .dot{background:var(--warn);}
  .styled-table{
    border-collapse:collapse;
    width:100%;
    border-radius:12px;
    overflow:hidden;
    box-shadow:0 4px 10px rgba(0,0,0,.08);
    margin:12px 0;
  }
  .styled-table th{
    background:var(--accent);
    color:#fff;
    text-align:left;
    padding:10px;
    font-size:14px;
  }
  .styled-table td{
    padding:10px;
    font-size:13px;
    border-bottom:1px solid #e2e8f0;
    vertical-align:top;
  }
  .styled-table tr:nth-child(even){background:#f8fafc;}
  div[data-testid="stDownloadButton"] > button{
    background:linear-gradient(135deg,#06b6d4 0%,#6366f1 100%) !important;
    color:#fff !important;
    border:0 !important;
    border-radius:12px !important;
    font-weight:800 !important;
    padding:10px 14px !important;
  }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def _norm_col(c: str) -> str:
    return (
        str(c or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

def _find_col(df_in: pd.DataFrame, candidates: list[str]):
    if df_in is None or df_in.empty:
        return None

    col_map = {_norm_col(c): c for c in df_in.columns}

    for cand in candidates:
        key = _norm_col(cand)
        if key in col_map:
            return col_map[key]

    return None

def _clean_display_value(v):
    if pd.isna(v):
        return ""
    s = str(v).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def _safe_pdf_text(s):
    s = str(s or "")
    replacements = {
        "₹": "Rs ",
        "—": "-",
        "–": "-",
        "•": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    return s.encode("latin1", "ignore").decode("latin1")

def _safe_filename(s):
    s = str(s or "").strip()
    for ch in '\\/:*?"<>|':
        s = s.replace(ch, "")
    return " ".join(s.split()) or "Civil_Changes"

@st.cache_data(ttl=180, show_spinner=False)
def _t8_load_booking_df(cache_buster: int = 0) -> pd.DataFrame:
    # Prefer already-loaded dataframe from your app
    if "sheet_df" in globals() and isinstance(sheet_df, pd.DataFrame) and not sheet_df.empty:
        return sheet_df.copy()

    if "booking_df" in globals() and isinstance(booking_df, pd.DataFrame) and not booking_df.empty:
        return booking_df.copy()

    if "df" in globals() and isinstance(df, pd.DataFrame) and not df.empty:
        return df.copy()

    # Supabase fallback
    try:
        res = supabase.table(BOOKING_TABLE).select("*").execute()
        return pd.DataFrame(res.data or [])
    except Exception:
        return pd.DataFrame()

# ---------- Connectivity checks ----------
if "t8_cache_buster" not in st.session_state:
    st.session_state["t8_cache_buster"] = 0

if "supabase_connected" in globals() and not supabase_connected:
    st.warning("📋 Please connect to Supabase to use this feature.")
    st.stop()

sheet_df_t8 = _t8_load_booking_df(st.session_state["t8_cache_buster"])

if sheet_df_t8.empty:
    st.info("No booking data found.")
    st.stop()

# ---------- Column detection ----------
wing_col = _find_col(sheet_df_t8, ["Wing", "wing"])
floor_col = _find_col(sheet_df_t8, ["Floor", "floor"])
flat_col = _find_col(sheet_df_t8, ["Flat Number", "flat_number", "Flat No", "flat_no"])
civil_col = _find_col(sheet_df_t8, ["Civil Changes", "civil_changes"])

missing_cols = []
if not wing_col:
    missing_cols.append("Wing")
if not floor_col:
    missing_cols.append("Floor")
if not flat_col:
    missing_cols.append("Flat Number")
if not civil_col:
    missing_cols.append("Civil Changes")

if missing_cols:
    st.error(f"❌ Required columns missing in booking data: {', '.join(missing_cols)}")
    st.stop()

# ============================================================
# CIVIL CHANGES LOOKUP
# ============================================================
st.markdown(
    '<div class="title">🏗️ Civil Changes Lookup</div>'
    '<div class="sub">Filter by Wing & Floor, view only rows with Civil Changes filled.</div>',
    unsafe_allow_html=True
)

# ---------- Dropdown options ----------
wing_values = (
    sheet_df_t8[wing_col]
    .dropna()
    .map(_clean_display_value)
    .loc[lambda s: s.str.strip().ne("")]
    .unique()
    .tolist()
)

floor_values = (
    sheet_df_t8[floor_col]
    .dropna()
    .map(_clean_display_value)
    .loc[lambda s: s.str.strip().ne("")]
    .unique()
    .tolist()
)

wings = ["All"] + sorted(wing_values, key=lambda x: str(x))
floors = ["All"] + sorted(floor_values, key=lambda x: str(x))

c1, c2 = st.columns(2)

with c1:
    selected_wing = st.selectbox(
        "Select Wing",
        wings,
        key="t8_cc_wing"
    )

with c2:
    selected_floor = st.selectbox(
        "Select Floor",
        floors,
        key="t8_cc_floor"
    )

# ---------- Filtering ----------
filtered_df = sheet_df_t8.copy()

filtered_df["_WingClean"] = filtered_df[wing_col].map(_clean_display_value)
filtered_df["_FloorClean"] = filtered_df[floor_col].map(_clean_display_value)
filtered_df["_FlatClean"] = filtered_df[flat_col].map(_clean_display_value)
filtered_df["_CivilClean"] = filtered_df[civil_col].fillna("").astype(str).str.strip()

if selected_wing != "All":
    filtered_df = filtered_df[filtered_df["_WingClean"] == str(selected_wing)]

if selected_floor != "All":
    filtered_df = filtered_df[filtered_df["_FloorClean"] == str(selected_floor)]

result_df = filtered_df[filtered_df["_CivilClean"].ne("")].copy()

st.markdown(
    f'<div class="chips">'
    f'<span class="chip"><span class="dot"></span> Wing: {selected_wing}</span>'
    f'<span class="chip"><span class="dot"></span> Floor: {selected_floor}</span>'
    f'<span class="chip ok"><span class="dot"></span> Matches: {len(result_df)}</span>'
    f'</div>',
    unsafe_allow_html=True
)

# ---------- Output ----------
if result_df.empty:
    st.warning("No Civil Changes data available for selected criteria.")
else:
    display_df = result_df[["_FlatClean", "_CivilClean"]].copy()
    display_df = display_df.rename(columns={
        "_FlatClean": "Flat Number",
        "_CivilClean": "Civil Changes"
    })

    st.markdown('<div class="pane">', unsafe_allow_html=True)
    st.markdown("### 🧾 Civil Changes Table")
    st.markdown(
        display_df.to_html(index=False, classes="styled-table", escape=True),
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- PDF ----------
    def create_pdf(df_pdf: pd.DataFrame) -> bytes:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        page_w = pdf.w - pdf.l_margin - pdf.r_margin

        pdf.set_font("Arial", "B", 13)
        title = f"Civil Changes - Wing: {selected_wing}, Floor: {selected_floor}"
        pdf.cell(0, 10, _safe_pdf_text(title), ln=True, align="C")
        pdf.ln(4)

        col_flat = 40
        col_change = page_w - col_flat
        line_h = 5.5

        def write_header():
            pdf.set_font("Arial", "B", 10)
            pdf.set_fill_color(37, 99, 235)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(col_flat, 8, "Flat Number", border=1, align="C", fill=True)
            pdf.cell(col_change, 8, "Civil Changes", border=1, align="C", fill=True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0)

        def split_lines(text, width):
            text = _safe_pdf_text(text)
            words = text.split()
            lines = []
            current = ""

            pdf.set_font("Arial", "", 9)

            for word in words:
                candidate = f"{current} {word}".strip()
                if pdf.get_string_width(candidate) <= width:
                    current = candidate
                else:
                    if current:
                        lines.append(current)
                    current = word

            if current:
                lines.append(current)

            return lines or [""]

        write_header()

        pdf.set_font("Arial", "", 9)

        for _, row in df_pdf.iterrows():
            flat = _safe_pdf_text(row.get("Flat Number", ""))
            changes = _safe_pdf_text(row.get("Civil Changes", ""))

            change_lines = split_lines(changes, col_change - 4)
            row_h = max(8, len(change_lines) * line_h + 3)

            if pdf.get_y() + row_h > pdf.h - pdf.b_margin:
                pdf.add_page()
                write_header()
                pdf.set_font("Arial", "", 9)

            x0 = pdf.get_x()
            y0 = pdf.get_y()

            pdf.rect(x0, y0, col_flat, row_h)
            pdf.rect(x0 + col_flat, y0, col_change, row_h)

            pdf.set_xy(x0 + 2, y0 + 2)
            pdf.cell(col_flat - 4, line_h, flat, border=0, align="C")

            pdf.set_xy(x0 + col_flat + 2, y0 + 2)
            for line in change_lines:
                pdf.cell(col_change - 4, line_h, line, border=0, ln=True)

            pdf.set_xy(x0, y0 + row_h)

        out = pdf.output(dest="S")
        return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin1", "ignore")

    pdf_bytes = create_pdf(display_df)

    file_name = _safe_filename(
        f"Civil_Changes_Wing_{selected_wing}_Floor_{selected_floor}.pdf"
    )

    st.download_button(
        label="📥 Download PDF",
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf",
        key="t8_cc_pdf"
    )
