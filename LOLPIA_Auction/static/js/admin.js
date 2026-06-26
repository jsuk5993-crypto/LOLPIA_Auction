const socket = io();

let selectedPlayerIndex = null;
let latestState = null;

socket.on("state_update", (state) => {
  latestState = state;

  document.getElementById("admin-phase").textContent = state.phase;
  document.getElementById("admin-player").textContent = state.current_player || "-";
  document.getElementById("admin-team").textContent = state.highest_team || "-";
  document.getElementById("admin-bid").textContent = state.current_bid || 0;

  renderPlayerList(state);
  renderTeamStatus(state);
  renderSelectedPlayer(state);
  renderSoldResults(state);
});

function renderPlayerList(state) {
  const playerList = document.getElementById("player-list");
  if (!playerList) return;

  playerList.innerHTML = "";

  if (!state.players || state.players.length === 0) {
    playerList.innerHTML = "<p>아직 불러온 선수가 없습니다.</p>";
    return;
  }

  state.players.forEach((player, index) => {
    const div = document.createElement("button");

    let statusText = "⚪ 대기";
    let statusClass = "waiting";

    if (index === state.current_player_index && state.phase === "auction") {
      statusText = state.is_paused ? "⏸ 일시정지" : "⏳ 경매중";
      statusClass = "active";
    } else if (player.sold) {
      if (player.team) {
        statusText = `✅ ${player.team}팀 ${player.price}P`;
      } else {
        statusText = "❌ 유찰";
      }
      statusClass = "sold";
    }

    if (selectedPlayerIndex === index) {
      statusClass += " selected";
    }

    div.type = "button";
    div.className = `admin-player-item ${statusClass}`;
    div.innerHTML = `
      <span>${index + 1}. ${player.nickname}</span>
      <strong>${player.position}</strong>
      <em>${statusText}</em>
    `;

    div.addEventListener("click", () => {
      selectedPlayerIndex = index;
      renderPlayerList(latestState);
      renderSelectedPlayer(latestState);
    });

    playerList.appendChild(div);
  });
}

function renderSelectedPlayer(state) {
  const box = document.getElementById("selected-player-box");
  if (!box) return;

  if (selectedPlayerIndex === null || !state.players || !state.players[selectedPlayerIndex]) {
    box.innerHTML = "<p>선수를 선택하면 상세 정보가 표시됩니다.</p>";
    return;
  }

  const player = state.players[selectedPlayerIndex];

  box.innerHTML = `
    <div class="selected-player-name">${player.nickname}</div>
    <div class="selected-player-meta">${player.position} / ${player.tier || "-"}</div>
    <div class="selected-player-result">
      상태: ${
        player.sold
          ? player.team
            ? `${player.team}팀 ${player.price}P 낙찰`
            : "유찰"
          : "대기중"
      }
    </div>
  `;
}

function renderTeamStatus(state) {
  const teamStatus = document.getElementById("admin-team-status");
  if (!teamStatus) return;

  teamStatus.innerHTML = "";

  Object.entries(state.teams).forEach(([name, team]) => {
    const remain = team.budget - team.spent;
    const spent = team.spent || 0;
    const playerCount = team.players ? team.players.length : 0;

    const div = document.createElement("div");
    div.className = "admin-team-row";
    div.innerHTML = `
      <strong>${name}팀</strong>
      <span>${remain}P 남음</span>
      <span>${spent}P 사용</span>
      <em>${playerCount}명</em>
    `;

    teamStatus.appendChild(div);
  });
}

function renderSoldResults(state) {
  const soldResultList = document.getElementById("sold-result-list");
  if (!soldResultList) return;

  soldResultList.innerHTML = "";

  if (!state.sold_results || state.sold_results.length === 0) {
    soldResultList.innerHTML = "<p>아직 낙찰 결과가 없습니다.</p>";
    return;
  }

  state.sold_results.forEach((result, index) => {
    const div = document.createElement("div");
    div.className = "sold-result-item";

    const teamText = result.team ? `${result.team}팀` : "유찰";
    const priceText = result.team ? `${result.price}P` : "-";

    div.innerHTML = `
      <span>${index + 1}. ${result.nickname}</span>
      <strong>${result.position}</strong>
      <em>${teamText}</em>
      <b>${priceText}</b>
    `;

    soldResultList.appendChild(div);
  });
}

document.getElementById("set-player-btn").addEventListener("click", () => {
  const name = document.getElementById("test-player-name").value;
  const position = document.getElementById("test-player-position").value;

  socket.emit("admin_set_player", { name, position });
  document.getElementById("test-player-name").value = "";
});

document.getElementById("load-players-btn").addEventListener("click", () => {
  socket.emit("admin_load_players");
});

document.getElementById("start-auction-btn").addEventListener("click", () => {
  socket.emit("admin_start_auction");
});

document.getElementById("next-player-btn").addEventListener("click", () => {
  socket.emit("admin_next_player");
});

document.getElementById("pause-auction-btn").addEventListener("click", () => {
  socket.emit("admin_pause_auction");
});

document.getElementById("resume-auction-btn").addEventListener("click", () => {
  socket.emit("admin_resume_auction");
});

document.getElementById("set-selected-player-btn").addEventListener("click", () => {
  if (selectedPlayerIndex === null) {
    alert("먼저 선수를 선택하세요.");
    return;
  }

  socket.emit("admin_set_player_by_index", {
    index: selectedPlayerIndex
  });
});

document.getElementById("undo-btn").addEventListener("click", () => {
  socket.emit("admin_undo");
});

document.getElementById("mark-unsold-btn").addEventListener("click", () => {
  if (selectedPlayerIndex === null) {
    alert("먼저 선수를 선택하세요.");
    return;
  }

  if (!confirm("선택한 선수를 유찰 처리할까요?")) {
    return;
  }

  socket.emit("admin_mark_unsold", {
    index: selectedPlayerIndex
  });
});

document.getElementById("force-sell-btn").addEventListener("click", () => {
  if (selectedPlayerIndex === null) {
    alert("먼저 선수를 선택하세요.");
    return;
  }

  const team = document.getElementById("force-sell-team").value;
  const price = Number(document.getElementById("force-sell-price").value);

  if (!price || price <= 0) {
    alert("낙찰 가격을 입력하세요.");
    return;
  }

  socket.emit("admin_force_sell", {
    index: selectedPlayerIndex,
    team: team,
    price: price
  });

  document.getElementById("force-sell-price").value = "";
});

document.getElementById("save-results-btn").addEventListener("click", () => {
  socket.emit("admin_save_results");
  alert("결과 저장을 요청했습니다.");
});
document.getElementById("save-state-btn").addEventListener("click", () => {
  socket.emit("admin_save_state");
  alert("현재 상태 저장을 요청했습니다.");
});

document.getElementById("load-state-btn").addEventListener("click", () => {
  if (!confirm("저장된 상태를 불러올까요? 현재 화면 상태가 덮어씌워집니다.")) {
    return;
  }

  socket.emit("admin_load_state");
});
document.getElementById("reset-keep-players-btn").addEventListener("click", () => {
  if (!confirm("경매를 초기화할까요? 선수 목록은 유지됩니다.")) {
    return;
  }

  socket.emit("admin_reset_keep_players");
});

document.getElementById("reset-full-btn").addEventListener("click", () => {
  if (!confirm("새 대회를 시작할까요? 선수 목록과 경매 결과가 모두 초기화됩니다.")) {
    return;
  }

  socket.emit("admin_reset_full");
});