# ============================================================
# TAB 12 — BULK AGREEMENT GENERATOR
# Requires:
#   pip install docxtpl python-docx
#
# GitHub folder:
#   templates/
#     1_bhk_agreement.docx
#     1_bhk_agreement_6_percent.docx
#     2_bhk_agreement.docx
#     2_bhk_agreement_6_percent.docx
# ============================================================

from pathlib import Path
import tempfile
import re
import io
import json
import zipfile
import math
import streamlit as st
from docxtpl import DocxTemplate

# ---------- CONFIG ----------
BASE_DIR = Path(__file__).resolve().parent

PREFIX_OPTIONS = ["Mr.", "Mrs."]
WING_NAME_OPTIONS = ["E", "F", "C"]
PARKING_LOCATION_OPTIONS = ["Basement", "Ground", "Stilt"]
FLOOR_NUMBERS = ["1st", "2nd", "3rd"] + [f"{i}th" for i in range(4, 14)]

CARPET_MAP = {
    "480.94": {"carpet_sqm": "40.74", "balcony_sqm": "3.95"},
    "482.12": {"carpet_sqm": "40.81", "balcony_sqm": "3.98"},
    "655.10": {"carpet_sqm": "57.00", "balcony_sqm": "3.86"},
    "665.65": {"carpet_sqm": "58.04", "balcony_sqm": "3.80"},
    "666.29": {"carpet_sqm": "58.04", "balcony_sqm": "3.86"},
}

CARPET_OPTIONS = list(CARPET_MAP.keys())

TEMPLATE_FILENAMES = {
    "1 BHK Agreement": "1_bhk_agreement.docx",
    "1 BHK Agreement 6%": "1_bhk_agreement_6_percent.docx",
    "2 BHK Agreement": "2_bhk_agreement.docx",
    "2 BHK Agreement 6%": "2_bhk_agreement_6_percent.docx",
}

# ---------- GENERAL HELPERS ----------
def k(i: int, name: str) -> str:
    return f"t12_bulk_{i}_{name}"


def sanitize_filename(value: str) -> str:
    value = (value or "").strip().replace(" ", "_")
    value = re.sub(r"[^A-Za-z0-9_\-]", "", value)
    return value or "Agreement"


def build_doc_filename(context: dict) -> str:
    return (
        f"{sanitize_filename(context.get('ALLOTTEE_NAME_1', ''))}_"
        f"{sanitize_filename(context.get('WING', ''))}_"
        f"{sanitize_filename(context.get('FLAT_NUMBER', ''))}.docx"
    )


def pronoun_from_prefix(prefix: str) -> str:
    prefix_clean = (prefix or "").strip().lower()
    if prefix_clean.startswith("mrs"):
        return "she"
    return "he"


def compute_residing_phrase(prefix_1: str, allottee_count: int) -> str:
    if allottee_count <= 1:
        pronoun = pronoun_from_prefix(prefix_1)
        return f"{pronoun} is residing at"
    if allottee_count == 2:
        return "Both residing at"
    return "All residing at"


def get_parking_height(parking_location: str) -> str:
    location = (parking_location or "").strip().lower()
    if location == "basement":
        return "3.5"
    return "3.0"


def format_indian_commas(n: int) -> str:
    s = str(abs(int(n)))

    if len(s) <= 3:
        out = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []

        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]

        if rest:
            parts.insert(0, rest)

        out = ",".join(parts + [last3])

    return f"-{out}" if n < 0 else out


def format_rupees(n: int) -> str:
    return f"₹ {format_indian_commas(int(n))}/-"


def round_up_to_next_100(amount: float) -> int:
    amount = float(amount or 0)
    if amount <= 0:
        return 0
    return int(math.ceil(amount / 100.0) * 100)


def get_stamp_duty_rate(doc_label: str, template_path: Path) -> float:
    label = (doc_label or "").lower()
    fname = template_path.name.lower()

    six_percent_keywords = [
        "6 percent",
        "6%",
        "6_percent",
        "6pct",
        "six percent",
    ]

    if any(keyword in label for keyword in six_percent_keywords):
        return 0.06

    if any(keyword in fname for keyword in six_percent_keywords):
        return 0.06

    return 0.07


def compute_stamp_duty_amount(agreement_cost: float, rate: float) -> int:
    raw_amount = float(agreement_cost or 0) * rate
    return round_up_to_next_100(raw_amount)


