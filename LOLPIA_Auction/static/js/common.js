const socket = io();

socket.on("state_update", (state) => {
  document.getElementById("phase").textContent = state.phase;
  document.getElementById("player-card-name").textContent = state.current_player || "-";
  document.getElementById("player-position").textContent = state.current_position || "POSITION";
  document.getElementById("bid").textContent = state.current_bid || 0;
  document.getElementById("team").textContent = state.highest_team || "-";

  const timerEl = document.getElementById("timer");
  if (timerEl) {
    timerEl.textContent = state.remaining_time ?? 15;
  }

  const teamsDiv = document.getElementById("teams");
  teamsDiv.innerHTML = "";

  Object.entries(state.teams).forEach(([name, team]) => {
    const remain = team.budget - team.spent;
    const percent = Math.max(0, Math.min(100, (remain / team.budget) * 100));

    const div = document.createElement("div");
    div.className = "team";
    div.innerHTML = `
      <div class="team-top">
        <span>${name}팀</span>
        <span>${remain}P</span>
      </div>
      <div class="point-bar">
        <div class="point-fill" style="width: ${percent}%"></div>
      </div>
    `;

    teamsDiv.appendChild(div);
  });

  const logList = document.getElementById("log-list");
  logList.innerHTML = "";

  if (!state.logs || state.logs.length === 0) {
    logList.innerHTML = "<p>아직 로그가 없습니다.</p>";
  } else {
    state.logs.slice(0, 8).forEach((log) => {
      const p = document.createElement("p");

      if (log.includes("입찰")) {
        p.className = "log-bid";
      } else if (log.includes("낙찰")) {
        p.className = "log-sold";
      } else if (log.includes("유찰")) {
        p.className = "log-unsold";
      } else {
        p.className = "log-normal";
      }

      p.textContent = `• ${log}`;
      logList.appendChild(p);
    });
  }
});