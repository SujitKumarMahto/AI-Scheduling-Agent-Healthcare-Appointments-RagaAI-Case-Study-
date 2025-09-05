
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
EXPORT_DIR = Path(__file__).parent / "exports"
TEMPLATES_DIR = Path(__file__).parent / "templates"

PATIENTS_CSV = DATA_DIR / "patients.csv"
SCHEDULE_XLSX = DATA_DIR / "doctor_schedules.xlsx"
INTAKE_FORM = TEMPLATES_DIR / "New Patient Intake Form.pdf"

# ---- Helpers ----
@st.cache_data
def load_patients():
    return pd.read_csv(PATIENTS_CSV)

@st.cache_data
def load_schedule():
    return pd.read_excel(SCHEDULE_XLSX, sheet_name="schedule")

def save_schedule(df):
    with pd.ExcelWriter(SCHEDULE_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="schedule")

def classify_patient(patients, name, dob):
    # Match by full name + DOB (YYYY-MM-DD)
    # Returns (is_returning, patient_row or None)
    full = name.strip().lower()
    dob_str = pd.to_datetime(dob).strftime("%Y-%m-%d")
    candidates = patients[
        (patients["dob"] == dob_str) &
        ((patients["first_name"].str.lower() + " " + patients["last_name"].str.lower()) == full)
    ]
    if not candidates.empty:
        row = candidates.iloc[0]
        return row["returning_patient"] == "Yes", row
    return False, None

def required_duration(is_returning):
    return 30 if is_returning else 60

def find_slots(schedule, doctor, start_date, location, duration_min=30):
    # Finds consecutive available slots to fit duration
    df = schedule.copy()
    df = df[(df["doctor"] == doctor) & (df["location"] == location) & (df["booked"] == "No")]
    df = df[df["date"] >= start_date.strftime("%Y-%m-%d")]
    df = df.sort_values(["date","slot_start"])
    # duration must be 30 or 60; for 60 we need two consecutive slots same date/doctor/location
    options = []
    for date_val, group in df.groupby("date"):
        group = group.reset_index(drop=True)
        if duration_min == 30:
            for idx, row in group.iterrows():
                options.append((date_val, row["slot_start"], row["slot_end"]))
        else:
            for i in range(len(group)-1):
                a = group.iloc[i]
                b = group.iloc[i+1]
                if a["slot_end"] == b["slot_start"]:
                    options.append((date_val, a["slot_start"], b["slot_end"]))
    return options[:50]  # cap

def book_slot(schedule, patient_id, doctor, location, date_str, start, end, appt_type, notes=""):
    df = schedule.copy()
    if appt_type == "New Patient":
        # Need to mark two rows if 60 mins (two consecutive 30-min slots)
        mask_a = (df["date"]==date_str)&(df["doctor"]==doctor)&(df["location"]==location)&(df["slot_start"]==start)
        # locate the next row with slot_start == end-30min
        # easier: mark the first, then find row with slot_end == end
        # first slot to mark:
        idxs = df.index[mask_a].tolist()
        if not idxs:
            return False, df
        idx = idxs[0]
        # find second row contiguous
        row_a = df.loc[idx]
        mask_b = (df["date"]==date_str)&(df["doctor"]==doctor)&(df["location"]==location)&(df["slot_end"]==end)
        idxs_b = df.index[mask_b].tolist()
        if not idxs_b:
            return False, df
        idx_b = idxs_b[0]

        for i in [idx, idx_b]:
            if df.loc[i, "booked"] == "Yes":
                return False, df

        for i in [idx, idx_b]:
            df.loc[i, "booked"] = "Yes"
            df.loc[i, "patient_id"] = patient_id
            df.loc[i, "appointment_type"] = appt_type
            df.loc[i, "notes"] = notes
        return True, df
    else:
        # Returning 30-min
        mask = (df["date"]==date_str)&(df["doctor"]==doctor)&(df["location"]==location)&(df["slot_start"]==start)&(df["slot_end"]==end)
        idxs = df.index[mask].tolist()
        if not idxs:
            return False, df
        idx = idxs[0]
        if df.loc[idx, "booked"] == "Yes":
            return False, df
        df.loc[idx, "booked"] = "Yes"
        df.loc[idx, "patient_id"] = patient_id
        df.loc[idx, "appointment_type"] = appt_type
        df.loc[idx, "notes"] = notes
        return True, df

def export_admin_review(schedule_df):
    out = EXPORT_DIR / f"admin_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        schedule_df.to_excel(writer, index=False, sheet_name="schedule")
    return out

def simulate_send_email(to, subject, body, attachments=None):
    # Stub: log the "email" in exports/logs for demo
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    msg_path = EXPORT_DIR / f"email_{ts}.txt"
    with open(msg_path, "w") as f:
        f.write(f"TO: {to}\nSUBJECT: {subject}\n\n{body}\n")
        if attachments:
            f.write(f"\nAttachments: {attachments}\n")
    return msg_path

def simulate_send_sms(number, message):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sms_path = EXPORT_DIR / f"sms_{ts}.txt"
    with open(sms_path, "w") as f:
        f.write(f"TO: {number}\n\n{message}\n")
    return sms_path

# ---- UI ----
st.set_page_config(page_title="RagaAI - Medical Scheduling Agent (Demo)", page_icon="🩺")

st.title("🩺 RagaAI - AI Scheduling Agent (Demo)")

st.caption("MVP demo: greeting → lookup → smart scheduling → confirmation → intake form → reminders → admin export")

tab1, tab2, tab3 = st.tabs(["Book Appointment", "Reminders & Status", "Admin Review"])

