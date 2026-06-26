from flask_socketio import emit

from state import state
from config import MIN_BID, EXTEND_TIME


def register_team_handlers(socketio):
    @socketio.on("team_bid")
    def team_bid(data):
        team_name = data.get("team")

        try:
            bid_amount = int(data.get("amount", 0))
        except ValueError:
            emit("bid_error", {"message": "입찰 금액이 올바르지 않습니다."})
            return

        if state["phase"] != "auction":
            emit("bid_error", {"message": "현재 경매가 진행 중이 아닙니다."})
            return

        if team_name not in state["teams"]:
            emit("bid_error", {"message": "존재하지 않는 팀입니다."})
            return

        if state["highest_team"] == team_name:
            emit("bid_error", {"message": "현재 최고 입찰팀은 다시 입찰할 수 없습니다."})
            return

        team = state["teams"][team_name]
        remain = team["budget"] - team["spent"]

        if bid_amount > remain:
            emit("bid_error", {"message": "잔여 포인트보다 높게 입찰할 수 없습니다."})
            return

        min_required = state["current_bid"] + MIN_BID

        if bid_amount < min_required:
            emit("bid_error", {"message": f"최소 {min_required}P 이상 입찰해야 합니다."})
            return

        state["current_bid"] = bid_amount
        state["highest_team"] = team_name

        if state["remaining_time"] < EXTEND_TIME:
            state["remaining_time"] = EXTEND_TIME
        else:
            state["remaining_time"] += 3

        state["logs"].insert(0, f"{team_name}팀이 {bid_amount}P 입찰했습니다.")

        emit("bid_success", {"message": f"{bid_amount}P 입찰 성공!"})
        socketio.emit("state_update", state)