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
MUTATION_CHANCE = 0.01 # 1.0%
ROSTER_SIZE = 9
#PERCENT_CROSSOVER = 1.0 # 100.0%
PERCENT_CROSSOVER = 0.85 # 85.0%
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


total_players = sum([len(x) for x in (qbs, rbs, wrs, tes, ks, defs)])
print 'GENERATING ROSTERS... (with %s total players)'%(total_players,)


def generate_population(population_size, required_points=None):
    # rosters contains tuples of (cost, points, players)
    rosters = [] # collections.deque(maxlen=10)
    max_cap_rosters = []
    generated = 0
    while len(rosters) < population_size:
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

        if required_points and points < required_points:
            continue

        # What if instead of less than 60k...
        #
        if cost <= Decimal(SALARY_CAP):
            rosters.append((cost, points, roster))
        #
        # We only look at rosters that are exactly the 60k salary cap?
        if cost == Decimal(SALARY_CAP):
            max_cap_rosters.append((cost, points, roster))
    return rosters, max_cap_rosters, generated


rosters, max_cap_rosters, generated = generate_population(INITIAL_POPULATION_SIZE, required_points=Decimal(100.0))


AVERAGE_POINTS = sum(roster[1] for roster in rosters) / len(rosters)
print "AVERAGE_POINTS {}".format(AVERAGE_POINTS)


print "Generated %s rosters total, kept %s"%(generated, len(rosters))


# let's expect 90% of our population to be at least 75% as good as the best team
FITNESS = Decimal(0.75) * best_points
print "COMPLETELY ARBITRARY FITNESS POINTS: %s"%(FITNESS,)
ninety_percent_fitness = 0.0


def even_and_odd(rosters):
    return itertools.izip(itertools.islice(rosters, 0, None, 2),
                   itertools.islice(rosters, 1, None, 2))


def even_and_odd_reverse(rosters):
    return itertools.izip(itertools.islice(rosters, 0, None, 2),
                          reversed(list(itertools.islice(rosters, 1, None, 2))))

def sort_by_fitness(roster):
    """
    Here we're sorting based on how close to the fitness value
    these rosters are.
    """
    points = roster[1]
    order_key = points - FITNESS
    return order_key


POSITION_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8]
def crossover_single_players(rosters):
    n_crossovers = 0
    n_skips = 0
    n_drops = 0

    # sort by points and then cost:
    #rosters = sorted(rosters, key=lambda r: (r[1], r[0]), reverse=True)
    rosters = sorted(rosters, key=sort_by_fitness)
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
            #print "both parents are the same, dropping one"
            n_drops += 1
            new_generation.append(child1)
            continue

        # Rather than always crossing over we'll only crossover
        # some of the time so some parents will simply continue
        # on to the next generation, unchanged.
        if random.random() <= PERCENT_CROSSOVER:
            n_crossovers += 1
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
                    n_skips += 1
                    # print "I can't find a crossover for these 2 rosters:"
                    # #print "parent1:", parent1
                    # #print "parent2:", parent2
                    # print "parent1:", names1
                    # print "parent2:", names2
                    # print "Keeping 1"
                    new_generation.append(child1)
                    break

            if swapped == 2:
                new_generation.append(child1)
                new_generation.append(child2)
        else:
            new_generation.append(child1)
            new_generation.append(child2)

    print "%s crossovers, %s skips (crossover failures), and %s drops (inbreeding?) in this generation"%(n_crossovers, n_skips, n_drops)

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
    n_crossovers = 0


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
            n_crossovers += 1
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

    print "%s crossovers (position groups) in this generation"%(n_crossovers,)
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


def new_better_player_for_index(idx, current_player):
    attempts = 0
    players = list(itertools.ifilter(lambda x: x['ppr'] >= current_player['ppr'],  index_to_position_players(idx)))
    new_player = current_player

    while new_player['name'] == current_player['name']:
        new_player = random.choice(players)
        attempts += 1

        if attempts >= 10:
            break

    return new_player


def mutate(rosters):
    """
    Mutation would normally happen in a genetic algorithm at each possible position
    so we'll test each roster spot with our MUTATION_CHANCE and if it is time to
    mutate we'll pick a new random player for that position.

    """
    n_mutations = 0

    for players in rosters:
        for index in xrange(ROSTER_SIZE):
            if random.random() < MUTATION_CHANCE:
                n_mutations += 1
                players[index] = new_better_player_for_index(index, players[index])

    print "%s mutations performed in this generation"%(n_mutations,)

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
    return [ (cost, points, roster) for cost, points, roster in rosters if cost <= SALARY_CAP ] #and points >= AVERAGE_POINTS]


def compute_fitness(rosters):
    rosters = list(rosters)
    n_rosters = len(rosters)
    percent_fitness = (sum([1 for cost, points, players in rosters if points >= FITNESS]) / (n_rosters * 1.0)) * 100.0
    return percent_fitness


generation = 0
print "Calculating initial percent fitness for random population:"
percent_fitness = compute_fitness(rosters)
print "Initial percent_fitness:", percent_fitness

last_percent_fitness = percent_fitness


#top_25 = []

best_rosters = []


while generation < MAX_GENERATIONS and percent_fitness <= DESIRED_PERCENT_FITNESS:
    #if len(rosters) < 1000:
    ##print "Fewer than 1000 rosters left in the population, adding more..."
    #n_new_rosters = 1000 - len(rosters)
    more_rosters, _, generated = generate_population(100, required_points=AVERAGE_POINTS)
    #print "Adding {} new rosters (out of {} generated rosters) to add new blood".format(n_new_rosters, generated)
    rosters.extend(more_rosters)

    print "Not yet fit enough, performing crossover and mutation to generate new generation", generation, percent_fitness
    rosters = cull(add_cost_and_points(mutate(crossover_single_players(rosters))))

    percent_fitness = compute_fitness(rosters)
    generation += 1



    top_rosters = sorted(rosters, key=lambda r: r[1], reverse=True)[:40]
    n = len(top_rosters)

    avg_points = sum([r[1] for r in top_rosters]) / n
    avg_cost = sum([r[0] for r in top_rosters]) / n

    print "remaining rosters: {}, avg top 40 points {}, avg top 40 cost {}".format(
        len(list(rosters)), avg_points, avg_cost
    )

    if percent_fitness > last_percent_fitness:
        best_rosters = top_rosters

    last_percent_fitness = percent_fitness

if percent_fitness > DESIRED_PERCENT_FITNESS:
    print "Percent Fitness %s exceeded threshold %s"%(percent_fitness, DESIRED_PERCENT_FITNESS)

if generation >= MAX_GENERATIONS:
    print "Exceeded MAX_GENERATIONS!"

with open("templates/index.html", "r") as template_file:
    template = Template(template_file.read())

with open("roster_{}.html".format(GAME_ID), "w") as roster_file:
    html = template.render(
        rosters=best_rosters,
        max_rosters=[],
        best_roster=best_roster,
        best_cost=best_cost,
        best_points=best_points,
        fitness=FITNESS,
        week=WEEK,
        generated=generated,
        possible_players=total_players,
        game_id=GAME_ID
    )
    roster_file.write(html)
