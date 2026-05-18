import datetime
import re
from html import escape
from urllib.parse import quote

import pandas as pd
import altair as alt
import streamlit as st
import streamlit.components.v1 as components


FLOOR_TABLE = "construction_floor_progress"
FLAT_TABLE = "construction_flat_progress"

WINGS = [f"{w} Wing" for w in list("ABCDEFG")]
SERIES = [f"{i:02d}" for i in range(1, 11)]

FLOOR_LEVELS = [
    {"level_code": "BASEMENT", "level_label": "Basement", "floor_no": None, "display_order": 0},
    {"level_code": "GROUND", "level_label": "Ground", "floor_no": 0, "display_order": 1},
    {"level_code": "STILT", "level_label": "Stilt", "floor_no": 0, "display_order": 2},
] + [
    {"level_code": f"FLOOR_{i:02d}", "level_label": f"Floor {i}", "floor_no": i, "display_order": i + 2}
    for i in range(1, 14)
]

FLOOR_LEVELS_TOP_DOWN = [
    {"level_code": f"FLOOR_{i:02d}", "level_label": f"Floor {i}", "floor_no": i, "display_order": i + 2}
    for i in range(13, 0, -1)
] + [
    {"level_code": "STILT", "level_label": "Stilt", "floor_no": 0, "display_order": 2},
    {"level_code": "GROUND", "level_label": "Ground", "floor_no": 0, "display_order": 1},
    {"level_code": "BASEMENT", "level_label": "Basement", "floor_no": None, "display_order": 0},
]


RCC_CHECKPOINTS = [
    ("Line out & wooden thesi", "rcc_line_out_wooden_thesi"),
    ("Column Steel binding work", "rcc_column_steel_binding_work"),
    ("Columns Distribution Stirrups", "rcc_columns_distribution_stirrups"),
    ("Beams Reinforcement work", "rcc_beams_reinforcement_work"),
    ("Aluform Vertical Shuttering work", "rcc_aluform_vertical_shuttering_work"),
    ("Electrical Concealed boxes fixing", "rcc_electrical_concealed_boxes_fixing"),
    ("Aluform Horizontal shuttering work", "rcc_aluform_horizontal_shuttering_work"),
    ("Slab & Wall Conduit work", "rcc_slab_wall_conduit_work"),
    ("Sleeves fixing as per requirements", "rcc_sleeves_fixing_as_per_requirements"),
    ("Slab Reinforcement work", "rcc_slab_reinforcement_work"),
    ("Support work for Aluform shuttering", "rcc_support_work_for_aluform_shuttering"),
    ("Sunksides for Toilet & Terrace", "rcc_sunksides_for_toilet_terrace"),
    ("Cover blocks as per requirement", "rcc_cover_blocks_as_per_requirement"),
    ("RCC Consultant Checking", "rcc_consultant_checking"),
    ("MEP Consultant Checking", "rcc_mep_consultant_checking"),
    ("Architect Checking", "rcc_architect_checking"),
    ("Levelling of slab / Terrace / Toilet Gala", "rcc_levelling_of_slab_terrace_toilet_gala"),
    ("Pour casting as per drawing", "rcc_pour_casting_as_per_drawing"),
    ("After casting - Curing & Ponding", "rcc_after_casting_curing_ponding"),
    ("Tie patti / Tie Rod holes filling for Previous slab", "rcc_tie_patti_tie_rod_holes_filling_for_previous_slab"),
    ("Tachya / Hacking as per requirement", "rcc_tachya_hacking_as_per_requirement"),
    ("Grinding / Excess Concrete chipping if any", "rcc_grinding_excess_concrete_chipping_if_any"),
]

