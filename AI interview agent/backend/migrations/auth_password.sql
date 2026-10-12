-- Ensure the students password column can store bcrypt hashes.
ALTER TABLE students
MODIFY COLUMN password_hash VARCHAR(255) NOT NULL;