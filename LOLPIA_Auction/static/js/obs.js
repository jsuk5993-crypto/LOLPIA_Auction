const socket = io();

let prevPlayer = null;
let prevBid = 0;
let prevTeam = null;

socket.on("state_update", (state) => {
  const playerEl = document.getElementById("obs-player");
  const positionEl = document.getElementById("obs-position");
  const bidEl = document.getElementById("obs-bid");
  const timerEl = document.getElementById("obs-timer");
  const cardEl = document.querySelector(".auction-player-card");
  const priceBox = document.querySelector(".auction-price-box");
  const timerBox = document.querySelector(".auction-timer-box");
  const imageBox = document.querySelector(".player-image-placeholder");

  const currentPlayerData = getCurrentPlayerData(state);
  const tier = currentPlayerData ? currentPlayerData.tier : "UNRANKED";
  const tierClass = getTierClass(tier);

  const currentPlayer = state.current_player || "-";
  const currentBid = Number(state.current_bid || 0);
  const currentTeam = state.highest_team || "-";
  const remainTime = state.remaining_time ?? 15;

  cardEl.className = `auction-player-card ${tierClass}`;
  imageBox.innerHTML = getPlayerImageHtml(
    currentPlayerData,
    tier ? tier.slice(0, 2) : "?",
    "main-player-img"
  );

  if (prevPlayer !== null && prevPlayer !== currentPlayer) {
    triggerClass(cardEl, "anim-player-enter");
  }

  if (prevBid !== currentBid) {
    animateNumber(bidEl, prevBid, currentBid);
    triggerClass(priceBox, "anim-bid-pop");
  } else {
    bidEl.textContent = currentBid;
  }

  if (prevTeam !== null && prevTeam !== currentTeam) {
    triggerClass(priceBox, "anim-team-change");
  }

  playerEl.textContent = currentPlayer;
  positionEl.textContent = `${state.current_position || "POSITION"} / ${tier || "-"}`;
  timerEl.textContent = remainTime;

  timerBox.classList.remove("timer-warn", "timer-danger", "timer-critical");
  if (remainTime <= 2) {
    timerBox.classList.add("timer-critical");
  } else if (remainTime <= 5) {
    timerBox.classList.add("timer-danger");
  } else if (remainTime <= 10) {
    timerBox.classList.add("timer-warn");
  }

  prevPlayer = currentPlayer;
  prevBid = currentBid;
  prevTeam = currentTeam;

  renderObsRosters(state);
  renderObsBidRank(state);
  renderObsLogs(state);
  renderObsStats(state);
});

function getTeamColorClass(index) {
  return `team-color-${["A", "B", "C", "D", "E"][index] || "A"}`;
}

function getTierClass(tier) {
  const cleanTier = (tier || "UNRANKED").toUpperCase();
  return `tier-${cleanTier}`;
}

function getCurrentPlayerData(state) {
  if (!state.players || state.current_player_index < 0) return null;
  return state.players[state.current_player_index] || null;
}

function getPlayerByName(state, nickname) {
  if (state.players) {
    const found = state.players.find((player) => player.nickname === nickname);
    if (found) return found;
  }

  if (state.leader_profiles) {
    const leaders = Object.values(state.leader_profiles);
    const foundLeader = leaders.find((player) => player.nickname === nickname);
    if (foundLeader) return foundLeader;
  }

  return null;
}

function getPlayerImageHtml(player, fallbackText, className) {
  if (player && player.image) {
    return `<img class="${className}" src="/static/img/players/${player.image}" alt="${player.nickname}">`;
  }

  return `<div class="${className} image-fallback">${fallbackText}</div>`;
}

function animateNumber(el, from, to) {
  const duration = 350;
  const start = performance.now();

  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const value = Math.floor(from + (to - from) * progress);
    el.textContent = value;

    if (progress < 1) {
      requestAnimationFrame(tick);
    } else {
      el.textContent = to;
    }
  }

  requestAnimationFrame(tick);
}

function triggerClass(el, className) {
  if (!el) return;
  el.classList.remove(className);
  void el.offsetWidth;
  el.classList.add(className);
}

function renderObsRosters(state) {
  const box = document.getElementById("obs-team-roster-list");
  box.innerHTML = "";

  Object.entries(state.teams).forEach(([name, team], index) => {
    const remain = team.budget - team.spent;
    const row = document.createElement("div");
    row.className = `draft-team-row ${getTeamColorClass(index)}`;

    const slots = [];

    for (let i = 0; i < 5; i++) {
      const playerName = team.players && team.players[i] ? team.players[i] : null;
      const playerData = playerName ? getPlayerByName(state, playerName) : null;
      const tierClass = playerData ? getTierClass(playerData.tier) : "";

      slots.push(`
        <div class="draft-player-slot ${playerName ? "filled" : ""} ${tierClass}">
          ${getPlayerImageHtml(playerData, playerName ? playerName.slice(0, 1) : "+", "slot-img")}
          <span>${playerName || ""}</span>
        </div>
      `);
    }

    row.innerHTML = `
      <div class="draft-team-info">
        <small>TEAM</small>
        <strong>${name}팀</strong>
        <em>${remain}P</em>
      </div>
      <div class="draft-slots">
        ${slots.join("")}
      </div>
    `;

    box.appendChild(row);
  });
}

function renderObsBidRank(state) {
  const box = document.getElementById("obs-bid-rank-list");
  box.innerHTML = "";

  if (!state.highest_team || !state.current_bid) {
    box.innerHTML = "<p>아직 입찰이 없습니다.</p>";
    return;
  }

  const div = document.createElement("div");
  div.className = "bid-rank-item highest";
  div.innerHTML = `
    <span>${state.highest_team}팀</span>
    <strong>${state.current_bid}P</strong>
    <em>최고가</em>
  `;
  box.appendChild(div);
}

function renderObsLogs(state) {
  const topLog = document.getElementById("obs-top-log-list");
  const bigLog = document.getElementById("obs-log-list");

  topLog.innerHTML = "";
  bigLog.innerHTML = "";

  if (!state.logs || state.logs.length === 0) {
    topLog.innerHTML = "<p>아직 로그가 없습니다.</p>";
    bigLog.innerHTML = "<p>아직 로그가 없습니다.</p>";
    return;
  }

  state.logs.slice(0, 3).forEach((log) => {
    const p = document.createElement("p");
    p.textContent = log;
    topLog.appendChild(p);
  });

  state.logs.slice(0, 12).forEach((log) => {
    const p = document.createElement("p");

    if (log.includes("입찰")) {
      p.className = "obs-log-bid";
    } else if (log.includes("낙찰")) {
      p.className = "obs-log-sold";
    } else if (log.includes("유찰")) {
      p.className = "obs-log-unsold";
    } else {
      p.className = "obs-log-normal";
    }

    p.textContent = log;
    bigLog.appendChild(p);
  });
}

function renderObsStats(state) {
  const total = state.players ? state.players.length : 0;
  const sold = state.sold_results ? state.sold_results.length : 0;
  const left = Math.max(0, total - sold);

  document.getElementById("obs-stat-total").textContent = `${total}명`;
  document.getElementById("obs-stat-sold").textContent = `${sold}명`;
  document.getElementById("obs-stat-left").textContent = `${left}명`;
}