FLAT_WORKS = [
    {
        "main": "AAC Blockwork",
        "sections": {
            "General": [
                ("DPC Layout as per Approved Practice", "aac_dpc_layout_as_per_approved_practice"),
                ("ACC blockwork with block jointing mortar", "aac_blockwork_with_block_jointing_mortar"),
                ("Patli / RCC band in middle of wall", "aac_patli_rcc_band_in_middle_of_wall"),
                ("Above Patli AAC block work up to lintel", "aac_above_patli_blockwork_up_to_lintel"),
                ("Chemical Consumption", "aac_chemical_consumption"),
                ("Cement Consumption", "aac_cement_consumption"),
                ("Gap above Last layer & Beam Bottom proper filling", "aac_gap_above_last_layer_beam_bottom_filling"),
                ("Curing & Date marking after work completion", "aac_curing_date_marking_after_completion"),
            ]
        },
    },
    {
        "main": "Internal Plaster",
        "sections": {
            "General": [
                ("Internal Plaster Thiyya", "internal_plaster_thiyya"),
                ("Check for Concealed Electrical work", "internal_plaster_check_concealed_electrical_work"),
                ("Fibre mesh application on RCC & AAC Block Joint", "internal_plaster_fibre_mesh_rcc_aac_joint"),
                ("Fibre mesh application on Electrical Conduit Pipe", "internal_plaster_fibre_mesh_electrical_conduit_pipe"),
                ("Internal Plaster work", "internal_plaster_work"),
                ("Check Opening in Plaster", "internal_plaster_check_opening"),
            ]
        },
    },
    {
        "main": "Concealed Electrical Work",
        "sections": {
            "General": [
                ("Level marking on Wall", "concealed_electrical_level_marking_on_wall"),
                ("Marking & fixing of modular boxes", "concealed_electrical_marking_fixing_modular_boxes"),
                ("Wall cutting & Conduit Pipe fixing", "concealed_electrical_wall_cutting_conduit_pipe_fixing"),
            ]
        },
    },
    {
        "main": "Ceiling Gypsum Work",
        "sections": {
            "General": [
                ("Chemical Application for Ceiling", "ceiling_gypsum_chemical_application"),
                ("Dhada marking In Kach (Corners of Slab & Beam)", "ceiling_gypsum_dhada_marking_kach"),
                ("Ceiling Punning with 4-5mm gypsum with proper finish", "ceiling_gypsum_punning_proper_finish"),
            ]
        },
    },
    {
        "main": "Wall Gypsum Work",
        "sections": {
            "General": [
                ("Chemical Application for RCC beam/Column", "wall_gypsum_chemical_application_rcc_beam_column"),
                ("Diagonal making & Tikki marking on wall", "wall_gypsum_diagonal_tikki_marking"),
                ("Dhada marking on wall", "wall_gypsum_dhada_marking"),
                ("Wall Punning with proper finishing", "wall_gypsum_punning_proper_finish"),
            ]
        },
    },
    {
        "main": "Toilet Waterproofing Work",
        "sections": {
            "Common Toilet": [
                ("Cleaning of toilet", "toilet_common_cleaning"),
                ("Filling of cracks with Cement & Chemical", "toilet_common_crack_filling"),
                ("Kach khadi with 4 inch chemical coat", "toilet_common_kach_khadi_chemical_coat"),
                ("2 coat chemical", "toilet_common_2_coat_chemical"),
                ("Basecoat in 1:6 Cement mortar", "toilet_common_basecoat_cement_mortar"),
                ("Brickbat in 1:6 Cement mortar", "toilet_common_brickbat_cement_mortar"),
                ("Waterproofing finishing in 1:6 cement mortar", "toilet_common_waterproofing_finishing"),
            ],
            "Master Toilet": [
                ("Cleaning of toilet", "toilet_master_cleaning"),
                ("Filling of cracks with Cement & Chemical", "toilet_master_crack_filling"),
                ("Kach khadi with 4 inch chemical coat", "toilet_master_kach_khadi_chemical_coat"),
                ("2 coat chemical", "toilet_master_2_coat_chemical"),
                ("Basecoat in 1:6 Cement mortar", "toilet_master_basecoat_cement_mortar"),
                ("Brickbat in 1:6 Cement mortar", "toilet_master_brickbat_cement_mortar"),
                ("Waterproofing finishing in 1:6 cement mortar", "toilet_master_waterproofing_finishing"),
            ],
        },
    },
    {
        "main": "Dry Terrace / Terrace Waterproofing",
        "sections": {
            "Balcony": [
                ("Cleaning of terrace", "terrace_balcony_cleaning"),
                ("Filling of cracks with Cement & Chemical", "terrace_balcony_crack_filling"),
                ("Kach khadi with 4 inch chemical coat", "terrace_balcony_kach_khadi_chemical_coat"),
                ("2 coat chemical", "terrace_balcony_2_coat_chemical"),
                ("Brickbat in 1:6 Cement mortar", "terrace_balcony_brickbat_cement_mortar"),
                ("Waterproofing finishing in 1:6 cement mortar", "terrace_balcony_waterproofing_finishing"),
            ],
            "Dry Balcony": [
                ("Cleaning of terrace", "terrace_dry_balcony_cleaning"),
                ("Filling of cracks with Cement & Chemical", "terrace_dry_balcony_crack_filling"),
                ("Kach khadi with 4 inch chemical coat", "terrace_dry_balcony_kach_khadi_chemical_coat"),
                ("2 coat chemical", "terrace_dry_balcony_2_coat_chemical"),
                ("Brickbat in 1:6 Cement mortar", "terrace_dry_balcony_brickbat_cement_mortar"),
                ("Waterproofing finishing in 1:6 cement mortar", "terrace_dry_balcony_waterproofing_finishing"),
            ],
        },
    },
    {
        "main": "Kitchen Platform Tile Work",
        "sections": {
            "General": [
                ("Level marking inside flat", "kitchen_platform_level_marking_inside_flat"),
                ("Marking of Vertical & Horizontal kadappa on wall", "kitchen_platform_marking_vertical_horizontal_kadappa"),
                ("Fixing of Vertical & horizontal kadappa", "kitchen_platform_fixing_vertical_horizontal_kadappa"),
                ("Granite Top fixing with sink", "kitchen_platform_granite_top_fixing_with_sink"),
                ("Granite Skirting fixing of Cement tikki", "kitchen_platform_granite_skirting_cement_tikki"),
                ("Granite Vertical Fixing", "kitchen_platform_granite_vertical_fixing"),
                ("Panera Piece Fixing at reqd level", "kitchen_platform_panera_piece_fixing"),
                ("Facia Patti fixing", "kitchen_platform_facia_patti_fixing"),
            ]
        },
    },
]

WORKS = [{"main": "RCC Work", "scope": "floor", "sections": {"Slab": RCC_CHECKPOINTS}}] + [
    {**w, "scope": "flat"} for w in FLAT_WORKS
]
WORK_BY_NAME = {w["main"]: w for w in WORKS}
FLOOR_DATE_COLS = [col for _, col in RCC_CHECKPOINTS]
FLAT_DATE_COLS = [col for work in FLAT_WORKS for checkpoints in work["sections"].values() for _, col in checkpoints]


def _safe_str(x):
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


def _to_int(x, default=0):
    try:
        if pd.isna(x):
            return default
        return int(float(x))
    except Exception:
        return default


def _pct(done, total):
    total = int(total or 0)
    if total <= 0:
        return 0.0
    return max(0.0, min((float(done or 0) / total) * 100.0, 100.0))


def _fmt_pct(x):
    try:
        return f"{float(x):.1f}%"
    except Exception:
        return "0.0%"


def _is_done(row, col):
    return _safe_str(row.get(col, "")) != ""


