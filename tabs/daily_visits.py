# =========================
# TAB 14 — Daily Visits
# Supabase table: public.daily_visits
# =========================
if selected_main_section == "Daily Visits":
    import datetime
    import pandas as pd
    import streamlit as st

    st.title("📆 Daily Visits")

    # ============================================================
    # SUPABASE CHECK
    # ============================================================
    if "supabase" not in globals() or supabase is None:
        st.warning("📋 Supabase client is not initialized. Please check your Supabase connection block.")
        st.stop()

    DAILY_VISITS_TABLE = "daily_visits"

    # ============================================================
    # UI POLISH
    # ============================================================
    st.markdown(
        """
        <style>
        div[data-testid="stForm"]{
            border: 1px solid rgba(49,51,63,0.10);
            border-radius: 20px;
            padding: 20px 20px 10px 20px;
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
            box-shadow: 0 10px 28px rgba(0,0,0,0.06);
        }
        .stNumberInput input, .stTextInput input, .stDateInput input,
        .stSelectbox div[data-baseweb="select"]{
            border-radius: 12px !important;
        }
        div[data-testid="stForm"] button[kind="primary"]{
            border-radius: 14px !important;
            height: 2.9rem !important;
            font-weight: 700 !important;
            width: 100%;
        }
        div[data-testid="stMetric"]{
            background: rgba(255,255,255,0.85);
            border: 1px solid rgba(49,51,63,0.08);
            border-radius: 16px;
            padding: 10px 14px;
        }
        .section-title{
            font-size: 1.02rem;
            font-weight: 800;
            margin-top: 8px;
            margin-bottom: 8px;
            color:#0f172a;
        }
        .dv-note{
            background:#eff6ff;
            border:1px solid #bfdbfe;
            color:#1e3a8a;
            border-radius:14px;
            padding:12px 14px;
            font-weight:700;
            margin-bottom:14px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='dv-note'>Enter source-wise visits and executive-wise performance. "
        "If an entry for the selected date already exists, it will be updated. Otherwise, a new row will be inserted.</div>",
        unsafe_allow_html=True
    )

    # ============================================================
    # HELPERS
    # ============================================================
    def _to_int(x):
        try:
            return int(float(str(x).strip() or 0))
        except Exception:
            return 0

    def _date_to_sheet_text(d: datetime.date) -> str:
        # Same as old imported data: 24/03/25
        return d.strftime("%d/%m/%y")

    def _month_label(d: datetime.date) -> str:
        # Same as old imported data: Mar-25
        return d.strftime("%b-%y")

    def _parse_any_date_to_date(x):
        s = str(x or "").strip().replace("'", "")
        if not s:
            return None

        for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d-%m-%Y"):
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except Exception:
                pass

        try:
            ts = pd.to_datetime(s, dayfirst=True, errors="coerce")
            if pd.isna(ts):
                return None
            return ts.date()
        except Exception:
            return None

    def _fetch_existing_daily_visit(target_date: datetime.date):
        """
        Finds existing row even if old table has date as 14/05/26,
        14/05/2026, or mistakenly saved as 2026-05-14.
        """
        try:
            possible_dates = [
                target_date.strftime("%d/%m/%y"),
                target_date.strftime("%d/%m/%Y"),
                target_date.strftime("%Y-%m-%d"),
            ]

            res = (
                supabase
                .table(DAILY_VISITS_TABLE)
                .select("*")
                .in_("visit_date", possible_dates)
                .order("id", desc=True)
                .execute()
            )

            return getattr(res, "data", []) or []

        except Exception as e:
            st.error(f"❌ Error checking existing Daily Visits row: {e}")
            return []

    def _insert_daily_visit(payload: dict):
        res = (
            supabase
            .table(DAILY_VISITS_TABLE)
            .insert(payload)
            .execute()
        )
        return getattr(res, "data", []) or []

    def _update_daily_visit(row_id: int, payload: dict):
        res = (
            supabase
            .table(DAILY_VISITS_TABLE)
            .update(payload)
            .eq("id", row_id)
            .execute()
        )
        return getattr(res, "data", []) or []

    def _load_recent_daily_visits(limit: int = 12) -> pd.DataFrame:
        try:
            res = (
                supabase
                .table(DAILY_VISITS_TABLE)
                .select("*")
                .order("id", desc=True)
                .limit(limit)
                .execute()
            )
            data = getattr(res, "data", []) or []
            return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()

    # ============================================================
    # FESTIVAL OPTIONS
    # ============================================================
    FESTIVALS = [
        "New Year",
        "Makar Sankranti",
        "Pongal",
        "Republic Day",
        "Vasant Panchami",
        "Maha Shivratri",
        "Holi",
        "Ram Navami",
        "Mahavir Jayanti",
        "Good Friday",
        "Eid al-Fitr",
        "Buddha Purnima",
        "Eid al-Adha",
        "Raksha Bandhan",
        "Independence Day",
        "Janmashtami",
        "Ganesh Chaturthi",
        "Onam",
        "Navratri",
        "Dussehra / Vijayadashami",
        "Gandhi Jayanti",
        "Karwa Chauth",
        "Diwali",
        "Bhai Dooj",
        "Chhath Puja",
        "Guru Nanak Jayanti",
        "Christmas",
    ]

    FESTIVAL_OPTIONS = ["None"] + FESTIVALS + ["Other (type)"]

    def festival_input_block(label: str, key_prefix: str) -> str:
        choice = st.selectbox(label, FESTIVAL_OPTIONS, index=0, key=f"{key_prefix}_choice")
        other = ""

        if choice == "Other (type)":
            other = st.text_input(
                f"Type {label} name",
                value="",
                placeholder="e.g., Lohri / Akshaya Tritiya / etc.",
                key=f"{key_prefix}_other",
            )

        if choice == "None":
            return ""

        if choice == "Other (type)":
            return str(other or "").strip()

        return str(choice).strip()

    # ============================================================
    # SALES EXECUTIVES
    # Make sure these columns exist in public.daily_visits:
    # tejas_p_revisits, tejas_p_attended, tejas_p_calls_answered, tejas_p_calls_unanswered
    # komal_k_revisits, komal_k_attended, komal_k_calls_answered, komal_k_calls_unanswered
    # ashutosh_s_revisits, ashutosh_s_attended, ashutosh_s_calls_answered, ashutosh_s_calls_unanswered
    # sailee_d_revisits, sailee_d_attended, sailee_d_calls_answered, sailee_d_calls_unanswered
    # dhanashree_w_revisits, dhanashree_w_attended, dhanashree_w_calls_answered, dhanashree_w_calls_unanswered
    # ============================================================
    SALES_EXECUTIVES = [
        ("Tejas P", "tejas_p"),
        ("Komal K", "komal_k"),
        ("Ashutosh S", "ashutosh_s"),
        ("Sailee D", "sailee_d"),
        ("Dhanashree W", "dhanashree_w"),
    ]

    EXECUTIVES_PER_ROW = 4

    # ============================================================
    # FORM
    # ============================================================
    with st.form("daily_visits_form_supabase", clear_on_submit=True):
        st.markdown("#### 🧾 Daily Visit Entry")

        top1, top2 = st.columns([1, 1])

        with top1:
            d = st.date_input(
                "Date",
                value=datetime.date.today(),
                format="DD/MM/YYYY",
                key="daily_visit_date_input"
            )

        with top2:
            st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
            st.info("💡 Entry for the selected day will update if already present.")

        st.markdown("<div class='section-title'>📍 Lead Sources</div>", unsafe_allow_html=True)

        s1, s2, s3 = st.columns(3)
        with s1:
            cp_visits = st.number_input("CP Visits", min_value=0, step=1, value=0)
        with s2:
            walkin = st.number_input("Direct Walk-in", min_value=0, step=1, value=0)
        with s3:
            refs = st.number_input("References", min_value=0, step=1, value=0)

        s4, s5 = st.columns(2)
        with s4:
            digital = st.number_input("Digital", min_value=0, step=1, value=0)
        with s5:
            newspaper = st.number_input("Newspaper", min_value=0, step=1, value=0)

        st.markdown("<div class='section-title'>👥 Sales Executive Wise</div>", unsafe_allow_html=True)

        revisits = {}
        attended = {}
        calls_answered = {}
        calls_unanswered = {}

        for start in range(0, len(SALES_EXECUTIVES), EXECUTIVES_PER_ROW):
            chunk = SALES_EXECUTIVES[start:start + EXECUTIVES_PER_ROW]
            exec_cols = st.columns(len(chunk))

            for idx, (exec_name, exec_key) in enumerate(chunk):
                with exec_cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"**{exec_name}**")

                        revisits[exec_key] = st.number_input(
                            f"{exec_name} Revisits",
                            min_value=0,
                            step=1,
                            value=0,
                            key=f"dv_{exec_key}_revisits"
                        )

                        attended[exec_key] = st.number_input(
                            f"{exec_name} Attended",
                            min_value=0,
                            step=1,
                            value=0,
                            key=f"dv_{exec_key}_attended"
                        )

                        calls_answered[exec_key] = st.number_input(
                            f"{exec_name} Calls Answered",
                            min_value=0,
                            step=1,
                            value=0,
                            key=f"dv_{exec_key}_calls_answered"
                        )

                        calls_unanswered[exec_key] = st.number_input(
                            f"{exec_name} Calls Unanswered",
                            min_value=0,
                            step=1,
                            value=0,
                            key=f"dv_{exec_key}_calls_unanswered"
                        )

        revisit_total = int(sum(revisits.values()))
        attended_total = int(sum(attended.values()))
        calls_answered_total = int(sum(calls_answered.values()))
        calls_unanswered_total = int(sum(calls_unanswered.values()))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revisits", revisit_total)
        m2.metric("Total Attended", attended_total)
        m3.metric("Calls Answered", calls_answered_total)
        m4.metric("Calls Unanswered", calls_unanswered_total)

        st.markdown("<div class='section-title'>📈 Outcome</div>", unsafe_allow_html=True)

        o1, o2 = st.columns(2)
        with o1:
            cancel = st.number_input("Today’s Cancellation", min_value=0, step=1, value=0)
        with o2:
            booking = st.number_input("Today’s Booking", min_value=0, step=1, value=0)

        st.markdown("<div class='section-title'>🎉 Festival (optional)</div>", unsafe_allow_html=True)

        f1, f2, f3 = st.columns(3)
        with f1:
            festival_1 = festival_input_block("Festival 1", "festival1")
        with f2:
            festival_2 = festival_input_block("Festival 2", "festival2")
        with f3:
            festival_3 = festival_input_block("Festival 3", "festival3")

        fest_list = [x for x in [festival_1, festival_2, festival_3] if x]
        if len(set(map(str.lower, fest_list))) != len(fest_list):
            st.warning("⚠️ Same festival selected multiple times. It will be saved as-is.")

        total_visits = int(cp_visits + walkin + refs + digital + newspaper + revisit_total)

        b1, b2 = st.columns(2)
        b1.success(f"📌 Total Visits = {total_visits}")
        b2.info(f"🗓️ Day = {d.strftime('%A')}")

        submit = st.form_submit_button("✅ Submit Entry", type="primary", use_container_width=True)

    # ============================================================
    # SUBMIT HANDLER
    # ============================================================
    if submit:
        try:
            payload = {
                "visit_date": _date_to_sheet_text(d),
                "month": _month_label(d),
                "day": d.strftime("%A"),

                "cp_visits": int(_to_int(cp_visits)),
                "direct_walk_in": int(_to_int(walkin)),
                "references_count": int(_to_int(refs)),
                "digital": int(_to_int(digital)),
                "newspaper": int(_to_int(newspaper)),

                "todays_cancellation": int(_to_int(cancel)),
                "todays_booking": int(_to_int(booking)),

                "total_revisits": int(_to_int(revisit_total)),
                "total_attended": int(_to_int(attended_total)),
                "total_calls_answered": int(_to_int(calls_answered_total)),
                "total_calls_unanswered": int(_to_int(calls_unanswered_total)),

                "festival_1": festival_1 or None,
                "festival_2": festival_2 or None,
                "festival_3": festival_3 or None,

                "total_visits": int(total_visits),
            }

            # Add executive-wise fields dynamically
            for exec_name, exec_key in SALES_EXECUTIVES:
                payload[f"{exec_key}_revisits"] = int(_to_int(revisits.get(exec_key, 0)))
                payload[f"{exec_key}_attended"] = int(_to_int(attended.get(exec_key, 0)))
                payload[f"{exec_key}_calls_answered"] = int(_to_int(calls_answered.get(exec_key, 0)))
                payload[f"{exec_key}_calls_unanswered"] = int(_to_int(calls_unanswered.get(exec_key, 0)))

            existing_rows = _fetch_existing_daily_visit(d)

            if existing_rows:
                latest_row = existing_rows[0]
                row_id = latest_row.get("id")

                if row_id is None:
                    st.error("❌ Existing row found, but ID is missing. Cannot update.")
                else:
                    updated_rows = _update_daily_visit(row_id, payload)

                    if updated_rows:
                        st.success(
                            f"✅ Updated successfully for {d.strftime('%d/%m/%Y')}. "
                            f"Saved Date: {_date_to_sheet_text(d)} | Row ID: {row_id}"
                        )
                    else:
                        st.error(
                            "❌ Supabase returned no updated row. "
                            "Please check table permissions and row ID."
                        )
            else:
                inserted_rows = _insert_daily_visit(payload)

                if inserted_rows:
                    new_id = inserted_rows[0].get("id", "new row")
                    st.success(
                        f"✅ Saved successfully for {d.strftime('%d/%m/%Y')}. "
                        f"Saved Date: {_date_to_sheet_text(d)} | Row ID: {new_id}"
                    )
                else:
                    st.error(
                        "❌ Supabase returned no inserted row. "
                        "Please check permissions and column names."
                    )

            try:
                st.cache_data.clear()
            except Exception:
                pass

        except Exception as e:
            st.error(f"❌ Error saving Daily Visits entry: {e}")

    # ============================================================
    # RECENT ENTRIES PREVIEW
    # ============================================================
    st.markdown("---")
    st.subheader("📋 Recent Daily Visit Entries")

    recent_df = _load_recent_daily_visits(limit=12)

    if recent_df.empty:
        st.info("No Daily Visits entries found yet.")
    else:
        preferred_cols = [
            "id",
            "created_at",
            "visit_date",
            "month",
            "day",
            "cp_visits",
            "direct_walk_in",
            "references_count",
            "digital",
            "newspaper",
            "total_revisits",
            "total_attended",
            "total_calls_answered",
            "total_calls_unanswered",
            "todays_cancellation",
            "todays_booking",
            "total_visits",
        ]

        for exec_name, exec_key in SALES_EXECUTIVES:
            preferred_cols.extend([
                f"{exec_key}_revisits",
                f"{exec_key}_attended",
                f"{exec_key}_calls_answered",
                f"{exec_key}_calls_unanswered",
            ])

        show_cols = [c for c in preferred_cols if c in recent_df.columns]
        display_df = recent_df[show_cols].copy()

        rename_map = {
            "id": "ID",
            "created_at": "Created At",
            "visit_date": "Date",
            "month": "Month",
            "day": "Day",
            "cp_visits": "CP Visits",
            "direct_walk_in": "Direct Walk-in",
            "references_count": "References",
            "digital": "Digital",
            "newspaper": "Newspaper",
            "total_revisits": "Total Revisits",
            "total_attended": "Total Attended",
            "total_calls_answered": "Calls Answered",
            "total_calls_unanswered": "Calls Unanswered",
            "todays_cancellation": "Today's Cancellation",
            "todays_booking": "Today's Booking",
            "total_visits": "Total Visits",
        }

        for exec_name, exec_key in SALES_EXECUTIVES:
            rename_map[f"{exec_key}_revisits"] = f"{exec_name} Revisits"
            rename_map[f"{exec_key}_attended"] = f"{exec_name} Attended"
            rename_map[f"{exec_key}_calls_answered"] = f"{exec_name} Calls Answered"
            rename_map[f"{exec_key}_calls_unanswered"] = f"{exec_name} Calls Unanswered"

        display_df = display_df.rename(columns=rename_map)

        st.dataframe(display_df, use_container_width=True, hide_index=True)
