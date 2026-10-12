-- M2.1 migration for databases created before the structured job knowledge base.
ALTER TABLE jobs ADD COLUMN dataset_job_id VARCHAR(32) NULL;
ALTER TABLE jobs ADD COLUMN work_mode VARCHAR(30) NULL;
ALTER TABLE jobs ADD COLUMN job_type VARCHAR(30) NULL;
ALTER TABLE jobs ADD COLUMN qualifications TEXT NULL;
ALTER TABLE jobs ADD COLUMN projects_or_domain VARCHAR(200) NULL;
ALTER TABLE jobs ADD COLUMN keywords TEXT NOT NULL DEFAULT '[]';
ALTER TABLE jobs ADD COLUMN source VARCHAR(100) NOT NULL DEFAULT 'Curated Sample Dataset';
ALTER TABLE jobs ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'Active';
CREATE UNIQUE INDEX uq_jobs_dataset_job_id ON jobs (dataset_job_id);