def _done_date(row, col):
    return _safe_str(row.get(col, ""))


def _date_iso(v):
    if isinstance(v, datetime.datetime):
        return v.date().isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    parsed = pd.to_datetime(v, errors="coerce")
    if pd.isna(parsed):
        return datetime.date.today().isoformat()
    return parsed.date().isoformat()


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def _unit_type(series, floor_no=None):
    if series == "COMMON":
        return "Common Area"
    if int(floor_no or 0) == 1 and series == "05":
        return "Society Office"
    if series in {"04", "05", "06", "07"}:
        return "1 BHK"
    return "2 BHK"


def _flat_number(floor_no, series):
    return f"{int(floor_no)}{series}"


def _flat_seed_rows():
    rows = []
    for wing in WINGS:
        for floor_no in range(1, 14):
            for idx, series in enumerate(SERIES, start=1):
                flat_no = _flat_number(floor_no, series)
                rows.append({
                    "wing": wing,
                    "floor_no": floor_no,
                    "flat_number": flat_no,
                    "series": series,
                    "unit_type": _unit_type(series, floor_no),
                    "display_order": idx,
                })
            rows.append({
                "wing": wing,
                "floor_no": floor_no,
                "flat_number": "COMMON",
                "series": "COMMON",
                "unit_type": "Common Area",
                "display_order": 99,
            })
    return rows


def _floor_seed_rows():
    rows = []
    for wing in WINGS:
        for level in FLOOR_LEVELS:
            rows.append({
                "wing": wing,
                "level_code": level["level_code"],
                "level_label": level["level_label"],
                "floor_no": level["floor_no"],
                "display_order": level["display_order"],
            })
    return rows


def _select_all(supabase_client, table_name):
    rows = []
    page_size = 1000
    start = 0
    while True:
        query = supabase_client.table(table_name).select("*")
        try:
            query = query.order("id")
        except Exception:
            pass
        res = query.range(start, start + page_size - 1).execute()
        batch = getattr(res, "data", None) or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return rows


def _insert_many(supabase_client, table_name, rows):
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        supabase_client.table(table_name).insert(rows[i:i + chunk_size]).execute()


def _load_table(supabase_client, table_name):
    try:
        return pd.DataFrame(_select_all(supabase_client, table_name)), None
    except Exception as e:
        return pd.DataFrame(), str(e)


def _ensure_floor_rows(supabase_client, df):
    df = df.copy()
    existing = set()
    if not df.empty:
        existing = set(zip(df["wing"].astype(str), df["level_code"].astype(str)))
    missing = [
        row for row in _floor_seed_rows()
        if (row["wing"], row["level_code"]) not in existing
    ]
    if missing:
        _insert_many(supabase_client, FLOOR_TABLE, missing)
        df, _ = _load_table(supabase_client, FLOOR_TABLE)
    return df


def _ensure_flat_rows(supabase_client, df):
    df = df.copy()
    existing = set()
    if not df.empty:
        existing = set(zip(df["wing"].astype(str), df["floor_no"].map(lambda x: _to_int(x)), df["flat_number"].astype(str)))
    missing = [
        row for row in _flat_seed_rows()
        if (row["wing"], row["floor_no"], row["flat_number"]) not in existing
    ]
    if missing:
        _insert_many(supabase_client, FLAT_TABLE, missing)
        df, _ = _load_table(supabase_client, FLAT_TABLE)
    return df


def _normalize_floor_df(df):
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    for col in ["id", "wing", "level_code", "level_label", "floor_no", "display_order"] + FLOOR_DATE_COLS:
        if col not in df.columns:
            df[col] = None
    df["display_order"] = df["display_order"].apply(_to_int)
    return df


def _normalize_flat_df(df):
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    for col in ["id", "wing", "floor_no", "flat_number", "series", "unit_type", "display_order"] + FLAT_DATE_COLS:
        if col not in df.columns:
            df[col] = None
    df["floor_no"] = df["floor_no"].apply(_to_int)
    df["display_order"] = df["display_order"].apply(_to_int)
    return df


def _work_columns(work):
    return [col for checkpoints in work["sections"].values() for _, col in checkpoints]


def _row_progress(row, cols):
    total = len(cols)
    done = sum(1 for col in cols if _is_done(row, col))
    return done, total, _pct(done, total)


def _rows_progress(rows, cols):
    if rows is None or rows.empty:
        return 0, 0, 0.0
    total = len(rows) * len(cols)
    done = 0
    for _, row in rows.iterrows():
        done += sum(1 for col in cols if _is_done(row, col))
    return done, total, _pct(done, total)


def _parse_done_dates(row, cols):
    dates = []
    for col in cols:
        val = _safe_str(row.get(col, ""))
        if not val:
            continue
        parsed = pd.to_datetime(val, errors="coerce")
        if pd.notna(parsed):
            dates.append(parsed.normalize())
    return dates


def _level_date_summary(floor_df, flat_df, wing, level):
    dates = []
    floor_row = _floor_row(floor_df, wing, level["level_code"])
    if not floor_row.empty:
        dates.extend(_parse_done_dates(floor_row, FLOOR_DATE_COLS))

    floor_no = level.get("floor_no")
    if floor_no and int(floor_no) >= 1:
        rows = _flat_rows(flat_df, wing, floor_no)
        for _, row in rows.iterrows():
            dates.extend(_parse_done_dates(row, FLAT_DATE_COLS))

    if not dates:
        return "", "", 0

    first = min(dates)
    latest = max(dates)
    return first.date().isoformat(), latest.date().isoformat(), int((latest - first).days)


