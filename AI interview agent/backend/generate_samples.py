import os
from docx import Document

from pdf_utils import make_pdf

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_resumes")
os.makedirs(TEST_DIR, exist_ok=True)


def make_docx(path, lines):
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    doc.save(path)


# Sample 1: Fresh graduate with skills, education, projects, certifications, achievements
sample1_lines = [
    "Asha Raman",
    "asha.raman@example.com | +91 9876543210 | Location: Chennai",
    "LinkedIn: https://linkedin.com/in/asha-raman",
    "GitHub: https://github.com/asha-raman",
    "Portfolio: https://asha.dev",
    "",
    "SKILLS",
    "Python, React, FastAPI, MySQL, Machine Learning, Git, Docker",
    "",
    "EDUCATION",
    "B.Tech Artificial Intelligence, ABC University, 2023 - 2027",
    "",
    "PROJECTS",
    "AI Interview Agent",
    "Technologies: Python, FastAPI, React",
    "An AI-powered mock interview platform with real-time feedback.",
    "",
    "Resume Parser",
    "Technologies: Python, Django, NLP",
    "Extracts structured data from resumes using regex and LLM.",
    "",
    "CERTIFICATIONS",
    "Python Programming - IBM - 2025",
    "Machine Learning Fundamentals - Coursera - 2024",
    "",
    "ACHIEVEMENTS",
    "Winner, College Hackathon 2025",
    "Published research paper on NLP techniques.",
]

make_docx(os.path.join(TEST_DIR, "sample1_fresh_graduate.docx"), sample1_lines)
make_pdf(os.path.join(TEST_DIR, "sample1_fresh_graduate.pdf"), sample1_lines)

# Sample 2: Experienced professional with work experience, internships
sample2_lines = [
    "Ravi Kumar",
    "ravi.kumar@example.com | +1-555-123-4567 | Location: San Francisco, CA",
    "LinkedIn: https://linkedin.com/in/ravikumar",
    "GitHub: https://github.com/ravikumar",
    "",
    "PROFESSIONAL SUMMARY",
    "Full-stack developer with 3 years of experience building scalable web applications.",
    "",
    "SKILLS",
    "Python, JavaScript, TypeScript, React, Node.js, Django, PostgreSQL, AWS, Docker, Kubernetes",
    "",
    "EXPERIENCE",
    "Software Engineer | TechCorp Inc. | June 2023 - Present",
    "Developed REST APIs with Django and PostgreSQL, serving 100k+ users.",
    "Led migration of monolithic app to microservices using Docker and Kubernetes.",
    "",
    "Python Developer Intern | ABC Technologies | June 2022 - August 2022",
    "Built automated data pipelines using Python and Pandas.",
    "",
    "EDUCATION",
    "B.S. Computer Science, State University, 2019 - 2023",
    "",
    "PROJECTS",
    "E-Commerce Platform",
    "Technologies: React, Node.js, MongoDB, Stripe",
    "Built a full-stack e-commerce platform with payment integration.",
    "",
    "Real-time Chat Application",
    "Technologies: WebSocket, Node.js, Redis",
    "Developed a scalable chat app supporting 10k concurrent users.",
    "",
    "CERTIFICATIONS",
    "AWS Certified Solutions Architect - Amazon - 2024",
    "",
    "ACHIEVEMENTS",
    "Employee of the Month - TechCorp Inc. - 2024",
]

make_docx(os.path.join(TEST_DIR, "sample2_experienced.docx"), sample2_lines)
make_pdf(os.path.join(TEST_DIR, "sample2_experienced.pdf"), sample2_lines)

# Sample 3: Data science focused resume
sample3_lines = [
    "Priya Patel",
    "priya.patel@example.com | +91 8765432109 | Location: Bangalore",
    "LinkedIn: https://linkedin.com/in/priya-patel-ds",
    "GitHub: https://github.com/priya-patel",
    "Portfolio: https://priyapatel.me",
    "",
    "SKILLS",
    "Python, R, SQL, TensorFlow, PyTorch, Pandas, NumPy, Scikit-learn, NLP, LLM, RAG",
    "",
    "EDUCATION",
    "M.Tech Data Science, Indian Institute of Technology, 2022 - 2024",
    "B.Tech Information Technology, NIT Trichy, 2018 - 2022",
    "",
    "EXPERIENCE",
    "Data Science Intern | DataDriven Labs | Jan 2024 - June 2024",
    "Built LLM-based document summarization pipeline using RAG.",
    "Improved model accuracy by 15% using fine-tuning techniques.",
    "",
    "Machine Learning Intern | AI Startup | May 2023 - Aug 2023",
    "Developed sentiment analysis model for customer reviews.",
    "",
    "PROJECTS",
    "RAG-based Customer Support Bot",
    "Technologies: Python, LangChain, Pinecone, OpenAI",
    "Implemented a retrieval-augmented generation system for support queries.",
    "",
    "Credit Card Fraud Detection",
    "Technologies: Python, XGBoost, SHAP",
    "Built anomaly detection model with 98% precision.",
    "",
    "CERTIFICATIONS",
    "Deep Learning Specialization - Coursera - 2023",
    "TensorFlow Developer Certificate - Google - 2023",
    "",
    "ACHIEVEMENTS",
    "Top 10 in national-level Data Science Hackathon 2023",
    "Best Project Award at IIT Tech Fest 2024",
]

make_docx(os.path.join(TEST_DIR, "sample3_data_scientist.docx"), sample3_lines)
make_pdf(os.path.join(TEST_DIR, "sample3_data_scientist.pdf"), sample3_lines)

# Sample 4: Minimal resume (missing optional sections)
sample4_lines = [
    "Nina Shah",
    "nina.shah@example.com",
    "",
    "SKILLS",
    "Python, Java, Git",
    "",
    "EDUCATION",
    "B.Sc Computer Science, Mumbai University, 2021 - 2024",
]

make_docx(os.path.join(TEST_DIR, "sample4_minimal.docx"), sample4_lines)
make_pdf(os.path.join(TEST_DIR, "sample4_minimal.pdf"), sample4_lines)

print("Sample resumes generated successfully in:", TEST_DIR)
print("Files:", os.listdir(TEST_DIR))
