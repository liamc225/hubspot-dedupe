const scenarios = {
  contacts: {
    title: "C-001 · Contacts",
    confidence: "High confidence",
    description:
      "Two contact records collapsed into a single merge cluster after matching on exact email, exact phone, and the same company domain.",
    reasons: [
      "exact email match",
      "exact phone match",
      "same company",
      "same company domain",
    ],
    masterRecord: "101 · Alice Smith",
    masterDetail: "alice@example.com · Example Inc · lead · Owner AE 1",
    mergeAction: "Merge 102 into 101",
    mergeDetail: "Alicia Smith keeps the same email and phone but has a less complete source record.",
    command: "hubspot-dedupe contacts data/sample_contacts.csv --format json",
    jsonSnippet: `{
  "cluster_id": "C-001",
  "object_type": "contacts",
  "confidence": "high",
  "score": 100,
  "master_record": {
    "record_id": "101",
    "email": "alice@example.com"
  },
  "pair_matches": [
    {
      "left_id": "101",
      "right_id": "102",
      "score": 100
    }
  ]
}`,
  },
  companies: {
    title: "C-001 · Companies",
    confidence: "High confidence",
    description:
      "Two company records joined into one cluster through exact domain, exact phone, normalized name, and shared city context.",
    reasons: [
      "exact domain match",
      "exact phone match",
      "exact company-name match",
      "same city",
    ],
    masterRecord: "201 · Acme, Inc.",
    masterDetail: "acme.com · Chicago · Illinois · Owner 1",
    mergeAction: "Merge 202 into 201",
    mergeDetail: "Acme Incorporated is missing the explicit domain field, so the more complete record remains master.",
    command: "hubspot-dedupe companies data/sample_companies.csv --format json",
    jsonSnippet: `{
  "cluster_id": "C-001",
  "object_type": "companies",
  "confidence": "high",
  "score": 100,
  "master_record": {
    "record_id": "201",
    "name": "Acme, Inc."
  },
  "pair_matches": [
    {
      "left_id": "201",
      "right_id": "202",
      "score": 100
    }
  ]
}`,
  },
};

const clusterTitle = document.querySelector("#cluster-title");
const confidencePill = document.querySelector("#confidence-pill");
const clusterDescription = document.querySelector("#cluster-description");
const reasonList = document.querySelector("#reason-list");
const masterRecord = document.querySelector("#master-record");
const masterDetail = document.querySelector("#master-detail");
const mergeAction = document.querySelector("#merge-action");
const mergeDetail = document.querySelector("#merge-detail");
const commandSnippet = document.querySelector("#command-snippet");
const jsonSnippet = document.querySelector("#json-snippet");
const toggleButtons = document.querySelectorAll("[data-scenario]");

function renderScenario(name) {
  const scenario = scenarios[name];
  if (!scenario) return;

  clusterTitle.textContent = scenario.title;
  confidencePill.textContent = scenario.confidence;
  clusterDescription.textContent = scenario.description;
  masterRecord.textContent = scenario.masterRecord;
  masterDetail.textContent = scenario.masterDetail;
  mergeAction.textContent = scenario.mergeAction;
  mergeDetail.textContent = scenario.mergeDetail;
  commandSnippet.textContent = scenario.command;
  jsonSnippet.textContent = scenario.jsonSnippet;

  reasonList.innerHTML = "";
  scenario.reasons.forEach((reason) => {
    const pill = document.createElement("span");
    pill.className = "reason-pill";
    pill.textContent = reason;
    reasonList.appendChild(pill);
  });

  toggleButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.scenario === name);
  });
}

toggleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    renderScenario(button.dataset.scenario);
  });
});

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.16 }
);

document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));

renderScenario("contacts");
