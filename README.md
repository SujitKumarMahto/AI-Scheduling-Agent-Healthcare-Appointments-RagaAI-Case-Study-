
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
- <img width="1417" height="690" alt="Screenshot 2025-09-05 at 5 41 28 PM" src="https://github.com/user-attachments/assets/c6545b03-43ea-4cb9-a7eb-5577df1d7f26" />
<img width="1403" height="681" alt="Screenshot 2025-09-05 at 5 41 44 PM" src="https://github.com/user-attachments/assets/376fa779-4478-43bf-9a47-2c2dbe66c903" />
<img width="1393" height="668" alt="Screenshot 2025-09-05 at 5 42 07 PM" src="https://github.com/user-attachments/assets/f25d9a07-715b-4b23-82c0-c8e8ed5bd23b" />
<img width="1374" height="662" alt="Screenshot 2025-09-05 at 5 42 25 PM" src="https://github.com/user-attachments/assets/9c7f23f4-305f-428e-a53a-22e90610e0ef" />





