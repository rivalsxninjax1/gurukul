# run_once: generate_sample.py
import pandas as pd
data = {
    "user_id": [101, 102, 101, 103],
    "timestamp": [
        "2026-01-15 08:05:00",
        "2026-01-15 08:10:00",
        "2026-01-15 12:30:00",
        "2026-01-15 08:20:00",
    ]
}
pd.DataFrame(data).to_excel("sample_attendance.xlsx", index=False)
print("Sample file created!")