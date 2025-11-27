"""
Migration script to add profile setup fields to users table and create experiences/educations tables.

This migration adds:
- Extended profile fields to users table (email, headline, summary, location, industry, linkedin_profile_url, cv_filename, skills, profile_setup_completed)
- experiences table for work experience
- educations table for educational background

Run this script with: python -m server.migrations.add_profile_setup_fields
"""

from sqlalchemy import text
from server.database import engine
from server.config import settings


def run_migration():
    """Execute the migration to add profile setup fields and tables."""

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            print("Starting migration: add_profile_setup_fields")

            # Add new columns to users table
            print("Adding columns to users table...")

            # Check if columns already exist before adding
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='email'
            """))

            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR"))
                print("  - Added email column")

            # Add remaining columns
            columns_to_add = [
                ("headline", "VARCHAR"),
                ("summary", "TEXT"),
                ("location", "VARCHAR"),
                ("industry", "VARCHAR"),
                ("linkedin_profile_url", "VARCHAR"),
                ("cv_filename", "VARCHAR"),
                ("skills", "VARCHAR[]"),
                ("profile_setup_completed", "BOOLEAN DEFAULT FALSE")
            ]

            for col_name, col_type in columns_to_add:
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='{col_name}'
                """))

                if result.fetchone() is None:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    print(f"  - Added {col_name} column")

            # Create experiences table
            print("Creating experiences table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    company VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    start_date VARCHAR,
                    end_date VARCHAR,
                    is_current BOOLEAN DEFAULT FALSE,
                    description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("  - Created experiences table")

            # Create educations table
            print("Creating educations table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS educations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    school VARCHAR NOT NULL,
                    degree VARCHAR NOT NULL,
                    field_of_study VARCHAR,
                    start_date VARCHAR,
                    end_date VARCHAR,
                    description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("  - Created educations table")

            # Create indexes for better query performance
            print("Creating indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_experiences_user_id ON experiences(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_educations_user_id ON educations(user_id)"))
            print("  - Created indexes")

            # Commit transaction
            trans.commit()
            print("Migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {e}")
            raise


if __name__ == "__main__":
    print(f"Running migration on database: {settings.database_url}")
    run_migration()
