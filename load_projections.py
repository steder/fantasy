import glob
import json
import sys

from sqlalchemy import create_engine
from sqlalchemy import text


PATHS = [
    "QB_{}.data",
    "DEF_{}.data",
    "K_{}.data",
    "RB_{}.data",
    "TE_{}.data",
    "WR_{}.data",
]


engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)
connection = engine.connect()

week = int(sys.argv[1])

assert 1 <= week <= 17

connection.execute(text("delete from players where week = :week"), week=week)

for pattern in PATHS:
    path = pattern.format(week)
    print path
    with open(path, "r") as infile:
        data = json.load(infile)
    year = 2014
    week = data['Week']
    players = data['Rankings']
    for player in players:
        connection.execute(text("""
        INSERT INTO players
        (name, team, position, year, week,
        standard, standard_low, standard_high,
        ppr, ppr_low, ppr_high,
        injury, practice_status, game_status)
        VALUES (:name, :team, :position, :year, :week,
        :standard, :standard_low, :standard_high,
        :ppr, :ppr_low, :ppr_high,
        :injury, :practice_status, :game_status)
        """), **dict(
            name=player['name'],
            team=player['team'],
            position=player['position'],
            year=year,
            week=week,
            standard=player['standard'],
            standard_low=player['standardLow'],
            standard_high=player['standardHigh'],
            ppr=player['ppr'],
            ppr_low=player['pprLow'],
            ppr_high=player['pprHigh'],
            injury=player['injury'],
            practice_status=player['practiceStatus'],
            game_status=player['gameStatus']
        ))
