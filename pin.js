/* Bouton « Enregistrer sur Pinterest » sous chaque tableau (.kit).
   Simple lien vers Pinterest : aucun script Pinterest chargé, aucun pisteur. */
(function () {
  var fr = (document.documentElement.lang || 'fr').slice(0, 2) !== 'en';
  var st = document.createElement('style');
  st.textContent = '.pin{display:flex;align-items:center;justify-content:center;gap:.4rem;margin-top:.2rem;border:2px solid #E60023;color:#E60023;background:transparent;text-decoration:none;font-weight:600;border-radius:14px;padding:.55rem 1rem;font-size:.95rem}.pin:hover{background:#E60023;color:#fff}';
  document.head.appendChild(st);
  var marque = fr ? 'Mon Tableau de Motivation' : 'My Motivation Board';
  var suite = fr ? ' · gratuit à imprimer · ' : ' · free printable · ';
  var kits = document.querySelectorAll('.kit');
  for (var i = 0; i < kits.length; i++) {
    var k = kits[i], img = k.querySelector('img'), body = k.querySelector('.body'), h = k.querySelector('h3');
    if (!img || !body) continue;
    var sec = k.closest('section[id]');
    var page = location.origin + location.pathname + (sec && sec.id !== 'tableaux' && sec.id !== 'epingler' ? '#' + sec.id : '');
    var media = new URL(img.getAttribute('src'), location.href).href;
    var titre = h ? h.textContent.trim() : '';
    var a = document.createElement('a');
    a.className = 'pin';
    a.target = '_blank';
    a.rel = 'noopener';
    a.href = 'https://www.pinterest.com/pin/create/button/?url=' + encodeURIComponent(page) +
      '&media=' + encodeURIComponent(media) +
      '&description=' + encodeURIComponent((img.getAttribute('alt') || titre) + suite + marque);
    var court = sec && sec.id === 'epingler';
    a.textContent = court ? (fr ? '📌 Épingler' : '📌 Save') : (fr ? '📌 Enregistrer sur Pinterest' : '📌 Save to Pinterest');
    var pdf = body.querySelector('[data-goatcounter-click]');
    a.setAttribute('data-goatcounter-click', 'pinterest-' + (pdf ? pdf.getAttribute('data-goatcounter-click').replace(/^pdf-/, '') : i));
    body.appendChild(a);
  }
})();
