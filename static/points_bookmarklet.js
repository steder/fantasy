function get_points() {
  var players = $(".roster li");
  var points = 0;
  var player_names = [];
  for (var i = 0; i < players.length; i++) {
    var player_li = players[i];
    var player_id = parseInt(player_li.getAttribute('data-player-id'));
    var player = FD.playerpicker.allPlayersFullData[player_id];

    var player_name = player[1];
    var player_points = player[6];
    player_names.push(player_name);
    points += player_points;
  }

  var req = $.getJSON("https://localhost:5000/points", {week: 8,
                                                    names: player_names});
  req.done(function(data) {
    console.log("Successfully got player points...");
    var total_points = 0;
    for (var i = 0; i < data.players.length; i++) {
      var player = data.players[i];
      console.log(player.name + ": " + player.points);
      total_points += player.points;
    }
    console.log("Total Points for Roster: " + total_points);
    alert("Total Points for Roster: " + total_points);
  });
  req.fail(function(err) {
    console.log("failed to get points");
  });
  req.always(function() {
    console.log("DONE");
  });

  return [points, player_names];
}

get_points();
