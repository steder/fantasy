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
INITIAL_POPULATION_SIZE = 10000
MUTATION_CHANCE = 0.001 # 0.1%
ROSTER_SIZE = 9
PERCENT_CROSSOVER = 1.0 # 100.0%
#PERCENT_CROSSOVER = 0.85 # 85.0%
MAX_GENERATIONS = 100
DESIRED_PERCENT_FITNESS = 90.0


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


print "Best possible roster (regardless of salary cap):"
best_roster = [best_qb] + best_rbs + best_wrs + [best_te] + [best_k] + [best_def]
best_cost = 0
best_points = 0
for player in best_roster:
    best_cost += player['salary']
    best_points += player['ppr']
    print player
print "best cost:", best_cost
print "best points:", best_points


# let's expect 90% of our population to be at least 75% as good as the best team
fitness = Decimal(0.75) * best_points
ninety_percent_fitness = 0.0

total_players = sum([len(x) for x in (qbs, rbs, wrs, tes, ks, defs)])
print 'GENERATING ROSTERS... (with %s total players)'%(total_players,)


def generate_initial_population():
    # rosters contains tuples of (cost, points, players)
    rosters = [] # collections.deque(maxlen=10)
    max_cap_rosters = []
    generated = 0
    while len(rosters) < INITIAL_POPULATION_SIZE:
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
        if cost <= Decimal(SALARY_CAP):
            rosters.append((cost, points, roster))
        #
        # We only look at rosters that are exactly the 60k salary cap?
        if cost == Decimal(SALARY_CAP):
            max_cap_rosters.append((cost, points, roster))
    return rosters, max_cap_rosters, generated


rosters, max_cap_rosters, generated = generate_initial_population()

print "Generated %s rosters total, kept %s"%(generated, len(rosters))


def even_and_odd(rosters):
    return itertools.izip(itertools.islice(rosters, 0, None, 2),
                   itertools.islice(rosters, 1, None, 2))


def even_and_odd_reverse(rosters):
    return itertools.izip(itertools.islice(rosters, 0, None, 2),
                          reversed(list(itertools.islice(rosters, 1, None, 2))))



POSITION_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8]
def crossover_single_players(rosters):
    # sort by points and then cost:
    rosters = sorted(rosters, key=lambda r: (r[1], r[0]), reverse=True)
    new_generation = []
    for parent1, parent2 in even_and_odd(rosters):
        # parent roster tuple is (cost, projected_points, players)
        # so parent[2] is the players list
        child1 = copy.copy(parent1[2])
        child2 = copy.copy(parent2[2])

        names1 = [p.name for p in child1]
        names2 = [p.name for p in child2]
        names1.sort()
        names2.sort()

        if names1 == names2:
            print "both parents are the same, dropping one"
            new_generation.append(child1)
            continue

        # Rather than always crossing over we'll only crossover
        # some of the time so some parents will simply continue
        # on to the next generation, unchanged.
        if random.random() <= PERCENT_CROSSOVER:
            # pick a position and swap all the players at that position from one
            # roster to another:
            swapped = 0
            attempts = 0
            while swapped < 2:
                attempts += 1
                position = random.choice(POSITION_INDICES)
                names1 = [p.name for p in child1]
                names2 = [p.name for p in child2]
                if ((child1[position].name != parent2[2][position].name)
                    and
                    (child2[position].name != parent1[2][position].name)
                    and parent2[2][position].name not in names1
                    and parent1[2][position].name not in names2
                ):
                    child1[position] = parent2[2][position]
                    child2[position] = parent1[2][position]
                    swapped += 1

                if attempts > 100:
                    print "I can't find a crossover for these 2 rosters:"
                    #print "parent1:", parent1
                    #print "parent2:", parent2
                    print "parent1:", names1
                    print "parent2:", names2
                    print "Keeping 1"
                    new_generation.append(child1)
                    break

            if swapped == 2:
                new_generation.append(child1)
                new_generation.append(child2)
        else:
            new_generation.append(child1)
            new_generation.append(child2)

    return new_generation