def _work_progress_for_wing(floor_df, flat_df, wing, work):
    if work["scope"] == "floor":
        rows = floor_df[floor_df["wing"] == wing].copy()
        return _rows_progress(rows, _work_columns(work))

    rows = flat_df[flat_df["wing"] == wing].copy()
    return _rows_progress(rows, _work_columns(work))


def _wing_overall_progress(floor_df, flat_df, wing):
    floor_rows = floor_df[floor_df["wing"] == wing].copy()
    flat_rows = flat_df[flat_df["wing"] == wing].copy()

    floor_done, floor_total, _ = _rows_progress(floor_rows, FLOOR_DATE_COLS)
    flat_done, flat_total, _ = _rows_progress(flat_rows, FLAT_DATE_COLS)
    return floor_done + flat_done, floor_total + flat_total, _pct(floor_done + flat_done, floor_total + flat_total)


def _dashboard_wing_rows(floor_df, flat_df):
    rows = []
    for wing in WINGS:
        done, total, pct = _wing_overall_progress(floor_df, flat_df, wing)
        rows.append({
            "Wing": wing,
            "Done": done,
            "Total": total,
            "Progress %": pct,
        })
    return pd.DataFrame(rows)


def _dashboard_work_rows(floor_df, flat_df, wing):
    rows = []
    for work in WORKS:
        done, total, pct = _work_progress_for_wing(floor_df, flat_df, wing, work)
        rows.append({
            "Main Work": work["main"],
            "Done": done,
            "Total": total,
            "Progress %": pct,
        })
    return pd.DataFrame(rows)


def _dashboard_level_rows(floor_df, flat_df, wing):
    rows = []
    for level in FLOOR_LEVELS_TOP_DOWN:
        report_rows = _level_report_rows(floor_df, flat_df, wing, level)
        total = sum(int(r["Total"]) for r in report_rows)
        done = sum(int(r["Done"]) for r in report_rows)
        first_date, latest_date, duration_days = _level_date_summary(floor_df, flat_df, wing, level)
        rows.append({
            "Level": level["level_label"],
            "Done": done,
            "Total": total,
            "Progress %": _pct(done, total),
            "First Date": first_date,
            "Latest Date": latest_date,
            "Duration Days": duration_days,
        })
    return pd.DataFrame(rows)


def _floor_row(floor_df, wing, level_code):
    sub = floor_df[(floor_df["wing"] == wing) & (floor_df["level_code"] == level_code)]
    if sub.empty:
        return pd.Series(dtype=object)
    return sub.iloc[0]


def _flat_rows(flat_df, wing, floor_no):
    return flat_df[(flat_df["wing"] == wing) & (flat_df["floor_no"] == int(floor_no))].copy()


def _work_progress_for_level(floor_df, flat_df, wing, level, work):
    if work["scope"] == "floor":
        row = _floor_row(floor_df, wing, level["level_code"])
        if row.empty:
            return 0, len(FLOOR_DATE_COLS), 0.0
        return _row_progress(row, _work_columns(work))

    floor_no = level.get("floor_no")
    if not floor_no or int(floor_no) < 1:
        return 0, 0, 0.0

    rows = _flat_rows(flat_df, wing, floor_no)
    cols = _work_columns(work)
    total = len(rows) * len(cols)
    done = 0
    for _, row in rows.iterrows():
        done += sum(1 for col in cols if _is_done(row, col))
    return done, total, _pct(done, total)


def _level_report_rows(floor_df, flat_df, wing, level):
    rows = []
    for work in WORKS:
        done, total, pct = _work_progress_for_level(floor_df, flat_df, wing, level, work)
        if total <= 0:
            continue
        rows.append({
            "Main Work": work["main"],
            "Done": done,
            "Total": total,
            "Progress %": pct,
        })
    return rows


def _level_progress(floor_df, flat_df, wing, level):
    rows = _level_report_rows(floor_df, flat_df, wing, level)
    if not rows:
        return 0.0
    return sum(float(r["Progress %"]) for r in rows) / len(rows)


def _flat_report_rows(row):
    rows = []
    for work in FLAT_WORKS:
        cols = _work_columns({**work, "scope": "flat"})
        done, total, pct = _row_progress(row, cols)
        rows.append({
            "Main Work": work["main"],
            "Done": done,
            "Total": total,
            "Progress %": pct,
        })
    return rows


def _flat_progress(row):
    total = 0
    done = 0
    for work in FLAT_WORKS:
        cols = _work_columns({**work, "scope": "flat"})
        total += len(cols)
        done += sum(1 for col in cols if _is_done(row, col))
    return _pct(done, total)


def _tone(pct):
    pct = float(pct or 0)
    if pct >= 99.9:
        return "cp-done"
    if pct >= 75:
        return "cp-good"
    if pct >= 50:
        return "cp-mid"
    if pct >= 25:
        return "cp-low"
    if pct > 0:
        return "cp-start"
    return "cp-zero"


def _report_html(title, rows):
    tr = []
    for row in rows:
        tr.append(
            "<tr>"
            f"<td>{escape(str(row['Main Work']))}</td>"
            f"<td>{int(row['Done'])}/{int(row['Total'])}</td>"
            f"<td>{_fmt_pct(row['Progress %'])}</td>"
            "</tr>"
        )
    return (
        f"<h3>{escape(str(title))}</h3>"
        "<table class='cp-report-table'>"
        "<thead><tr><th>Main Work</th><th>Done</th><th>Progress</th></tr></thead>"
        f"<tbody>{''.join(tr)}</tbody></table>"
    )


