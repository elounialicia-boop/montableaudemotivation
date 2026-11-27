// Encadré « Reçois ton tableau gratuit par email » (Brevo). Sans traceur, sans cookie.
(function () {
  var ACTION = "https://b89baba5.sibforms.com/serve/MUIFAM_DbL5DOcakFXjXg_IACy2KEAyxylCeGfHTM0Qx-kihlve0WlNYCvpUHvbi7zCaLIH13-ITfF9l3tiBOymPZC3SyIrj_8gr8qCeaY_ZdTqZs2BC8mwjaCYz02pDrywSIN9KZzg8I10lPJrOPzwTClc6-qVJZQ8p7nQ5r6UrXtS8OVQxS2nA_yAiZ6cqZ6seBFYPgIcerDWovw==";
  var CHOIX = [["matin", "☀️ Routine du matin (3-7\u00a0ans)"], ["soir", "🌙 Routine du soir (3-7\u00a0ans)"],
               ["recompense", "⭐ Tableau de récompense (3-7\u00a0ans)"], ["7-10", "🏆 Tableau trophée (7-10\u00a0ans)"]];
  var css = "#lettre-moty .lm{max-width:560px;margin:0 auto;background:#fff8e8;border:2px solid #f6d98c;border-radius:22px;padding:22px 20px;text-align:left}" +
    "#lettre-moty .lm-top{display:flex;gap:14px;align-items:center}#lettre-moty .lm-top img{width:88px;height:auto;flex:none}" +
    "#lettre-moty h2{margin:0;font-size:1.45rem;line-height:1.2}#lettre-moty .lm-sub{margin:.4rem 0 1rem;color:#6b5f86}" +
    "#lettre-moty label.opt{display:flex;align-items:center;gap:10px;border:2px solid #e6e0ef;border-radius:14px;padding:10px 12px;margin:7px 0;background:#fff;cursor:pointer;font-weight:500}" +
    "#lettre-moty label.opt:has(input:checked){border-color:#e95496;background:#fff0f7}#lettre-moty input[type=radio]{accent-color:#e95496;width:18px;height:18px}" +
    "#lettre-moty input[type=email]{width:100%;box-sizing:border-box;font:inherit;padding:12px 14px;border:2px solid #e6e0ef;border-radius:14px;margin:10px 0 6px}" +
    "#lettre-moty .lm-ok{display:flex;gap:8px;align-items:flex-start;font-size:.88rem;color:#6b5f86;margin:6px 0 12px}#lettre-moty .lm-ok input{margin-top:3px;accent-color:#e95496}" +
    "#lettre-moty button{width:100%;font:inherit;font-weight:700;font-size:1.05rem;background:#e95496;color:#fff;border:0;border-radius:999px;padding:13px;cursor:pointer}" +
    "#lettre-moty button:disabled{opacity:.6}#lettre-moty .lm-msg{margin:.8rem 0 0;font-weight:600;text-align:center}#lettre-moty .lm-hp{position:absolute;left:-9999px}" +
    "#lettre-moty .lm-note{font-size:.85rem;color:#8a7fa3;text-align:center;margin:.7rem 0 0}";
  document.querySelectorAll("#lettre-moty").forEach(function (box) {
    var def = box.getAttribute("data-defaut") || "matin";
    var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
    var base = box.getAttribute("data-base") || "../";
    box.innerHTML = '<form class="lm" novalidate><div class="lm-top"><img src="' + base + 'images/moty-salut.png" alt="Moty">' +
      '<h2>Reçois ton tableau gratuit par email 💌</h2></div>' +
      '<p class="lm-sub">Choisis ton tableau, il arrive dans ta boîte mail en 1 minute. Ensuite, Moty t\'écrit 1 à 2 fois par mois : nouveaux tableaux, astuces et cartes offertes.</p>' +
      CHOIX.map(function (c) { return '<label class="opt"><input type="radio" name="TABLEAU" value="' + c[0] + '"' + (c[0] === def ? " checked" : "") + '> ' + c[1] + '</label>'; }).join("") +
      '<input type="email" name="EMAIL" placeholder="Ton adresse email" autocomplete="email" required>' +
      '<input class="lm-hp" type="text" name="email_address_check" value="" tabindex="-1" autocomplete="off" aria-hidden="true">' +
      '<label class="lm-ok"><input type="checkbox" required> J\'accepte de recevoir le tableau choisi et la lettre de Moty (1 à 2 emails par mois). Désinscription en 1 clic.</label>' +
      '<button type="submit">Recevoir mon tableau</button><p class="lm-msg" role="status"></p>' +
      '<p class="lm-note">Tu préfères sans email ? Les boutons « Télécharger » restent juste au-dessus.</p></form>';
    var f = box.querySelector("form"), msg = f.querySelector(".lm-msg"), btn = f.querySelector("button");
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var mail = f.EMAIL.value.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(mail)) { msg.textContent = "Vérifie ton adresse email 🙂"; return; }
      if (!f.querySelector(".lm-ok input").checked) { msg.textContent = "Coche la case pour recevoir ton tableau."; return; }
      var d = new FormData(); d.append("EMAIL", mail); d.append("TABLEAU", f.TABLEAU.value);
      d.append("email_address_check", f.email_address_check.value); d.append("locale", "fr"); d.append("html_type", "simple");
      btn.disabled = true; msg.textContent = "Envoi…";
      fetch(ACTION, { method: "POST", body: d, mode: "no-cors" }).then(function () {
        msg.textContent = "C'est envoyé ! Ton tableau arrive dans ta boîte mail dans 1 minute (pense à regarder les spams). 💌";
        f.EMAIL.value = "";
        if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: "lettre-" + f.TABLEAU.value, title: "Inscription lettre de Moty", event: true });
      }).catch(function () { msg.textContent = "Oups, ça n'a pas marché. Réessaie dans un instant."; })
        .finally(function () { btn.disabled = false; });
    });
  });
})();
