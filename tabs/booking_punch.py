if selected_main_section == "Booking Punch":
    # --- BOOKING PUNCH ---
    st.header("📝 Booking Punch")

    # Supabase connection guard
    if not supabase_connected:
        st.warning("📋 Please connect to Supabase to submit bookings.")
        st.stop()

    # ---- session defaults ----
    st.session_state.setdefault("inputs_locked", False)
    st.session_state.setdefault("calculated", False)
    st.session_state.setdefault("booking_selected_rate", None)
    st.session_state.setdefault("agreement_cost", None)
    st.session_state.setdefault("first_visit_date", None)
    st.session_state.setdefault("stamp_duty_percent", 7)

    # Multi-parking defaults
    st.session_state.setdefault("parkings", [{"type": "Stilt", "number": ""}])

    # Offer defaults
    st.session_state.setdefault("offer_1", "")
    st.session_state.setdefault("offer_2", "")

    # Basic defaults
    st.session_state.setdefault("floor", 1)
    st.session_state.setdefault("wing", "E")

    # Carpet selection state
    st.session_state.setdefault("booking_carpet_area_main", None)

    # Merged Units default
    st.session_state.setdefault("merged_units", "")

    # Location default
    st.session_state.setdefault("location", "")

    # Visit Count default
    st.session_state.setdefault("visit_count", "")

    # Location dropdown options
    location_options = [
        "",
        "Dhayari",
        "Dhayari Gaon",
        "Dhayari Phata",
        "Chavan Baug",
        "Benkar Nagar",
        "Ganesh Nagar (Dhayari)",
        "Shree Nagar (Dhayari)",
        "Raykar Mala",
        "Garmal",
        "Morya Nagar (Dhayari)",
        "Saikrupa Nagar",
        "Siddharth Nagar (Dhayari side)",
        "Laxmi Nagar (Dhayari)",
        "Nanded",
        "Nanded Gaon",
        "Nanded Fata",
        "Nanded City",
        "Deshmukh Nagar",
        "Pandurang Industrial Area",
        "Vadgaon Budruk",
        "Santosh Nagar (Vadgaon)",
        "Kirloskar Colony",
        "Anand Nagar (Sinhagad Road)",
        "Manik Baug",
        "Suncity",
        "Narhe",
        "Narhe Gaon",
        "Khadewadi",
        "Kirkatwadi",
        "Kirkatwadi Gaon",
        "Kolhewadi",
        "Donje",
        "Donje Gaon",
        "Mukai Nagar",
        "Shivane",
        "Uttam Nagar",
        "Warje",
        "Warje Malwadi",
        "Ram Nagar (Warje)",
        "Gokul Nagar (Warje)",
        "Hingne Budruk",
        "Hingne Khurd",
        "Karve Nagar",
        "Kothrud",
        "Swargate"
    ]

    # ---- helpers ----
    def _none_if_blank(v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    def _ensure_parking_keys():
        """Ensure widget keys exist for current parking rows."""
        for i, p in enumerate(st.session_state.parkings):
            st.session_state.setdefault(f"parking_type_{i}", p.get("type", "Stilt"))
            st.session_state.setdefault(f"parking_number_{i}", p.get("number", ""))

    def _sync_parkings_from_keys():
        """Read current widget values into st.session_state.parkings."""
        new_list = []
        for i in range(len(st.session_state.parkings)):
            p_type = st.session_state.get(f"parking_type_{i}", "Stilt")
            p_num = (st.session_state.get(f"parking_number_{i}", "") or "").strip()
            new_list.append({"type": p_type, "number": p_num})
        st.session_state.parkings = new_list

    def _has_at_least_one_parking():
        """Parking compulsory: at least one complete Type+Number entry."""
        for p in st.session_state.get("parkings", []):
            p_type = (p.get("type") or "").strip()
            p_num = (p.get("number") or "").strip()
            if p_type and p_num:
                return True
        return False

    def _parking_text():
        parking_parts = []
        for p in st.session_state.get("parkings", []):
            p_type = (p.get("type") or "").strip()
            p_num = (p.get("number") or "").strip()
            if p_type and p_num:
                parking_parts.append(f"{p_type}-{p_num}")
        return " , ".join(parking_parts) if parking_parts else ""

    def _reset_booking_form_state():
        st.session_state.calculated = False
        st.session_state.inputs_locked = False
        st.session_state.booking_selected_rate = None
        st.session_state.agreement_cost = None

        reset_keys = [
            "booking_date",
            "first_visit_date",
            "visit_count",
            "cust_name",
            "wing",
            "floor",
            "flat_number",
            "unit_type",
            "location",
            "merged_units",
            "booking_carpet_area_main",
            "final_price_lakhs",
            "stamp_duty_percent",
            "offer_1",
            "offer_2",
            "civil_changes",
            "lead_type",
            "sales_exec",
        ]

        for k in reset_keys:
            st.session_state.pop(k, None)

        for i in range(len(st.session_state.get("parkings", []))):
            st.session_state.pop(f"parking_type_{i}", None)
            st.session_state.pop(f"parking_number_{i}", None)

        st.session_state.parkings = [{"type": "Stilt", "number": ""}]
        _ensure_parking_keys()

    _ensure_parking_keys()

    # Keep calc false while editing unlocked
    if not st.session_state.inputs_locked:
        st.session_state.calculated = False

    all_carpets = [480.94, 482.12, 655.10, 665.65, 666.29, 678, 689, 790, 545, 756]

    offer_options = [
        "",
        "1 Gram Gold Coin",
        "2 Gram Gold Coin",
        "200 Gram Silver",
        "Kitchen Trolley",
        "25000 Electronic Voucher"
    ]

    def offer_label(opt: str) -> str:
        return "— No Offer —" if opt == "" else opt

    visit_count_options = [""] + list(range(1, 11))

    def _visit_label(x):
        return "Select" if x == "" else str(x)

    # ---- SINGLE FORM: fill everything + add parking + lock ----
    with st.form("booking_inputs_form", clear_on_submit=False):
        st.caption("Fill all details including Carpet Area. Use ➕ in Parking if needed. Then Lock Inputs to calculate.")

        # Dates
        with st.container(border=True):
            st.subheader("🗓️ Dates", divider="gray")
            c1, c2, c3 = st.columns(3)

            with c1:
                st.date_input(
                    "Date of Booking *",
                    format="DD/MM/YYYY",
                    key="booking_date",
                    disabled=st.session_state.inputs_locked
                )

            with c2:
                st.date_input(
                    "Date of First Visit *",
                    format="DD/MM/YYYY",
                    key="first_visit_date",
                    disabled=st.session_state.inputs_locked
                )

            with c3:
                st.selectbox(
                    "Visit Count *",
                    options=visit_count_options,
                    format_func=_visit_label,
                    key="visit_count",
                    help="On which visit booking happened, 1 to 10.",
                    disabled=st.session_state.inputs_locked
                )

        st.divider()

        # Basic Details
        with st.container(border=True):
            st.subheader("👤 Basic Details", divider="gray")

            b1, b2, b3 = st.columns(3)

            with b1:
                st.text_input(
                    "Customer Name *",
                    key="cust_name",
                    placeholder="e.g., Rohan Sharma",
                    disabled=st.session_state.inputs_locked
                )

            with b2:
                st.selectbox(
                    "Wing *",
                    ["E", "F", "C"],
                    key="wing",
                    disabled=st.session_state.inputs_locked
                )

            with b3:
                st.selectbox(
                    "Floor *",
                    list(range(1, 14)),
                    key="floor",
                    disabled=st.session_state.inputs_locked
                )

            u1, u2 = st.columns(2)

            with u1:
                st.text_input(
                    "Flat Number *",
                    key="flat_number",
                    placeholder="e.g., 1004",
                    disabled=st.session_state.inputs_locked
                )

            with u2:
                st.selectbox(
                    "Type *",
                    ["1BHK", "2BHK"],
                    key="unit_type",
                    disabled=st.session_state.inputs_locked
                )

            l1, l2 = st.columns(2)

            with l1:
                st.selectbox(
                    "Location *",
                    options=location_options,
                    key="location",
                    disabled=st.session_state.inputs_locked
                )

            with l2:
                st.selectbox(
                    "Merged Units",
                    options=["", "1+1", "2+1", "2+2"],
                    key="merged_units",
                    help="Select if this booking is for combined flats. Leave blank if not merged.",
                    disabled=st.session_state.inputs_locked
                )

        st.divider()

        # Carpet Area
        with st.container(border=True):
            st.subheader("📐 Carpet Area", divider="gray")

            st.selectbox(
                "Booking: Carpet Area *",
                options=all_carpets,
                key="booking_carpet_area_main",
                disabled=st.session_state.inputs_locked
            )

        st.divider()

        # Parking
        with st.container(border=True):
            st.subheader("🚗 Parking", divider="gray")
            st.caption(
                "Saved as Type-Number, for example Basement-121. "
                "If multiple: Basement-121 , Basement-122"
            )

            parking_types = ["Stilt", "Ground", "Basement", "Tandum S", "Tandum B"]

            add_row_cols = st.columns([3, 1])

            with add_row_cols[1]:
                add_parking_clicked = st.form_submit_button(
                    "➕ Add",
                    use_container_width=True,
                    disabled=st.session_state.inputs_locked
                )

            if add_parking_clicked:
                _sync_parkings_from_keys()
                st.session_state.parkings.append({"type": "Stilt", "number": ""})
                _ensure_parking_keys()

            for i in range(len(st.session_state.parkings)):
                r1, r2 = st.columns([1, 1])

                with r1:
                    st.selectbox(
                        f"Parking Type {i + 1}",
                        parking_types,
                        key=f"parking_type_{i}",
                        disabled=st.session_state.inputs_locked
                    )

                with r2:
                    st.text_input(
                        f"Parking Number {i + 1} *",
                        key=f"parking_number_{i}",
                        placeholder="e.g., 121 or 121A",
                        help="Letters allowed, example 21A.",
                        disabled=st.session_state.inputs_locked
                    )

        st.divider()

        # Commercials
        with st.container(border=True):
            st.subheader("💰 Commercials", divider="gray")

            m1, m2 = st.columns([1, 1])

            with m1:
                st.number_input(
                    "Final Price (in Lakhs) *",
                    value=st.session_state.get("final_price_lakhs")
                    if st.session_state.get("final_price_lakhs") is not None else 0.0,
                    placeholder="Enter Final Price",
                    key="final_price_lakhs",
                    disabled=st.session_state.inputs_locked
                )

            with m2:
                st.selectbox(
                    "Stamp Duty (for calc only) *",
                    options=[6, 7],
                    format_func=lambda x: f"{x}%",
                    key="stamp_duty_percent",
                    help="Used in calculation and saved in Supabase as stamp_duty_percent.",
                    disabled=st.session_state.inputs_locked
                )

        st.divider()

        # Offers & Remarks
        with st.container(border=True):
            st.subheader("🎁 Offers & Remarks", divider="gray")

            o1, o2 = st.columns(2)

            with o1:
                st.selectbox(
                    "Offer 1",
                    offer_options,
                    key="offer_1",
                    format_func=offer_label,
                    disabled=st.session_state.inputs_locked
                )

            with o2:
                st.selectbox(
                    "Offer 2",
                    offer_options,
                    key="offer_2",
                    format_func=offer_label,
                    disabled=st.session_state.inputs_locked
                )

            st.text_input(
                "Civil Changes (if any)",
                key="civil_changes",
                placeholder="e.g., Kitchen platform shift, extra electrical points",
                disabled=st.session_state.inputs_locked
            )

        st.divider()

        # Lead & Exec
        with st.container(border=True):
            st.subheader("👥 Lead & Executive", divider="gray")

            le1, le2 = st.columns(2)

            with le1:
                st.selectbox(
                    "Lead Type *",
                    ["Direct", "CP", "Digital", "Referral", "Hoarding"],
                    key="lead_type",
                    disabled=st.session_state.inputs_locked
                )

            with le2:
                st.selectbox(
                    "Sales Executive *",
                    ["Komal K", "Tejas P", "Ashutosh S", "Sailee D", "Dhanashree W"],
                    key="sales_exec",
                    disabled=st.session_state.inputs_locked
                )

        st.markdown("")

        lock_clicked = st.form_submit_button(
            "🔒 Lock Inputs & Calculate",
            use_container_width=True,
            disabled=st.session_state.inputs_locked
        )

    # ---- handle lock ----
    if lock_clicked:
        _sync_parkings_from_keys()

        valid = True

        # Dates compulsory
        if not st.session_state.get("booking_date") or not st.session_state.get("first_visit_date"):
            st.error("❌ Please fill both dates: Date of Booking and Date of First Visit.")
            valid = False

        # Visit Count compulsory
        if st.session_state.get("visit_count") == "" or st.session_state.get("visit_count") is None:
            st.error("❌ Visit Count is compulsory. Please select 1 to 10.")
            valid = False

        # Basic details compulsory
        if not (st.session_state.get("cust_name") or "").strip():
            st.error("❌ Customer Name is compulsory.")
            valid = False

        if not (st.session_state.get("flat_number") or "").strip():
            st.error("❌ Flat Number is compulsory.")
            valid = False

        if not (st.session_state.get("location") or "").strip():
            st.error("❌ Location is compulsory.")
            valid = False

        # Carpet area compulsory
        if st.session_state.get("booking_carpet_area_main") is None:
            st.error("❌ Please select Carpet Area before locking.")
            valid = False

        # Parking compulsory
        if not _has_at_least_one_parking():
            st.error("❌ Parking is compulsory. Please enter at least 1 Parking Number.")
            valid = False

        # Commercials compulsory
        fp = st.session_state.get("final_price_lakhs")

        if fp is None or fp <= 0:
            st.error("❌ Please enter a valid Final Price in Lakhs before locking inputs.")
            valid = False

        # Validate date order
        if valid and st.session_state.get("first_visit_date") and st.session_state.get("booking_date"):
            gap = (st.session_state.booking_date - st.session_state.first_visit_date).days

            if gap < 0:
                st.error("❌ First Visit Date cannot be after Date of Booking.")
                valid = False

        if valid:
            booking_carpet_area = st.session_state.get("booking_carpet_area_main")
            booking_saleable = round(booking_carpet_area * 1.38, 2)

            # GST logic based on total package
            registration = 30000
            total_package = fp * 100000
            booking_adjusted_cost = total_package - registration

            gst_percent = 1 if total_package <= 4889999 else 5
            stamp = st.session_state.stamp_duty_percent

            booking_divisor = 1 + ((stamp + gst_percent) / 100)

            agreement_cost = round(booking_adjusted_cost / booking_divisor)
            booking_selected_rate = round(agreement_cost / booking_saleable)

            st.session_state.booking_selected_rate = booking_selected_rate
            st.session_state.agreement_cost = agreement_cost
            st.session_state.inputs_locked = True
            st.session_state.calculated = True

            st.success("Inputs locked and calculation done. You can now submit booking.")

    # ---- Show conversion period ----
    if st.session_state.get("first_visit_date") and st.session_state.get("booking_date"):
        conversion_days = (st.session_state.booking_date - st.session_state.first_visit_date).days

        if conversion_days >= 0:
            st.info(f"🕒 Conversion Period: {conversion_days} days")
        else:
            st.warning("⚠️ First Visit Date is after Date of Booking. Please check the dates.")

    # ---- Show results ----
    st.text_input(
        "Rate Per Sqft (Auto)",
        value=st.session_state.get("booking_selected_rate"),
        disabled=True
    )

    st.text_input(
        "Agreement Cost (Auto)",
        value=st.session_state.get("agreement_cost"),
        disabled=True
    )

    # ---- Submit Booking ----
    can_submit = st.session_state.inputs_locked and st.session_state.calculated

    if st.button("✅ Submit Booking", disabled=not can_submit):
        try:
            _sync_parkings_from_keys()

            # Safety validations again
            if not st.session_state.get("booking_date") or not st.session_state.get("first_visit_date"):
                st.error("❌ Both dates are compulsory.")
                st.stop()

            if st.session_state.get("visit_count") == "" or st.session_state.get("visit_count") is None:
                st.error("❌ Visit Count is compulsory.")
                st.stop()

            if not (st.session_state.get("cust_name") or "").strip():
                st.error("❌ Customer Name is compulsory.")
                st.stop()

            if not (st.session_state.get("flat_number") or "").strip():
                st.error("❌ Flat Number is compulsory.")
                st.stop()

            if not (st.session_state.get("location") or "").strip():
                st.error("❌ Location is compulsory.")
                st.stop()

            if st.session_state.get("booking_carpet_area_main") is None:
                st.error("❌ Carpet Area is compulsory.")
                st.stop()

            if not _has_at_least_one_parking():
                st.error("❌ Parking is compulsory. Please enter at least 1 Parking Number.")
                st.stop()

            _days_gap = (st.session_state.booking_date - st.session_state.first_visit_date).days

            if _days_gap < 0:
                st.error("❌ First Visit Date cannot be after Date of Booking.")
                st.stop()

            booking_date_obj = st.session_state.booking_date
            first_visit_date_obj = st.session_state.first_visit_date

            month_label = booking_date_obj.strftime("%B %y").upper()

            agreement_cost = float(st.session_state.agreement_cost)

            parking_text = _parking_text()

            # Supabase row for public.bookings
            booking_row = {
                "booking_date": booking_date_obj.isoformat(),
                "customer_name": (st.session_state.get("cust_name") or "").strip(),
                "wing": st.session_state.get("wing"),
                "floor": int(st.session_state.get("floor")),
                "flat_number": (st.session_state.get("flat_number") or "").strip(),
                "type": st.session_state.get("unit_type"),
                "final_price": float(st.session_state.get("final_price_lakhs")),
                "rate": float(st.session_state.get("booking_selected_rate")),
                "agreement_cost": agreement_cost,
                "lead_type": st.session_state.get("lead_type"),
                "sales_executive": st.session_state.get("sales_exec"),
                "month": month_label,

                "civil_changes": _none_if_blank(st.session_state.get("civil_changes", "")),
                "offer_1": _none_if_blank(st.session_state.get("offer_1", "")),
                "offer_2": _none_if_blank(st.session_state.get("offer_2", "")),
                "offer_1_rewarded": None,
                "offer_2_rewarded": None,
                "referral_given": None,

                "stamp_duty": None,
                "agreement_done": None,
                "incentive": None,
                "rcc": None,
                "possession_handover": None,
                "insider_banker": None,
                "outsider_banker": None,

                "carpet_area": float(st.session_state.get("booking_carpet_area_main")),

                "first_visit_date": first_visit_date_obj.isoformat(),
                "conversion_period_days": int(_days_gap),
                "parking_number": parking_text,
                "merged_units": _none_if_blank(st.session_state.get("merged_units", "")),
                "location": (st.session_state.get("location") or "").strip(),
                "visit_count": int(st.session_state.get("visit_count")),
                "received_amount": None,
                "stamp_duty_percent": float(st.session_state.get("stamp_duty_percent")),
            }

            # Insert into Supabase
            supabase.table("bookings").insert(booking_row).execute()

            # Clear cached data if load_all_data uses Streamlit cache
            try:
                st.cache_data.clear()
            except Exception:
                pass

            st.success("🎉 Booking, Conversion Period & Remarks submitted successfully to Supabase!")

            # ---- Reset ----
            _reset_booking_form_state()

        except Exception as e:
            st.error(f"❌ Error submitting to Supabase: {e}")
