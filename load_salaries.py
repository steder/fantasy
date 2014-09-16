"""
Load salaries from a file and update the corresponding player record with their salary

"""
import glob
import json

from sqlalchemy import create_engine
from sqlalchemy import text


GLOBS = [
    "FANDUEL_*.data",
]


engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)
connection = engine.connect()


for pattern in GLOBS:
    for path in glob.glob(pattern):
        print path
        with open(path, "r") as infile:
            players = json.load(infile)
        year = 2014
        week = 2
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
