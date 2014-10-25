var Fantasy = (function (me, $) {
  me.helloWorld = function () {
    alert("Hello World!");
  };

  me.loadStats = function() {
    var week = 8;
    var promise = $.getJSON("https://localhost:5000/stats/" + week).
        done(function(data) {
          console.log("Successfully got player data:");
          /*console.log(data.players[0]);
          var peyton = data.players[0];
          me.tweakPlayerInDom(peyton);*/
          for (var i = 0; i < data.players.length; i++) {
            me.tweakPlayerInDom(data.players[i]);
          }
          console.log("Updated all players...");
          me.updateHeader();
        }).
        fail(function(err) {
          console.log("Failed to get player data!");
        }).
        always(function() {
          console.log("DONE");
        });
    return promise;
  };

  me.tweakPlayerInDom = function(player) {
    var player_div = $(".player-name > div:contains('" + player.name + "')");
    // Not all players from the json data may exist in this specific context
    if (player_div.length > 0) {
      var player_row = player_div.parent().parent();
      var columns = player_row.children();
      var points_column = columns[2];
      points_column.textContent = player.points;
      var ratio_column = columns[3];
      ratio_column.textContent = player.proj;
    }
  };

  me.updateHeader = function() {
    var fppg_header = $("th.player-fppg")[0];
    fppg_header.textContent = "Proj";
    var played_header = $("th.player-played")[0];
    played_header.textContent = "Points/$1k";
  };

  return me;
}(Fantasy || {}, jQuery));

Fantasy.loadStats();
