# Seed script for Firestore backend
import google.auth
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-1b731aa11332"

credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
db = firestore.Client(project=PROJECT_ID, credentials=credentials)

def seed():
    print(f"Seeding Firestore in project: {PROJECT_ID}...")

    # Workout Catalog collection
    catalog_items = [
        {
            "id": "workout-1",
            "title": "Zone 2 Base Run",
            "category": "Running",
            "intensity_zone": "Zone 2 (Aerobic)",
            "duration_mins": 45,
            "target_hr_range": "125 - 142 bpm",
            "description": "Low intensity long aerobic run to build endurance base.",
        },
        {
            "id": "workout-2",
            "title": "VO2 Max Hill Repeats",
            "category": "Running",
            "intensity_zone": "Zone 5 (Max Effort)",
            "duration_mins": 40,
            "target_hr_range": "165 - 180 bpm",
            "description": "High intensity hill sprints to maximize oxygen uptake.",
        },
        {
            "id": "workout-3",
            "title": "Sweetspot Cycling Intervals",
            "category": "Cycling",
            "intensity_zone": "Zone 3/4 (Tempo/Threshold)",
            "duration_mins": 60,
            "target_hr_range": "145 - 160 bpm",
            "description": "Sustained efforts just below functional threshold power.",
        },
        {
            "id": "workout-4",
            "title": "Active Recovery Swim",
            "category": "Swimming",
            "intensity_zone": "Zone 1 (Active Recovery)",
            "duration_mins": 30,
            "target_hr_range": "< 120 bpm",
            "description": "Easy technique drills and relaxing laps for muscle recovery.",
        },
    ]

    for item in catalog_items:
        db.collection("workout_catalog").document(item["id"]).set(item)
        print(f"Seeded workout_catalog item: {item['id']}")

    # Workout Logs collection
    log_items = [
        {
            "log_id": "log-001",
            "activity": "Running",
            "workout_name": "Morning Zone 2 Run",
            "distance_km": 8.5,
            "duration_mins": 48,
            "rpe": 5,
            "notes": "Felt super smooth, kept heart rate under 140 bpm.",
            "logged_at": "2026-09-23T07:30:00Z",
        },
        {
            "log_id": "log-002",
            "activity": "Cycling",
            "workout_name": "Endurance Ride",
            "distance_km": 35.0,
            "duration_mins": 75,
            "rpe": 6,
            "notes": "Good cadence work on flat road section.",
            "logged_at": "2026-09-23T16:00:00Z",
        },
    ]

    for log in log_items:
        db.collection("workout_logs").document(log["log_id"]).set(log)
        print(f"Seeded workout_logs item: {log['log_id']}")

    print("Firestore seeding complete!")

if __name__ == "__main__":
    seed()
