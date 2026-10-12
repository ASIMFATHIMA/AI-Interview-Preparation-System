-- Resume Parsing & Extraction - Database Migration
-- Adds raw_resume_text to students and creates structured parsed data tables

-- Add raw_resume_text column to students table
ALTER TABLE students
ADD COLUMN IF NOT EXISTS raw_resume_text TEXT NULL AFTER portfolio_url,
ADD COLUMN IF NOT EXISTS parsed_resume_email VARCHAR(150) NULL AFTER raw_resume_text;

-- Candidate Skills table
CREATE TABLE IF NOT EXISTS candidate_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    skill VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id),
    UNIQUE KEY uk_student_skill (student_id, skill)
);

-- Candidate Education table
CREATE TABLE IF NOT EXISTS candidate_education (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    degree VARCHAR(200) NULL,
    institution VARCHAR(255) NULL,
    start_year VARCHAR(10) NULL,
    end_year VARCHAR(10) NULL,
    description VARCHAR(1000) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id)
);

-- Candidate Experience table
CREATE TABLE IF NOT EXISTS candidate_experience (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    company VARCHAR(255) NULL,
    role VARCHAR(255) NULL,
    start_date VARCHAR(50) NULL,
    end_date VARCHAR(50) NULL,
    description VARCHAR(2000) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id)
);

-- Candidate Projects table
CREATE TABLE IF NOT EXISTS candidate_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    project_name VARCHAR(255) NULL,
    technologies VARCHAR(500) NULL,
    description VARCHAR(2000) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id)
);

-- Candidate Certifications table
CREATE TABLE IF NOT EXISTS candidate_certifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    certification_name VARCHAR(255) NULL,
    organization VARCHAR(255) NULL,
    year VARCHAR(10) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id)
);

-- Candidate Achievements table
CREATE TABLE IF NOT EXISTS candidate_achievements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    achievement VARCHAR(1000) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id)
);
