import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.resume_parser import parse_resume

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_resumes")

samples = [
    ("sample1_fresh_graduate.pdf", "Fresh Graduate"),
    ("sample2_experienced.pdf", "Experienced Professional"),
    ("sample3_data_scientist.pdf", "Data Scientist"),
    ("sample4_minimal.pdf", "Minimal Resume"),
]

for filename, label in samples:
    file_path = os.path.join(TEST_DIR, filename)
    if not os.path.exists(file_path):
        print(f"[SKIP] {label}: {file_path} not found")
        continue

    with open(file_path, "rb") as f:
        _, ext = os.path.splitext(filename)
        data = parse_resume(f.read(), ext.lower())

    print(f"\n========== {label} ({filename}) ==========\n")
    print("Name:", data.get("name"))
    print("Email:", data.get("email"))
    print("Phone:", data.get("phone"))
    print("Location:", data.get("location"))
    print("LinkedIn:", data.get("linkedin_url"))
    print("GitHub:", data.get("github_url"))
    print("Portfolio:", data.get("portfolio_url"))

    print("\nSkills:")
    for skill in data.get("skills", []):
        print("-", skill)

    print("\nEducation:")
    for edu in data.get("education", []):
        print("-", edu)

    print("\nExperience:")
    for exp in data.get("experience", []):
        print("-", exp)

    print("\nProjects:")
    for proj in data.get("projects", []):
        print("-", proj)

    print("\nCertifications:")
    for cert in data.get("certifications", []):
        print("-", cert)

    print("\nAchievements:")
    for ach in data.get("achievements", []):
        print("-", ach)
