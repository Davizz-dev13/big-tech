/* Big Tech — lo mínimo en el navegador: ordenar las tarjetas. */
(function () {
  "use strict";
  var orden = document.getElementById("orden");
  if (!orden) return;
  var num = function (el, k) { var v = el.getAttribute("data-" + k); return v === "" || v === null ? NaN : parseFloat(v); };
  function aplicar() {
    var k = orden.value;
    document.querySelectorAll(".bt-cards[data-grupo]").forEach(function (cont) {
      var cards = Array.prototype.slice.call(cont.children);
      cards.sort(function (a, b) {
        if (k === "az") return a.dataset.nombre.localeCompare(b.dataset.nombre, "es");
        var x = num(a, k), y = num(b, k);
        if (k === "p_fcf") { if (!(x > 0)) x = NaN; if (!(y > 0)) y = NaN; }
        if (isNaN(x) && isNaN(y)) return 0;
        if (isNaN(x)) return 1;
        if (isNaN(y)) return -1;
        return k === "p_fcf" ? x - y : y - x;
      });
      cards.forEach(function (el) { cont.appendChild(el); });
    });
  }
  orden.addEventListener("change", aplicar);
  aplicar();
})();
