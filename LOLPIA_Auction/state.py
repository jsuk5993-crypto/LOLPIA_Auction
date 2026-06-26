from config import TEAM_NAMES, START_BUDGET

state = {
    "phase": "waiting",

    "current_player": None,

    "current_position": None,

    "current_bid": 0,

    "highest_team": None,
    "remaining_time": 15,
    "timer_version": 0,
    "is_paused": False,

    "logs": [],
    "sold_results": [],
    "players": [],
"current_player_index": -1,

    "teams": {
        team: {
            "budget": START_BUDGET,
            "spent": 0,
            "players": []
        }
        for team in TEAM_NAMES
    }
}