def _widget_css():
    return """
    <style>
    .cp-shell{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px;color:#0f172a}
    .cp-topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}
    .cp-title{font-size:20px;font-weight:900}
    .cp-btn{border:0;border-radius:10px;padding:8px 12px;background:#2563eb;color:#fff;font-weight:800;cursor:pointer}
    .cp-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 14px}
    .cp-tab{border:1px solid #cbd5e1;background:#f8fafc;color:#0f172a;border-radius:999px;padding:7px 12px;font-weight:900;cursor:pointer}
    .cp-tab.active{background:#0f172a;color:#fff;border-color:#0f172a}
    .cp-panel{display:none}.cp-panel.active{display:block}
    .cp-building-core{max-width:920px;margin:0 auto;background:linear-gradient(90deg,#e2e8f0 0,#f8fafc 8%,#fff 50%,#f8fafc 92%,#e2e8f0 100%);border:4px solid #94a3b8;border-radius:14px;padding:10px 12px 14px;box-shadow:0 18px 40px rgba(15,23,42,.12)}
    .cp-building-roof{height:18px;background:#475569;border-radius:12px 12px 4px 4px;margin:0 auto 8px;max-width:760px}
    .cp-building-row{display:grid;grid-template-columns:110px 1fr 70px;gap:10px;align-items:center;border:1px solid #cbd5e1;border-radius:4px;padding:8px;margin-bottom:5px;cursor:pointer;background:#f8fafc;box-shadow:inset 0 0 0 1px rgba(255,255,255,.55)}
    .cp-building-row:hover,.cp-cell:hover{outline:3px solid rgba(37,99,235,.18)}
    .cp-level{font-size:13px;font-weight:900}.cp-bar{height:18px;background:#e5e7eb;border-radius:999px;overflow:hidden}.cp-bar span{display:block;height:100%;border-radius:999px}.cp-pct{text-align:right;font-weight:900;font-size:13px}
    .cp-flat-grid{display:grid;grid-template-columns:72px repeat(11,minmax(68px,1fr));gap:6px;min-width:980px}
    .cp-flat-head{background:#0f172a;color:#fff;border-radius:8px;padding:8px 6px;text-align:center;font-size:12px;font-weight:900}
    .cp-floor-label{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:8px;padding:9px 6px;text-align:center;font-weight:900;font-size:12px}
    .cp-cell{min-height:58px;border-radius:8px;padding:7px 5px;text-align:center;font-size:12px;font-weight:900;cursor:pointer;border:1px solid rgba(15,23,42,.08);display:flex;flex-direction:column;justify-content:center;gap:3px}
    .cp-cell small{font-size:10px;font-weight:800}
    .cp-done span,.cp-good span,.cp-mid span,.cp-low span,.cp-start span,.cp-zero span{background:currentColor}
    .cp-done{background:#dcfce7;color:#166534}.cp-good{background:#ccfbf1;color:#0f766e}.cp-mid{background:#dbeafe;color:#1d4ed8}.cp-low{background:#fef3c7;color:#92400e}.cp-start{background:#ffedd5;color:#c2410c}.cp-zero{background:#f8fafc;color:#475569}
    .cp-modal{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(15,23,42,.58);z-index:99999}.cp-modal.active{display:flex}
    .cp-modal-card{background:#fff;width:min(760px,94vw);max-height:82vh;overflow:auto;border-radius:16px;padding:18px;box-shadow:0 24px 70px rgba(0,0,0,.30)}
    .cp-modal-top{display:flex;justify-content:flex-end;margin-bottom:8px}.cp-close{border:0;border-radius:8px;background:#0f172a;color:#fff;padding:7px 11px;font-weight:900;cursor:pointer}
    .cp-report-table{width:100%;border-collapse:collapse;font-size:14px}.cp-report-table th{background:#2563eb;color:#fff;padding:9px;text-align:left}.cp-report-table td{border-bottom:1px solid #e2e8f0;padding:9px}
    #cpFloorWidget:fullscreen,#cpFlatWidget:fullscreen{background:#fff;width:100vw;height:100vh;overflow:auto;padding:18px;box-sizing:border-box}
    </style>
    """


def _widget_js(widget_id):
    return f"""
    <script>
    function cpShowPanel(prefix,id,btn){{
        document.querySelectorAll('.'+prefix+'-panel').forEach(el=>el.classList.remove('active'));
        document.querySelectorAll('.'+prefix+'-tab').forEach(el=>el.classList.remove('active'));
        document.getElementById(id).classList.add('active');
        btn.classList.add('active');
    }}
    function cpOpenReport(encoded){{
        document.getElementById('{widget_id}_body').innerHTML=decodeURIComponent(encoded);
        document.getElementById('{widget_id}_modal').classList.add('active');
    }}
    function cpCloseReport(){{document.getElementById('{widget_id}_modal').classList.remove('active');}}
    function cpOpenFullScreen(){{
        const elem=document.getElementById('{widget_id}');
        if(elem.requestFullscreen){{elem.requestFullscreen();}}
        else if(elem.webkitRequestFullscreen){{elem.webkitRequestFullscreen();}}
        else if(elem.msRequestFullscreen){{elem.msRequestFullscreen();}}
    }}
    </script>
    """


