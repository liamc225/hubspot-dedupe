const form = document.querySelector("#analyze-form");
const minScoreInput = document.querySelector("#min-score");
const minScoreOutput = document.querySelector("#min-score-output");
const resetButton = document.querySelector("#reset-form");
const sampleButtons = document.querySelectorAll(".sample-button");
const summaryTitle = document.querySelector("#summary-title");
const summaryText = document.querySelector("#summary-text");
const metrics = document.querySelector("#metrics");
const resultsList = document.querySelector("#results-list");
const emptyState = document.querySelector("#empty-state");
const errorBanner = document.querySelector("#error-banner");
const loadingBadge = document.querySelector("#loading-badge");

minScoreInput.addEventListener("input", () => {
  minScoreOutput.textContent = minScoreInput.value;
});

resetButton.addEventListener("click", () => {
  form.reset();
  minScoreInput.value = "70";
  minScoreOutput.textContent = "70";
  clearResults();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  await requestAnalysis("/api/analyze", {
    method: "POST",
    body: formData,
  });
});

sampleButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const selectedType = button.dataset.sample;
    const radio = document.querySelector(`input[name="object_type"][value="${selectedType}"]`);
    if (radio) {
      radio.checked = true;
    }
    await requestAnalysis(`/api/samples/${selectedType}?min_score=${encodeURIComponent(minScoreInput.value)}`);
  });
});

async function requestAnalysis(url, options = {}) {
  setLoading(true);
  setError("");

  try {
    const response = await fetch(url, options);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Analysis failed.");
    }
    renderResults(payload);
  } catch (error) {
    clearResults();
    setError(error.message || "Analysis failed.");
  } finally {
    setLoading(false);
  }
}

function renderResults(payload) {
  emptyState.classList.add("is-hidden");
  resultsList.innerHTML = "";
  renderSummary(payload);

  if (payload.cluster_count === 0) {
    const card = document.createElement("article");
    card.className = "panel empty-state";
    card.innerHTML = `
      <h3>No duplicates above the current threshold</h3>
      <p>Try lowering the minimum score or double-checking the CSV object type.</p>
    `;
    resultsList.appendChild(card);
    return;
  }

  payload.clusters.forEach((cluster) => {
    const card = document.createElement("article");
    card.className = "panel cluster-card";

    const actionsMarkup = cluster.actions
      .map(
        (action) => `
          <div class="action-item">
            <div class="action-header">
              <strong>Merge ${escapeHtml(action.duplicate_id)} into ${escapeHtml(cluster.master_record.record_id)}</strong>
              <span class="badge badge-score">${escapeHtml(String(action.score))} pts</span>
            </div>
            <div>${escapeHtml(action.duplicate_label)}</div>
            <div class="reason-list">
              ${action.reasons.map((reason) => `<span class="reason-pill">${escapeHtml(reason)}</span>`).join("")}
            </div>
          </div>
        `
      )
      .join("");

    card.innerHTML = `
      <div class="cluster-header">
        <div>
          <p class="eyebrow">Cluster ${escapeHtml(cluster.cluster_id)}</p>
          <h3>${escapeHtml(cluster.master_label)}</h3>
        </div>
        <div class="cluster-meta">
          <span class="badge badge-confidence-${escapeHtml(cluster.confidence)}">${escapeHtml(cluster.confidence)} confidence</span>
          <span class="badge badge-score">${escapeHtml(String(cluster.score))} pts</span>
        </div>
      </div>
      <div class="cluster-grid">
        <div class="info-card">
          <p class="eyebrow">Master record</p>
          <strong>${escapeHtml(cluster.master_label)}</strong>
          <div class="muted">${escapeHtml(describeRecord(cluster.master_record))}</div>
        </div>
        <div class="info-card">
          <p class="eyebrow">Cluster size</p>
          <strong>${escapeHtml(String(cluster.records.length))} records</strong>
          <div class="muted">${escapeHtml(String(cluster.actions.length))} recommended merge action(s)</div>
        </div>
      </div>
      <div class="action-list">${actionsMarkup}</div>
    `;
    resultsList.appendChild(card);
  });
}

function renderSummary(payload) {
  summaryTitle.textContent = `Analyzed ${payload.source_name}`;
  summaryText.textContent = `${payload.object_type} export with minimum score ${payload.min_score}. Review ${payload.cluster_count} duplicate cluster(s) before merging.`;

  const metricItems = [
    ["Records scanned", String(payload.record_count)],
    ["Clusters found", String(payload.cluster_count)],
    ["Merges recommended", String(payload.merge_count)],
  ];

  metrics.innerHTML = metricItems
    .map(
      ([label, value]) => `
        <article class="metric-card">
          <span class="metric-value">${escapeHtml(value)}</span>
          <span class="metric-label">${escapeHtml(label)}</span>
        </article>
      `
    )
    .join("");
}

function clearResults() {
  summaryTitle.textContent = "No analysis yet";
  summaryText.textContent = "Upload a CSV or load one of the included samples to review duplicate clusters here.";
  metrics.innerHTML = "";
  resultsList.innerHTML = "";
  emptyState.classList.remove("is-hidden");
}

function setError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.toggle("is-hidden", !message);
}

function setLoading(isLoading) {
  loadingBadge.classList.toggle("is-hidden", !isLoading);
}

function describeRecord(record) {
  const parts = [
    record.email,
    record.name,
    record.company,
    record.domain,
    record.phone,
    record.city,
    record.state,
  ].filter(Boolean);
  return parts.join(" · ") || `Record ${record.record_id}`;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
