import glob
import json

from sqlalchemy import create_engine
from sqlalchemy import text


GLOBS = [
    "QB_*.data",
    "DEF_*.data",
    "K_*.data",
    "RB_*.data",
    "TE_*.data",
    "WR_*.data",
]


engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)
connection = engine.connect()


for pattern in GLOBS:
    for path in glob.glob(pattern):
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
            ppr, ppr_low, ppr_high)
            VALUES (:name, :team, :position, :year, :week,
            :standard, :standard_low, :standard_high,
            :ppr, :ppr_low, :ppr_high)
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
            ))
