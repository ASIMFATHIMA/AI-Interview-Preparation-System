"""Generate the curated sample internship dataset across 15 technical domains with verifiable data cleaning."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
sys.path.insert(0, str(ROOT / "backend"))

from app.services.job_data_cleaner import clean_records

LOCATIONS = [
    "Bengaluru, Karnataka", "Hyderabad, Telangana", "Chennai, Tamil Nadu",
    "Pune, Maharashtra", "Mumbai, Maharashtra", "Delhi, NCR",
    "Noida, Uttar Pradesh", "Kochi, Kerala", "Remote, India",
    "Gurugram, Haryana", "Ahmedabad, Gujarat",
]

COMPANIES = [
    "TechNova Solutions", "BlueOrbit Labs", "Vertex Digital", "DataSpring Systems",
    "CloudMosaic Technologies", "NexaWorks", "BrightStack Innovations", "Aster Analytics",
    "CodeHarbor India", "QuantumLeaf AI", "Northstar Software", "OpenTrail Systems",
    "SignalForge Labs", "CivicByte Labs", "Riverstone Technologies", "Zenith Cyberworks",
    "Aura Intelligence", "CoreLogic Infotech", "Prism Cloud Solutions", "Apex DataWorks",
]

# 15 distinct technical domains with realistic titles, skills, and project contexts
DOMAINS = [
    {
        "domain": "Artificial Intelligence",
        "title": "AI Research & Development Intern",
        "required": ["Python", "Artificial Intelligence", "Machine Learning", "PyTorch"],
        "preferred": ["Computer Vision", "TensorFlow", "CUDA", "FastAPI"],
        "project": "applied AI perception and inference systems",
        "description": "Collaborate with senior researchers to benchmark deep neural architectures and prototype intelligent agents for enterprise workflows.",
        "responsibilities": [
            "Implement and evaluate cutting-edge AI architectures on real-world datasets",
            "Optimize model inference latency and memory footprints using PyTorch and ONNX",
            "Document experimental findings, ablation studies, and technical metrics",
            "Partner with software engineers to package AI prototypes into microservices",
        ],
        "education": "B.Tech/B.E./M.S. in Computer Science, Artificial Intelligence, or Data Science",
        "qualifications": "Strong foundation in calculus, linear algebra, and modern AI algorithms. Demonstrable project work in Python.",
    },
    {
        "domain": "Machine Learning",
        "title": "Machine Learning Engineer Intern",
        "required": ["Python", "Machine Learning", "Scikit-learn", "Pandas", "NumPy"],
        "preferred": ["XGBoost", "MLflow", "SQL", "Docker"],
        "project": "predictive modeling and classification pipelines",
        "description": "Join our ML platform team to develop robust tabular predictors and anomaly detection pipelines from dirty real-world sensor streams.",
        "responsibilities": [
            "Perform feature engineering, imputation, and exploratory data analysis",
            "Train, tune, and evaluate ensemble models (XGBoost, Random Forests, LightGBM)",
            "Track experiments, hyperparameter runs, and model versions via MLflow",
            "Build automated data validation tests for production inference feeds",
        ],
        "education": "B.Tech/B.E. in Computer Science, AI, Data Science, or related engineering branch",
        "qualifications": "Hands-on experience with scikit-learn and statistical modeling. Solid knowledge of model evaluation metrics.",
    },
    {
        "domain": "Data Science",
        "title": "Data Science Intern",
        "required": ["Python", "Pandas", "NumPy", "SQL", "Statistics"],
        "preferred": ["Scikit-learn", "Tableau", "Hypothesis Testing", "Seaborn"],
        "project": "customer behavior clustering and statistical inference",
        "description": "Apply statistical rigor and scientific methodology to extract actionable signals and build predictive customer segmentation models.",
        "responsibilities": [
            "Formulate and execute hypothesis tests (A/B testing, ANOVA, chi-square)",
            "Extract, aggregate, and normalize multi-source transaction logs using SQL",
            "Construct customer clustering and propensity scoring algorithms",
            "Present data-driven insights and interactive dashboards to business stakeholders",
        ],
        "education": "B.Tech/B.Sc./M.Sc. in Data Science, Statistics, Mathematics, or Computer Science",
        "qualifications": "Comfortable with probability, statistical significance, and Python data manipulation toolchains.",
    },
    {
        "domain": "Data Analytics",
        "title": "Data Analytics Intern",
        "required": ["SQL", "Python", "Data Visualization", "Power BI", "Excel"],
        "preferred": ["Tableau", "ETL", "Statistics", "DAX"],
        "project": "operational KPI dashboards and business intelligence reporting",
        "description": "Design interactive analytical reports and automated ETL pipelines that give executive leadership visibility into operational metrics.",
        "responsibilities": [
            "Write complex SQL queries, window functions, and views to extract enterprise KPIs",
            "Develop executive-ready dashboards in Power BI and Tableau with clean UX",
            "Automate recurring weekly and monthly reporting flows using Python scripts",
            "Audit raw transactional databases for integrity gaps and data discrepancies",
        ],
        "education": "B.Tech/B.Sc./BCA in Computer Applications, Information Systems, or Business Analytics",
        "qualifications": "High proficiency in SQL querying and data visualization principles. Sharp analytical and problem-solving mindset.",
    },
    {
        "domain": "Generative AI",
        "title": "Generative AI & LLM Intern",
        "required": ["Python", "Generative AI", "LLM", "Prompt Engineering", "RAG"],
        "preferred": ["LangChain", "Vector Database", "FAISS", "Hugging Face"],
        "project": "context-grounded retrieval-augmented generation and autonomous agents",
        "description": "Push the frontier of enterprise LLM applications by building hallucination-resistant RAG systems and semantic search engines.",
        "responsibilities": [
            "Design multi-stage RAG pipelines combining dense retrieval and re-ranking",
            "Experiment with system prompt structuring, few-shot conditioning, and guardrails",
            "Benchmark retrieval accuracy and faithfulness across diverse vector embeddings",
            "Deploy conversational API endpoints using FastAPI and vector store indexes",
        ],
        "education": "B.Tech/B.E. in Computer Science, AI, Information Technology or related discipline",
        "qualifications": "Familiarity with transformer architectures, embeddings, vector databases, and modern LLM orchestration libraries.",
    },
    {
        "domain": "NLP",
        "title": "Natural Language Processing Intern",
        "required": ["Python", "NLP", "Machine Learning", "Transformers"],
        "preferred": ["PyTorch", "SpaCy", "Hugging Face", "Text Processing"],
        "project": "named entity recognition and multilingual text classification",
        "description": "Develop NLP models that extract semantic entities, classify intent, and summarize unstructured documentation at scale.",
        "responsibilities": [
            "Preprocess and tokenize unstructured text corpora across multiple languages",
            "Fine-tune pre-trained transformer backbones (BERT, RoBERTa) for domain tasks",
            "Evaluate precision, recall, and F1 scores on imbalanced linguistic datasets",
            "Deploy inference pipelines with ONNX runtime for ultra-low latency parsing",
        ],
        "education": "B.Tech/M.Tech in Computer Science, Artificial Intelligence, or Computational Linguistics",
        "qualifications": "Solid grasp of tokenization, attention mechanisms, embeddings, and sequence-to-sequence modeling.",
    },
    {
        "domain": "Python Development",
        "title": "Python Developer Intern",
        "required": ["Python", "Git", "REST API", "Data Structures"],
        "preferred": ["FastAPI", "Flask", "Pytest", "PostgreSQL"],
        "project": "automated workflow pipelines and CLI development utilities",
        "description": "Contribute to core internal Python tooling, microservice integrations, and automated batch processing systems.",
        "responsibilities": [
            "Write modular, object-oriented, PEP-8 compliant Python code",
            "Build clean RESTful endpoints and integrate external third-party SDKs",
            "Author automated unit and regression tests with Pytest to achieve high coverage",
            "Refactor legacy script workflows into maintainable asynchronous tasks",
        ],
        "education": "B.Tech/B.E./BCA in Computer Science, IT, or Software Engineering",
        "qualifications": "Strong Python fundamentals: generators, decorators, typing, and standard library data structures.",
    },
    {
        "domain": "Backend Development",
        "title": "Backend Engineering Intern",
        "required": ["Python", "FastAPI", "SQL", "PostgreSQL", "REST API"],
        "preferred": ["Docker", "Redis", "SQLAlchemy", "Celery"],
        "project": "high-throughput transactional microservices and caching",
        "description": "Engineer resilient backend architectures, schema migrations, and REST APIs that power high-concurrency client applications.",
        "responsibilities": [
            "Design normalized relational schemas and database indexes in PostgreSQL",
            "Develop asynchronous REST API endpoints with FastAPI and Pydantic validation",
            "Implement distributed caching strategies with Redis to minimize database load",
            "Containerize microservice environments using Docker and Docker Compose",
        ],
        "education": "B.Tech/B.E. in Computer Science, Software Engineering, or Information Technology",
        "qualifications": "Sound understanding of HTTP protocol, client-server models, relational databases, and API design principles.",
    },
    {
        "domain": "Full Stack Development",
        "title": "Full Stack Developer Intern",
        "required": ["JavaScript", "React", "Node.js", "HTML", "CSS", "REST API"],
        "preferred": ["TypeScript", "MongoDB", "Express", "Tailwind CSS"],
        "project": "end-to-end customer portal with real-time state synchronization",
        "description": "Bridge frontend user experiences and backend business logic by delivering complete, polished end-to-end features.",
        "responsibilities": [
            "Craft responsive, accessible UI views in React with clean component modularity",
            "Implement server-side controllers, routing, and middleware in Node.js/Express",
            "Manage persistent document models and queries using MongoDB or PostgreSQL",
            "Integrate secure authentication (JWT) and client-side route authorization",
        ],
        "education": "B.Tech/B.E./BCA/MCA in Computer Science, IT, or Web Development",
        "qualifications": "Demonstrated full-stack project portfolio showcasing frontend interactivity and backend API endpoints.",
    },
    {
        "domain": "Frontend Development",
        "title": "Frontend Engineer Intern",
        "required": ["JavaScript", "React", "HTML", "CSS", "Responsive Design"],
        "preferred": ["TypeScript", "Next.js", "Tailwind CSS", "Redux"],
        "project": "design system component library and interactive client dashboards",
        "description": "Collaborate with UI/UX designers to translate Figma specifications into fluid, micro-animated web interfaces.",
        "responsibilities": [
            "Build reusable, themeable component systems using React and modern CSS",
            "Optimize web performance, Core Web Vitals, and asset delivery pipelines",
            "Ensure cross-browser compatibility, WCAG 2.1 accessibility, and mobile responsiveness",
            "Connect client state to backend REST and GraphQL endpoints with caching",
        ],
        "education": "B.Tech/B.Sc./BCA in Computer Science, Web Technologies, or Design Computing",
        "qualifications": "Deep familiarity with DOM manipulation, CSS layout (Flexbox/Grid), React hooks, and component lifecycle.",
    },
    {
        "domain": "Java Development",
        "title": "Java Backend Intern",
        "required": ["Java", "Object-Oriented Programming", "REST API", "SQL"],
        "preferred": ["Spring Boot", "Hibernate", "Maven", "PostgreSQL"],
        "project": "enterprise ledger services and microservice architecture",
        "description": "Build high-reliability enterprise backend components using modern Java, Spring Boot, and robust relational persistence.",
        "responsibilities": [
            "Develop secure REST APIs using Spring Boot and Spring MVC architectures",
            "Implement object-relational mappings and repository interfaces with Hibernate/JPA",
            "Write comprehensive JUnit test suites and mock integration tests",
            "Troubleshoot database transaction rollbacks and thread concurrency edge cases",
        ],
        "education": "B.Tech/B.E./MCA in Computer Science, IT, or Software Systems",
        "qualifications": "Strong command of core Java (collections, OOP, generics, exceptions) and relational database queries.",
    },
    {
        "domain": "Software Engineering",
        "title": "Software Development Engineer Intern",
        "required": ["Data Structures", "Algorithms", "Git", "Python", "Problem Solving"],
        "preferred": ["C++", "Java", "Linux", "System Design"],
        "project": "high-performance algorithms and distributed compute primitives",
        "description": "Tackle challenging algorithmic problems, optimize time-complexity bottlenecks, and write clean production software.",
        "responsibilities": [
            "Implement efficient data structures and algorithms to process high-throughput events",
            "Conduct structured peer code reviews and contribute to architecture design docs",
            "Profile execution bottlenecks, memory leaks, and CPU utilization across workloads",
            "Maintain continuous integration workflows and automated regression pipelines",
        ],
        "education": "B.Tech/B.E. in Computer Science or Software Engineering",
        "qualifications": "Excellent algorithmic foundation (graphs, dynamic programming, sorting), clean coding discipline, and Git fluency.",
    },
    {
        "domain": "Cloud/DevOps",
        "title": "Cloud & DevOps Intern",
        "required": ["Linux", "Docker", "Git", "CI/CD", "Cloud Computing"],
        "preferred": ["AWS", "Kubernetes", "Terraform", "Bash"],
        "project": "automated container orchestration and infrastructure as code",
        "description": "Empower product teams by building continuous deployment pipelines, monitoring systems, and scalable cloud infrastructure.",
        "responsibilities": [
            "Author declarative CI/CD pipelines in GitHub Actions and GitLab CI",
            "Package application microservices into hardened, multi-stage Docker images",
            "Provision cloud compute, VPC networks, and managed databases using Terraform",
            "Configure logging, alerting, and metrics aggregators (Prometheus, Grafana)",
        ],
        "education": "B.Tech/B.E. in Computer Science, IT, or Cloud Infrastructure Engineering",
        "qualifications": "Working proficiency in Unix/Linux shell commands, containerization concepts, and cloud networking basics.",
    },
    {
        "domain": "Cybersecurity",
        "title": "Cybersecurity & InfoSec Intern",
        "required": ["Cybersecurity", "Network Security", "Linux", "Vulnerability Assessment"],
        "preferred": ["Cryptography", "OWASP", "Wireshark", "Python"],
        "project": "application security scanning and intrusion detection auditing",
        "description": "Work with our security operations team to defend infrastructure, conduct vulnerability assessments, and verify compliance.",
        "responsibilities": [
            "Perform vulnerability scans on internal APIs using OWASP testing methodologies",
            "Analyze system audit trails, authentication logs, and network traffic captures",
            "Assist in remediation guidance for reported CVEs and misconfigured cloud assets",
            "Script security verification checks in Python and Bash for automated CI/CD gating",
        ],
        "education": "B.Tech/B.Sc. in Cybersecurity, Computer Science, Information Security, or Networking",
        "qualifications": "Solid understanding of OSI model, TCP/IP, common web vulnerabilities (XSS, SQLi, CSRF), and cryptography basics.",
    },
    {
        "domain": "Database/SQL",
        "title": "Database Engineer Intern",
        "required": ["SQL", "Database", "PostgreSQL", "MySQL", "Data Modeling"],
        "preferred": ["Query Optimization", "NoSQL", "MongoDB", "Python"],
        "project": "relational database normalization and query performance tuning",
        "description": "Optimize enterprise relational databases, design normalized schemas, and ensure high-integrity persistent storage.",
        "responsibilities": [
            "Design third-normal-form entity-relationship models for enterprise applications",
            "Analyze query execution plans (EXPLAIN ANALYZE) and engineer strategic indexes",
            "Develop complex stored procedures, triggers, and automated archival jobs",
            "Assist with database backup verification, replication monitoring, and failover checks",
        ],
        "education": "B.Tech/B.E./BCA in Computer Science, Information Systems, or Database Administration",
        "qualifications": "Proficiency in ANSI SQL, ACID transaction guarantees, schema indexing, and database performance tuning.",
    },
]


def make_valid_record(index, domain_info, company, location, work_mode, job_type):
    job_id = f"JOB{index:03d}"
    title = domain_info["title"]
    domain = domain_info["domain"]
    project = domain_info["project"]
    required = list(domain_info["required"])
    preferred = list(domain_info["preferred"])
    keywords = list(dict.fromkeys(required + preferred + [domain, project]))

    description = f"{domain_info['description']} As an intern at {company} in {location}, you will focus on {project} under the mentorship of senior engineers."
    responsibilities = [
        resp for resp in domain_info["responsibilities"]
    ]

    return {
        "job_id": job_id,
        "job_title": title,
        "company": company,
        "location": location,
        "work_mode": work_mode,
        "job_type": job_type,
        "job_description": description,
        "responsibilities": responsibilities,
        "required_skills": required,
        "preferred_skills": preferred,
        "qualifications": domain_info["qualifications"],
        "experience_requirements": "0-1 years; academic projects or prior internships accepted",
        "education_requirements": domain_info["education"],
        "projects_or_domain": project,
        "keywords": keywords,
        "source": "Curated Knowledge Base",
        "status": "Active",
    }


def generate_raw_dataset():
    raw_records = []
    current_index = 1

    # 1. Generate 178 valid unique records covering all 15 domains evenly (11 to 12 jobs per domain)
    # 15 domains * 12 variants = 180 slots -> let's generate 178 clean valid jobs
    total_valid_target = 178
    domain_count = len(DOMAINS)

    for i in range(total_valid_target):
        domain_idx = i % domain_count
        domain_info = DOMAINS[domain_idx]
        company = COMPANIES[(i + domain_idx * 3) % len(COMPANIES)]
        location = LOCATIONS[(i * 2 + domain_idx) % len(LOCATIONS)]
        work_mode = ["Hybrid", "Remote", "On-site"][(i + domain_idx) % 3]
        job_type = "Entry-level" if (i % 8 == 0) else "Internship"

        rec = make_valid_record(current_index, domain_info, company, location, work_mode, job_type)
        raw_records.append(rec)
        current_index += 1

    # 2. Add realistic DUPLICATE records (exact same company + title + location, or duplicate job_id)
    # We will add 8 intentional duplicates
    for d in range(8):
        donor = raw_records[d * 10]
        duplicate_rec = dict(donor)
        if d % 2 == 0:
            # Duplicate job_id
            duplicate_rec["job_id"] = donor["job_id"]
            duplicate_rec["company"] = donor["company"]
        else:
            # New job_id but duplicate company + title + location
            duplicate_rec["job_id"] = f"JOB_DUP_{d+1:02d}"
            duplicate_rec["company"] = donor["company"]
            duplicate_rec["job_title"] = donor["job_title"]
            duplicate_rec["location"] = donor["location"]
        raw_records.append(duplicate_rec)

    # 3. Add realistic INCOMPLETE records (missing essential fields: title, company, description, or required_skills)
    # We will add 5 intentional incomplete records
    raw_records.append({
        "job_id": f"JOB_INC_01",
        "job_title": "",  # missing title
        "company": "BrokenCorp",
        "location": "Bengaluru, Karnataka",
        "job_description": "We need someone to write code.",
        "required_skills": ["Python"],
    })
    raw_records.append({
        "job_id": f"JOB_INC_02",
        "job_title": "Python Developer",
        "company": "",  # missing company
        "location": "Pune, Maharashtra",
        "job_description": "Join our team to develop backend systems.",
        "required_skills": ["Python"],
    })
    raw_records.append({
        "job_id": f"JOB_INC_03",
        "job_title": "Machine Learning Intern",
        "company": "GhostAI Labs",
        "location": "Remote, India",
        "job_description": "",  # missing description
        "required_skills": ["Python", "Machine Learning"],
    })
    raw_records.append({
        "job_id": f"JOB_INC_04",
        "job_title": "Data Analyst Intern",
        "company": "NullData Inc",
        "location": "Mumbai, Maharashtra",
        "job_description": "Analyze spreadsheets and databases.",
        "required_skills": [],  # missing required skills
    })
    raw_records.append({
        "job_id": "",  # missing job_id
        "job_title": "Cloud Engineering Intern",
        "company": "CloudX",
        "location": "Hyderabad, Telangana",
        "job_description": "Work with Docker and AWS.",
        "required_skills": ["AWS", "Docker"],
    })

    # 4. Add realistic IRRELEVANT records (non-technical jobs that don't belong in engineering/tech internship KB)
    # We will add 4 intentional irrelevant records
    raw_records.append({
        "job_id": "JOB_IRR_01",
        "job_title": "Real Estate Sales Associate",
        "company": "Prime Properties",
        "location": "Delhi, NCR",
        "job_description": "Cold call prospective buyers, arrange property visits, and negotiate apartment leasing contracts.",
        "required_skills": ["Cold Calling", "Negotiation", "Lead Generation"],
        "projects_or_domain": "residential leasing",
    })
    raw_records.append({
        "job_id": "JOB_IRR_02",
        "job_title": "Retail Cashier and Store Clerk",
        "company": "FreshMart Groceries",
        "location": "Bengaluru, Karnataka",
        "job_description": "Operate cash registers, restock supermarket shelves, and assist in-store shoppers with checkouts.",
        "required_skills": ["Cash Handling", "Inventory Stocking", "Customer Service"],
        "projects_or_domain": "supermarket retail",
    })
    raw_records.append({
        "job_id": "JOB_IRR_03",
        "job_title": "Hotel Front Desk Receptionist",
        "company": "Grand Palace Hotel",
        "location": "Kochi, Kerala",
        "job_description": "Greet hotel guests, check them into reservations, manage keycards, and coordinate housekeeping requests.",
        "required_skills": ["Concierge", "Reservation Management", "Hospitality"],
        "projects_or_domain": "hotel hospitality",
    })
    raw_records.append({
        "job_id": "JOB_IRR_04",
        "job_title": "Restaurant Line Cook",
        "company": "Spicy Bistro",
        "location": "Chennai, Tamil Nadu",
        "job_description": "Prepare ingredients, grill meat, maintain kitchen sanitation standards, and plate dinner appetizers.",
        "required_skills": ["Food Preparation", "Grilling", "Kitchen Safety"],
        "projects_or_domain": "culinary dining",
    })

    return raw_records


def main():
    raw = generate_raw_dataset()
    print(f"Raw records generated: {len(raw)}")

    cleaned, report = clean_records(raw)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save raw records as reference
    (DATA_DIR / "raw_jobs_dataset.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")

    # Save cleaned records as json and csv
    (DATA_DIR / "jobs_dataset.json").write_text(json.dumps(cleaned, indent=2), encoding="utf-8")

    with (DATA_DIR / "jobs_dataset.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cleaned[0].keys()))
        writer.writeheader()
        for record in cleaned:
            row = {}
            for k, v in record.items():
                if isinstance(v, list):
                    row[k] = json.dumps(v)
                else:
                    row[k] = v
            writer.writerow(row)

    (DATA_DIR / "cleaning_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Cleaned dataset saved with {report['final_records']} valid postings.")
    print("Cleaning Report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
