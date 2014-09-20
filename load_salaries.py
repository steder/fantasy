"""
Load salaries from a file and update the corresponding player record with their salary

Usage:

  python load_salaries.py 3 data.json

"""
import glob
import json
import sys

from sqlalchemy import create_engine
from sqlalchemy import text


def load_salaries_for_week(week, path, year=2014):
    engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)
    connection = engine.connect()
    with open(path, "r") as infile:
        players = json.load(infile)
        for player_id, player in players.iteritems():
            connection.execute(text("""
            UPDATE players
            SET salary = :salary, fanduel_points_per_game = :fanduel
            WHERE name = :name
            AND year = :year
            AND week = :week;
            """), **dict(
                year=year,
                week=week,
                name=player[1],
                salary=int(player[5]),
                fanduel=float(player[6]),
            ))


if __name__=="__main__":
    load_salaries_for_week(int(sys.argv[1]), sys.argv[2])
