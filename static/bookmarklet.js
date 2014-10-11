var Fantasy = (function (me, $) {
  me.helloWorld = function () {
    alert("Hello World!");
  };
  return me;
}(Fantasy || {}, jQuery));

Fantasy.helloWorld();