def get_candidate_template_dirs():
    candidates = [
        BASE_DIR / "templates",
        Path.cwd() / "templates",
        BASE_DIR.parent / "templates",
        Path("/mount/src") / "templates",
        Path("/mount/src") / "prathamvihar" / "templates",
    ]

    seen = set()
    out = []

    for p in candidates:
        try:
            key = str(p.resolve()) if p.exists() else str(p)
        except Exception:
            key = str(p)

        if key not in seen:
            seen.add(key)
            out.append(p)

    return out


def resolve_template_path(filename: str):
    for folder in get_candidate_template_dirs():
        candidate = folder / filename
        if candidate.exists():
            return candidate
    return None


def get_available_template_files() -> list[str]:
    files = []

    for folder in get_candidate_template_dirs():
        if folder.exists():
            files.extend([p.name for p in folder.glob("*.docx")])

    return sorted(set(files))


# ---------- INDIAN NUMBER TO WORDS ----------
ONES = [
    "",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
]

TEENS = [
    "Ten",
    "Eleven",
    "Twelve",
    "Thirteen",
    "Fourteen",
    "Fifteen",
    "Sixteen",
    "Seventeen",
    "Eighteen",
    "Nineteen",
]

TENS = [
    "",
    "",
    "Twenty",
    "Thirty",
    "Forty",
    "Fifty",
    "Sixty",
    "Seventy",
    "Eighty",
    "Ninety",
]


def two_digit_words(n: int) -> str:
    n = int(n)

    if n == 0:
        return ""

    if n < 10:
        return ONES[n]

    if 10 <= n < 20:
        return TEENS[n - 10]

    t, o = divmod(n, 10)
    return (TENS[t] + (" " + ONES[o] if o else "")).strip()


def three_digit_words(n: int) -> str:
    n = int(n)
    h, r = divmod(n, 100)

    out = []

    if h:
        out.append(ONES[h] + " Hundred")

    if r:
        out.append(two_digit_words(r))

    return " ".join(out).strip()


def indian_number_to_words(n: int) -> str:
    n = int(n)

    if n == 0:
        return "Zero"

    if n < 0:
        return "Minus " + indian_number_to_words(-n)

    crore = n // 10000000
    n %= 10000000

    lakh = n // 100000
    n %= 100000

    thousand = n // 1000
    n %= 1000

    hundred_part = n

    parts = []

    if crore:
        parts.append(three_digit_words(crore) + " Crore")

    if lakh:
        parts.append(three_digit_words(lakh) + " Lakh")

    if thousand:
        parts.append(three_digit_words(thousand) + " Thousand")

    if hundred_part:
        parts.append(three_digit_words(hundred_part))

    return " ".join(p for p in parts if p).strip()


def as_rupees_words(n: int) -> str:
    return f"Rupees {indian_number_to_words(int(n))} Only"


# ---------- SCHEDULE HELPERS ----------
def split_gross_into_base_gst(gross: float, rate: float) -> tuple[int, int]:
    gross = float(gross or 0)

    if gross <= 0:
        return (0, 0)

    gst_part = gross * (rate / (1.0 + rate))
    gst_i = int(round(gst_part))
    base_i = int(round(gross - gst_i))

    gross_i = int(round(gross))
    drift = gross_i - (base_i + gst_i)
    base_i += drift

    return base_i, gst_i