def crossover(rosters):
    """
    Swap position / position groups randomly between rosters to build a new generation of rosters

    Think of each position on the roster as a chromosome.  For each pair of rosters will
    select 2 positions and we'll swap all the players in those positions between the parents.

    Note:
      input rosters here are tuples of (cost, points, players)
      output rosters are just players

    """

    # sort by points and then cost:
    rosters = sorted(rosters, key=lambda r: (r[1], r[0]), reverse=True)
    new_generation = []
    for parent1, parent2 in even_and_odd(rosters):
        # parent roster tuple is (cost, projected_points, players)
        # so parent[2] is the players list
        child1 = copy.copy(parent1[2])
        child2 = copy.copy(parent2[2])

        # Rather than always crossing over we'll only crossover
        # some of the time so some parents will simply continue
        # on to the next generation, unchanged.
        if random.random() <= PERCENT_CROSSOVER:
            # pick a position and swap all the players at that position from one
            # roster to another:
            positions = random.sample(POSITIONS, 2)
            for position in positions:
                if position == 'QB':
                    # swap the quarterbacks between the rosters
                    # (child1 gets parent2's QB and vice versus)
                    child1[0] = parent2[2][0]
                    child2[0] = parent1[2][0]
                if position == 'RB':
                    # running backs are position 1 and 2
                    child1[1] = parent2[2][1]
                    child1[2] = parent2[2][2]
                    child2[1] = parent1[2][1]
                    child2[2] = parent1[2][2]
                if position == 'WR':
                    # wide receivers backs are positions 3-5
                    child1[3] = parent2[2][3]
                    child1[4] = parent2[2][4]
                    child1[5] = parent2[2][5]
                    child2[3] = parent1[2][3]
                    child2[4] = parent1[2][4]
                    child2[5] = parent1[2][5]
                if position == "TE":
                    child1[6] = parent2[2][6]
                    child2[6] = parent1[2][6]
                if position == "K":
                    child1[7] = parent2[2][7]
                    child2[7] = parent1[2][7]
                if position == "DEF":
                    child1[8] = parent2[2][8]
                    child2[8] = parent1[2][8]

        new_generation.append(child1)
        new_generation.append(child2)

    return new_generation


def index_to_position_players(idx):
    if idx in (0,):
        return qbs
    elif idx in (1, 2):
        return rbs
    elif idx in (3, 4, 5):
        return wrs
    elif idx in (6,):
        return tes
    elif idx in (7,):
        return ks
    elif idx in (8,):
        return defs
    else:
        raise Exception("Invalid index, I don't have a position for this index")


def new_player_for_index(idx, current_player):
    players = index_to_position_players(idx)
    new_player = current_player
    while new_player['name'] == current_player['name']:
        new_player = random.choice(players)
    return new_player


def mutate(rosters):
    """
    Mutation would normally happen in a genetic algorithm at each possible position
    so we'll test each roster spot with our MUTATION_CHANCE and if it is time to
    mutate we'll pick a new random player for that position.

    """

    for players in rosters:
        for index in xrange(ROSTER_SIZE):
            if random.random() < MUTATION_CHANCE:
                players[index] = new_player_for_index(index, players[index])

    return rosters


def add_cost_and_points(rosters):
    decorated_rosters = []
    for roster in rosters:
        cost = 0
        points = 0
        for player in roster:
            cost += player['salary']
            points += player['ppr']
        decorated_rosters.append((cost, points, roster))
    return decorated_rosters


def cull(rosters):
    return [(cost, points, roster) for cost, points, roster in rosters if cost <= SALARY_CAP]


def compute_fitness(rosters):
    rosters = list(rosters)
    n_rosters = len(rosters)
    percent_fitness = (sum([1 for cost, points, players in rosters if points >= fitness]) / (n_rosters * 1.0)) * 100.0
    return percent_fitness


generation = 0
print "Calculating initial percent fitness for random population:"
percent_fitness = compute_fitness(rosters)
print "Initial percent_fitness:", percent_fitness


while generation < MAX_GENERATIONS and percent_fitness <= DESIRED_PERCENT_FITNESS:
    print "Not yet fit enough, performing crossover and mutation to generate new generation", generation, percent_fitness
    rosters = cull(add_cost_and_points(mutate(crossover_single_players(rosters))))
    print "remaining rosters:", len(list(rosters))
    percent_fitness = compute_fitness(rosters)
    generation += 1


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


with open("templates/index.html", "r") as template_file:
    template = Template(template_file.read())

with open("roster_{}.html".format(GAME_ID), "w") as roster_file:
    html = template.render(
        rosters=rosters[:10],
        max_rosters=max_cap_rosters[:10],
        best_roster=best_roster,
        best_cost=best_cost,
        best_points=best_points,
        fitness=fitness,
        week=WEEK,
        generated=generated,
        possible_players=total_players,
        game_id=GAME_ID
    )
    roster_file.write(html)
