var Fantasy = (function (me, $) {
  me.helloWorld = function () {
    alert("Hello World!");
  };

  me.loadStats = function() {
    var week = "6";
    var promise = $.getJSON("https://localhost:5000/stats/" + week).
        done(function(data) {
          console.log("Successfully got player data:");
          console.log(data.players[0]);
        }).
        fail(function(err) {
          console.log("Failed to get player data!");
        });
    return promise;
  }

  return me;
}(Fantasy || {}, jQuery));

Fantasy.helloWorld();
Fantasy.loadStats();
