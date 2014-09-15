#!/usr/bin/env python

import collections
import functools
import itertools
import json
import os
import re
import sys

import requests


FANDUEL_BASE_URL = "https://wwww.fanduel.com/e/Game/{}"


def memoize_to_disk(func):
    @functools.wraps(func)
    def wrapper(*args):
        data_path = "_".join(args) + ".data"

        if os.path.exists(data_path):
            with open(data_path, "r") as f:
                data = json.load(f)
        else:
            data = func(*args)
            with open(data_path, "w") as f:
                json.dump(data, f)

        return data

    return wrapper


def get_fanduel_game(game_id):
    print "Getting markup"
    response = requests.get(FANDUEL_BASE_URL.format(game_id))
    html = response.text
    return html


@memoize_to_disk
def get_fanduel_players_for_game(game_id):
    html = get_fanduel_game(game_id)
    regex = re.compile(r'allPlayersFullData.*=([^;]+);', re.MULTILINE)
    matches = regex.findall(html)
    print matches
    print "parsing json"
    players = json.loads(matches[0])
    print "returning players"
    return players


if __name__=="__main__":
    game_id = sys.argv[1]
    players = get_fanduel_players_for_game(game_id)


    def sort_by_position(data):
        player_id, player = data
        return player[0]

    players_by_position = collections.defaultdict(dict)

    for position, players in itertools.groupby(sorted(players.iteritems(), key=sort_by_position), sort_by_position):
        #print "position:", position
        for player_id, player in players:
            #print player_id, player[0], player[1], player[5], player[6], player[7]
            # keyed by position, then name:
            players_by_position[position][player[1]] = dict(
                player_id=player_id,
                position=player[0],
                name=player[1],
                salary=int(player[5]),
                fantasy_points_per_game=float(player[6]),
                played=int(player[7])
            )

    # let's calculate best values at each position just based on fanduel data:
    for position in ('QB', 'RB', 'WR', 'TE', 'D', 'K'):
        values = []
        for name, player in players_by_position[position].iteritems():
            points_per_thousand = player['fantasy_points_per_game'] / (player['salary'] / 1000.0)
            stats = (player['name'],
                     player['fantasy_points_per_game'],
                     player['salary'],
                     points_per_thousand)
            values.append(stats)


        values.sort(key=lambda x: x[3], reverse=True)
        print "top 10 %ss:"%(position,)
        for p in  values[:10]:
            print p
