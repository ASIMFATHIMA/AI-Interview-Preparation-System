const API_BASE = "http://localhost:8000";

let currentStudentId = null;

const profileForm = document.getElementById("profile-form");
const profileResult = document.getElementById("profile-result");
const uploadSection = document.getElementById("upload-section");
const uploadForm = document.getElementById("upload-form");
const uploadResult = document.getElementById("upload-result");
const profileViewSection = document.getElementById("profile-view-section");
const profileView = document.getElementById("profile-view");

profileForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;
  const phone = document.getElementById("phone").value;

  try {
    const res = await fetch(`${API_BASE}/students`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, phone: phone || null }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create profile.");

    currentStudentId = data.id;
    profileResult.innerHTML = `<span class="success">Profile created! Student ID: ${data.id}</span>`;
    uploadSection.style.display = "block";
  } catch (err) {
    profileResult.innerHTML = `<span class="error">${err.message}</span>`;
  }
});

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!currentStudentId) return;

  const fileInput = document.getElementById("resume-file");
  const file = fileInput.files[0];
  if (!file) return;

  uploadResult.innerHTML = "Uploading...";

  try {
    const formData = new FormData();
    formData.append("file", file);

    const uploadRes = await fetch(`${API_BASE}/students/${currentStudentId}/resume`, {
      method: "POST",
      body: formData,
    });
    const uploadData = await uploadRes.json();
    if (!uploadRes.ok) throw new Error(uploadData.detail || "Upload failed.");

    uploadResult.innerHTML = `<span class="success">Uploaded. Parsing with LLM...</span>`;

    const parseRes = await fetch(
      `${API_BASE}/students/${currentStudentId}/resume/${uploadData.id}/parse`,
      { method: "POST" }
    );
    const parseData = await parseRes.json();
    if (!parseRes.ok) throw new Error(parseData.detail || "Parsing failed.");

    uploadResult.innerHTML = `<span class="success">Resume parsed successfully!</span>`;
    renderProfile(parseData.profile);
  } catch (err) {
    uploadResult.innerHTML = `<span class="error">${err.message}</span>`;
  }
});

function renderProfile(profile) {
  profileViewSection.style.display = "block";

  const skillsHtml = profile.skills
    .map((s) => `<span class="tag">${s.name}${s.category ? " · " + s.category : ""}</span>`)
    .join("");

  const educationHtml = profile.education
    .map(
      (e) => `<div class="entry">
        <div class="entry-title">${e.degree || ""} ${e.field ? "— " + e.field : ""}</div>
        <div class="entry-meta">${e.institution || ""} (${e.start_date || "?"} - ${e.end_date || "?"})${e.gpa ? " · GPA: " + e.gpa : ""}</div>
      </div>`
    )
    .join("");

  const experienceHtml = profile.experience
    .map(
      (x) => `<div class="entry">
        <div class="entry-title">${x.title || ""} — ${x.company || ""}</div>
        <div class="entry-meta">${x.start_date || "?"} - ${x.end_date || "?"}</div>
        <div>${x.description || ""}</div>
      </div>`
    )
    .join("");

  const projectsHtml = profile.projects
    .map(
      (p) => `<div class="entry">
        <div class="entry-title">${p.name || ""}</div>
        <div class="entry-meta">${p.technologies || ""}</div>
        <div>${p.description || ""}</div>
      </div>`
    )
    .join("");

  profileView.innerHTML = `
    <div class="profile-section">
      <h3>Summary</h3>
      <p>${profile.summary || "—"}</p>
    </div>
    <div class="profile-section">
      <h3>Skills</h3>
      ${skillsHtml || "<em>None extracted</em>"}
    </div>
    <div class="profile-section">
      <h3>Education</h3>
      ${educationHtml || "<em>None extracted</em>"}
    </div>
    <div class="profile-section">
      <h3>Experience</h3>
      ${experienceHtml || "<em>None extracted</em>"}
    </div>
    <div class="profile-section">
      <h3>Projects</h3>
      ${projectsHtml || "<em>None extracted</em>"}
    </div>
  `;
}
