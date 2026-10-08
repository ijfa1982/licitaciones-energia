"""Feed de ejemplo con la estructura ATOM/CODICE de la Plataforma de Contratación."""

CABECERA = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:cbc-place-ext="urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2"
      xmlns:cac-place-ext="urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2"
      xmlns:cbc="urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2"
      xmlns:cac="urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2"
      xmlns:at="http://purl.org/atompub/tombstones/1.0">
  <author><name>Plataforma de Contratación del Sector Público</name></author>
  <id>https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom</id>
  <link href="https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom" rel="self"/>
  {next}
  <title>Licitaciones publicadas en www.contrataciondelestado.es</title>
  <updated>2026-10-08T08:00:00.000+02:00</updated>
"""


def entrada(
    num: int,
    titulo: str,
    cpvs: list[str],
    estado: str = "PUB",
    nuts: str = "ES511",
    lugar: str = "Barcelona",
    fecha_limite: str = "2026-10-30",
    actualizado: str = "2026-10-08T07:00:00.000+02:00",
    importe: str = "150000",
    tipo: str = "1",
    con_resultado: bool = False,
) -> str:
    cpv_xml = "".join(
        f"""<cac:RequiredCommodityClassification>
              <cbc:ItemClassificationCode listURI="http://contrataciondelestado.es/codice/cl/1.04/CPV2008-1.04.gc">{c}</cbc:ItemClassificationCode>
            </cac:RequiredCommodityClassification>"""
        for c in cpvs
    )
    resultado = """<cac:TenderResult>
          <cbc:ResultCode>8</cbc:ResultCode>
          <cac:WinningParty><cac:PartyName><cbc:Name>Solar Ejemplo SL</cbc:Name></cac:PartyName></cac:WinningParty>
          <cac:AwardedTenderedProject><cac:LegalMonetaryTotal>
            <cbc:TaxExclusiveAmount currencyID="EUR">120000</cbc:TaxExclusiveAmount>
          </cac:LegalMonetaryTotal></cac:AwardedTenderedProject>
        </cac:TenderResult>""" if con_resultado else ""
    return f"""
  <entry>
    <id>https://contrataciondelsectorpublico.gob.es/sindicacion/licitacionesPerfilContratante/{num}</id>
    <link href="https://contrataciondelsectorpublico.gob.es/wps/poc?uri=deeplink:detalle_licitacion&amp;idEvl={num}"/>
    <summary type="text">Id licitación: EXP-{num}; Estado: {estado}</summary>
    <title>{titulo}</title>
    <updated>{actualizado}</updated>
    <cac-place-ext:ContractFolderStatus>
      <cbc:ContractFolderID>EXP-{num}</cbc:ContractFolderID>
      <cbc-place-ext:ContractFolderStatusCode listURI="https://contrataciondelestado.es/codice/cl/2.04/SyndicationContractFolderStatusCode-2.04.gc">{estado}</cbc-place-ext:ContractFolderStatusCode>
      <cac-place-ext:LocatedContractingParty>
        <cbc:ContractingPartyTypeCode>3</cbc:ContractingPartyTypeCode>
        <cac:Party>
          <cac:PartyIdentification><cbc:ID schemeName="DIR3">L01080193</cbc:ID></cac:PartyIdentification>
          <cac:PartyIdentification><cbc:ID schemeName="NIF">P0801900B</cbc:ID></cac:PartyIdentification>
          <cac:PartyName><cbc:Name>Ayuntamiento de Ejemplo</cbc:Name></cac:PartyName>
          <cac:PostalAddress><cbc:CityName>Ejemplo</cbc:CityName></cac:PostalAddress>
        </cac:Party>
        <cac-place-ext:ParentLocatedParty>
          <cac:PartyName><cbc:Name>ENTIDADES LOCALES</cbc:Name></cac:PartyName>
          <cac-place-ext:ParentLocatedParty>
            <cac:PartyName><cbc:Name>Cataluña</cbc:Name></cac:PartyName>
          </cac-place-ext:ParentLocatedParty>
        </cac-place-ext:ParentLocatedParty>
      </cac-place-ext:LocatedContractingParty>
      <cac:ProcurementProject>
        <cbc:Name>{titulo}</cbc:Name>
        <cbc:TypeCode listURI="x">{tipo}</cbc:TypeCode>
        <cac:BudgetAmount>
          <cbc:EstimatedOverallContractAmount currencyID="EUR">{importe}</cbc:EstimatedOverallContractAmount>
          <cbc:TotalAmount currencyID="EUR">{float(importe) * 1.21:.2f}</cbc:TotalAmount>
          <cbc:TaxExclusiveAmount currencyID="EUR">{importe}</cbc:TaxExclusiveAmount>
        </cac:BudgetAmount>
        {cpv_xml}
        <cac:RealizedLocation>
          <cbc:CountrySubentity>{lugar}</cbc:CountrySubentity>
          <cbc:CountrySubentityCode listURI="x">{nuts}</cbc:CountrySubentityCode>
          <cac:Address><cbc:CityName>Ejemplo</cbc:CityName></cac:Address>
        </cac:RealizedLocation>
        <cac:PlannedPeriod><cbc:DurationMeasure unitCode="MON">6</cbc:DurationMeasure></cac:PlannedPeriod>
      </cac:ProcurementProject>
      {resultado}
      <cac:TenderingProcess>
        <cbc:ProcedureCode listURI="x">1</cbc:ProcedureCode>
        <cac:TenderSubmissionDeadlinePeriod>
          <cbc:EndDate>{fecha_limite}</cbc:EndDate>
          <cbc:EndTime>14:00:00</cbc:EndTime>
        </cac:TenderSubmissionDeadlinePeriod>
      </cac:TenderingProcess>
      <cac:LegalDocumentReference>
        <cbc:ID>PCAP.pdf</cbc:ID>
        <cac:Attachment><cac:ExternalReference><cbc:URI>https://contrataciondelsectorpublico.gob.es/doc/{num}/pcap</cbc:URI></cac:ExternalReference></cac:Attachment>
      </cac:LegalDocumentReference>
    </cac-place-ext:ContractFolderStatus>
  </entry>"""


def pagina(entradas: list[str], siguiente: str | None = None) -> bytes:
    nxt = f'<link href="{siguiente}" rel="next"/>' if siguiente else ""
    tombstone = '<at:deleted-entry ref="https://contrataciondelsectorpublico.gob.es/sindicacion/licitacionesPerfilContratante/999" when="2026-10-08T06:00:00+02:00"/>'
    return (CABECERA.replace("{next}", nxt) + "".join(entradas) + tombstone + "\n</feed>").encode("utf-8")


URL_PAG2 = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_20261007_120000.atom"
URL_PAG3 = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_20260901_120000.atom"

PAGINA_1 = pagina(
    [
        entrada(1, "Suministro e instalación de planta fotovoltaica para autoconsumo en el polideportivo", ["09331200", "45261215"]),
        entrada(2, "Renovación del alumbrado público con tecnología LED en el casco urbano", ["45000000"], nuts="ES618", lugar="Sevilla", importe="480000", tipo="3"),
        entrada(3, "Servicio de limpieza de edificios municipales", ["90910000"], tipo="2"),
        entrada(4, "Instalación fotovoltaica en cubierta del colegio", ["09331200"], estado="ADJ", con_resultado=True),
        entrada(5, "Sustitución de calderas por bomba de calor aerotermia", ["45331000"], fecha_limite="2026-10-01"),
        entrada(6, "Suministro de energía eléctrica para los edificios de la Diputación", ["09310000"], nuts="ES300", lugar="Madrid", importe="2500000", tipo="1"),
    ],
    siguiente=URL_PAG2,
)

PAGINA_2 = pagina(
    [
        # Versión anterior de la licitación 1: debe ignorarse (ya vimos la más reciente)
        entrada(1, "Suministro e instalación de planta fotovoltaica (versión antigua)", ["09331200"], actualizado="2026-10-07T09:00:00.000+02:00"),
        entrada(7, "Instalación de puntos de recarga para vehículos eléctricos", ["45310000"], nuts="ES523", lugar="Valencia", actualizado="2026-10-07T08:00:00.000+02:00", importe="60000"),
        entrada(8, "Mantenimiento de jardines", ["77310000"], actualizado="2026-09-20T08:00:00.000+02:00"),
    ],
    siguiente=URL_PAG3,
)

PAGINA_3 = pagina(
    [entrada(9, "Alumbrado antiguo fuera del periodo", ["45316110"], actualizado="2026-09-01T08:00:00.000+02:00")],
)

PAGINAS = {
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom": PAGINA_1,
    URL_PAG2: PAGINA_2,
    URL_PAG3: PAGINA_3,
}
