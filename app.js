"use strict";

const STARTING_ENDOWMENT = 20;
const MULTIPLIER = 3;
const ROUNDS_PER_PERIOD = 2;

const state = {
  players: [],
  treatment: {
    picture: false,
    error: false,
    label: "Standard Trust",
  },
  schedule: [],
  records: [],
  current: {
    periodIndex: 0,
    round: 1,
    pairIndex: 0,
    phase: "setup",
  },
};

const els = {
  setupView: document.querySelector("#setup-view"),
  runView: document.querySelector("#run-view"),
  completeView: document.querySelector("#complete-view"),
  subtitle: document.querySelector("#session-subtitle"),
  playerCount: document.querySelector("#player-count"),
  playersEditor: document.querySelector("#players-editor"),
  roleCounts: document.querySelector("#role-counts"),
  generatePlayers: document.querySelector("#generate-players"),
  startSession: document.querySelector("#start-session"),
  treatments: [...document.querySelectorAll(".treatment")],
  exportCsv: document.querySelector("#export-csv"),
  exportJson: document.querySelector("#export-json"),
  completeExportCsv: document.querySelector("#complete-export-csv"),
  completeExportJson: document.querySelector("#complete-export-json"),
  resetSession: document.querySelector("#reset-session"),
  periodStatus: document.querySelector("#period-status"),
  roundStatus: document.querySelector("#round-status"),
  pairStatus: document.querySelector("#pair-status"),
  treatmentStatus: document.querySelector("#treatment-status"),
  stage: document.querySelector("#stage"),
  scheduleList: document.querySelector("#schedule-list"),
  summary: document.querySelector("#summary"),
};

function init() {
  generatePlayers(10);
  bindEvents();
  renderSetup();
}

function bindEvents() {
  els.generatePlayers.addEventListener("click", () => {
    const count = getEvenPlayerCount();
    generatePlayers(count);
    renderSetup();
  });

  els.playerCount.addEventListener("change", () => {
    els.playerCount.value = getEvenPlayerCount();
  });

  els.treatments.forEach((button) => {
    button.addEventListener("click", () => {
      els.treatments.forEach((item) => item.classList.remove("selected"));
      button.classList.add("selected");
      state.treatment = {
        picture: button.dataset.picture === "true",
        error: button.dataset.error === "true",
        label: button.querySelector("strong").textContent,
      };
    });
  });

  els.startSession.addEventListener("click", startSession);
  els.exportCsv.addEventListener("click", () => exportData("csv"));
  els.exportJson.addEventListener("click", () => exportData("json"));
  els.completeExportCsv.addEventListener("click", () => exportData("csv"));
  els.completeExportJson.addEventListener("click", () => exportData("json"));
  els.resetSession.addEventListener("click", resetSession);
}

function getEvenPlayerCount() {
  const raw = Number.parseInt(els.playerCount.value, 10);
  const bounded = Math.max(2, Math.min(40, Number.isFinite(raw) ? raw : 10));
  return bounded % 2 === 0 ? bounded : bounded + 1;
}

function generatePlayers(count) {
  const half = count / 2;
  state.players = Array.from({ length: count }, (_, index) => {
    const id = index + 1;
    const isProposer = index < half;
    return {
      id,
      role: isProposer ? "proposer" : "responder",
      name: `${isProposer ? "Proposer" : "Responder"} ${isProposer ? id : id - half}`,
      note: "",
      picture: "",
    };
  });
}

function renderSetup() {
  const proposerCount = state.players.filter((player) => player.role === "proposer").length;
  const responderCount = state.players.filter((player) => player.role === "responder").length;
  els.roleCounts.textContent = `${proposerCount} proposers, ${responderCount} responders`;
  els.playersEditor.innerHTML = state.players.map(renderPlayerEditor).join("");

  state.players.forEach((player) => {
    document.querySelector(`#name-${player.id}`).addEventListener("input", (event) => {
      player.name = event.target.value.trim() || `Player ${player.id}`;
    });
    document.querySelector(`#name-${player.id}`).addEventListener("blur", () => {
      renderSetup();
    });
    document.querySelector(`#note-${player.id}`).addEventListener("input", (event) => {
      player.note = event.target.value.trim();
    });
    document.querySelector(`#picture-${player.id}`).addEventListener("change", (event) => {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.addEventListener("load", () => {
        player.picture = String(reader.result);
        renderSetup();
      });
      reader.readAsDataURL(file);
    });
  });
}

