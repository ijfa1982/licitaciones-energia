// Provincia de cada código NUTS-3 que usa la Plataforma de Contratación (islas agrupadas en su provincia).
window.PROVINCIAS = {
  ES111: "A Coruña", ES112: "Lugo", ES113: "Ourense", ES114: "Pontevedra", ES120: "Asturias", ES130: "Cantabria",
  ES211: "Araba/Álava", ES212: "Gipuzkoa", ES213: "Bizkaia", ES220: "Navarra", ES230: "La Rioja",
  ES241: "Huesca", ES242: "Teruel", ES243: "Zaragoza", ES300: "Madrid",
  ES411: "Ávila", ES412: "Burgos", ES413: "León", ES414: "Palencia", ES415: "Salamanca", ES416: "Segovia",
  ES417: "Soria", ES418: "Valladolid", ES419: "Zamora",
  ES421: "Albacete", ES422: "Ciudad Real", ES423: "Cuenca", ES424: "Guadalajara", ES425: "Toledo",
  ES431: "Badajoz", ES432: "Cáceres",
  ES511: "Barcelona", ES512: "Girona", ES513: "Lleida", ES514: "Tarragona",
  ES521: "Alicante/Alacant", ES522: "Castellón/Castelló", ES523: "Valencia/València",
  ES530: "Illes Balears", ES531: "Illes Balears", ES532: "Illes Balears", ES533: "Illes Balears",
  ES611: "Almería", ES612: "Cádiz", ES613: "Córdoba", ES614: "Granada", ES615: "Huelva", ES616: "Jaén",
  ES617: "Málaga", ES618: "Sevilla", ES620: "Murcia", ES630: "Ceuta", ES640: "Melilla",
  ES701: "Las Palmas", ES704: "Las Palmas", ES705: "Las Palmas", ES708: "Las Palmas",
  ES702: "Santa Cruz de Tenerife", ES703: "Santa Cruz de Tenerife", ES706: "Santa Cruz de Tenerife",
  ES707: "Santa Cruz de Tenerife", ES709: "Santa Cruz de Tenerife",
};
// Mapa de teselas: cada comunidad en una casilla de una rejilla que respeta su posición aproximada.
// [comunidad tal como viene en los datos, nombre corto, columna, fila, ancho, código ISO 3166-2 para pantallas estrechas]
window.TESELAS = [
  ["Galicia", "Galicia", 1, 1, 1, "GA"], ["Principado de Asturias", "Asturias", 2, 1, 1, "AS"], ["Cantabria", "Cantabria", 3, 1, 1, "CB"],
  ["País Vasco", "País Vasco", 4, 1, 1, "PV"], ["Comunidad Foral de Navarra", "Navarra", 5, 1, 1, "NC"],
  ["Castilla y León", "Castilla y León", 2, 2, 2, "CL"], ["La Rioja", "La Rioja", 4, 2, 1, "RI"], ["Aragón", "Aragón", 5, 2, 1, "AR"],
  ["Cataluña", "Cataluña", 6, 2, 1, "CT"],
  ["Extremadura", "Extremadura", 2, 3, 1, "EX"], ["Comunidad de Madrid", "Madrid", 3, 3, 1, "MD"],
  ["Castilla-La Mancha", "Castilla-La Mancha", 4, 3, 2, "CM"], ["Comunitat Valenciana", "C. Valenciana", 6, 3, 1, "VC"],
  ["Illes Balears", "Baleares", 7, 3, 1, "IB"],
  ["Andalucía", "Andalucía", 2, 4, 3, "AN"], ["Región de Murcia", "Murcia", 5, 4, 1, "MC"],
  ["Canarias", "Canarias", 1, 5, 1, "CN"], ["Ceuta", "Ceuta", 3, 5, 1, "CE"], ["Melilla", "Melilla", 4, 5, 1, "ML"],
];
