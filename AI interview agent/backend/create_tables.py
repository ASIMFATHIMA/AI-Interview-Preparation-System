"""
Utility script to test MySQL connection and create database tables.
Usage:
    python create_tables.py
"""
import sys
from app.database import engine, Base, check_db_connection
import app.models  # Register models


def main():
    print("=" * 60)
    print("AI Career Companion - Database Initialization & Verification")
    print("=" * 60)
    
    print("\n1. Testing MySQL connection...")
    if not check_db_connection():
        print("[-] Connection failed!")
        print("    Please ensure MySQL server is running and credentials in .env are correct.")
        print(f"    Target Database URL: {engine.url.render_as_string(hide_password=True)}")
        sys.exit(1)
        
    print("[+] MySQL connection successful!")

    print("\n2. Creating database tables if they do not exist...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[+] Tables successfully created / verified:")
        for table_name in Base.metadata.tables.keys():
            print(f"    - {table_name}")
    except Exception as e:
        print(f"[-] Error creating tables: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Database foundation is ready!")
    print("=" * 60)


if __name__ == "__main__":
    main()