function renderPlayerEditor(player) {
  const initials = getInitials(player.name);
  const avatar = player.picture
    ? `<img src="${player.picture}" alt="">`
    : `<span>${escapeHtml(initials)}</span>`;

  return `
    <div class="player-row">
      <div class="player-role">
        <div class="avatar">${avatar}</div>
        <span>${escapeHtml(player.role)}</span>
      </div>
      <div class="player-fields">
        <input id="name-${player.id}" type="text" value="${escapeAttr(player.name)}" aria-label="Player name">
        <input id="picture-${player.id}" type="file" accept="image/*" aria-label="Player picture">
      </div>
      <div class="player-fields">
        <textarea id="note-${player.id}" rows="3" aria-label="Demographic note" placeholder="Demographic note">${escapeHtml(player.note)}</textarea>
      </div>
    </div>
  `;
}

function startSession() {
  const proposers = state.players.filter((player) => player.role === "proposer");
  const responders = state.players.filter((player) => player.role === "responder");
  if (proposers.length !== responders.length) {
    window.alert("This scheduler requires the same number of proposers and responders.");
    return;
  }

  state.schedule = buildSchedule(proposers, responders);
  state.records = [];
  state.current = {
    periodIndex: 0,
    round: 1,
    pairIndex: 0,
    phase: "proposer",
  };

  els.setupView.classList.add("hidden");
  els.completeView.classList.add("hidden");
  els.runView.classList.remove("hidden");
  els.exportCsv.disabled = false;
  els.exportJson.disabled = false;
  renderRun();
}

function buildSchedule(proposers, responders) {
  return responders.map((_, periodIndex) => {
    const pairs = proposers.map((proposer, proposerIndex) => ({
      proposerId: proposer.id,
      responderId: responders[(proposerIndex + periodIndex) % responders.length].id,
    }));
    return {
      period: periodIndex + 1,
      pairs,
    };
  });
}

function renderRun() {
  const period = getCurrentPeriod();
  const pair = getCurrentPair();
  els.subtitle.textContent = `${state.players.length} players, ${state.schedule.length} periods, ${ROUNDS_PER_PERIOD} rounds per period`;
  els.periodStatus.textContent = `${period.period} / ${state.schedule.length}`;
  els.roundStatus.textContent = `${state.current.round} / ${ROUNDS_PER_PERIOD}`;
  els.pairStatus.textContent = `${state.current.pairIndex + 1} / ${period.pairs.length}`;
  els.treatmentStatus.textContent = state.treatment.picture ? "Pictures shown" : "Anonymous partners";
  els.scheduleList.innerHTML = renderSchedule();

  if (state.current.phase === "proposer") {
    renderProposerStage(pair);
  } else if (state.current.phase === "responder") {
    renderResponderStage(pair);
  } else {
    renderResultStage(pair);
  }
}

function renderSchedule() {
  return state.schedule.map((period, periodIndex) => {
    const rows = period.pairs.map((pair, pairIndex) => {
      const active = periodIndex === state.current.periodIndex && pairIndex === state.current.pairIndex;
      const proposer = getPlayer(pair.proposerId);
      const responder = getPlayer(pair.responderId);
      return `
        <div class="pair-line ${active ? "active" : ""}">
          <span>${escapeHtml(proposer.name)}</span>
          <span>${escapeHtml(responder.name)}</span>
        </div>
      `;
    }).join("");

    return `
      <div class="period-block">
        <div class="period-title">
          <span>Period ${period.period}</span>
          <span>${period.pairs.length} pairs</span>
        </div>
        ${rows}
      </div>
    `;
  }).join("");
}

