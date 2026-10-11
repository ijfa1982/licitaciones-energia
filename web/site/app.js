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
  const PROV = window.PROVINCIAS || {};
  const provinciaDe = (r) => r.provincia || PROV[(r.codigoNuts || "").slice(0, 5)] || "";
  const capitalizar = (t) => t.toLocaleLowerCase("es").replace(/(^|[\s\-\/(])(\p{L})/gu, (m, a, b) => a + b.toLocaleUpperCase("es"))
    .replace(/\b(De|Del|La|Las|Los|El|Y|I|D')\b/g, (m, x, off) => (off ? x.toLowerCase() : x));
  const municipioDe = (r) => { const t = (r.municipio || "").trim(); return t && t === t.toUpperCase() ? capitalizar(t) : t; };

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
    const tipo = $("f-tipo").value;
    const provincia = $("f-provincia").value;
    const municipio = $("f-municipio").value;
    const minimo = Number($("f-importe").value) || 0;
    const orden = $("f-orden").value;
    const lista = datos.abiertas.filter((r) => {
      if (sector && !(r.sectores || []).includes(sector)) return false;
      if (comunidad && r.comunidadAutonoma !== comunidad) return false;
      if (tipo && r.tipoContrato !== tipo) return false;
      if (provincia && provinciaDe(r) !== provincia) return false;
      if (municipio && municipioDe(r) !== municipio) return false;
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
    rellenarSelect($("f-tipo"), datos.abiertas.map((r) => r.tipoContrato));
    encadenar();
    pintar();
    pintarSectores();
    pintarMapa();
    pintarRanking();
  }

  function opciones(sel, valores, todos) {
    const actual = sel.value;
    sel.replaceChildren(new Option(todos, ""));
    rellenarSelect(sel, valores);
    sel.value = [...sel.options].some((o) => o.value === actual) ? actual : "";
  }
  function encadenar() {
    const ca = $("f-comunidad").value;
    const enCa = datos.abiertas.filter((r) => !ca || r.comunidadAutonoma === ca);
    opciones($("f-provincia"), enCa.map(provinciaDe), "Todas");
    const pr = $("f-provincia").value;
    opciones($("f-municipio"), enCa.filter((r) => !pr || provinciaDe(r) === pr).map(municipioDe), "Todos");
  }

  const contar = (lista, f) => lista.reduce((m, r) => { const k = f(r); if (k) m[k] = (m[k] || 0) + 1; return m; }, {});
  let geo = null;
  const NS = "http://www.w3.org/2000/svg";
  const nivel = (n, max) => (n === 0 ? 0 : Math.min(4, 1 + Math.floor((n / max) * 3.999)));
  function caja(d) {
    const nums = d.match(/-?\d+(\.\d+)?/g).map(Number);
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (let i = 0; i < nums.length; i += 2) {
      x0 = Math.min(x0, nums[i]); x1 = Math.max(x1, nums[i]); y0 = Math.min(y0, nums[i + 1]); y1 = Math.max(y1, nums[i + 1]);
    }
    return [x0, y0, x1 - x0, y1 - y0];
  }
  function pintarSvg() {
    const svg = $("mapa-svg");
    const ca = $("f-comunidad").value;
    const lista = datos.abiertas;
    svg.replaceChildren();
    let capa, viewBox;
    if (ca) {
      capa = geo.provincias.filter((p) => p.comunidad === ca);
      const cuenta = contar(lista.filter((r) => r.comunidadAutonoma === ca), provinciaDe);
      capa = capa.map((p) => ({ ...p, n: cuenta[p.nombre] || 0, valor: p.nombre, campo: "f-provincia" }));
      const cajas = capa.map((p) => caja(p.d));
      if (cajas.length) {
        const x0 = Math.min(...cajas.map((c) => c[0])), y0 = Math.min(...cajas.map((c) => c[1]));
        const x1 = Math.max(...cajas.map((c) => c[0] + c[2])), y1 = Math.max(...cajas.map((c) => c[1] + c[3]));
        const m = Math.max(x1 - x0, y1 - y0) * 0.08;
        viewBox = [x0 - m, y0 - m, x1 - x0 + 2 * m, y1 - y0 + 2 * m];
      }
    } else {
      const cuenta = contar(lista, (r) => r.comunidadAutonoma);
      capa = geo.comunidades.map((c) => ({ ...c, n: cuenta[c.nombre] || 0, valor: c.nombre, campo: "f-comunidad" }));
    }
    viewBox = viewBox || [0, 0, geo.ancho, geo.alto];
    svg.setAttribute("viewBox", viewBox.join(" "));
    const escalaTexto = viewBox[2] / geo.ancho;
    const max = Math.max(1, ...capa.map((c) => c.n));
    if (!ca && geo.recuadroCanarias) {
      const [x, y, w, hh] = geo.recuadroCanarias;
      const r = document.createElementNS(NS, "rect");
      Object.entries({ x, y, width: w, height: hh, class: "recuadro" }).forEach(([k, v]) => r.setAttribute(k, v));
      svg.append(r);
    }
    const sel = $("f-provincia").value;
    capa.forEach((c) => {
      const p = document.createElementNS(NS, "path");
      p.setAttribute("d", c.d);
      p.setAttribute("class", "zona");
      p.dataset.nivel = nivel(c.n, max);
      p.setAttribute("tabindex", "0");
      p.setAttribute("role", "button");
      p.setAttribute("aria-label", `${c.nombre}: ${c.n} ${c.n === 1 ? "licitación abierta" : "licitaciones abiertas"}`);
      if (ca && sel === c.nombre) p.setAttribute("aria-pressed", "true");
      const titulo = document.createElementNS(NS, "title"); titulo.textContent = `${c.nombre}: ${c.n}`; p.append(titulo);
      const accion = () => {
        if (c.campo === "f-comunidad") { $("f-comunidad").value = c.valor; $("f-provincia").value = ""; }
        else { $("f-provincia").value = sel === c.valor ? "" : c.valor; }
        $("f-municipio").value = "";
        refrescar();
      };
      p.addEventListener("click", accion);
      p.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); accion(); } });
      svg.append(p);
    });
    capa.forEach((c) => {
      if (!c.n) return;
      const t = document.createElementNS(NS, "text");
      t.setAttribute("x", c.c[0]); t.setAttribute("y", c.c[1]);
      t.setAttribute("class", "cifra");
      t.setAttribute("font-size", (ca ? 30 : 26) * escalaTexto);
      t.setAttribute("stroke-width", 5 * escalaTexto);
      t.textContent = c.n;
      svg.append(t);
    });
    $("volver").hidden = !ca;
  }
  async function cargarMapa() {
    try {
      const r = await fetch("data/mapa.json");
      if (!r.ok) return;
      geo = await r.json();
      if (!geo.comunidades?.length) { geo = null; return; }
      $("mapa-svg").removeAttribute("hidden"); $("teselas").hidden = true; $("leyenda").hidden = false;
      if (datos.abiertas.length) pintarMapa();
    } catch (e) { geo = null; }
  }
  $("volver").addEventListener("click", () => {
    $("f-comunidad").value = ""; $("f-provincia").value = ""; $("f-municipio").value = ""; refrescar();
  });

  function pintarMapa() {
    if (geo) { pintarSvg(); pintarDetalle(); return; }
    const cont = $("teselas");
    const porCa = contar(datos.abiertas, (r) => r.comunidadAutonoma);
    const max = Math.max(1, ...Object.values(porCa));
    const sel = $("f-comunidad").value;
    cont.replaceChildren();
    (window.TESELAS || []).forEach(([ca, corto, col, fila, ancho, iso]) => {
      const n = porCa[ca] || 0;
      const b = document.createElement("button");
      b.className = "tesela";
      b.style.gridColumn = `${col} / span ${ancho}`;
      b.style.gridRow = String(fila);
      // Intensidad de 0 a 4 según el número de licitaciones (escala relativa a la comunidad con más).
      b.dataset.nivel = n === 0 ? 0 : Math.min(4, 1 + Math.floor((n / max) * 3.999));
      b.setAttribute("aria-pressed", String(sel === ca));
      b.setAttribute("aria-label", `${ca}: ${n} ${n === 1 ? "licitación abierta" : "licitaciones abiertas"}`);
      b.innerHTML = `<span class="tesela-n"></span><span class="tesela-nombre" aria-hidden="true"></span><span class="tesela-iso" aria-hidden="true"></span>`;
      b.children[0].textContent = n;
      b.children[1].textContent = corto;
      b.children[2].textContent = iso || corto;
      b.addEventListener("click", () => {
        $("f-comunidad").value = sel === ca ? "" : ca;
        $("f-provincia").value = ""; $("f-municipio").value = "";
        refrescar();
      });
      cont.append(b);
    });
    pintarDetalle();
  }
  function pintarDetalle() {
    const d = $("detalle");
    const ca = $("f-comunidad").value;
    if (!ca) { d.innerHTML = '<p class="detalle-vacio">Elige una comunidad en el mapa.</p>'; return; }
    const lista = datos.abiertas.filter((r) => r.comunidadAutonoma === ca);
    const provs = Object.entries(contar(lista, provinciaDe)).sort((a, b) => b[1] - a[1]);
    const munis = Object.entries(contar(lista, municipioDe)).sort((a, b) => b[1] - a[1]).slice(0, 8);
    d.replaceChildren();
    const h = document.createElement("h3"); h.textContent = `${ca}: ${lista.length} ${lista.length === 1 ? "abierta" : "abiertas"}`; d.append(h);
    const bloque = (titulo, filas, campo) => {
      if (!filas.length) return;
      const t = document.createElement("p"); t.className = "detalle-titulo"; t.textContent = titulo; d.append(t);
      const ul = document.createElement("ul"); ul.className = "barras";
      const max = filas[0][1];
      filas.forEach(([nombre, n]) => {
        const li = document.createElement("li");
        const b = document.createElement("button");
        b.innerHTML = '<span class="barra-nombre"></span><span class="barra-n"></span><span class="barra-fondo"><span class="barra-relleno"></span></span>';
        b.querySelector(".barra-nombre").textContent = nombre;
        b.querySelector(".barra-n").textContent = n;
        b.querySelector(".barra-relleno").style.width = `${(n / max) * 100}%`;
        b.setAttribute("aria-pressed", String($(campo).value === nombre));
        b.addEventListener("click", () => {
          if (campo === "f-provincia") { $("f-provincia").value = $("f-provincia").value === nombre ? "" : nombre; $("f-municipio").value = ""; }
          else { encadenar(); $("f-municipio").value = $("f-municipio").value === nombre ? "" : nombre; }
          refrescar();
        });
        li.append(b); ul.append(li);
      });
      d.append(ul);
    };
    bloque("Provincias", provs, "f-provincia");
    bloque("Municipios con más licitaciones", munis, "f-municipio");
  }
  function refrescar() {
    const muni = $("f-municipio").value;
    encadenar();
    if (muni && [...$("f-municipio").options].some((o) => o.value === muni)) $("f-municipio").value = muni;
    visibles = POR_PAGINA; pintar(); pintarSectores(); pintarMapa();
  }

  function pintarSectores() {
    document.querySelectorAll(".sector").forEach((b) => {
      const n = datos.abiertas.filter((r) => (r.sectores || []).includes(b.dataset.sector)).length;
      b.querySelector(".sector-n").textContent = `${n} ${n === 1 ? "abierta" : "abiertas"}`;
      b.setAttribute("aria-pressed", String($("f-sector").value === b.dataset.sector));
    });
  }
  document.querySelectorAll(".sector").forEach((b) => b.addEventListener("click", () => {
    const sel = $("f-sector");
    if (![...sel.options].some((o) => o.value === b.dataset.sector)) sel.add(new Option(b.dataset.sector, b.dataset.sector));
    sel.value = sel.value === b.dataset.sector ? "" : b.dataset.sector;
    visibles = POR_PAGINA; pintar(); pintarSectores(); pintarMapa();
    $("lista").scrollIntoView({ behavior: "smooth" });
  }));

  async function cargarCreditos() {
    try {
      const r = await fetch("img/fotos/creditos.json");
      if (!r.ok) return;
      const lista = await r.json();
      const p = $("creditos");
      p.textContent = "Fotos de Wikimedia Commons: ";
      lista.forEach((c, i) => {
        const a = document.createElement("a");
        a.href = c.pagina; a.target = "_blank"; a.rel = "noopener";
        a.textContent = `${c.alt}, ${c.autor}`;
        p.append(a, ` (${c.licencia})${i < lista.length - 1 ? "; " : "."}`);
      });
    } catch (e) { /* sin créditos si no hay fotos */ }
  }

  ["f-texto", "f-sector", "f-tipo", "f-importe", "f-orden", "f-municipio"].forEach((id) =>
    $(id).addEventListener("input", () => { visibles = POR_PAGINA; pintar(); pintarSectores(); pintarDetalle(); }));
  $("f-comunidad").addEventListener("input", () => { $("f-provincia").value = ""; $("f-municipio").value = ""; refrescar(); });
  $("f-provincia").addEventListener("input", () => { $("f-municipio").value = ""; refrescar(); });
  $("mas").addEventListener("click", () => { visibles += POR_PAGINA; pintar(); });

  let aviso;
  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); aviso = e; $("instalar").hidden = false; });
  $("instalar").addEventListener("click", async () => { if (!aviso) return; aviso.prompt(); await aviso.userChoice; $("instalar").hidden = true; });
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});

  enlacesPlanes();
  cargar().then(cargarMapa);
  cargarCreditos();
})();
