#!/usr/bin/env bash

set -e -u -x

USAGE=<<EOF

    doit.sh <FANDUEL GAME ID> <WEEK>

EOF

game_id=$1
week=$2

echo "Getting players/salaries..."
python get_player_data.py $game_id
echo "Getting projection data from FFN..."
python get_projections.py $week
echo "Loading projectin data from FFN..."
python load_projections.py $week
echo "Loading salaries..."
python load_salaries.py $week $game_id.data
echo "Generating roster(s)..."
python get_roster.py $week
#open roster.html
