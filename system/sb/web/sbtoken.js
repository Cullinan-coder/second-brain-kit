/* Oturum jetonu (denetim D-04): sunucu sayfayı yüklerken <meta name="sb-token"> içine gömer; aynı kökene giden bütün fetch
   isteklerine X-SB-Token başlığı eklenir. Başka siteler jetonu okuyamaz (aynı köken ilkesi), <img src> gibi istekler ekleyemez. */
(function () {
  var m = document.querySelector('meta[name="sb-token"]');
  var t = m ? m.getAttribute('content') : '';
  if (!t || t.indexOf('__') === 0) return;
  var orig = window.fetch;
  window.fetch = function (input, init) {
    try {
      var url = new URL(typeof input === 'string' ? input : (input && input.url) || String(input), location.href);
      if (url.origin === location.origin) {
        init = init || {};
        var h = new Headers(init.headers || (typeof input !== 'string' && input && input.headers) || {});
        h.set('X-SB-Token', t);
        init.headers = h;
      }
    } catch (e) { /* jeton eklenemezse istek olduğu gibi gider */ }
    return orig.call(this, input, init);
  };
})();
