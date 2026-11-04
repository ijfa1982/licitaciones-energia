// Ajustes de la web. Rellena los valores marcados con PENDIENTE antes de anunciarla.
window.CONFIG = {
  nombre: "Licitaciones Energía",
  // Enlaces de pago de Stripe (Payment Links). Mientras estén vacíos, el botón abre un email de alta.
  stripePro: "https://buy.stripe.com/00w6oH6cQeIifxB4n90VO02",       // Plan Pro, 19 €/mes + IVA, 14 días de prueba
  stripeEmpresa: "https://buy.stripe.com/28E4gzcBeas2fxBdXJ0VO03",   // Plan Empresa, 49 €/mes + IVA, 14 días de prueba
  portalClientes: "https://billing.stripe.com/p/login/eVq14n0SwcAa859bPB0VO00",  // portal de clientes de Stripe (cuenta Arcas Lab)
  emailContacto: "soporte@arcaslab.es",
  // Datos del titular (obligatorios en el aviso legal, Ley 34/2002 LSSI art. 10)
  titular: "",         // PENDIENTE: nombre y apellidos o razón social
  nif: "",             // PENDIENTE
  domicilio: "",       // PENDIENTE: dirección postal
};