def _build_floor_widget(floor_df, flat_df):
    tabs = []
    panels = []
    for idx, wing in enumerate(WINGS):
        panel_id = f"cp_floor_{wing[0]}"
        tabs.append(
            f"<button class='cp-tab cpfloor-tab {'active' if idx == 0 else ''}' onclick=\"cpShowPanel('cpfloor','{panel_id}',this)\">{escape(wing)}</button>"
        )
        level_rows = []
        for level in FLOOR_LEVELS_TOP_DOWN:
            pct = _level_progress(floor_df, flat_df, wing, level)
            report = _report_html(f"{wing} - {level['level_label']}", _level_report_rows(floor_df, flat_df, wing, level))
            level_rows.append(
                f"<div class='cp-building-row {_tone(pct)}' onclick=\"cpOpenReport('{quote(report)}')\">"
                f"<div class='cp-level'>{escape(level['level_label'])}</div>"
                f"<div class='cp-bar'><span style='width:{pct:.1f}%'></span></div>"
                f"<div class='cp-pct'>{pct:.1f}%</div></div>"
            )
        panels.append(
            f"<div id='{panel_id}' class='cp-panel cpfloor-panel {'active' if idx == 0 else ''}'>"
            f"<div class='cp-building-core'><div class='cp-building-roof'></div>{''.join(level_rows)}</div>"
            "</div>"
        )
    return f"""
    {_widget_css()}
    <div class="cp-shell" id="cpFloorWidget">
      <div class="cp-topbar"><div class="cp-title">Floor-wise Progress</div><button class="cp-btn" onclick="cpOpenFullScreen()">Open Full Screen</button></div>
      <div class="cp-tabs">{''.join(tabs)}</div>
      {''.join(panels)}
      <div class="cp-modal" id="cpFloorWidget_modal"><div class="cp-modal-card"><div class="cp-modal-top"><button class="cp-close" onclick="cpCloseReport()">Close</button></div><div id="cpFloorWidget_body"></div></div></div>
    </div>
    {_widget_js("cpFloorWidget")}
    """


def _build_flat_widget(flat_df):
    tabs = []
    panels = []
    headers = ["Floor"] + SERIES + ["Common"]
    header_html = "".join(f"<div class='cp-flat-head'>{escape(h)}</div>" for h in headers)
    for idx, wing in enumerate(WINGS):
        panel_id = f"cp_flat_{wing[0]}"
        tabs.append(
            f"<button class='cp-tab cpflat-tab {'active' if idx == 0 else ''}' onclick=\"cpShowPanel('cpflat','{panel_id}',this)\">{escape(wing)}</button>"
        )
        cells = [header_html]
        for floor_no in range(13, 0, -1):
            floor_rows = _flat_rows(flat_df, wing, floor_no).sort_values("display_order")
            by_series = {str(r["series"]): r for _, r in floor_rows.iterrows()}
            cells.append(f"<div class='cp-floor-label'>Floor {floor_no}</div>")
            for series in SERIES:
                row = by_series.get(series)
                if row is None:
                    cells.append("<div class='cp-cell cp-zero'>-</div>")
                    continue
                pct = _flat_progress(row)
                report = _report_html(f"{wing} - Flat {row['flat_number']} - Floor {floor_no}", _flat_report_rows(row))
                cells.append(
                    f"<div class='cp-cell {_tone(pct)}' onclick=\"cpOpenReport('{quote(report)}')\"><div>{escape(str(row['flat_number']))}</div><small>{pct:.1f}%</small></div>"
                )
            common = by_series.get("COMMON")
            if common is None:
                cells.append("<div class='cp-cell cp-zero'>Common</div>")
            else:
                pct = _flat_progress(common)
                report = _report_html(f"{wing} - Common Area - Floor {floor_no}", _flat_report_rows(common))
                cells.append(
                    f"<div class='cp-cell {_tone(pct)}' onclick=\"cpOpenReport('{quote(report)}')\"><div>Common</div><small>{pct:.1f}%</small></div>"
                )
        panels.append(f"<div id='{panel_id}' class='cp-panel cpflat-panel {'active' if idx == 0 else ''}'><div style='overflow:auto'><div class='cp-flat-grid'>{''.join(cells)}</div></div></div>")
    return f"""
    {_widget_css()}
    <div class="cp-shell" id="cpFlatWidget">
      <div class="cp-topbar"><div class="cp-title">Flat-wise Progress</div><button class="cp-btn" onclick="cpOpenFullScreen()">Open Full Screen</button></div>
      <div class="cp-tabs">{''.join(tabs)}</div>
      {''.join(panels)}
      <div class="cp-modal" id="cpFlatWidget_modal"><div class="cp-modal-card"><div class="cp-modal-top"><button class="cp-close" onclick="cpCloseReport()">Close</button></div><div id="cpFlatWidget_body"></div></div></div>
    </div>
    {_widget_js("cpFlatWidget")}
    """


