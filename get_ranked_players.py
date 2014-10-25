import collections
import copy
from decimal import Decimal
import itertools
import math
import random
import sys

from jinja2 import Template
from sqlalchemy import create_engine
from sqlalchemy import text


WEEK = int(sys.argv[1])
GAME_ID = int(sys.argv[2])
SALARY_CAP = 60000
POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']
ROSTER_SIZE = 9


engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)
connection = engine.connect()


query = text("""
select name, team, position, practice_status, injury, game_status, salary :: numeric, ppr, (ppr_high / (salary / MONEY(1000))) as PROJ,
  ppr_high as HIGH
from players where week = :week and salary > MONEY(0)
AND position = :position
AND ppr > 0
order by PROJ DESC
""")


qbs = connection.execute(query, week=WEEK, position='QB')
rbs = connection.execute(query, week=WEEK, position='RB')
wrs = connection.execute(query, week=WEEK, position='WR')
tes = connection.execute(query, week=WEEK, position='TE')
ks = connection.execute(query, week=WEEK, position='K')
defs = connection.execute(query, week=WEEK, position='DEF')


TOP_N = 50

qbs = list(qbs)
best_qbs = sorted(qbs, key=lambda p: p['proj'], reverse=True)# [:TOP_N]

rbs = list(rbs)
best_rbs = sorted(rbs, key=lambda p: p['proj'], reverse=True)# [:TOP_N]

wrs = list(wrs)
best_wrs = sorted(wrs, key=lambda p: p['proj'], reverse=True)# [:TOP_N]

tes = list(tes)
best_tes = sorted(tes, key=lambda p: p['proj'], reverse=True)# [:TOP_N]

ks = list(ks)
best_ks = sorted(ks, key=lambda p: p['proj'], reverse=True)# [:TOP_N]

defs = list(defs)
best_defs = sorted(defs, key=lambda p: p['proj'], reverse=True)# [:TOP_N]


positions = [
    ('QB', best_qbs),
    ('RB', best_rbs),
    ('WR', best_wrs),
    ('TE', best_tes),
    ('K', best_ks),
    ('DEF', best_defs)
]



total_players = sum([len(x) for x in (qbs, rbs, wrs, tes, ks, defs)])
print 'GENERATING ROSTERS... (with %s total players)'%(total_players,)


with open("templates/ranked.html", "r") as template_file:
    template = Template(template_file.read())

with open("ranked_{}.html".format(GAME_ID), "w") as ranked_file:
    html = template.render(
        week=WEEK,
        possible_players=total_players,
        game_id=GAME_ID,
        positions=positions,
        top_n=TOP_N
    )
    ranked_file.write(html)
