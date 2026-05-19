# Construction Progress tab.
# This file is intentionally self-contained so Streamlit Cloud does not need
# a root-level construction_progress_tab.py file.

import datetime as _dt
import re
from dataclasses import dataclass

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


FLOOR_TABLE = "construction_floor_progress"
FLAT_TABLE = "construction_flat_progress"


@dataclass(frozen=True)
class Checkpoint:
    heading: str
    section: str
    label: str
    slug: str
    aliases: tuple[str, ...] = ()


def _slug(text: str) -> str:
    s = str(text or "").strip().lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _cp(heading: str, section: str, label: str, slug: str | None = None, aliases=None) -> Checkpoint:
    slug = slug or _slug(label)
    return Checkpoint(heading, section, label, slug, tuple(aliases or ()))


def _prefixed_cp(heading: str, section: str, prefix: str, label: str) -> Checkpoint:
    base = _slug(label)
    slug = f"{prefix}_{base}"
    aliases = []
    if base.startswith("2_"):
        aliases.extend([
            f"{prefix}_two_{base[2:]}",
            f"{prefix}__{base}",
        ])
    return _cp(heading, section, label, slug, aliases)


RCC_CHECKPOINTS = [
    _cp("RCC Work", "RCC Work", "Line out & wooden thesi", "lineout_wooden_thesi", ["line_out_wooden_thesi", "line_out_and_wooden_thesi"]),
    _cp("RCC Work", "RCC Work", "Column Steel binding work", "column_steel_binding_work"),
    _cp("RCC Work", "RCC Work", "Columns Distribution Stirrups", "columns_distribution_stirrups"),
    _cp("RCC Work", "RCC Work", "Beams Reinforcement work", "beams_reinforcement_work"),
    _cp("RCC Work", "RCC Work", "Aluform Vertical Shuttering work", "aluform_vertical_shuttering_work"),
    _cp("RCC Work", "RCC Work", "Electrical Concealed boxes fixing", "electrical_concealed_boxes_fixing"),
    _cp("RCC Work", "RCC Work", "Aluform Horizontal shuttering work", "aluform_horizontal_shuttering_work"),
    _cp("RCC Work", "RCC Work", "Slab & Wall Conduit work", "slab_wall_conduit_work", ["slab_and_wall_conduit_work"]),
    _cp("RCC Work", "RCC Work", "Sleeves fixing as per requirements", "sleeves_fixing_as_per_requirements"),
    _cp("RCC Work", "RCC Work", "Slab Reinforcement work", "slab_reinforcement_work"),
    _cp("RCC Work", "RCC Work", "Support work for Aluform shuttering", "support_work_for_aluform_shuttering"),
    _cp("RCC Work", "RCC Work", "Sunk sides for Toilet & Terrace", "sunksides_for_toilet_terrace", ["sunk_sides_for_toilet_terrace", "sunk_sides_for_toilet_and_terrace"]),
    _cp("RCC Work", "RCC Work", "Cover blocks as per requirement", "cover_blocks_as_per_requirement"),
    _cp("RCC Work", "RCC Work", "RCC Consultant Checking", "rcc_consultant_checking"),
    _cp("RCC Work", "RCC Work", "MEP Consultant Checking", "mep_consultant_checking"),
    _cp("RCC Work", "RCC Work", "Architect Checking", "architect_checking"),
    _cp("RCC Work", "RCC Work", "Levelling of slab / Terrace / Toilet Gala", "levelling_of_slab_terrace_toilet_gala"),
    _cp("RCC Work", "RCC Work", "Pour casting as per drawing", "pour_casting_as_per_drawing"),
    _cp("RCC Work", "RCC Work", "After casting-Curing & Ponding", "after_casting_curing_ponding", ["after_casting_curing_ponding"]),
    _cp("RCC Work", "RCC Work", "Tie patti/ Tie Rod holes filling for Previous slab", "tie_patti_tie_rod_holes_filling_for_previous_slab"),
    _cp("RCC Work", "RCC Work", "Tachya / Hacking as per requirement", "tachya_hacking_as_per_requirement"),
    _cp("RCC Work", "RCC Work", "Grinding / Excess Concrete chipping if any", "grinding_excess_concrete_chipping_if_any"),
]


AAC_ITEMS = [
    "DPC Layout as per Approved Practice",
    "ACC blockwork with block jointing mortar",
    "Patli / RCC band in middle of wall",
    "Above Patli AAC block work up to lintel",
    "Chemical Consumption",
    "Cement Consumption",
    "Gap above Last layer & Beam Bottom proper filling",
    "Curing & Date marking after work completion",
]

INTERNAL_PLASTER_ITEMS = [
    "Internal Plaster Thiyya",
    "Check for Concealed Electrical work",
    "Fibre mesh application on RCC & AAC Block Joint",
    "Fibre mesh application on Electrical Conduit Pipe",
    "Internal Plaster work",
    "Check Opening in Plaster",
]

CONCEALED_ELECTRIC_ITEMS = [
    "Level marking on Wall",
    "Marking & fixing of modular boxes",
    "Wall cutting & Conduit Pipe fixing",
]

CEILING_GYPSUM_ITEMS = [
    "Chemical Application for Ceiling",
    "Dhada marking In Kach (Corners of Slab & Beam)",
    "Ceiling Punning with 4-5mm gypsum with proper finish",
]

WALL_GYPSUM_ITEMS = [
    "Chemical Application for RCC beam/Column",
    "Diagonal making & Tikki marking on wall",
    "Dhada marking on wall",
    "Wall Punning with proper finishing",
]

TOILET_WATERPROOFING_ITEMS = [
    "Cleaning of toilet",
    "Filling of cracks with Cement & Chemical",
    'Kach khadi with 4" chemical coat',
    "2 coat chemical",
    "Basecoat in 1:6 Cement mortar",
    "Brickbat in 1:6 Cement mortar",
    "Waterproofing finishing in 1:6 cement mortar",
]