def _card(title, value, sub=""):
    sub_html = f"<div style='font-size:12px;color:#64748b;font-weight:700;margin-top:6px'>{escape(str(sub))}</div>" if sub else ""
    st.markdown(
        f"""
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:13px 15px;min-height:92px;box-shadow:0 4px 14px rgba(15,23,42,.05);margin-bottom:10px">
          <div style="font-size:12px;color:#475569;text-transform:uppercase;font-weight:900;letter-spacing:.04em">{escape(str(title))}</div>
          <div style="font-size:26px;color:#0f172a;font-weight:900;margin-top:8px">{escape(str(value))}</div>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_construction_progress_tab(supabase_client):
    st.header("Construction Progress Tracking")

    st.markdown(
        """
        <style>
        .cp-section-title{margin:16px 0 10px;font-size:18px;font-weight:900;color:#0f172a}
        </style>
        """,
        unsafe_allow_html=True,
    )

    floor_df, floor_err = _load_table(supabase_client, FLOOR_TABLE)
    flat_df, flat_err = _load_table(supabase_client, FLAT_TABLE)

    if floor_err or flat_err:
        st.error(
            "Create the construction progress tables first using `supabase_construction_progress.sql`. "
            f"Floor table error: {floor_err or 'none'} | Flat table error: {flat_err or 'none'}"
        )
        return

    try:
        floor_df = _normalize_floor_df(_ensure_floor_rows(supabase_client, floor_df))
        flat_df = _normalize_flat_df(_ensure_flat_rows(supabase_client, flat_df))
    except Exception as e:
        st.error(f"Could not seed construction progress rows: {e}")
        return

    floor_done = int(sum(floor_df[col].fillna("").astype(str).str.strip().ne("").sum() for col in FLOOR_DATE_COLS))
    floor_total = len(floor_df) * len(FLOOR_DATE_COLS)
    flat_done = int(sum(flat_df[col].fillna("").astype(str).str.strip().ne("").sum() for col in FLAT_DATE_COLS))
    flat_total = len(flat_df) * len(FLAT_DATE_COLS)

    c1, c2, c3 = st.columns(3)
    with c1:
        _card("Rows Ready", f"{len(floor_df) + len(flat_df):,}", "Floor/slab rows + flat rows")
    with c2:
        _card("RCC Progress", _fmt_pct(_pct(floor_done, floor_total)), f"{floor_done:,}/{floor_total:,}")
    with c3:
        _card("Flat Work Progress", _fmt_pct(_pct(flat_done, flat_total)), f"{flat_done:,}/{flat_total:,}")

    dashboard_tab, slab_update_tab, flat_update_tab, floor_tab, flat_tab = st.tabs([
        "Dashboard",
        "Update Slab / RCC",
        "Update Flat Work",
        "Floor-wise Progress",
        "Flat-wise Progress",
    ])

    with dashboard_tab:
        st.markdown("<div class='cp-section-title'>Dashboard</div>", unsafe_allow_html=True)

        total_done = floor_done + flat_done
        total_possible = floor_total + flat_total
        wing_rows = _dashboard_wing_rows(floor_df, flat_df)

        dash_wing = st.selectbox("Select Wing", WINGS, key="cp_dash_wing")
        selected_wing_row = wing_rows[wing_rows["Wing"] == dash_wing].iloc[0]
        level_rows = _dashboard_level_rows(floor_df, flat_df, dash_wing)
        work_rows = _dashboard_work_rows(floor_df, flat_df, dash_wing)

        duration_rows = level_rows[level_rows["Duration Days"] > 0].copy()
        avg_duration = float(duration_rows["Duration Days"].mean()) if not duration_rows.empty else 0.0
        max_duration = int(duration_rows["Duration Days"].max()) if not duration_rows.empty else 0

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            _card("Overall Progress", _fmt_pct(_pct(total_done, total_possible)), f"{total_done:,}/{total_possible:,}")
        with d2:
            _card(f"{dash_wing} Progress", _fmt_pct(selected_wing_row["Progress %"]), f"{int(selected_wing_row['Done']):,}/{int(selected_wing_row['Total']):,}")
        with d3:
            _card("Avg Level Duration", f"{avg_duration:.1f} days", "First to latest completed checkpoint")
        with d4:
            _card("Max Level Duration", f"{max_duration} days", "Longest floor-wise date gap")

        st.markdown("<div class='cp-section-title'>Wing Progress</div>", unsafe_allow_html=True)
        wing_chart = alt.Chart(wing_rows).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Wing:N", title="Wing", sort=WINGS),
            y=alt.Y("Progress %:Q", title="Progress %", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Progress %:Q", scale=alt.Scale(scheme="tealblues"), legend=None),
            tooltip=["Wing:N", alt.Tooltip("Progress %:Q", format=".1f"), "Done:Q", "Total:Q"],
        ).properties(height=300)
        st.altair_chart(wing_chart, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='cp-section-title'>Main Work Progress</div>", unsafe_allow_html=True)
            work_chart = alt.Chart(work_rows).mark_bar(cornerRadiusTopLeft=5, cornerRadiusBottomLeft=5).encode(
                y=alt.Y("Main Work:N", title=None, sort="-x"),
                x=alt.X("Progress %:Q", title="Progress %", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("Progress %:Q", scale=alt.Scale(scheme="greens"), legend=None),
                tooltip=["Main Work:N", alt.Tooltip("Progress %:Q", format=".1f"), "Done:Q", "Total:Q"],
            ).properties(height=390)
            st.altair_chart(work_chart, use_container_width=True)

        with c2:
            st.markdown("<div class='cp-section-title'>Floor-wise Days Difference</div>", unsafe_allow_html=True)
            duration_chart = alt.Chart(level_rows).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X("Level:N", title="Level", sort=level_rows["Level"].tolist(), axis=alt.Axis(labelAngle=-45)),
                y=alt.Y("Duration Days:Q", title="Days"),
                color=alt.Color("Duration Days:Q", scale=alt.Scale(scheme="oranges"), legend=None),
                tooltip=["Level:N", "First Date:N", "Latest Date:N", "Duration Days:Q"],
            ).properties(height=390)
            st.altair_chart(duration_chart, use_container_width=True)

        st.markdown("<div class='cp-section-title'>Floor-wise Progress Table</div>", unsafe_allow_html=True)
        display_level = level_rows.copy()
        display_level["Progress %"] = display_level["Progress %"].map(lambda x: round(float(x), 1))
        st.dataframe(display_level, use_container_width=True, hide_index=True)

    with slab_update_tab:
        st.markdown("<div class='cp-section-title'>Update Slab / RCC Checkpoints</div>", unsafe_allow_html=True)

        selected_wing = st.selectbox("Wing", WINGS, key="cp_slab_update_wing")
        level_labels = [l["level_label"] for l in FLOOR_LEVELS]
        selected_level_label = st.selectbox("Slab / Level", level_labels, key="cp_slab_update_level")
        selected_level = next(l for l in FLOOR_LEVELS if l["level_label"] == selected_level_label)

        row_df = floor_df[(floor_df["wing"] == selected_wing) & (floor_df["level_code"] == selected_level["level_code"])]
        if row_df.empty:
            st.error("Selected slab row was not found in Supabase.")
            return

        row = row_df.iloc[0]
        row_id = row["id"]
        done_count, total_count, selected_pct = _row_progress(row, FLOOR_DATE_COLS)
        _card("Selected RCC Progress", _fmt_pct(selected_pct), f"{done_count}/{total_count} checkpoints | {selected_wing} - {selected_level_label}")

        selected_date = st.date_input(
            "Completion date for newly checked items",
            value=datetime.date.today(),
            format="DD/MM/YYYY",
            key="cp_slab_update_date",
        )

        with st.form("construction_slab_progress_form", clear_on_submit=False):
            st.caption("Checked RCC checkpoint columns store a completion date. Unchecking clears that checkpoint date.")
            checkbox_values = {}
            for label, col in RCC_CHECKPOINTS:
                existing_date = _done_date(row, col)
                display_label = f"{label} - {existing_date}" if existing_date else label
                checkbox_values[col] = st.checkbox(
                    display_label,
                    value=bool(existing_date),
                    key=f"cp_slab_{row_id}_{col}",
                )

            submitted = st.form_submit_button("Save Slab / RCC Progress", use_container_width=True)

        if submitted:
            updates = {}
            done_date = _date_iso(selected_date)
            for _, col in RCC_CHECKPOINTS:
                currently_done = _is_done(row, col)
                should_be_done = bool(checkbox_values[col])
                if should_be_done and not currently_done:
                    updates[col] = done_date
                elif (not should_be_done) and currently_done:
                    updates[col] = None

            if not updates:
                st.info("No RCC checkpoint changes to save.")
            else:
                try:
                    supabase_client.table(FLOOR_TABLE).update(updates).eq("id", row_id).execute()
                    st.success(f"Updated {len(updates)} RCC checkpoint column(s).")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not save RCC progress: {e}")

        with st.expander("Show selected slab row dates", expanded=False):
            st.dataframe(row_df[["wing", "level_label"] + FLOOR_DATE_COLS], use_container_width=True, hide_index=True)

    with flat_update_tab:
        st.markdown("<div class='cp-section-title'>Update Flat-wise Detailed Checkpoints</div>", unsafe_allow_html=True)

        selected_wing = st.selectbox("Wing", WINGS, key="cp_flat_update_wing")
        selected_floor = st.selectbox("Floor", list(range(1, 14)), key="cp_flat_update_floor")
        options_df = _flat_rows(flat_df, selected_wing, selected_floor).sort_values("display_order")

        if options_df.empty:
            st.error("No flat rows found for this wing and floor.")
            return

        option_labels = [
            f"{r['flat_number']} - {r['unit_type']}"
            for _, r in options_df.iterrows()
        ]
        selected_label = st.selectbox("Flat / Area", option_labels, key="cp_flat_update_flat")
        selected_idx = option_labels.index(selected_label)
        selected_row_id = options_df.iloc[selected_idx]["id"]
        row_df = flat_df[flat_df["id"] == selected_row_id]

        if row_df.empty:
            st.error("Selected flat row was not found in Supabase.")
            return

        row = row_df.iloc[0]
        row_id = row["id"]
        done_count, total_count, selected_pct = _row_progress(row, FLAT_DATE_COLS)
        _card("Selected Flat Progress", _fmt_pct(selected_pct), f"{done_count}/{total_count} checkpoints | {selected_label}")

        selected_date = st.date_input(
            "Completion date for newly checked items",
            value=datetime.date.today(),
            format="DD/MM/YYYY",
            key="cp_flat_update_date",
        )

        with st.form("construction_flat_progress_form", clear_on_submit=False):
            st.caption("Every detailed checkpoint for the selected flat is shown below. Toilet and terrace sections are separated.")
            checkbox_values = {}

            for work in FLAT_WORKS:
                st.markdown(f"### {work['main']}")
                for section, checkpoints in work["sections"].items():
                    if section != "General":
                        st.markdown(f"**{section}**")

                    for label, col in checkpoints:
                        existing_date = _done_date(row, col)
                        display_label = f"{label} - {existing_date}" if existing_date else label
                        checkbox_values[col] = st.checkbox(
                            display_label,
                            value=bool(existing_date),
                            key=f"cp_flat_{row_id}_{col}",
                        )

                st.markdown("---")

            submitted = st.form_submit_button("Save Flat Progress", use_container_width=True)

        if submitted:
            updates = {}
            done_date = _date_iso(selected_date)
            for col in FLAT_DATE_COLS:
                currently_done = _is_done(row, col)
                should_be_done = bool(checkbox_values.get(col, False))
                if should_be_done and not currently_done:
                    updates[col] = done_date
                elif (not should_be_done) and currently_done:
                    updates[col] = None

            if not updates:
                st.info("No flat checkpoint changes to save.")
            else:
                try:
                    supabase_client.table(FLAT_TABLE).update(updates).eq("id", row_id).execute()
                    st.success(f"Updated {len(updates)} flat checkpoint column(s).")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not save flat progress: {e}")

        with st.expander("Show selected flat row dates", expanded=False):
            st.dataframe(row_df[["wing", "floor_no", "flat_number", "unit_type"] + FLAT_DATE_COLS], use_container_width=True, hide_index=True)

    with floor_tab:
        st.markdown("<div class='cp-section-title'>Floor-wise Building View</div>", unsafe_allow_html=True)
        st.caption("Click a level to view progress by main work heading.")
        components.html(_build_floor_widget(floor_df, flat_df), height=940, scrolling=True)

    with flat_tab:
        st.markdown("<div class='cp-section-title'>Flat-wise Progress View</div>", unsafe_allow_html=True)
        st.caption("Click a flat or common-area cell to view progress by main work heading.")
        components.html(_build_flat_widget(flat_df), height=980, scrolling=True)
