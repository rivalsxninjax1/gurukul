"""Run this once to generate sample Excel files for testing."""
import pandas as pd
import os

os.makedirs("sample_data", exist_ok=True)

# Format 1 — combined timestamp
pd.DataFrame({
    "user_id":   [101, 102, 101, 103, 102, 103],
    "timestamp": [
        "2026-04-01 08:05:00",
        "2026-04-01 08:10:00",
        "2026-04-01 12:30:00",
        "2026-04-01 08:20:00",
        "2026-04-01 12:45:00",
        "2026-04-01 12:50:00",
    ]
}).to_excel("sample_data/attendance_format1.xlsx", index=False)

# Format 2 — separate date + time columns
pd.DataFrame({
    "user_id": [101, 102, 101, 103],
    "date":    ["2026-04-02", "2026-04-02", "2026-04-02", "2026-04-02"],
    "time":    ["08:01:00",   "08:15:00",   "12:30:00",   "08:22:00"],
}).to_excel("sample_data/attendance_format2.xlsx", index=False)

print("✅ Sample files created in sample_data/")