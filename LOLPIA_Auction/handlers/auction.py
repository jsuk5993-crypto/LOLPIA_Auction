from state import state
from config import START_TIME


def prepare_next_player():
    if len(state["players"]) == 0:
        return False

    state["current_player_index"] += 1

    if state["current_player_index"] >= len(state["players"]):
        state["phase"] = "finished"
        state["current_player"] = None
        state["current_position"] = None
        state["logs"].insert(0, "모든 선수 경매가 종료되었습니다.")
        return False

    player = state["players"][state["current_player_index"]]

    state["phase"] = "ready"
    state["current_player"] = player["nickname"]
    state["current_position"] = player["position"]
    state["current_bid"] = 0
    state["highest_team"] = None
    state["remaining_time"] = START_TIME
    state["is_paused"] = True
    state["timer_version"] += 1

    state["logs"].insert(0, f"{player['nickname']}({player['position']}) 선수가 준비되었습니다.")
    return True


def start_auction():
    if state["phase"] != "ready":
        return False

    state["phase"] = "auction"
    state["is_paused"] = False
    state["remaining_time"] = START_TIME
    state["timer_version"] += 1

    state["logs"].insert(0, f"{state['current_player']} 경매가 시작되었습니다.")
    return True


def next_player():
    return prepare_next_player()


def set_player_by_index(index):
    if index < 0 or index >= len(state["players"]):
        return False

    player = state["players"][index]

    if player["sold"]:
        return False

    state["current_player_index"] = index
    state["phase"] = "ready"
    state["current_player"] = player["nickname"]
    state["current_position"] = player["position"]
    state["current_bid"] = 0
    state["highest_team"] = None
    state["remaining_time"] = START_TIME
    state["is_paused"] = True
    state["timer_version"] += 1

    state["logs"].insert(0, f"{player['nickname']} 선수가 수동으로 준비되었습니다.")
    return True


def pause_auction():
    if state["phase"] == "auction":
        state["is_paused"] = True
        state["logs"].insert(0, "경매가 일시정지되었습니다.")
        return True
    return False


def resume_auction():
    if state["phase"] == "auction":
        state["is_paused"] = False
        state["logs"].insert(0, "경매가 재개되었습니다.")
        return True
    return False


def finish_current_auction():
    index = state["current_player_index"]

    if index < 0 or index >= len(state["players"]):
        return

    player = state["players"][index]
    team_name = state["highest_team"]
    price = state["current_bid"]

    if team_name and price > 0:
        team = state["teams"][team_name]
        team["spent"] += price
        team["players"].append(player["nickname"])

        player["sold"] = True
        player["team"] = team_name
        player["price"] = price

        state["sold_results"].append({
            "nickname": player["nickname"],
            "position": player["position"],
            "team": team_name,
            "price": price
        })

        state["logs"].insert(0, f"{player['nickname']} 선수가 {team_name}팀에 {price}P로 낙찰되었습니다.")
    else:
        player["sold"] = True
        player["team"] = None
        player["price"] = 0

        state["sold_results"].append({
            "nickname": player["nickname"],
            "position": player["position"],
            "team": None,
            "price": 0
        })

        state["logs"].insert(0, f"{player['nickname']} 선수는 유찰되었습니다.")

    state["phase"] = "sold"
    state["is_paused"] = True
    state["timer_version"] += 1


def undo_last_sold():
    if not state["sold_results"]:
        return False

    last = state["sold_results"].pop()
    nickname = last["nickname"]
    team_name = last["team"]
    price = last["price"]

    if team_name and team_name in state["teams"]:
        team = state["teams"][team_name]
        team["spent"] -= price

        if nickname in team["players"]:
            team["players"].remove(nickname)

    target_index = None

    for index, player in enumerate(state["players"]):
        if player["nickname"] == nickname:
            target_index = index
            player["sold"] = False
            player["team"] = None
            player["price"] = 0
            break

    if target_index is None:
        return False

    player = state["players"][target_index]

    state["current_player_index"] = target_index
    state["phase"] = "ready"
    state["current_player"] = player["nickname"]
    state["current_position"] = player["position"]
    state["current_bid"] = 0
    state["highest_team"] = None
    state["remaining_time"] = START_TIME
    state["is_paused"] = True
    state["timer_version"] += 1

    state["logs"].insert(0, f"{nickname} 선수 낙찰이 되돌려졌습니다. READY 상태입니다.")
    return True