def compute_schedule_placeholders(
    unit_type: str,
    agreement_cost: float,
    received_amt_gross: float
) -> dict:
    out = {f"SLAB_{i}": "Nil" for i in range(1, 14)}
    out["TDS"] = "Nil"

    agreement_cost = float(agreement_cost or 0)
    received_amt_gross = float(received_amt_gross or 0)

    if agreement_cost <= 0:
        out["TOTAL_BALANCE"] = format_rupees(0)
        out["TOTAL_BALANCE_WORDS"] = as_rupees_words(0)
        out["TOTAL_BALANCE_WORDS_ONLY"] = indian_number_to_words(0)
        return out

    gst_rate = 0.01 if unit_type == "1bhk" else 0.05

    schedule_1bhk = [
        (1, 5.0, True),
        (2, 10.0, True),
        (3, 15.0, True),
        (4, 7.5, True),
        (5, 7.5, True),
        (6, 7.5, True),
        (7, 7.5, True),
        (8, 7.5, True),
        (9, 7.5, True),
        (10, 7.5, True),
        (11, 7.5, True),
        (12, 5.0, True),
        (13, 5.0, True),
    ]

    schedule_2bhk = [
        (1, 5.0, True),
        (2, 9.0, True),
        ("TDS", 1.0, False),
        (3, 15.0, True),
        (4, 7.5, True),
        (5, 7.5, True),
        (6, 7.5, True),
        (7, 7.5, True),
        (8, 7.5, True),
        (9, 7.5, True),
        (10, 7.5, True),
        (11, 7.5, True),
        (12, 5.0, True),
        (13, 5.0, True),
    ]

    schedule = schedule_2bhk if unit_type == "2bhk" else schedule_1bhk

    rows = []

    for key, perc, apply_received in schedule:
        req_base = int(round(agreement_cost * (perc / 100.0)))
        req_gst = int(round(req_base * gst_rate))
        req_total = req_base + req_gst

        rows.append({
            "key": key,
            "apply_received": apply_received,
            "req_base": req_base,
            "req_gst": req_gst,
            "req_total": req_total,
            "paid_base": 0,
            "paid_gst": 0,
        })

    received_remaining = float(received_amt_gross)

    for r in rows:
        if not r["apply_received"]:
            continue

        slab_paid_gross = min(received_remaining, float(r["req_total"]))
        slab_paid_base, slab_paid_gst = split_gross_into_base_gst(
            slab_paid_gross,
            gst_rate
        )

        paid_gst = min(r["req_gst"], int(round(slab_paid_gst)))
        paid_base = min(r["req_base"], int(round(slab_paid_base)))

        used = paid_base + paid_gst
        target = int(round(slab_paid_gross))
        diff = target - used

        if diff != 0:
            if diff > 0:
                add_base = min(r["req_base"] - paid_base, diff)
                paid_base += add_base
                diff -= add_base

                add_gst = min(r["req_gst"] - paid_gst, diff)
                paid_gst += add_gst
            else:
                take_base = min(paid_base, -diff)
                paid_base -= take_base
                diff += take_base

                take_gst = min(paid_gst, -diff)
                paid_gst -= take_gst

        paid_total = paid_base + paid_gst
        received_remaining = max(0.0, received_remaining - float(paid_total))

        r["paid_base"] = paid_base
        r["paid_gst"] = paid_gst

    total_balance_base = 0

    for r in rows:
        bal_base = max(0, r["req_base"] - r["paid_base"])
        bal_gst = max(0, r["req_gst"] - r["paid_gst"])
        bal_total = bal_base + bal_gst

        display = "Nil" if bal_total <= 0 else format_rupees(bal_base)

        if r["key"] == "TDS":
            out["TDS"] = "Nil" if bal_total <= 0 else format_rupees(bal_base)
            total_balance_base += bal_base
        else:
            out[f"SLAB_{int(r['key'])}"] = display
            total_balance_base += bal_base

    out["TOTAL_BALANCE"] = format_rupees(total_balance_base)
    out["TOTAL_BALANCE_WORDS"] = as_rupees_words(total_balance_base)
    out["TOTAL_BALANCE_WORDS_ONLY"] = indian_number_to_words(total_balance_base)

    return out


@st.cache_data(show_spinner=False)
def render_docx_cached(
    template_path_str: str,
    template_mtime: float,
    context_json: str
) -> bytes:
    context = json.loads(context_json)

    doc = DocxTemplate(template_path_str)
    doc.render(context)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        doc.save(tmp.name)
        return Path(tmp.name).read_bytes()


def clear_t12_zip():
    st.session_state["t12_bulk_zip_bytes"] = None
    st.session_state["t12_bulk_zip_name"] = None


def is_filled_agreement(i: int) -> bool:
    name_1 = (st.session_state.get(k(i, "name_1"), "") or "").strip()
    flat_no = (st.session_state.get(k(i, "flat_number"), "") or "").strip()
    address = (st.session_state.get(k(i, "address"), "") or "").strip()
    agree_cost = float(st.session_state.get(k(i, "agreement_cost"), 0) or 0)

    return bool(name_1 and flat_no and address and agree_cost > 0)


# ============================================================
# PUT THIS BLOCK WHERE YOUR TABS ARE USED
# Example:
# tab1, tab2, ..., tab12 = st.tabs([...])
# with tab12:
#     below code
# ============================================================