TERRACE_WATERPROOFING_ITEMS = [
    "Cleaning of terrace",
    "Filling of cracks with Cement & Chemical",
    'Kach khadi with 4" chemical coat',
    "2 coat chemical",
    "Brickbat in 1:6 Cement mortar",
    "Waterproofing finishing in 1:6 cement mortar",
]

KITCHEN_PLATFORM_ITEMS = [
    "Level marking inside flat",
    "Marking of Vertical & Horizontal kadappa on wall",
    "Fixing of Vertical & horizontal kadappa",
    "Granite Top fixing with sink",
    "Granite Skirting fixing of Cement tikki",
    "Granite Vertical Fixing",
    "Panera Piece Fixing at reqd level",
    "Facia Patti fixing",
]


def _flat_group(heading: str, items: list[str]) -> list[Checkpoint]:
    return [_cp(heading, heading, label) for label in items]


FLAT_CHECKPOINT_GROUPS = {
    "AAC Blockwork": _flat_group("AAC Blockwork", AAC_ITEMS),
    "Internal Plaster": _flat_group("Internal Plaster", INTERNAL_PLASTER_ITEMS),
    "Concealed Electrical Work": _flat_group("Concealed Electrical Work", CONCEALED_ELECTRIC_ITEMS),
    "Ceiling Gypsum Work": _flat_group("Ceiling Gypsum Work", CEILING_GYPSUM_ITEMS),
    "Wall Gypsum Work": _flat_group("Wall Gypsum Work", WALL_GYPSUM_ITEMS),
    "Toilet Waterproofing Work": (
        [_prefixed_cp("Toilet Waterproofing Work", "Common Toilet", "common_toilet", label) for label in TOILET_WATERPROOFING_ITEMS]
        + [_prefixed_cp("Toilet Waterproofing Work", "Master Toilet", "master_toilet", label) for label in TOILET_WATERPROOFING_ITEMS]
    ),
    "Dry Terrace / Terrace Waterproofing Work": (
        [_prefixed_cp("Dry Terrace / Terrace Waterproofing Work", "Balcony", "balcony", label) for label in TERRACE_WATERPROOFING_ITEMS]
        + [_prefixed_cp("Dry Terrace / Terrace Waterproofing Work", "Dry Balcony", "dry_balcony", label) for label in TERRACE_WATERPROOFING_ITEMS]
    ),
    "Kitchen Platform Tile Work": _flat_group("Kitchen Platform Tile Work", KITCHEN_PLATFORM_ITEMS),
}

FLAT_CHECKPOINTS = [cp for checkpoints in FLAT_CHECKPOINT_GROUPS.values() for cp in checkpoints]
ALL_WORK_HEADINGS = ["RCC Work"] + list(FLAT_CHECKPOINT_GROUPS.keys())
PARKING_RCC_SKIP_WORDS = ("aluform", "cover_blocks", "electrical", "sunksides", "sunk_sides")


def _norm_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name or "").lower())


def _column_lookup(df: pd.DataFrame, checkpoints: list[Checkpoint]) -> dict[Checkpoint, str | None]:
    if df is None or df.empty:
        columns = []
    else:
        columns = list(df.columns)

    norm_to_col = {_norm_col(c): c for c in columns}
    out = {}

    for cp in checkpoints:
        candidates = [cp.slug, *cp.aliases, _slug(cp.label)]
        found = None

        for cand in candidates:
            if cand in columns:
                found = cand
                break

            norm = _norm_col(cand)
            if norm in norm_to_col:
                found = norm_to_col[norm]
                break

        out[cp] = found

    return out


def _is_done(value) -> bool:
    if pd.isna(value):
        return False

    s = str(value).strip()
    return bool(s and s.lower() not in {"nan", "none", "nat", "null"})


def _parse_date(value):
    if not _is_done(value):
        return pd.NaT
    return pd.to_datetime(value, errors="coerce", dayfirst=True)


def _date_label(value) -> str:
    d = _parse_date(value)
    if pd.isna(d):
        return "-"
    return d.strftime("%d-%b-%Y")


def _fmt_pct(value) -> str:
    try:
        return f"{float(value):.0f}%"
    except Exception:
        return "0%"


def _fmt_days(value) -> str:
    if pd.isna(value):
        return "-"
    try:
        return f"{int(round(float(value)))} days"
    except Exception:
        return "-"


def _fmt_int(value) -> str:
    try:
        return f"{int(round(float(value))):,}"
    except Exception:
        return "0"


def _level_label(row) -> str:
    for col in ["level_label", "Level Label", "level", "Level"]:
        if col in row and _is_done(row.get(col)):
            return str(row.get(col)).strip()

    floor_no = row.get("floor_no", row.get("Floor", ""))
    try:
        floor_i = int(float(floor_no))
        if floor_i == -1:
            return "Basement"
        if floor_i == 0:
            return "Ground / Stilt"
        return f"Floor {floor_i}"
    except Exception:
        return str(floor_no or "-")


def _level_code(row) -> str:
    for col in ["level_code", "Level Code"]:
        if col in row and _is_done(row.get(col)):
            return str(row.get(col)).strip()
    return _slug(_level_label(row))


def _floor_no(row):
    for col in ["floor_no", "Floor", "floor"]:
        if col in row and _is_done(row.get(col)):
            try:
                return int(float(row.get(col)))
            except Exception:
                return None
    return None


def _display_order(row):
    for col in ["display_order", "Display Order"]:
        if col in row and _is_done(row.get(col)):
            try:
                return float(row.get(col))
            except Exception:
                pass

    f = _floor_no(row)
    return -999 if f is None else f


def _is_parking_level(row) -> bool:
    label = _level_label(row).strip().lower()
    code = _level_code(row).strip().lower()
    floor_no = _floor_no(row)

    return (
        label in {"basement", "ground", "stilt", "ground / stilt"}
        or code in {"basement", "ground", "stilt"}
        or (floor_no is not None and floor_no <= 0)
    )


def _active_rcc_checkpoints(row) -> list[Checkpoint]:
    if not _is_parking_level(row):
        return RCC_CHECKPOINTS

    active = []
    for cp in RCC_CHECKPOINTS:
        slug = cp.slug.lower()
        if any(word in slug for word in PARKING_RCC_SKIP_WORDS):
            continue
        active.append(cp)
    return active


