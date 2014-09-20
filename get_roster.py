import collections
from decimal import Decimal
import itertools
import math
import random
import sys

from jinja2 import Template
from sqlalchemy import create_engine
from sqlalchemy import text

with open("templates/index.html", "r") as template_file:
    template = Template(template_file.read())


WEEK = int(sys.argv[1])


engine = create_engine('postgresql://127.0.0.1/fantasy', echo=True)
connection = engine.connect()


query = text("""
select name, team, position, practice_status, injury, game_status, salary :: numeric, ppr, (ppr / (salary / MONEY(1000))) as PROJ,
  (ppr_low / (salary / MONEY(1000))) as LOW,
  (ppr_high / (salary / MONEY(1000))) as HIGH,
  (ppr_high / (salary / MONEY(1000))) -  (ppr_low / (salary / MONEY(1000))) AS DELTA
from players where week = :week and salary > MONEY(0)
AND position = :position
AND ppr > 0
order by (ppr / (salary / MONEY(1000))) DESC
""")


qbs = connection.execute(query, week=WEEK, position='QB')
rbs = connection.execute(query, week=WEEK, position='RB')
wrs = connection.execute(query, week=WEEK, position='WR')
tes = connection.execute(query, week=WEEK, position='TE')
ks = connection.execute(query, week=WEEK, position='K')
defs = connection.execute(query, week=WEEK, position='DEF')


# By using the floor function we're dropping players
# from the sets of possible qbs, rbs, etc if they don't
# meet at least 1.0 cost effectiveness (points / salary)
qbs = list(qbs)
best_qb = sorted(qbs, key=lambda p: p['ppr'], reverse=True)[0]
print "BEST QB", best_qb
adjusted_qbs = []
for qb in qbs:
    adjusted_qbs.extend([qb] * int(math.floor(qb['proj'])))
qbs = adjusted_qbs

for qb in qbs:
    print qb['name'], qb['salary'], qb['ppr'], qb['proj']

rbs = list(rbs)
best_rbs = sorted(rbs, key=lambda p: p['ppr'], reverse=True)[:2]
adjusted_rbs = []
for rb in rbs:
    adjusted_rbs.extend([rb] * int(math.floor(rb['proj'])))
rbs = adjusted_rbs

wrs = list(wrs)
best_wrs = sorted(wrs, key=lambda p: p['ppr'], reverse=True)[:3]
adjusted_wrs = []
for wr in wrs:
    adjusted_wrs.extend([wr] * int(math.floor(wr['proj'])))
wrs = adjusted_wrs

tes = list(tes)
best_te = sorted(tes, key=lambda p: p['ppr'], reverse=True)[0]
adjusted_tes = []
for te in tes:
    adjusted_tes.extend([te] * int(math.floor(te['proj'])))
tes = adjusted_tes

ks = list(ks)
best_k = sorted(ks, key=lambda p: p['ppr'], reverse=True)[0]
adjusted_ks = []
for k in ks:
    adjusted_ks.extend([k] * int(math.floor(k['proj'])))
ks = adjusted_ks

defs = list(defs)
best_def = sorted(defs, key=lambda p: p['ppr'], reverse=True)[0]
adjusted_defs = []
for def_ in defs:
    adjusted_defs.extend([def_] * int(math.floor(def_['proj'])))
defs = adjusted_defs


total_players = sum([len(x) for x in (qbs, rbs, wrs, tes, ks, defs)])
print 'GENERATING ROSTERS... (with %s total players)'%(total_players,)


# rosters contains tuples of (cost, points, players)
rosters = [] # collections.deque(maxlen=10)
max_cap_rosters = []
generated = 0
while len(rosters) < 10000:
    roster = []
    roster.append(random.choice(qbs))
    roster.extend(random.sample(rbs, 2))
    roster.extend(random.sample(wrs, 3))
    roster.append(random.choice(tes))
    roster.append(random.choice(ks))
    roster.append(random.choice(defs))

    cost = sum( player['salary'] for player in roster )
    #print "Total Cost:", cost
    points = sum( player['ppr'] for player in roster )
    #print "Total Projected Points(PPR):", points

    generated += 1

    # What if instead of less than 60k...
    #
    if cost <= Decimal(60000):
        rosters.append((cost, points, roster))
    #
    # We only look at rosters that are exactly the 60k salary cap?
    if cost == Decimal(60000):
        max_cap_rosters.append((cost, points, roster))

print "Generated %s rosters total, kept %s"%(generated, len(rosters))

# sort by cost then points
rosters.sort(key=lambda r: (r[1], r[0]), reverse=True)
print "ROSTERS:"
for i, roster in enumerate(rosters[:10]):
    print "ROSTER: %s"%(i,)
    cost, points, players = roster
    for player in players:
        print player
    print cost, points

max_cap_rosters.sort(key=lambda r: (r[1], r[0]), reverse=True)
print "MAX ROSTERS:"
for i, roster in enumerate(max_cap_rosters[:10]):
    print "MAX ROSTER: %s"%(i,)
    cost, points, players = roster
    for player in players:
        print player
    print cost, points


print "Best possible roster (regardless of cap):"
best_roster = [best_qb] + best_rbs + best_wrs + [best_te] + [best_k] + [best_def]
cost = 0
points = 0
for player in best_roster:
    cost += player['salary']
    points += player['ppr']
    print player
print "best cost:", cost
print "best points:", points


with open("roster.html", "w") as roster_file:
    html = template.render(
        rosters=rosters[:10],
        max_rosters=max_cap_rosters[:10],
        best_roster=best_roster,
        best_cost=cost,
        best_points=points,
        week=WEEK,
        generated=generated,
        possible_players=total_players
    )
    roster_file.write(html)