with tab1:
    st.subheader("Patient Greeting")
    name = st.text_input("Full Name (First Last) *")
    dob = st.date_input("Date of Birth *", value=None, min_value=datetime(1900,1,1), max_value=datetime.today())
    doctor = st.selectbox("Preferred Doctor *", ["Dr. Rao", "Dr. Banerjee", "Dr. Kapoor"])
    location = st.selectbox("Location *", ["Bengaluru Clinic", "Mumbai Clinic", "Delhi Clinic"])

    patients = load_patients()
    schedule = load_schedule()

    if st.button("Lookup Patient"):
        if not name or not dob:
            st.error("Please enter name and date of birth.")
        else:
            ret, row = classify_patient(patients, name, dob)
            if row is not None:
                st.success(f"Patient found: {row['first_name']} {row['last_name']} | Returning: {'Yes' if ret else 'No'}")
                st.session_state["patient_id"] = row["patient_id"]
                st.session_state["patient_email"] = row["email"]
                st.session_state["patient_phone"] = row["phone"]
                st.session_state["is_returning"] = ret
                st.session_state["insurance"] = (row["insurance_carrier"], row["member_id"], row["group_number"])
            else:
                st.warning("New patient. We'll collect insurance info.")
                st.session_state["patient_id"] = f"NP-{int(datetime.now().timestamp())}"
                st.session_state["patient_email"] = ""
                st.session_state["patient_phone"] = ""
                st.session_state["is_returning"] = False
                st.session_state["insurance"] = ("", "", "")

    if "is_returning" in st.session_state:
        st.subheader("Insurance Collection")
        carrier, member, group = st.session_state["insurance"]
        carrier = st.text_input("Insurance Carrier", value=carrier)
        member = st.text_input("Member ID", value=member)
        group = st.text_input("Group Number", value=group)

        st.subheader("Smart Scheduling")
        dur = 30 if st.session_state["is_returning"] else 60
        st.write(f"Appointment duration set to **{dur} minutes** based on patient type.")

        start_date = st.date_input("Search availability starting from", value=datetime.today())
        options = find_slots(schedule, doctor, start_date, location, duration_min=dur)

        if not options:
            st.info("No slots available. Try another date/doctor/location.")
        else:
            chosen = st.selectbox("Available Slots", [f"{d} | {s}-{e}" for (d,s,e) in options])
            notes = st.text_area("Notes for clinic (optional)")
            email = st.text_input("Email for confirmation", value=st.session_state.get("patient_email",""))
            phone = st.text_input("Phone for SMS", value=st.session_state.get("patient_phone",""))
            if st.button("Confirm Booking"):
                d, s, e = chosen.split(" | ")[0], chosen.split(" | ")[1].split("-")[0], chosen.split(" | ")[1].split("-")[1]
                ok, new_sched = book_slot(schedule, st.session_state["patient_id"], doctor, location, d, s, e,
                                          "Returning Patient" if dur==30 else "New Patient", notes)
                if ok:
                    save_schedule(new_sched)
                    st.success("Appointment booked! Confirmation sent.")
                    # Confirmation export and messages
                    path = export_admin_review(new_sched)
                    simulate_send_email(email, "Appointment Confirmed",
                                        f"Your appointment with {doctor} at {location} on {d} {s}-{e} is confirmed.\n"
                                        f"Please complete the intake form attached or linked.",
                                        attachments=str(INTAKE_FORM))
                    simulate_send_sms(phone, f"Appt confirmed with {doctor} at {location} on {d} {s}-{e}. Check email for forms.")
                    # Create reminder records
                    rem = pd.DataFrame([{
                        "patient_id": st.session_state["patient_id"],
                        "email": email,
                        "phone": phone,
                        "doctor": doctor,
                        "location": location,
                        "date": d,
                        "start": s,
                        "end": e,
                        "forms_filled": "Pending",
                        "visit_confirmed": "Pending",
                        "cancel_reason": ""
                    }])
                    rem_path = EXPORT_DIR / "reminders.csv"
                    if rem_path.exists():
                        old = pd.read_csv(rem_path)
                        pd.concat([old, rem], ignore_index=True).to_csv(rem_path, index=False)
                    else:
                        rem.to_csv(rem_path, index=False)
                else:
                    st.error("Failed to book slot. It may have just been taken. Please refresh and try another slot.")

with tab2:
    st.subheader("Automated Reminders")
    st.caption("This simulates 3 reminders: initial reminder, then two actionable reminders (forms? confirm/cancel?).")
    rem_path = EXPORT_DIR / "reminders.csv"
    if rem_path.exists():
        df = pd.read_csv(rem_path)
        st.dataframe(df)
        idx = st.number_input("Row to update", min_value=0, max_value=max(len(df)-1,0), step=1, value=0)
        forms = st.selectbox("Forms filled?", ["Pending","Yes","No"], index=0)
        confirm = st.selectbox("Visit confirmed?", ["Pending","Yes","No"], index=0)
        reason = st.text_input("Cancellation reason (if any)")
        if st.button("Send Next Reminder & Update Status"):
            df.loc[idx, "forms_filled"] = forms
            df.loc[idx, "visit_confirmed"] = confirm
            df.loc[idx, "cancel_reason"] = reason
            df.to_csv(rem_path, index=False)
            st.success("Reminder logged + status updated. (Simulated email/SMS sent)")
    else:
        st.info("No reminders yet. Book an appointment first.")

with tab3:
    st.subheader("Admin Review & Export")
    schedule = load_schedule()
    st.dataframe(schedule.tail(50))
    if st.button("Export current schedule for Admin"):
        path = export_admin_review(schedule)
        st.success(f"Exported to {path.name} in 'exports' folder.")
    st.download_button("Download Intake Form (PDF)", data=open(INTAKE_FORM,'rb').read(),
                       file_name="New Patient Intake Form.pdf", mime="application/pdf")