function renderProposerStage(pair) {
  const proposer = getPlayer(pair.proposerId);
  const responder = getPlayer(pair.responderId);
  els.stage.innerHTML = `
    <div class="phase-header">
      <div>
        <h2>Proposer Decision</h2>
        <p>${escapeHtml(proposer.name)} chooses a whole-dollar amount from $0 to $${STARTING_ENDOWMENT} to send.</p>
      </div>
      <span class="tag">Step 1 of 3</span>
    </div>

    <div class="identity-grid">
      ${renderIdentity("Proposer", proposer, true)}
      ${renderIdentity("Responder", responder, state.treatment.picture)}
    </div>

    <form id="offer-form" class="decision-form">
      <label>
        Amount sent to responder
        <div class="range-row">
          <input id="offer-range" type="range" min="0" max="${STARTING_ENDOWMENT}" step="1" value="10">
          <input id="offer-input" type="number" min="0" max="${STARTING_ENDOWMENT}" step="1" value="10">
        </div>
      </label>
      <div class="money-grid">
        <div class="money-box">
          <span>Proposer keeps before return</span>
          <strong id="kept-preview">$10.00</strong>
        </div>
        <div class="money-box">
          <span>Responder receives after tripling</span>
          <strong id="tripled-preview">$30.00</strong>
        </div>
      </div>
      <button type="submit">Submit Offer</button>
    </form>
  `;

  const range = document.querySelector("#offer-range");
  const input = document.querySelector("#offer-input");
  const sync = (value) => {
    const amount = clampInteger(value, 0, STARTING_ENDOWMENT);
    range.value = String(amount);
    input.value = String(amount);
    document.querySelector("#kept-preview").textContent = money(STARTING_ENDOWMENT - amount);
    document.querySelector("#tripled-preview").textContent = money(amount * MULTIPLIER);
  };

  range.addEventListener("input", (event) => sync(event.target.value));
  input.addEventListener("input", (event) => sync(event.target.value));
  document.querySelector("#offer-form").addEventListener("submit", (event) => {
    event.preventDefault();
    submitOffer(clampInteger(input.value, 0, STARTING_ENDOWMENT));
  });
}

function renderResponderStage(pair) {
  const record = getActiveRecord();
  const proposer = getPlayer(pair.proposerId);
  const responder = getPlayer(pair.responderId);
  els.stage.innerHTML = `
    <div class="phase-header">
      <div>
        <h2>Responder Decision</h2>
        <p>${escapeHtml(responder.name)} chooses how much of the tripled transfer to send back.</p>
      </div>
      <span class="tag">Step 2 of 3</span>
    </div>

    <div class="identity-grid">
      ${renderIdentity("Responder", responder, true)}
      ${renderIdentity("Proposer", proposer, state.treatment.picture)}
    </div>

    <div class="money-grid">
      <div class="money-box">
        <span>Offer received</span>
        <strong>${money(record.offer)}</strong>
      </div>
      <div class="money-box">
        <span>Tripled amount available</span>
        <strong>${money(record.tripledAmount)}</strong>
      </div>
    </div>

    <form id="return-form" class="decision-form">
      <label>
        Amount sent back to proposer
        <div class="range-row">
          <input id="return-range" type="range" min="0" max="${record.tripledAmount}" step="1" value="${Math.floor(record.tripledAmount / 2)}">
          <input id="return-input" type="number" min="0" max="${record.tripledAmount}" step="1" value="${Math.floor(record.tripledAmount / 2)}">
        </div>
      </label>
      <div class="money-grid">
        <div class="money-box">
          <span>Responder keeps from tripled amount</span>
          <strong id="responder-keeps-preview">${money(record.tripledAmount - Math.floor(record.tripledAmount / 2))}</strong>
        </div>
        <div class="money-box">
          <span>Amount responder chooses to return</span>
          <strong id="return-preview">${money(Math.floor(record.tripledAmount / 2))}</strong>
        </div>
      </div>
      <button type="submit">Submit Return</button>
    </form>
  `;

  const range = document.querySelector("#return-range");
  const input = document.querySelector("#return-input");
  const sync = (value) => {
    const amount = clampInteger(value, 0, record.tripledAmount);
    range.value = String(amount);
    input.value = String(amount);
    document.querySelector("#responder-keeps-preview").textContent = money(record.tripledAmount - amount);
    document.querySelector("#return-preview").textContent = money(amount);
  };

  range.addEventListener("input", (event) => sync(event.target.value));
  input.addEventListener("input", (event) => sync(event.target.value));
  document.querySelector("#return-form").addEventListener("submit", (event) => {
    event.preventDefault();
    submitReturn(clampInteger(input.value, 0, record.tripledAmount));
  });
}