def mark_player_unsold(index):
    if index < 0 or index >= len(state["players"]):
        return False

    player = state["players"][index]

    if player["sold"]:
        return False

    player["sold"] = True
    player["team"] = None
    player["price"] = 0

    state["sold_results"].append({
        "nickname": player["nickname"],
        "position": player["position"],
        "team": None,
        "price": 0
    })

    if state["current_player_index"] == index:
        state["phase"] = "sold"
        state["is_paused"] = True
        state["timer_version"] += 1

    state["logs"].insert(0, f"{player['nickname']} 선수가 강제 유찰 처리되었습니다.")
    return True


def force_sell_player(index, team_name, price):
    if index < 0 or index >= len(state["players"]):
        return False

    if team_name not in state["teams"]:
        return False

    player = state["players"][index]

    if player["sold"]:
        return False

    team = state["teams"][team_name]
    remain = team["budget"] - team["spent"]

    if price <= 0 or price > remain:
        return False

    player["sold"] = True
    player["team"] = team_name
    player["price"] = price

    team["spent"] += price
    team["players"].append(player["nickname"])

    state["sold_results"].append({
        "nickname": player["nickname"],
        "position": player["position"],
        "team": team_name,
        "price": price
    })

    if state["current_player_index"] == index:
        state["phase"] = "sold"
        state["is_paused"] = True
        state["timer_version"] += 1

    state["logs"].insert(0, f"{player['nickname']} 선수가 강제로 {team_name}팀에 {price}P 낙찰되었습니다.")
    return True


def reset_auction_keep_players():
    state["phase"] = "waiting"
    state["current_player"] = None
    state["current_position"] = None
    state["current_bid"] = 0
    state["highest_team"] = None
    state["remaining_time"] = START_TIME
    state["current_player_index"] = -1
    state["is_paused"] = True
    state["timer_version"] += 1

    state["sold_results"] = []

    for player in state["players"]:
        player["sold"] = False
        player["team"] = None
        player["price"] = 0

    for team in state["teams"].values():
        team["spent"] = 0
        team["players"] = []

    state["logs"] = ["경매가 초기화되었습니다. 선수 목록은 유지됩니다."]
    return True


def reset_auction_full():
    state["phase"] = "waiting"
    state["current_player"] = None
    state["current_position"] = None
    state["current_bid"] = 0
    state["highest_team"] = None
    state["remaining_time"] = START_TIME
    state["current_player_index"] = -1
    state["is_paused"] = True
    state["timer_version"] += 1

    state["players"] = []
    state["sold_results"] = []

    for team in state["teams"].values():
        team["spent"] = 0
        team["players"] = []

    state["logs"] = ["새 대회 시작 상태로 초기화되었습니다. 선수목록을 다시 불러오세요."]
    return True


def start_timer(socketio):
    version = state["timer_version"]

    def timer_loop():
        while (
            state["phase"] == "auction"
            and state["remaining_time"] > 0
            and state["timer_version"] == version
        ):
            socketio.sleep(1)

            if state["is_paused"]:
                socketio.emit("state_update", state)
                continue

            state["remaining_time"] -= 1
            socketio.emit("state_update", state)

        if (
            state["phase"] == "auction"
            and state["remaining_time"] <= 0
            and state["timer_version"] == version
        ):
            finish_current_auction()
            socketio.emit("state_update", state)

    socketio.start_background_task(timer_loop)