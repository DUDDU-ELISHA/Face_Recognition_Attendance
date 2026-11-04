let activeStream = null;

async function startWebcam() {
  const video = document.getElementById("video");
  const placeholder = document.getElementById("cameraPlaceholder");
  if (!video) return;
  try {
    activeStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
    video.srcObject = activeStream;
    if (placeholder) placeholder.style.display = "none";
    return true;
  } catch (error) {
    alert("Camera access failed. Allow camera permission and try again.");
    return false;
  }
}

function captureFrame() {
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  if (!video || !canvas || !video.videoWidth) return null;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.88);
}

function setupEnrollment() {
  const start = document.getElementById("startCamera");
  const capture = document.getElementById("captureFace");
  const train = document.getElementById("trainModel");
  const message = document.getElementById("captureMessage");
  let count = 0;
  start?.addEventListener("click", async () => {
    const ok = await startWebcam();
    if (ok) capture.disabled = false;
  });
  capture?.addEventListener("click", async () => {
    const studentId = document.getElementById("captureStudentId").value.trim();
    if (!studentId) {
      message.textContent = "Enter the saved Student ID first.";
      return;
    }
    const image = captureFrame();
    if (!image) return;
    capture.disabled = true;
    const response = await fetch("/api/capture", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: studentId, image })
    });
    const result = await response.json();
    message.textContent = result.message;
    if (result.success) {
      count = result.count;
      document.getElementById("sampleCount").textContent = `${count} / 20`;
      document.getElementById("sampleProgress").style.width = `${count * 5}%`;
    }
    capture.disabled = false;
  });
  train?.addEventListener("click", async () => {
    train.disabled = true;
    const response = await fetch("/api/train", { method: "POST" });
    const result = await response.json();
    document.getElementById("trainMessage").textContent = result.message;
    train.disabled = false;
  });
}

function setupRecognition() {
  const start = document.getElementById("startCamera");
  const scan = document.getElementById("scanFace");
  const message = document.getElementById("scanMessage");
  start?.addEventListener("click", async () => {
    const ok = await startWebcam();
    if (ok) scan.disabled = false;
  });
  scan?.addEventListener("click", async () => {
    const image = captureFrame();
    if (!image) {
      message.textContent = "Camera is not ready yet.";
      return;
    }
    scan.disabled = true;
    message.textContent = "Scanning face. Please wait...";
    try {
      const response = await fetch("/api/recognize", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image })
      });
      const result = await response.json();
      message.textContent = result.message;
      const panel = document.getElementById("recognitionResult");
      if (result.success && result.recognized) {
        const s = result.student;
        panel.innerHTML = `<div class="result-success"><span>✓</span></div><h2>${escapeHTML(s.name)}</h2><p>${escapeHTML(s.student_id)} · ${escapeHTML(s.department)}</p><div class="result-details"><div><small>Attendance</small><strong>${result.marked ? "Marked Present" : "Already Marked"}</strong></div><div><small>Match score</small><strong>${result.confidence}</strong></div></div><span class="attendance-badge">● ${result.marked ? "Present" : "Previously marked"}</span>`;
      } else {
        panel.innerHTML = `<div class="result-empty"><span>!</span><strong>Face not recognized</strong><small>${escapeHTML(result.message)}</small></div>`;
      }
    } catch (error) {
      message.textContent = "Unable to contact the server. Please try again.";
    }
    scan.disabled = false;
  });
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}
