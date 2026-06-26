import csv
import os
import json

from state import state
from handlers.auction import (
    prepare_next_player,
    start_auction,
    next_player,
    start_timer,
    pause_auction,
    resume_auction,
    set_player_by_index,
    undo_last_sold,
    mark_player_unsold,
    force_sell_player,
    reset_auction_keep_players,
    reset_auction_full,
)


def load_players_from_csv():
    team_leaders = {
        "A": "사 라",
        "B": "이 궤",
        "C": "이 브",
        "D": "싶 오",
        "E": "채집당함",
    }

    leader_profiles = {}
    players = []

    with open("data/players.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            nickname = row.get("nickname", "").strip()

            player_data = {
                "nickname": nickname,
                "position": row.get("position", "").strip(),
                "tier": row.get("tier", "").strip(),
                "image": row.get("image", "").strip(),
                "sold": False,
                "team": None,
                "price": 0
            }

            leader_team = None
            for team_name, leader_name in team_leaders.items():
                if nickname == leader_name:
                    leader_team = team_name
                    break

            if leader_team:
                leader_profiles[leader_team] = player_data
                continue

            players.append(player_data)

    state["players"] = players
    state["leader_profiles"] = leader_profiles
    state["current_player_index"] = -1
    state["sold_results"] = []
    state["current_player"] = None
    state["current_position"] = None
    state["current_bid"] = 0
    state["highest_team"] = None
    state["phase"] = "waiting"
    state["remaining_time"] = 15
    state["is_paused"] = True
    state["timer_version"] += 1

    for team_name, team in state["teams"].items():
        team["spent"] = 0
        team["players"] = []

        if team_name in team_leaders:
            team["players"].append(team_leaders[team_name])

    state["logs"].insert(0, f"팀장 5명을 배치하고 경매 선수 {len(players)}명을 불러왔습니다.")

    return players

    state["players"] = players
    state["current_player_index"] = -1
    state["sold_results"] = []
    state["current_player"] = None
    state["current_position"] = None
    state["current_bid"] = 0
    state["highest_team"] = None
    state["phase"] = "waiting"
    state["remaining_time"] = 15
    state["is_paused"] = True
    state["timer_version"] += 1

    for team in state["teams"].values():
        team["spent"] = 0
        team["players"] = []

    state["logs"].insert(0, f"선수 목록 {len(players)}명을 불러왔습니다.")

    return players


def save_results_to_csv():
    os.makedirs("data", exist_ok=True)

    with open("data/results.csv", "w", newline="", encoding="utf-8-sig") as file:
        fieldnames = ["nickname", "position", "team", "price"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for result in state["sold_results"]:
            writer.writerow({
                "nickname": result.get("nickname", ""),
                "position": result.get("position", ""),
                "team": result.get("team") or "유찰",
                "price": result.get("price", 0)
            })

    state["logs"].insert(0, "낙찰 결과가 data/results.csv 파일로 저장되었습니다.")


def save_state_to_json():
    os.makedirs("data", exist_ok=True)

    with open("data/state_backup.json", "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)

    state["logs"].insert(0, "현재 경매 상태가 저장되었습니다.")


def load_state_from_json():
    if not os.path.exists("data/state_backup.json"):
        state["logs"].insert(0, "저장된 경매 상태 파일이 없습니다.")
        return False

    with open("data/state_backup.json", "r", encoding="utf-8") as file:
        saved_state = json.load(file)

    state.clear()
    state.update(saved_state)

    state["is_paused"] = True
    state["timer_version"] += 1
    state["logs"].insert(0, "저장된 경매 상태를 불러왔습니다. READY/일시정지 상태입니다.")

    return True


def register_admin_handlers(socketio):
    @socketio.on("admin_load_players")
    def admin_load_players():
        load_players_from_csv()
        socketio.emit("state_update", state)

    @socketio.on("admin_start_auction")
    def admin_start_auction():
        if start_auction():
            socketio.emit("state_update", state)
            start_timer(socketio)

    @socketio.on("admin_next_player")
    def admin_next_player():
        if next_player():
            socketio.emit("state_update", state)

    @socketio.on("admin_pause_auction")
    def admin_pause_auction():
        if pause_auction():
            socketio.emit("state_update", state)

    @socketio.on("admin_resume_auction")
    def admin_resume_auction():
        if resume_auction():
            socketio.emit("state_update", state)
            start_timer(socketio)

    @socketio.on("admin_set_player_by_index")
    def admin_set_player_by_index(data):
        try:
            index = int(data.get("index", -1))
        except ValueError:
            return

        if set_player_by_index(index):
            socketio.emit("state_update", state)

    @socketio.on("admin_undo")
    def admin_undo():
        if undo_last_sold():
            socketio.emit("state_update", state)

    @socketio.on("admin_mark_unsold")
    def admin_mark_unsold(data):
        try:
            index = int(data.get("index", -1))
        except ValueError:
            return

        if mark_player_unsold(index):
            socketio.emit("state_update", state)

    @socketio.on("admin_force_sell")
    def admin_force_sell(data):
        try:
            index = int(data.get("index", -1))
            price = int(data.get("price", 0))
        except ValueError:
            return

        team_name = data.get("team")

        if force_sell_player(index, team_name, price):
            socketio.emit("state_update", state)

    @socketio.on("admin_save_results")
    def admin_save_results():
        save_results_to_csv()
        socketio.emit("state_update", state)

    @socketio.on("admin_save_state")
    def admin_save_state():
        save_state_to_json()
        socketio.emit("state_update", state)

    @socketio.on("admin_load_state")
    def admin_load_state():
        if load_state_from_json():
            socketio.emit("state_update", state)

    @socketio.on("admin_reset_keep_players")
    def admin_reset_keep_players():
        if reset_auction_keep_players():
            socketio.emit("state_update", state)

    @socketio.on("admin_reset_full")
    def admin_reset_full():
        if reset_auction_full():
            socketio.emit("state_update", state)

    @socketio.on("admin_set_player")
    def admin_set_player(data):
        name = data.get("name", "").strip()
        position = data.get("position", "TOP")

        if not name:
            return

        state["phase"] = "ready"
        state["current_player"] = name
        state["current_position"] = position
        state["current_bid"] = 0
        state["highest_team"] = None
        state["remaining_time"] = 15
        state["is_paused"] = True
        state["timer_version"] += 1
        state["logs"].insert(0, f"{name}({position}) 선수가 현재 경매 선수로 설정되었습니다.")

        socketio.emit("state_update", state)