if selected_main_section == "Agreement Document Editor":
    st.session_state.setdefault("t12_bulk_zip_bytes", None)
    st.session_state.setdefault("t12_bulk_zip_name", None)

    available_template_files = get_available_template_files()

    st.markdown(
        """
        <style>
          .t12-card{
            background:rgba(255,255,255,0.92);
            border:1px solid rgba(0,0,0,0.06);
            border-radius:18px;
            padding:16px;
            margin-bottom:14px;
            box-shadow:0 8px 22px rgba(0,0,0,0.04);
          }
          .t12-title{
            font-size:26px;
            font-weight:800;
            margin:0;
          }
          .t12-sub{
            color:rgba(0,0,0,0.55);
            margin:4px 0 0 0;
          }
          .t12-note{
            background:#eff6ff;
            border:1px solid #bfdbfe;
            border-radius:14px;
            padding:12px 14px;
            margin:10px 0 16px 0;
            color:#1e3a8a;
            font-weight:700;
          }
        </style>

        <div class="t12-card">
          <div class="t12-title">🧾 Bulk Agreement Generator (Up to 5)</div>
          <div class="t12-sub">Fill 1–5 agreements → Generate once → Download ZIP. Only filled agreements are included.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not available_template_files:
        st.warning(
            "No DOCX templates found. Add a `templates` folder in GitHub beside `main.py` "
            "and upload the 4 DOCX template files."
        )
    else:
        st.markdown(
            f"""
            <div class="t12-note">
              Templates found: {", ".join(available_template_files)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.form("t12_bulk_form_final_with_words", clear_on_submit=False):
        for i in range(1, 6):
            with st.expander(f"Agreement {i}", expanded=(i == 1)):
                st.selectbox(
                    "Template *",
                    list(TEMPLATE_FILENAMES.keys()),
                    key=k(i, "template")
                )

                st.markdown("### 💰 Schedule Inputs")

                s1, s2 = st.columns(2)

                with s1:
                    st.number_input(
                        "Agreement Cost (₹) *",
                        min_value=0,
                        step=1000,
                        key=k(i, "agreement_cost")
                    )

                with s2:
                    st.number_input(
                        "Received Amount (₹) — Gross incl. GST",
                        min_value=0,
                        step=1000,
                        key=k(i, "received_amount")
                    )

                st.divider()

                st.markdown("### 👤 Allottee 1 (Required)")

                a1, a2, a3, a4, a5 = st.columns([1, 2, 1.6, 1, 2])

                with a1:
                    st.selectbox(
                        "Prefix",
                        PREFIX_OPTIONS,
                        key=k(i, "prefix_1")
                    )

                with a2:
                    st.text_input(
                        "Name *",
                        key=k(i, "name_1")
                    )

                with a3:
                    st.text_input(
                        "PAN",
                        key=k(i, "pan_1")
                    )

                with a4:
                    st.number_input(
                        "Age",
                        0,
                        120,
                        0,
                        key=k(i, "age_1")
                    )

                with a5:
                    st.text_input(
                        "Occupation",
                        key=k(i, "occ_1")
                    )

                with st.expander("👤 Allottee 2 (Optional)"):
                    b1, b2, b3, b4, b5 = st.columns([1, 2, 1.6, 1, 2])

                    with b1:
                        st.selectbox(
                            "Prefix",
                            PREFIX_OPTIONS,
                            key=k(i, "prefix_2")
                        )

                    with b2:
                        st.text_input(
                            "Name",
                            key=k(i, "name_2")
                        )

                    with b3:
                        st.text_input(
                            "PAN",
                            key=k(i, "pan_2")
                        )

                    with b4:
                        st.number_input(
                            "Age",
                            0,
                            120,
                            0,
                            key=k(i, "age_2")
                        )

                    with b5:
                        st.text_input(
                            "Occupation",
                            key=k(i, "occ_2")
                        )

                with st.expander("👤 Allottee 3 (Optional)"):
                    c1, c2, c3, c4, c5 = st.columns([1, 2, 1.6, 1, 2])

                    with c1:
                        st.selectbox(
                            "Prefix",
                            PREFIX_OPTIONS,
                            key=k(i, "prefix_3")
                        )

                    with c2:
                        st.text_input(
                            "Name",
                            key=k(i, "name_3")
                        )

                    with c3:
                        st.text_input(
                            "PAN",
                            key=k(i, "pan_3")
                        )

                    with c4:
                        st.number_input(
                            "Age",
                            0,
                            120,
                            0,
                            key=k(i, "age_3")
                        )

                    with c5:
                        st.text_input(
                            "Occupation",
                            key=k(i, "occ_3")
                        )

                st.divider()

                st.markdown("### 🏠 Property Details")

                p1, p2, p3, p4 = st.columns([1, 1, 1, 1.2])

                with p1:
                    st.selectbox(
                        "Wing Name *",
                        WING_NAME_OPTIONS,
                        key=k(i, "wing_name")
                    )

                with p2:
                    st.selectbox(
                        "Floor",
                        FLOOR_NUMBERS,
                        key=k(i, "floor_number")
                    )

                with p3:
                    st.text_input(
                        "Flat No *",
                        key=k(i, "flat_number")
                    )

                with p4:
                    st.selectbox(
                        "Carpet (sq ft) *",
                        CARPET_OPTIONS,
                        key=k(i, "carpet_sqft")
                    )

                st.divider()

                st.markdown("### 🚗 Parking & 📍 Address")

                q1, q2 = st.columns(2)

                with q1:
                    st.text_input(
                        "Parking Number",
                        key=k(i, "parking_number")
                    )

                with q2:
                    st.selectbox(
                        "Parking Location",
                        PARKING_LOCATION_OPTIONS,
                        key=k(i, "parking_location")
                    )

                st.text_area(
                    "Address *",
                    height=95,
                    key=k(i, "address")
                )

        generate_all = st.form_submit_button("✅ Generate Agreements ZIP")

    if generate_all:
        clear_t12_zip()

        errors = []
        docs = []

        for i in range(1, 6):
            if not is_filled_agreement(i):
                continue

            doc_label = st.session_state.get(
                k(i, "template"),
                list(TEMPLATE_FILENAMES.keys())[0]
            )

            template_filename = TEMPLATE_FILENAMES[doc_label]
            template_path = resolve_template_path(template_filename)

            if template_path is None:
                errors.append(
                    f"Agreement {i}: Template not found → {template_filename}. "
                    f"Available DOCX found: {', '.join(available_template_files) if available_template_files else 'None'}"
                )
                continue

            unit_type = "1bhk" if "1 BHK" in doc_label else "2bhk"
            gst_rate = 0.01 if unit_type == "1bhk" else 0.05

            agreement_cost_raw = float(
                st.session_state.get(k(i, "agreement_cost"), 0) or 0
            )

            received_gross_raw = float(
                st.session_state.get(k(i, "received_amount"), 0) or 0
            )

            stamp_duty_rate = get_stamp_duty_rate(doc_label, template_path)
            stamp_duty_amount = compute_stamp_duty_amount(
                agreement_cost_raw,
                stamp_duty_rate
            )

            received_base, received_gst = split_gross_into_base_gst(
                received_gross_raw,
                gst_rate
            )

            sched_ctx = compute_schedule_placeholders(
                unit_type,
                agreement_cost_raw,
                received_gross_raw
            )

            name_1 = (st.session_state.get(k(i, "name_1"), "") or "").strip()
            name_2 = (st.session_state.get(k(i, "name_2"), "") or "").strip()
            name_3 = (st.session_state.get(k(i, "name_3"), "") or "").strip()

            prefix_1 = st.session_state.get(k(i, "prefix_1"), "Mr.")

            allottee_count = sum(1 for n in [name_1, name_2, name_3] if n)
            residing_phrase = compute_residing_phrase(prefix_1, allottee_count)

            carpet_sqft = st.session_state.get(k(i, "carpet_sqft"), CARPET_OPTIONS[0])
            auto_carpet_sqm = CARPET_MAP[carpet_sqft]["carpet_sqm"]
            auto_balcony_sqm = CARPET_MAP[carpet_sqft]["balcony_sqm"]

            parking_location = st.session_state.get(k(i, "parking_location"), "Basement")
            parking_height = get_parking_height(parking_location)

            context = {
                # Money
                "AGREEMENT_COST": format_rupees(int(round(agreement_cost_raw))),
                "AGREEMENT_COST_WORDS": as_rupees_words(int(round(agreement_cost_raw))),

                "RECEIVED_AMOUNT": format_rupees(int(round(received_gross_raw))),
                "RECEIVED_AMOUNT_WORDS": as_rupees_words(int(round(received_gross_raw))),

                "RECEIVED_AMOUNT_EXCL_GST": format_rupees(int(round(received_base))),
                "RECEIVED_AMOUNT_EXCL_GST_WORDS": as_rupees_words(int(round(received_base))),

                "RECEIVED_GST": format_rupees(int(round(received_gst))),
                "STAMP_DUTY": format_rupees(stamp_duty_amount),
                "STAMP_DUTY_WORDS": as_rupees_words(stamp_duty_amount),

                # Allottee 1
                "PREFIX_1": prefix_1,
                "ALLOTTEE_NAME_1": name_1,
                "PAN_1": (st.session_state.get(k(i, "pan_1"), "") or "").strip(),
                "AGE_1": int(st.session_state.get(k(i, "age_1"), 0) or 0),
                "OCCUPATION_1": (st.session_state.get(k(i, "occ_1"), "") or "").strip(),

                # Allottee 2
                "PREFIX_2": st.session_state.get(k(i, "prefix_2"), "Mr."),
                "ALLOTTEE_NAME_2": name_2,
                "PAN_2": (st.session_state.get(k(i, "pan_2"), "") or "").strip(),
                "AGE_2": int(st.session_state.get(k(i, "age_2"), 0) or 0),
                "OCCUPATION_2": (st.session_state.get(k(i, "occ_2"), "") or "").strip(),

                # Allottee 3
                "PREFIX_3": st.session_state.get(k(i, "prefix_3"), "Mr."),
                "ALLOTTEE_NAME_3": name_3,
                "PAN_3": (st.session_state.get(k(i, "pan_3"), "") or "").strip(),
                "AGE_3": int(st.session_state.get(k(i, "age_3"), 0) or 0),
                "OCCUPATION_3": (st.session_state.get(k(i, "occ_3"), "") or "").strip(),

                # Address
                "RESIDING_PHRASE": residing_phrase,
                "ADDRESS": (st.session_state.get(k(i, "address"), "") or "").strip(),

                # Property
                "WING": st.session_state.get(k(i, "wing_name"), "E"),
                "FLOOR_NUMBER": st.session_state.get(k(i, "floor_number"), "1st"),
                "FLAT_NUMBER": (st.session_state.get(k(i, "flat_number"), "") or "").strip(),

                # Parking
                "PARKING_NUMBER": (st.session_state.get(k(i, "parking_number"), "") or "").strip(),
                "PARKING_LOCATION": parking_location,
                "PARKING_HEIGHT": parking_height,

                # Areas
                "CARPET_AREA": auto_carpet_sqm,
                "BALCONY_AREA": auto_balcony_sqm,
                "CARPET_SQFT": carpet_sqft,
            }

            context.update(sched_ctx)

            context_json = json.dumps(context, sort_keys=True)
            template_mtime = template_path.stat().st_mtime

            try:
                docx_bytes = render_docx_cached(
                    str(template_path),
                    template_mtime,
                    context_json
                )

                docs.append((build_doc_filename(context), docx_bytes))

            except Exception as e:
                errors.append(
                    f"Agreement {i}: Render failed for {template_path.name}. Error: {str(e)}"
                )

        if errors:
            st.error("Fix these issues and try again:")
            for e in errors:
                st.write(f"- {e}")

        elif not docs:
            st.warning(
                "No agreements generated. Fill at least: Name 1 + Flat No + Address + Agreement Cost greater than 0."
            )

        else:
            buf = io.BytesIO()

            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for fname, content in docs:
                    zf.writestr(fname, content)

            st.session_state["t12_bulk_zip_bytes"] = buf.getvalue()
            st.session_state["t12_bulk_zip_name"] = f"Agreements_{len(docs)}.zip"

            st.success(f"✅ Generated {len(docs)} agreement(s). Download ZIP below.")

    if st.session_state.get("t12_bulk_zip_bytes"):
        st.download_button(
            "📦 Download ZIP",
            data=st.session_state["t12_bulk_zip_bytes"],
            file_name=st.session_state["t12_bulk_zip_name"],
            mime="application/zip",
        )

        st.button("Clear ZIP", on_click=clear_t12_zip)