def _row_key(row) -> str:
    if "id" in row and _is_done(row.get("id")):
        return f"id:{row.get('id')}"

    bits = []
    for col in ["wing", "Wing", "level_code", "flat_number", "Flat Number", "floor_no"]:
        if col in row:
            bits.append(str(row.get(col)))
    return "|".join(bits)


def _safe_key(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", str(value or "")).strip("_")


def _wing_value(row) -> str:
    for col in ["wing", "Wing"]:
        if col in row and _is_done(row.get(col)):
            return str(row.get(col)).strip().upper()
    return ""


def _flat_label(row) -> str:
    wing = _wing_value(row)
    flat_no = ""
    for col in ["flat_number", "Flat Number", "flat"]:
        if col in row and _is_done(row.get(col)):
            flat_no = str(row.get(col)).strip()
            break

    unit_type = ""
    for col in ["unit_type", "Type", "type"]:
        if col in row and _is_done(row.get(col)):
            unit_type = str(row.get(col)).strip()
            break

    label = f"{wing} {flat_no}".strip()
    if unit_type:
        label = f"{label} ({unit_type})"
    return label or "-"


def _row_progress(row, checkpoints: list[Checkpoint], col_map: dict[Checkpoint, str | None]) -> tuple[int, int, float]:
    total = 0
    done = 0

    for cp in checkpoints:
        col = col_map.get(cp)
        if not col:
            continue
        total += 1
        if _is_done(row.get(col)):
            done += 1

    pct = 0.0 if total == 0 else (done / total) * 100
    return done, total, pct


def _date_values_for_row(row, checkpoints: list[Checkpoint], col_map: dict[Checkpoint, str | None]) -> list[pd.Timestamp]:
    dates = []
    for cp in checkpoints:
        col = col_map.get(cp)
        if col:
            d = _parse_date(row.get(col))
            if pd.notna(d):
                dates.append(d)
    return dates


def _work_progress_for_level(
    floor_row,
    flat_rows: pd.DataFrame,
    floor_col_map: dict[Checkpoint, str | None],
    flat_col_map: dict[Checkpoint, str | None],
) -> pd.DataFrame:
    rows = []

    rcc_cps = _active_rcc_checkpoints(floor_row)
    done, total, pct = _row_progress(floor_row, rcc_cps, floor_col_map)
    rows.append({
        "Main Work": "RCC Work",
        "Done": done,
        "Total": total,
        "Progress %": pct,
    })

    for heading, checkpoints in FLAT_CHECKPOINT_GROUPS.items():
        total = 0
        done = 0

        if flat_rows is not None and not flat_rows.empty:
            for _, flat_row in flat_rows.iterrows():
                d, t, _ = _row_progress(flat_row, checkpoints, flat_col_map)
                done += d
                total += t

        pct = 0.0 if total == 0 else (done / total) * 100
        rows.append({
            "Main Work": heading,
            "Done": done,
            "Total": total,
            "Progress %": pct,
        })

    return pd.DataFrame(rows)


def _overall_progress_from_work(work_df: pd.DataFrame) -> float:
    if work_df is None or work_df.empty:
        return 0.0

    valid = work_df[work_df["Total"] > 0]
    if valid.empty:
        return 0.0

    return float(valid["Progress %"].mean())


def _floor_flat_rows(flat_df: pd.DataFrame, wing: str, floor_no) -> pd.DataFrame:
    if flat_df is None or flat_df.empty or floor_no is None:
        return pd.DataFrame()

    out = flat_df.copy()
    out["_wing_norm"] = out.apply(_wing_value, axis=1)

    if "floor_no" in out.columns:
        out["_floor_no_norm"] = pd.to_numeric(out["floor_no"], errors="coerce")
    elif "Floor" in out.columns:
        out["_floor_no_norm"] = pd.to_numeric(out["Floor"], errors="coerce")
    else:
        return pd.DataFrame()

    return out[(out["_wing_norm"] == wing) & (out["_floor_no_norm"] == floor_no)].copy()


def _level_progress_rows(
    floor_df: pd.DataFrame,
    flat_df: pd.DataFrame,
    wing: str,
    floor_col_map: dict[Checkpoint, str | None],
    flat_col_map: dict[Checkpoint, str | None],
) -> pd.DataFrame:
    if floor_df is None or floor_df.empty:
        return pd.DataFrame()

    wing_df = floor_df[floor_df.apply(_wing_value, axis=1) == wing].copy()
    if wing_df.empty:
        return pd.DataFrame()

    rows = []
    for _, floor_row in wing_df.iterrows():
        floor_no = _floor_no(floor_row)
        level_flats = _floor_flat_rows(flat_df, wing, floor_no)
        work_df = _work_progress_for_level(floor_row, level_flats, floor_col_map, flat_col_map)
        progress = _overall_progress_from_work(work_df)

        dates = _date_values_for_row(floor_row, _active_rcc_checkpoints(floor_row), floor_col_map)
        if not level_flats.empty:
            for _, flat_row in level_flats.iterrows():
                dates.extend(_date_values_for_row(flat_row, FLAT_CHECKPOINTS, flat_col_map))

        first_date = min(dates) if dates else pd.NaT
        last_date = max(dates) if dates else pd.NaT
        duration = np.nan if pd.isna(first_date) or pd.isna(last_date) else (last_date - first_date).days

        rows.append({
            "Wing": wing,
            "Level": _level_label(floor_row),
            "Level Code": _level_code(floor_row),
            "Floor No": floor_no,
            "Display Order": _display_order(floor_row),
            "Progress %": progress,
            "First Work Date": first_date,
            "Latest Work Date": last_date,
            "Days Difference": duration,
        })

    return pd.DataFrame(rows).sort_values("Display Order", ascending=False)


def _flat_progress_rows(flat_df: pd.DataFrame, wing: str, flat_col_map: dict[Checkpoint, str | None]) -> pd.DataFrame:
    if flat_df is None or flat_df.empty:
        return pd.DataFrame()

    out_rows = []
    wing_df = flat_df[flat_df.apply(_wing_value, axis=1) == wing].copy()

    for _, row in wing_df.iterrows():
        done, total, pct = _row_progress(row, FLAT_CHECKPOINTS, flat_col_map)
        out_rows.append({
            "Row Key": _row_key(row),
            "Wing": _wing_value(row),
            "Floor No": _floor_no(row),
            "Flat": _flat_label(row),
            "Done": done,
            "Total": total,
            "Progress %": pct,
            "Display Order": _display_order(row),
        })

    return pd.DataFrame(out_rows)


def _load_table(supabase_client, table_name: str) -> pd.DataFrame:
    response = supabase_client.table(table_name).select("*").execute()
    return pd.DataFrame(response.data or [])


def _load_data(supabase_client):
    try:
        floor_df = _load_table(supabase_client, FLOOR_TABLE)
    except Exception as exc:
        st.error(f"Could not load {FLOOR_TABLE}: {exc}")
        floor_df = pd.DataFrame()

    try:
        flat_df = _load_table(supabase_client, FLAT_TABLE)
    except Exception as exc:
        st.error(f"Could not load {FLAT_TABLE}: {exc}")
        flat_df = pd.DataFrame()

    return floor_df, flat_df


def _update_row(supabase_client, table_name: str, row, payload: dict):
    query = supabase_client.table(table_name).update(payload)

    if "id" in row and _is_done(row.get("id")):
        query = query.eq("id", int(row.get("id")))
    elif table_name == FLOOR_TABLE:
        query = query.eq("wing", _wing_value(row)).eq("level_code", _level_code(row))
    else:
        query = query.eq("wing", _wing_value(row)).eq("flat_number", str(row.get("flat_number", row.get("Flat Number", ""))).strip())

    return query.execute()


def _save_checkpoints(supabase_client, table_name: str, row, checkpoints, col_map, form_prefix: str):
    today = _dt.date.today().isoformat()
    payload = {}
    missing = []

    for cp in checkpoints:
        col = col_map.get(cp)
        if not col:
            missing.append(cp.label)
            continue

        key = f"{form_prefix}_{cp.slug}"
        checked = bool(st.session_state.get(key, False))
        current_done = _is_done(row.get(col))

        if checked and not current_done:
            payload[col] = today
        elif (not checked) and current_done:
            payload[col] = None

    if missing:
        st.warning("Some checkpoint columns are missing in Supabase, so they were skipped: " + ", ".join(missing[:8]))

    if not payload:
        st.info("No changes to save.")
        return

    _update_row(supabase_client, table_name, row, payload)
    st.success("Progress updated.")
    st.session_state["cp_refresh"] = st.session_state.get("cp_refresh", 0) + 1
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def _checkpoint_table(row, checkpoints, col_map) -> pd.DataFrame:
    rows = []
    for cp in checkpoints:
        col = col_map.get(cp)
        value = row.get(col) if col else None
        rows.append({
            "Main Work": cp.heading,
            "Section": cp.section,
            "Checkpoint": cp.label,
            "Status": "Done" if _is_done(value) else "Pending",
            "Date": _date_label(value),
        })
    return pd.DataFrame(rows)


def _flat_report_df(row, flat_col_map) -> pd.DataFrame:
    return _checkpoint_table(row, FLAT_CHECKPOINTS, flat_col_map)


def _slab_casting_rows(floor_df: pd.DataFrame, floor_col_map, wing: str | None = None) -> pd.DataFrame:
    pour_cp = next((cp for cp in RCC_CHECKPOINTS if cp.slug == "pour_casting_as_per_drawing"), None)
    pour_col = floor_col_map.get(pour_cp) if pour_cp else None

    if not pour_col or floor_df is None or floor_df.empty:
        return pd.DataFrame()

    df = floor_df.copy()
    df["_wing_norm"] = df.apply(_wing_value, axis=1)
    if wing:
        df = df[df["_wing_norm"] == wing]

    rows = []
    for wing_name, wdf in df.groupby("_wing_norm"):
        wdf = wdf.copy()
        wdf["_order"] = wdf.apply(_display_order, axis=1)
        wdf = wdf.sort_values("_order", ascending=True)

        prev_date = pd.NaT
        for _, row in wdf.iterrows():
            cast_date = _parse_date(row.get(pour_col))
            if pd.isna(cast_date):
                continue

            cycle_days = np.nan if pd.isna(prev_date) else (cast_date - prev_date).days
            rows.append({
                "Wing": wing_name,
                "Level": _level_label(row),
                "Display Order": _display_order(row),
                "Casting Date": cast_date,
                "Slab Cycle Days": cycle_days,
            })
            prev_date = cast_date

    return pd.DataFrame(rows)


def _dashboard_rows(floor_df, flat_df, floor_col_map, flat_col_map, wing: str | None = None):
    wings = _wing_options(floor_df, flat_df) if wing is None else [wing]
    level_rows = []
    work_rows = []

    for w in wings:
        ldf = _level_progress_rows(floor_df, flat_df, w, floor_col_map, flat_col_map)
        if not ldf.empty:
            level_rows.append(ldf)

        wing_floor_df = floor_df[floor_df.apply(_wing_value, axis=1) == w].copy() if not floor_df.empty else pd.DataFrame()
        for _, floor_row in wing_floor_df.iterrows():
            level_flats = _floor_flat_rows(flat_df, w, _floor_no(floor_row))
            wdf = _work_progress_for_level(floor_row, level_flats, floor_col_map, flat_col_map)
            wdf["Wing"] = w
            wdf["Level"] = _level_label(floor_row)
            work_rows.append(wdf)

    levels = pd.concat(level_rows, ignore_index=True) if level_rows else pd.DataFrame()
    works = pd.concat(work_rows, ignore_index=True) if work_rows else pd.DataFrame()
    slab_cycles = _slab_casting_rows(floor_df, floor_col_map, wing)

    return levels, works, slab_cycles


def _wing_options(floor_df: pd.DataFrame, flat_df: pd.DataFrame) -> list[str]:
    wings = set()
    if floor_df is not None and not floor_df.empty:
        wings.update([w for w in floor_df.apply(_wing_value, axis=1).tolist() if w])
    if flat_df is not None and not flat_df.empty:
        wings.update([w for w in flat_df.apply(_wing_value, axis=1).tolist() if w])
    return sorted(wings)


def _card(label: str, value: str, note: str = ""):
    st.markdown(
        f"""
        <div class="cp-kpi-card">
            <div class="cp-kpi-label">{label}</div>
            <div class="cp-kpi-value">{value}</div>
            <div class="cp-kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_dashboard_panel(floor_df, flat_df, floor_col_map, flat_col_map, wing: str | None):
    levels, works, slab_cycles = _dashboard_rows(floor_df, flat_df, floor_col_map, flat_col_map, wing)

    progress = 0.0 if levels.empty else float(levels["Progress %"].mean())
    avg_duration = np.nan if levels.empty else pd.to_numeric(levels["Days Difference"], errors="coerce").dropna().mean()
    max_duration = np.nan if levels.empty else pd.to_numeric(levels["Days Difference"], errors="coerce").dropna().max()
    avg_cycle = np.nan if slab_cycles.empty else pd.to_numeric(slab_cycles["Slab Cycle Days"], errors="coerce").dropna().mean()
    slabs_casted = 0 if slab_cycles.empty else len(slab_cycles)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        _card("Overall Progress", _fmt_pct(progress), "Average of level progress")
    with c2:
        _card("Slabs Casted", _fmt_int(slabs_casted), "Using Pour casting date")
    with c3:
        _card("Avg Slab Cycle", _fmt_days(avg_cycle), "Between two casting dates")
    with c4:
        _card("Avg Level Duration", _fmt_days(avg_duration), "First to latest checkpoint")
    with c5:
        _card("Max Level Duration", _fmt_days(max_duration), "Slowest active level")

    st.markdown("### Slab Casting Cycle")
    if slab_cycles.empty:
        st.info("No slab casting dates found yet.")
    else:
        chart_df = slab_cycles.dropna(subset=["Slab Cycle Days"]).copy()
        if chart_df.empty:
            st.info("At least two slabs need casting dates to calculate cycle days.")
        else:
            cycle_chart = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Level:N", sort=chart_df.sort_values("Display Order")["Level"].tolist(), title="Slab"),
                    y=alt.Y("Slab Cycle Days:Q", title="Days from previous slab"),
                    color=alt.Color("Wing:N", title="Wing"),
                    tooltip=["Wing", "Level", "Casting Date:T", "Slab Cycle Days:Q"],
                )
                .properties(height=320)
            )
            st.altair_chart(cycle_chart, use_container_width=True)

        show_cycles = slab_cycles.copy()
        show_cycles["Casting Date"] = show_cycles["Casting Date"].dt.strftime("%d-%b-%Y")
        show_cycles["Slab Cycle Days"] = show_cycles["Slab Cycle Days"].apply(lambda x: "-" if pd.isna(x) else int(x))
        st.dataframe(
            show_cycles[["Wing", "Level", "Casting Date", "Slab Cycle Days"]],
            use_container_width=True,
            hide_index=True,
        )

    left, right = st.columns(2)

    with left:
        st.markdown("### Main Work Progress")
        if works.empty:
            st.info("No work progress data available.")
        else:
            work_summary = (
                works.groupby("Main Work", as_index=False)
                .agg(Done=("Done", "sum"), Total=("Total", "sum"))
            )
            work_summary["Progress %"] = np.where(
                work_summary["Total"] > 0,
                work_summary["Done"] / work_summary["Total"] * 100,
                0,
            )
            work_chart = (
                alt.Chart(work_summary)
                .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    y=alt.Y("Main Work:N", sort="-x", title=None),
                    x=alt.X("Progress %:Q", scale=alt.Scale(domain=[0, 100])),
                    color=alt.Color("Progress %:Q", scale=alt.Scale(scheme="tealblues"), legend=None),
                    tooltip=["Main Work", "Done", "Total", "Progress %"],
                )
                .properties(height=360)
            )
            st.altair_chart(work_chart, use_container_width=True)

    with right:
        st.markdown("### Floor-wise Progress")
        if levels.empty:
            st.info("No floor progress data available.")
        else:
            level_chart_df = levels.copy()
            level_chart = (
                alt.Chart(level_chart_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Level:N", sort=level_chart_df.sort_values("Display Order")["Level"].tolist(), title="Level"),
                    y=alt.Y("Progress %:Q", scale=alt.Scale(domain=[0, 100])),
                    color=alt.Color("Wing:N", title="Wing"),
                    tooltip=["Wing", "Level", "Progress %", "Days Difference"],
                )
                .properties(height=360)
            )
            st.altair_chart(level_chart, use_container_width=True)

    st.markdown("### Floor-wise Days Difference")
    if levels.empty:
        st.info("No floor duration data available.")
    else:
        day_df = levels.dropna(subset=["Days Difference"]).copy()
        if day_df.empty:
            st.info("No completed checkpoint dates found for day-difference calculation.")
        else:
            day_chart = (
                alt.Chart(day_df)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Level:N", sort=day_df.sort_values("Display Order")["Level"].tolist()),
                    y=alt.Y("Days Difference:Q", title="Days"),
                    color=alt.Color("Wing:N"),
                    tooltip=["Wing", "Level", "First Work Date:T", "Latest Work Date:T", "Days Difference"],
                )
                .properties(height=300)
            )
            st.altair_chart(day_chart, use_container_width=True)

        table_df = levels.copy()
        table_df["Progress %"] = table_df["Progress %"].round(1)
        table_df["First Work Date"] = table_df["First Work Date"].apply(_date_label)
        table_df["Latest Work Date"] = table_df["Latest Work Date"].apply(_date_label)
        st.dataframe(
            table_df[["Wing", "Level", "Progress %", "First Work Date", "Latest Work Date", "Days Difference"]],
            use_container_width=True,
            hide_index=True,
        )


def _render_update_slab(supabase_client, floor_df, floor_col_map):
    st.markdown("### Update Slab / RCC Checkpoints")

    if floor_df.empty:
        st.warning("No slab/floor rows found. Please run the construction progress SQL first.")
        return

    choices = []
    for idx, row in floor_df.iterrows():
        wing = _wing_value(row)
        label = f"{wing} - {_level_label(row)}"
        choices.append((idx, label))

    choices = sorted(choices, key=lambda x: str(x[1]))
    label_to_idx = {label: idx for idx, label in choices}
    labels = list(label_to_idx.keys())

    with st.form("cp_rcc_load_form", clear_on_submit=False):
        selected_label = st.selectbox(
            "Select slab / level",
            labels,
            index=labels.index(st.session_state.get("cp_rcc_selected_label", labels[0])) if st.session_state.get("cp_rcc_selected_label") in labels else 0,
        )
        load = st.form_submit_button("Show RCC Checkpoints", use_container_width=True)

    if load or "cp_rcc_selected_label" not in st.session_state:
        st.session_state["cp_rcc_selected_label"] = selected_label

    selected_label = st.session_state.get("cp_rcc_selected_label", labels[0])
    selected_row = floor_df.loc[label_to_idx[selected_label]]
    active_cps = _active_rcc_checkpoints(selected_row)
    form_prefix = f"cp_rcc_save_{_safe_key(_row_key(selected_row))}"

    if _is_parking_level(selected_row):
        st.info("Parking slab selected. Aluform, cover block, electrical, and sunk-side toilet checkpoints are not considered here.")

    with st.form("cp_rcc_save_form", clear_on_submit=False):
        st.markdown(f"#### {selected_label}")
        for cp in active_cps:
            col = floor_col_map.get(cp)
            current = selected_row.get(col) if col else None
            st.checkbox(
                f"{cp.label} ({_date_label(current)})",
                value=_is_done(current),
                key=f"{form_prefix}_{cp.slug}",
            )

        save = st.form_submit_button("Save RCC Progress", type="primary", use_container_width=True)

    if save:
        _save_checkpoints(supabase_client, FLOOR_TABLE, selected_row, active_cps, floor_col_map, form_prefix)


def _render_update_flat(supabase_client, flat_df, flat_col_map):
    st.markdown("### Update Flat-wise Detailed Checkpoints")

    if flat_df.empty:
        st.warning("No flat rows found. Please run the construction progress SQL first.")
        return

    choices = []
    for idx, row in flat_df.iterrows():
        floor_no = _floor_no(row)
        label = f"{_flat_label(row)} - Floor {floor_no if floor_no is not None else '-'}"
        choices.append((idx, label))

    choices = sorted(choices, key=lambda x: str(x[1]))
    label_to_idx = {label: idx for idx, label in choices}
    labels = list(label_to_idx.keys())

    with st.form("cp_flat_load_form", clear_on_submit=False):
        selected_label = st.selectbox(
            "Select flat / common area",
            labels,
            index=labels.index(st.session_state.get("cp_flat_selected_label", labels[0])) if st.session_state.get("cp_flat_selected_label") in labels else 0,
        )
        load = st.form_submit_button("Show Flat Checkpoints", use_container_width=True)

    if load or "cp_flat_selected_label" not in st.session_state:
        st.session_state["cp_flat_selected_label"] = selected_label

    selected_label = st.session_state.get("cp_flat_selected_label", labels[0])
    selected_row = flat_df.loc[label_to_idx[selected_label]]
    form_prefix = f"cp_flat_save_{_safe_key(_row_key(selected_row))}"

    with st.form("cp_flat_save_form", clear_on_submit=False):
        st.markdown(f"#### {selected_label}")
        for heading, checkpoints in FLAT_CHECKPOINT_GROUPS.items():
            st.markdown(f"##### {heading}")
            for section in dict.fromkeys([cp.section for cp in checkpoints]):
                section_cps = [cp for cp in checkpoints if cp.section == section]
                if section != heading:
                    st.markdown(f"**{section}**")
                for cp in section_cps:
                    col = flat_col_map.get(cp)
                    current = selected_row.get(col) if col else None
                    st.checkbox(
                        f"{cp.label} ({_date_label(current)})",
                        value=_is_done(current),
                        key=f"{form_prefix}_{cp.slug}",
                    )

        save = st.form_submit_button("Save Flat Progress", type="primary", use_container_width=True)

    if save:
        _save_checkpoints(supabase_client, FLAT_TABLE, selected_row, FLAT_CHECKPOINTS, flat_col_map, form_prefix)


def _progress_color(pct: float) -> str:
    if pct >= 90:
        return "#16a34a"
    if pct >= 60:
        return "#0ea5e9"
    if pct >= 30:
        return "#f59e0b"
    return "#ef4444"


def _render_floorwise(floor_df, flat_df, floor_col_map, flat_col_map, wings):
    st.markdown("### Floor-wise Progress")

    if not wings:
        st.warning("No wings found.")
        return

    with st.form("cp_floor_view_form", clear_on_submit=False):
        selected_wing = st.selectbox(
            "Select Wing",
            wings,
            index=wings.index(st.session_state.get("cp_floor_wing", wings[0])) if st.session_state.get("cp_floor_wing") in wings else 0,
        )
        show = st.form_submit_button("Show Floor Progress", use_container_width=True)

    if show or "cp_floor_wing" not in st.session_state:
        st.session_state["cp_floor_wing"] = selected_wing

    wing = st.session_state.get("cp_floor_wing", wings[0])
    levels = _level_progress_rows(floor_df, flat_df, wing, floor_col_map, flat_col_map)

    if levels.empty:
        st.info("No floor progress found for this wing.")
        return

    building_rows = []
    for _, row in levels.iterrows():
        pct = float(row["Progress %"])
        color = _progress_color(pct)
        building_rows.append(
            f"""
            <div class="cp-building-row">
                <div class="cp-floor-label">{row['Level']}</div>
                <div class="cp-floor-body">
                    <div class="cp-floor-fill" style="width:{max(0, min(pct, 100))}%; background:{color};"></div>
                    <div class="cp-floor-text">{pct:.0f}%</div>
                </div>
                <div class="cp-floor-days">{_fmt_days(row['Days Difference'])}</div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="cp-building-core">
            <div class="cp-building-roof"></div>
            {''.join(building_rows)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    level_labels = levels["Level"].tolist()
    report_level = st.selectbox(
        "Open floor report",
        level_labels,
        key="cp_floor_report_level",
    )

    wing_floor_df = floor_df[floor_df.apply(_wing_value, axis=1) == wing].copy()
    floor_row = wing_floor_df[wing_floor_df.apply(_level_label, axis=1) == report_level].iloc[0]
    floor_flats = _floor_flat_rows(flat_df, wing, _floor_no(floor_row))
    report = _work_progress_for_level(floor_row, floor_flats, floor_col_map, flat_col_map)
    report["Progress %"] = report["Progress %"].round(1)

    st.dataframe(report, use_container_width=True, hide_index=True)


def _render_flatwise(flat_df, flat_col_map, wings):
    st.markdown("### Flat-wise Progress")

    if flat_df.empty:
        st.warning("No flat progress rows found.")
        return

    with st.form("cp_flat_view_form", clear_on_submit=False):
        selected_wing = st.selectbox(
            "Select Wing",
            wings,
            index=wings.index(st.session_state.get("cp_flat_view_wing", wings[0])) if st.session_state.get("cp_flat_view_wing") in wings else 0,
        )
        show = st.form_submit_button("Show Flat Progress", use_container_width=True)

    if show or "cp_flat_view_wing" not in st.session_state:
        st.session_state["cp_flat_view_wing"] = selected_wing

    wing = st.session_state.get("cp_flat_view_wing", wings[0])
    progress_df = _flat_progress_rows(flat_df, wing, flat_col_map)

    if progress_df.empty:
        st.info("No flat progress found for this wing.")
        return

    flat_df_local = flat_df[flat_df.apply(_wing_value, axis=1) == wing].copy()
    key_to_row = {_row_key(row): row for _, row in flat_df_local.iterrows()}

    floors = sorted([f for f in progress_df["Floor No"].dropna().unique().tolist()], reverse=True)

    st.markdown(
        f"""
        <div class="cp-flat-building-shell">
            <div class="cp-flat-building-title">Wing {wing} Flat Progress</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for floor in floors:
        floor_progress = progress_df[progress_df["Floor No"] == floor].sort_values("Flat")
        st.markdown("<div class='cp-flat-floor-band'>", unsafe_allow_html=True)
        label_col, *flat_cols = st.columns([0.95, *([1] * 10)], gap="small")

        with label_col:
            st.markdown(
                f"<div class='cp-flat-floor-label'>Floor<br>{int(floor)}</div>",
                unsafe_allow_html=True,
            )

        for idx, (_, row) in enumerate(floor_progress.iterrows()):
            pct = float(row["Progress %"])
            color = _progress_color(pct)
            flat_name = str(row["Flat"]).replace(f"{wing} ", "").split("(")[0].strip()
            with flat_cols[idx % 10]:
                st.markdown(
                    f"""
                    <div class="cp-flat-cell-preview" style="border-color:{color};">
                        <div class="cp-flat-cell-fill" style="width:{max(0, min(pct, 100))}%; background:{color};"></div>
                        <div class="cp-flat-cell-text">
                            <strong>{flat_name}</strong>
                            <span>{pct:.0f}%</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if flat_cols[idx % 10].button("Report", key=f"cp_flat_btn_{wing}_{floor}_{idx}_{row['Row Key']}", use_container_width=True):
                st.session_state["cp_selected_flat_report_key"] = row["Row Key"]
        st.markdown("</div>", unsafe_allow_html=True)

    selected_key = st.session_state.get("cp_selected_flat_report_key")
    if selected_key not in key_to_row and key_to_row:
        selected_key = next(iter(key_to_row.keys()))
        st.session_state["cp_selected_flat_report_key"] = selected_key

    if selected_key in key_to_row:
        selected_row = key_to_row[selected_key]
        st.markdown(f"### Detailed Flat Report - {_flat_label(selected_row)}")
        report_df = _flat_report_df(selected_row, flat_col_map)

        group_summary = (
            report_df.assign(Done=report_df["Status"].eq("Done").astype(int), Total=1)
            .groupby(["Main Work", "Section"], as_index=False)
            .agg(Done=("Done", "sum"), Total=("Total", "sum"))
        )
        group_summary["Progress %"] = (group_summary["Done"] / group_summary["Total"] * 100).round(1)

        c1, c2, c3 = st.columns(3)
        done_count = int((report_df["Status"] == "Done").sum())
        total_count = int(len(report_df))
        pending_count = total_count - done_count

        with c1:
            _card("Checkpoints Done", f"{done_count}/{total_count}", "Selected flat")
        with c2:
            _card("Flat Progress", _fmt_pct((done_count / total_count * 100) if total_count else 0), "All detailed checkpoints")
        with c3:
            _card("Pending Checkpoints", _fmt_int(pending_count), "Remaining work items")

        st.markdown("#### Detailed Checkpoints")

        for heading in FLAT_CHECKPOINT_GROUPS.keys():
            heading_df = report_df[report_df["Main Work"] == heading].copy()
            if heading_df.empty:
                continue

            heading_done = int((heading_df["Status"] == "Done").sum())
            heading_total = int(len(heading_df))
            heading_pct = (heading_done / heading_total * 100) if heading_total else 0

            with st.expander(f"{heading} - {heading_done}/{heading_total} ({heading_pct:.0f}%)", expanded=True):
                for section in dict.fromkeys(heading_df["Section"].tolist()):
                    section_df = heading_df[heading_df["Section"] == section].copy()
                    if section != heading:
                        st.markdown(f"**{section}**")

                    st.dataframe(
                        section_df[["Checkpoint", "Status", "Date"]],
                        use_container_width=True,
                        hide_index=True,
                    )

        st.markdown("#### Section Summary")
        st.dataframe(group_summary, use_container_width=True, hide_index=True)


def _inject_css():
    st.markdown(
        """
        <style>
        .cp-kpi-card{
            border:1px solid #e2e8f0;
            border-radius:12px;
            padding:14px 16px;
            background:#fff;
            box-shadow:0 6px 18px rgba(15,23,42,.06);
            min-height:112px;
        }
        .cp-kpi-label{
            font-size:12px;
            color:#475569;
            font-weight:800;
            text-transform:uppercase;
        }
        .cp-kpi-value{
            margin-top:8px;
            font-size:24px;
            line-height:1.1;
            color:#0f172a;
            font-weight:900;
        }
        .cp-kpi-note{
            margin-top:8px;
            font-size:12px;
            color:#64748b;
        }
        .cp-building-core{
            max-width:980px;
            margin:12px auto 18px;
            padding:12px 14px 16px;
            border:4px solid #94a3b8;
            border-radius:14px;
            background:linear-gradient(90deg,#e2e8f0 0,#f8fafc 8%,#fff 50%,#f8fafc 92%,#e2e8f0 100%);
            box-shadow:0 18px 42px rgba(15,23,42,.12);
        }
        .cp-building-roof{
            width:82%;
            height:18px;
            margin:0 auto 8px;
            border-radius:10px 10px 3px 3px;
            background:#475569;
        }
        .cp-building-row{
            display:grid;
            grid-template-columns:128px 1fr 96px;
            gap:10px;
            align-items:center;
            padding:6px 0;
            border-bottom:1px solid #e2e8f0;
        }
        .cp-building-row:last-child{border-bottom:0}
        .cp-floor-label{
            font-weight:900;
            color:#0f172a;
            font-size:13px;
        }
        .cp-floor-body{
            position:relative;
            height:28px;
            border:1px solid #cbd5e1;
            border-radius:6px;
            overflow:hidden;
            background:repeating-linear-gradient(90deg,#f8fafc 0,#f8fafc 22px,#e2e8f0 23px,#e2e8f0 24px);
        }
        .cp-floor-fill{
            position:absolute;
            left:0;
            top:0;
            bottom:0;
            opacity:.78;
        }
        .cp-floor-text{
            position:absolute;
            inset:0;
            display:flex;
            align-items:center;
            justify-content:center;
            color:#0f172a;
            font-weight:900;
            font-size:12px;
        }
        .cp-floor-days{
            font-size:12px;
            color:#334155;
            font-weight:800;
            text-align:right;
        }
        .cp-flat-building-shell{
            max-width:1180px;
            margin:8px auto 4px;
            padding:12px 16px;
            border-radius:14px 14px 4px 4px;
            background:#334155;
            color:#fff;
            box-shadow:0 12px 26px rgba(15,23,42,.12);
        }
        .cp-flat-building-title{
            text-align:center;
            font-size:16px;
            font-weight:900;
            letter-spacing:.03em;
            text-transform:uppercase;
        }
        .cp-flat-floor-band{
            max-width:1180px;
            margin:0 auto;
            padding:8px 10px;
            border-left:4px solid #94a3b8;
            border-right:4px solid #94a3b8;
            border-bottom:1px solid #cbd5e1;
            background:linear-gradient(90deg,#f1f5f9 0,#fff 6%,#fff 94%,#f1f5f9 100%);
        }
        .cp-flat-floor-label{
            min-height:58px;
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:center;
            border-radius:8px;
            background:#e2e8f0;
            color:#0f172a;
            font-size:12px;
            font-weight:900;
            line-height:1.15;
        }
        .cp-flat-cell-preview{
            position:relative;
            min-height:58px;
            border:2px solid #cbd5e1;
            border-radius:8px;
            overflow:hidden;
            background:#f8fafc;
            box-shadow:inset 0 0 0 1px rgba(255,255,255,.65);
        }
        .cp-flat-cell-fill{
            position:absolute;
            left:0;
            top:0;
            bottom:0;
            opacity:.18;
        }
        .cp-flat-cell-text{
            position:absolute;
            inset:0;
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            gap:3px;
            color:#0f172a;
            text-align:center;
        }
        .cp-flat-cell-text strong{
            font-size:13px;
            font-weight:900;
        }
        .cp-flat-cell-text span{
            font-size:12px;
            font-weight:900;
            color:#475569;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_construction_progress_tab(supabase_client):
    st.header("Construction Progress Tracking")
    _inject_css()

    if supabase_client is None:
        st.warning("Supabase client is not initialized.")
        return

    floor_df, flat_df = _load_data(supabase_client)
    floor_col_map = _column_lookup(floor_df, RCC_CHECKPOINTS)
    flat_col_map = _column_lookup(flat_df, FLAT_CHECKPOINTS)
    wings = _wing_options(floor_df, flat_df)

    dashboard_tab, slab_update_tab, flat_update_tab, floor_tab, flat_tab = st.tabs([
        "Dashboard",
        "Update Slab / RCC",
        "Update Flat Work",
        "Floor-wise Progress",
        "Flat-wise Progress",
    ])

    with dashboard_tab:
        if not wings:
            st.warning("No construction progress data found.")
        else:
            dash_tabs = st.tabs(["All Wings"] + [f"Wing {w}" for w in wings])
            with dash_tabs[0]:
                _render_dashboard_panel(floor_df, flat_df, floor_col_map, flat_col_map, None)

            for tab_obj, wing in zip(dash_tabs[1:], wings):
                with tab_obj:
                    _render_dashboard_panel(floor_df, flat_df, floor_col_map, flat_col_map, wing)

    with slab_update_tab:
        _render_update_slab(supabase_client, floor_df, floor_col_map)

    with flat_update_tab:
        _render_update_flat(supabase_client, flat_df, flat_col_map)

    with floor_tab:
        _render_floorwise(floor_df, flat_df, floor_col_map, flat_col_map, wings)

    with flat_tab:
        _render_flatwise(flat_df, flat_col_map, wings)


supabase_client = globals().get("supabase", None) or globals().get("supabase_client", None)
render_construction_progress_tab(supabase_client)