function renderResultStage(pair) {
  const record = getActiveRecord();
  const proposer = getPlayer(pair.proposerId);
  const responder = getPlayer(pair.responderId);
  els.stage.innerHTML = `
    <div class="phase-header">
      <div>
        <h2>Proposer Receipt</h2>
        <p>Show this receipt to the proposer only.</p>
      </div>
      <span class="tag">Step 3 of 3</span>
    </div>

    <div class="identity-grid">
      ${renderIdentity("Proposer", proposer, true)}
      ${renderIdentity("Responder", responder, state.treatment.picture)}
    </div>

    <div class="money-grid">
      <div class="money-box">
        <span>Offer sent</span>
        <strong>${money(record.offer)}</strong>
      </div>
      <div class="money-box">
        <span>Amount delivered back</span>
        <strong>${money(record.deliveredReturn)}</strong>
      </div>
      <div class="money-box">
        <span>Proposer payoff</span>
        <strong>${money(record.proposerPayoff)}</strong>
      </div>
    </div>

    <p class="result-note">Record saved. Continue to the next decision when both players are ready.</p>
    <button id="next-step" type="button">${getNextLabel()}</button>
  `;

  document.querySelector("#next-step").addEventListener("click", advanceAfterResult);
}

function renderIdentity(label, player, showPicture) {
  const initials = getInitials(player.name);
  if (!showPicture) {
    return `
      <div class="identity anonymous">
        <div>
          <span>${escapeHtml(label)}</span>
          <strong>Anonymous ${escapeHtml(label)}</strong>
          <p>Picture and demographic note hidden in this condition.</p>
        </div>
      </div>
    `;
  }

  const avatar = player.picture
    ? `<img src="${player.picture}" alt="">`
    : `<span>${escapeHtml(initials)}</span>`;
  const note = player.note ? escapeHtml(player.note) : "No demographic note entered.";
  return `
    <div class="identity">
      <div class="avatar">${avatar}</div>
      <div>
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(player.name)}</strong>
        <p>${note}</p>
      </div>
    </div>
  `;
}

function submitOffer(offer) {
  const period = getCurrentPeriod();
  const pair = getCurrentPair();
  state.records.push({
    sessionTreatment: state.treatment.label,
    pictureCondition: state.treatment.picture,
    errorCondition: state.treatment.error,
    period: period.period,
    round: state.current.round,
    pairNumber: state.current.pairIndex + 1,
    proposerId: pair.proposerId,
    proposerName: getPlayer(pair.proposerId).name,
    responderId: pair.responderId,
    responderName: getPlayer(pair.responderId).name,
    offer,
    tripledAmount: offer * MULTIPLIER,
    intendedReturn: null,
    errorApplied: null,
    deliveredReturn: null,
    proposerPayoff: null,
    responderPayoff: null,
  });
  state.current.phase = "responder";
  renderRun();
}

function submitReturn(intendedReturn) {
  const record = getActiveRecord();
  const errorApplied = state.treatment.error && Math.random() < 0.5;
  const deliveredReturn = errorApplied ? intendedReturn / 2 : intendedReturn;
  record.intendedReturn = intendedReturn;
  record.errorApplied = errorApplied;
  record.deliveredReturn = deliveredReturn;
  record.proposerPayoff = STARTING_ENDOWMENT - record.offer + deliveredReturn;
  record.responderPayoff = record.tripledAmount - intendedReturn;
  state.current.phase = "result";
  renderRun();
}

function advanceAfterResult() {
  const period = getCurrentPeriod();
  if (state.current.pairIndex < period.pairs.length - 1) {
    state.current.pairIndex += 1;
    state.current.phase = "proposer";
    renderRun();
    return;
  }

  if (state.current.round < ROUNDS_PER_PERIOD) {
    state.current.round += 1;
    state.current.pairIndex = 0;
    state.current.phase = "proposer";
    renderRun();
    return;
  }

  if (state.current.periodIndex < state.schedule.length - 1) {
    state.current.periodIndex += 1;
    state.current.round = 1;
    state.current.pairIndex = 0;
    state.current.phase = "proposer";
    renderRun();
    return;
  }

  completeSession();
}

