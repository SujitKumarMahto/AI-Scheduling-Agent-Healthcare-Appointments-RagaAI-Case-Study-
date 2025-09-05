
# RagaAI - AI Scheduling Agent (MVP Demo)

This package contains a **Streamlit** demo that fulfills the case study requirements:
- Patient greeting and lookup against simulated EMR (CSV with 50 synthetic patients)
- Smart scheduling: **60 min for new** vs **30 min for returning** patients
- Calendar integration simulated via **Excel schedule** (write-through booking)
- Insurance collection (captured during booking)
- Appointment confirmation: **admin Excel export** + simulated **email/SMS**
- Intake forms distributed **after confirmation** (PDF included in `/templates`)
- Reminder system with **3 reminders**, tracking forms filled and visit confirmation/cancellation reason
- Simple **error handling** for slot conflicts, missing inputs

## How to run
```bash
pip install -r requirements.txt
streamlit run app.py
```
The UI opens in your browser. Use the tabs to navigate.

## Data & Files
- `data/patients.csv` — 50 synthetic patients
- `data/doctor_schedules.xlsx` — 5 working days of 30-min slots for 3 doctors
- `templates/New Patient Intake Form.pdf` — provided sample intake form
- `exports/` — confirmation exports, email/SMS logs, reminders

## Notes
- Email/SMS are **simulated** by writing text files into `exports/`.
- For real integrations, implement in `utils.py` (e.g., SMTP credentials or Twilio API).

