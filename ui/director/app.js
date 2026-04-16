/* app.js — Director-AI frontend client */

const API_BASE = (() => {
    // If served by FastAPI at /ui, the API is on the same origin.
    // If opened as file://, fall back to localhost:8000.
    if (window.location.protocol === "file:") return "http://localhost:8000";
    return window.location.origin;
})();

const $ = (id) => document.getElementById(id);

const state = {
    files: [],
};

// ---------------------------------------------------------------------------
// Backend status
// ---------------------------------------------------------------------------

async function loadStatus() {
    try {
        const r = await fetch(`${API_BASE}/config`);
        const j = await r.json();
        $("backend-vision").textContent = `vision: ${j.vision_backend}`;
        $("backend-web").textContent    = `web: ${j.web_backend}`;
    } catch (e) {
        $("backend-vision").textContent = "vision: offline";
        $("backend-web").textContent    = "web: offline";
    }
}

// ---------------------------------------------------------------------------
// File input handling (click + drag & drop)
// ---------------------------------------------------------------------------

function initUploader() {
    const drop  = $("drop-zone");
    const input = $("image-input");

    drop.addEventListener("click", () => input.click());

    input.addEventListener("change", (e) => addFiles(e.target.files));

    ["dragenter", "dragover"].forEach((ev) => {
        drop.addEventListener(ev, (e) => {
            e.preventDefault();
            drop.classList.add("dragover");
        });
    });
    ["dragleave", "drop"].forEach((ev) => {
        drop.addEventListener(ev, (e) => {
            e.preventDefault();
            drop.classList.remove("dragover");
        });
    });
    drop.addEventListener("drop", (e) => {
        if (e.dataTransfer?.files) addFiles(e.dataTransfer.files);
    });
}

function addFiles(fileList) {
    for (const f of fileList) {
        if (!f.type.startsWith("image/")) continue;
        state.files.push(f);
    }
    renderPreviews();
}

function renderPreviews() {
    const grid = $("preview-grid");
    grid.innerHTML = "";
    state.files.forEach((f, i) => {
        const img = document.createElement("img");
        img.src   = URL.createObjectURL(f);
        img.title = f.name;
        img.addEventListener("click", () => {
            state.files.splice(i, 1);
            renderPreviews();
        });
        grid.appendChild(img);
    });
}

// ---------------------------------------------------------------------------
// Diagnose action
// ---------------------------------------------------------------------------

async function diagnose() {
    const text        = $("problem-text").value.trim();
    const deviceModel = $("device-model").value.trim();

    if (!text && state.files.length === 0) {
        alert("Please describe the problem or upload an image.");
        return;
    }

    const btn = $("diagnose-btn");
    btn.disabled = true;
    btn.textContent = "Diagnosing…";

    $("error-panel").hidden = true;
    $("result-panel").hidden = true;

    const form = new FormData();
    form.append("text", text);
    form.append("device_model", deviceModel);
    state.files.forEach((f) => form.append("images", f));

    try {
        const resp = await fetch(`${API_BASE}/diagnose`, {
            method: "POST",
            body: form,
        });
        if (!resp.ok) {
            const detail = await resp.text();
            throw new Error(`HTTP ${resp.status}: ${detail}`);
        }
        const data = await resp.json();
        renderResult(data);
    } catch (e) {
        $("error-panel").hidden = false;
        $("error-msg").textContent = e.message;
    } finally {
        btn.disabled = false;
        btn.textContent = "Diagnose";
    }
}

// ---------------------------------------------------------------------------
// Result rendering
// ---------------------------------------------------------------------------

function renderResult(data) {
    $("result-panel").hidden = false;

    const spec = data.specialist_output || {};
    const so   = data;  // flat fields already at top level

    $("r-domain").textContent     = data.domain || "unknown";
    $("r-confidence").textContent =
        (data.confidence != null ? `${Math.round(data.confidence * 100)}%` : "—") +
        (data.confidence_lvl ? ` (${data.confidence_lvl})` : "");
    $("r-confidence").className = "value " + (data.confidence_lvl || "");

    const severity = so.severity || "—";
    const sevEl = $("r-severity");
    sevEl.textContent = severity;
    sevEl.className   = "value " + severity.toLowerCase();

    $("r-summary").textContent = data.summary || "—";

    // Evidence (from findings)
    const evidenceUl = $("r-evidence");
    evidenceUl.innerHTML = "";
    const findings = data.findings || [];
    if (findings.length === 0) {
        evidenceUl.innerHTML = "<li>No evidence matched.</li>";
    } else {
        findings.forEach((f) => {
            const li = document.createElement("li");
            const pct = Math.round((f.score || 0) * 100);
            const matched = f.matched ? "✔" : "○";
            const evidence = (f.evidence || []).join(", ");
            li.textContent = `${matched} ${f.pattern_name} — ${pct}%` +
                             (evidence ? ` — ${evidence}` : "");
            evidenceUl.appendChild(li);
        });
    }

    // Actions
    const actionsOl = $("r-actions");
    actionsOl.innerHTML = "";
    (data.actions || []).forEach((a) => {
        const li = document.createElement("li");
        li.textContent = a;
        actionsOl.appendChild(li);
    });
    if (!(data.actions || []).length) {
        actionsOl.innerHTML = "<li>No actions returned.</li>";
    }

    // Parts needed
    const parts = data.parts_needed || [];
    $("r-parts-wrap").hidden = parts.length === 0;
    const partsUl = $("r-parts");
    partsUl.innerHTML = "";
    parts.forEach((p) => {
        const li = document.createElement("li");
        li.textContent = p;
        partsUl.appendChild(li);
    });

    // References
    const refs = data.references || [];
    $("r-refs-wrap").hidden = refs.length === 0;
    const refsUl = $("r-refs");
    refsUl.innerHTML = "";
    refs.forEach((r) => {
        const li = document.createElement("li");
        const a  = document.createElement("a");
        a.href   = r;
        a.target = "_blank";
        a.rel    = "noopener noreferrer";
        a.textContent = r;
        li.appendChild(a);
        refsUl.appendChild(li);
    });

    $("r-raw").textContent = JSON.stringify(data, null, 2);
    $("result-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    loadStatus();
    initUploader();
    $("diagnose-btn").addEventListener("click", diagnose);
});