function completeSession() {
  els.runView.classList.add("hidden");
  els.completeView.classList.remove("hidden");
  els.subtitle.textContent = "Session complete";
  renderSummary();
}

function renderSummary() {
  const completedRecords = state.records.filter((record) => record.deliveredReturn !== null);
  const averageOffer = average(completedRecords.map((record) => record.offer));
  const averageReturn = average(completedRecords.map((record) => record.intendedReturn));
  const errorCount = completedRecords.filter((record) => record.errorApplied).length;
  els.summary.innerHTML = `
    <div class="summary-box">
      <span>Decisions recorded</span>
      <strong>${completedRecords.length}</strong>
    </div>
    <div class="summary-box">
      <span>Average offer</span>
      <strong>${money(averageOffer)}</strong>
    </div>
    <div class="summary-box">
      <span>Average intended return</span>
      <strong>${money(averageReturn)}</strong>
    </div>
    <div class="summary-box">
      <span>Hidden errors applied</span>
      <strong>${errorCount}</strong>
    </div>
  `;
}

function exportData(format) {
  if (format === "json") {
    const payload = {
      exportedAt: new Date().toISOString(),
      startingEndowment: STARTING_ENDOWMENT,
      multiplier: MULTIPLIER,
      roundsPerPeriod: ROUNDS_PER_PERIOD,
      treatment: state.treatment,
      players: state.players.map(({ picture, ...player }) => player),
      schedule: state.schedule,
      records: state.records,
    };
    downloadFile("trust-game-data.json", "application/json", JSON.stringify(payload, null, 2));
    return;
  }

  const headers = [
    "sessionTreatment",
    "pictureCondition",
    "errorCondition",
    "period",
    "round",
    "pairNumber",
    "proposerId",
    "proposerName",
    "responderId",
    "responderName",
    "offer",
    "tripledAmount",
    "intendedReturn",
    "errorApplied",
    "deliveredReturn",
    "proposerPayoff",
    "responderPayoff",
  ];
  const rows = state.records.map((record) => headers.map((header) => record[header]));
  const csv = [headers, ...rows].map((row) => row.map(csvCell).join(",")).join("\n");
  downloadFile("trust-game-data.csv", "text/csv", csv);
}

function downloadFile(filename, type, content) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function resetSession() {
  const hasData = state.records.length > 0;
  if (hasData && !window.confirm("Reset the session and clear unsaved data?")) {
    return;
  }
  state.schedule = [];
  state.records = [];
  state.current = {
    periodIndex: 0,
    round: 1,
    pairIndex: 0,
    phase: "setup",
  };
  els.setupView.classList.remove("hidden");
  els.runView.classList.add("hidden");
  els.completeView.classList.add("hidden");
  els.exportCsv.disabled = true;
  els.exportJson.disabled = true;
  els.subtitle.textContent = "Configure a session";
}

function getCurrentPeriod() {
  return state.schedule[state.current.periodIndex];
}

function getCurrentPair() {
  return getCurrentPeriod().pairs[state.current.pairIndex];
}

function getActiveRecord() {
  const period = getCurrentPeriod();
  const pair = getCurrentPair();
  return state.records.find((record) => (
    record.period === period.period
    && record.round === state.current.round
    && record.pairNumber === state.current.pairIndex + 1
    && record.proposerId === pair.proposerId
    && record.responderId === pair.responderId
  ));
}

function getPlayer(id) {
  return state.players.find((player) => player.id === id);
}

function getNextLabel() {
  const period = getCurrentPeriod();
  if (state.current.pairIndex < period.pairs.length - 1) return "Next Pair";
  if (state.current.round < ROUNDS_PER_PERIOD) return "Start Round 2";
  if (state.current.periodIndex < state.schedule.length - 1) return "Next Period";
  return "Complete Session";
}

function clampInteger(value, min, max) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return min;
  return Math.max(min, Math.min(max, parsed));
}

function average(values) {
  if (values.length === 0) return 0;
  return values.reduce((total, value) => total + Number(value), 0) / values.length;
}

function money(value) {
  return `$${Number(value || 0).toFixed(2)}`;
}

function getInitials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("") || "?";
}

function csvCell(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

init();
