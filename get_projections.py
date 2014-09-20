
import json
import os
import sys

import requests

from utils import memoize_to_disk

API_KEY = os.environ.get("FFN_API_KEY", "test")
RANKING_URL = "http://www.fantasyfootballnerd.com/service/weekly-rankings/json/{key}/{position}/{week}"


def get_current_week():
    return int(sys.argv[1])


@memoize_to_disk
def get_projections_for_position_for_current_week(position, week):
    response = requests.get(RANKING_URL.format(key=API_KEY, position=position, week=week))
    return json.loads(response.text)


if __name__=="__main__":
    for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
        get_projections_for_position_for_current_week(position, get_current_week())
