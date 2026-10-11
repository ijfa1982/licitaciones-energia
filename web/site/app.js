(() => {
  const C = window.CONFIG || {};
  const ESCALA_DIAS = 60;
  const POR_PAGINA = 40;
  const $ = (id) => document.getElementById(id);
  const euros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
  const fecha = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "long" });
  const fechaHora = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" });
  let datos = { abiertas: [] };
  let visibles = POR_PAGINA;

  const quitarTildes = (t) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const diasHasta = (iso) => {
    if (!iso) return null;
    const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
    return Math.round((new Date(iso + "T00:00:00") - hoy) / 86400000);
  };
  const importeDe = (r) => r.presupuestoSinIva ?? r.valorEstimado ?? null;

  function enlacesPlanes() {
    document.querySelectorAll("[data-plan]").forEach((a) => {
      const plan = a.dataset.plan;
      const stripe = plan === "pro" ? C.stripePro : C.stripeEmpresa;
      if (stripe) { a.href = stripe; return; }
      const asunto = encodeURIComponent(`Alta plan ${plan === "pro" ? "Pro" : "Empresa"}`);
      const cuerpo = encodeURIComponent("Hola, quiero darme de alta.\n\nEmpresa:\nNIF:\nSectores que me interesan:\nComunidades:\nImporte mínimo:\nPalabras clave (opcional):\n");
      a.href = C.emailContacto ? `mailto:${C.emailContacto}?subject=${asunto}&body=${cuerpo}` : "#precios";
    });
    if (C.portalClientes) {
      $("baja").innerHTML = `Desde el <a href="${C.portalClientes}">portal de clientes</a>, con el email con el que pagaste, o respondiendo a cualquier email de alerta. No hay permanencia.`;
    }
  }

  function rellenarSelect(sel, valores) {
    [...new Set(valores.filter(Boolean))].sort((a, b) => a.localeCompare(b, "es"))
      .forEach((v) => sel.add(new Option(v, v)));
  }

  function filtradas() {
    const texto = quitarTildes($("f-texto").value.trim());
    const sector = $("f-sector").value;
    const comunidad = $("f-comunidad").value;
    const minimo = Number($("f-importe").value) || 0;
    const orden = $("f-orden").value;
    const lista = datos.abiertas.filter((r) => {
      if (sector && !(r.sectores || []).includes(sector)) return false;
      if (comunidad && r.comunidadAutonoma !== comunidad) return false;
      if (minimo && !(importeDe(r) >= minimo)) return false;
      if (texto && !quitarTildes(`${r.titulo} ${r.organoContratacion} ${r.municipio}`).includes(texto)) return false;
      return true;
    });
    const cmp = {
      plazo: (a, b) => (a.fechaLimite || "9999").localeCompare(b.fechaLimite || "9999"),
      importe: (a, b) => (importeDe(b) || 0) - (importeDe(a) || 0),
      recientes: (a, b) => (b.actualizado || "").localeCompare(a.actualizado || ""),
    }[orden];
    return lista.sort(cmp);
  }

  function pintar() {
    const lista = filtradas();
    const ol = $("licitaciones");
    const tpl = $("tpl-licitacion");
    const refUltima = datos.actualizado ? new Date(datos.actualizado) - 36 * 3600000 : 0;
    ol.replaceChildren();
    lista.slice(0, visibles).forEach((r) => {
      const li = tpl.content.firstElementChild.cloneNode(true);
      const a = li.querySelector(".titulo");
      a.textContent = r.titulo;
      a.href = r.urlDetalle || "#";
      li.querySelector(".organo").textContent = [r.organoContratacion, r.municipio || r.comunidadAutonoma].filter(Boolean).join(", ");
      const et = li.querySelector(".etiquetas");
      if (r.actualizado && new Date(r.actualizado) >= refUltima) {
        et.insertAdjacentHTML("beforeend", '<span class="etiqueta etiqueta-nueva">Últimas 24 h</span>');
      }
      [...(r.sectores || []).slice(0, 2), r.comunidadAutonoma, r.tipoContrato].filter(Boolean).forEach((t) => {
        const s = document.createElement("span"); s.className = "etiqueta"; s.textContent = t; et.append(s);
      });
      const imp = importeDe(r);
      li.querySelector(".importe").innerHTML = imp != null ? `${euros.format(imp)}<small>sin IVA</small>` : "<small>Importe no publicado</small>";
      const d = diasHasta(r.fechaLimite);
      const plazo = li.querySelector(".plazo");
      if (d == null) {
        li.querySelector(".dias").textContent = "Sin fecha límite publicada";
        li.querySelector(".cable").hidden = true;
      } else {
        li.querySelector(".conductor").style.width = `${Math.max(4, Math.min(100, (d / ESCALA_DIAS) * 100))}%`;
        li.querySelector(".dias").textContent = d === 0 ? "Cierra hoy" : `${d} ${d === 1 ? "día" : "días"} · hasta el ${fecha.format(new Date(r.fechaLimite + "T00:00:00"))}`;
        if (d <= 7) plazo.classList.add("urgente");
      }
      ol.append(li);
    });
    $("resumen").textContent = lista.length
      ? `${lista.length} ${lista.length === 1 ? "licitación" : "licitaciones"} con estos filtros.`
      : "Ninguna licitación abierta con estos filtros. Prueba con otra comunidad o quita el importe mínimo.";
    $("mas").hidden = lista.length <= visibles;
  }

  function pintarRanking() {
    const tb = $("ranking");
    tb.replaceChildren();
    (datos.ranking || []).forEach((e) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td></td><td class="num"></td><td class="num"></td><td></td>`;
      tr.children[0].textContent = e.nombre;
      if (e.sectores?.length) tr.children[0].insertAdjacentHTML("beforeend", `<small></small>`), (tr.children[0].lastChild.textContent = e.sectores.join(", "));
      tr.children[1].textContent = e.contratos;
      tr.children[2].textContent = e.importe ? euros.format(e.importe) : "—";
      tr.children[3].textContent = (e.comunidades || []).join(", ");
      tb.append(tr);
    });
    if (datos.empresasRanking) {
      $("ganadores-nota").textContent = `Las 10 primeras de ${datos.empresasRanking} empresas que han ganado alguna de las ${datos.adjudicacionesAnalizadas} adjudicaciones de energía de los últimos cuatro meses.`;
    }
  }

  async function cargar() {
    try {
      const r = await fetch("data/web.json", { cache: "no-cache" });
      if (!r.ok) throw new Error(r.status);
      datos = await r.json();
    } catch (e) {
      $("actualizado").textContent = "No se han podido cargar los datos. Recarga la página en unos minutos.";
      return;
    }
    const n = datos.abiertas.length;
    $("titular").innerHTML = `Hoy hay <span class="cuenta">${n.toLocaleString("es-ES")}</span> licitaciones de energía abiertas en España`;
    $("actualizado").innerHTML = `Actualizado el <b>${fechaHora.format(new Date(datos.actualizado))}</b>${datos.nuevasHoy ? ` · ${datos.nuevasHoy} nuevas desde ayer` : ""}.`;
    rellenarSelect($("f-sector"), datos.abiertas.flatMap((r) => r.sectores || []));
    rellenarSelect($("f-comunidad"), datos.abiertas.map((r) => r.comunidadAutonoma));
    pintar();
    pintarRanking();
  }

  ["f-texto", "f-sector", "f-comunidad", "f-importe", "f-orden"].forEach((id) =>
    $(id).addEventListener("input", () => { visibles = POR_PAGINA; pintar(); }));
  $("mas").addEventListener("click", () => { visibles += POR_PAGINA; pintar(); });

  let aviso;
  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); aviso = e; $("instalar").hidden = false; });
  $("instalar").addEventListener("click", async () => { if (!aviso) return; aviso.prompt(); await aviso.userChoice; $("instalar").hidden = true; });
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});

  enlacesPlanes();
  cargar();
})();
