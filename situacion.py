"""Estado de conocimiento: que se sabe, que se sospecha y que no se miro.

Es lo que alimenta a la recomendacion. Sin esto, "alcance" es una lista de lo que se
encontro, y una lista de hallazgos no dice nada sobre lo que falta.

Tres niveles, que son los veredictos del verificador con otro nombre:

  hecho         Afirmacion verificada: existe cita y la cita la sostiene.
  indicio       Compatible con la evidencia y sin verificar, o con cita parcial. Un
                hallazgo de un detector que nadie sometio al verificador es un indicio,
                no un hecho, por mas convincente que suene.
  desconocido   Nadie establecio nada ahi.

**El tercero es el que vale y el que cuesta.** Un informe que solo enumera lo encontrado
promete de mas: lo que decide si una contencion es prematura no es lo que se sabe, es lo que
no se miro.

El tercer nivel se parte en dos, y la distincion es la que decide si una contencion es
prematura:

  SIN MIRAR       Nadie consulto esa zona. Es un hueco de investigacion.
  MIRADO Y VACIO  Se consulto y no quedo ningun hecho. Es una zona descartada.

Los dos producen la misma lista de hallazgos y no significan lo mismo. Sale de cruzar la
cobertura con el registro de consultas (`bitacora.py`), que es el dato que la consola ve en
cada invocacion.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from cobertura import FUENTES, observable
from eventos import ACCIONES_POR_FUENTE, Evento
from verificador import Afirmacion, verificar

HECHO = "hecho"
INDICIO = "indicio"
DESCONOCIDO = "desconocido"


@dataclass
class Entrada:
    nivel: str
    afirmacion: str
    cita: list[str] = field(default_factory=list)
    motivo: str = ""

    def __str__(self) -> str:
        marca = {"hecho": "[H]", "indicio": "[i]", "desconocido": "[?]"}[self.nivel]
        linea = f"  {marca} {self.afirmacion}"
        if self.cita:
            muestra = ", ".join(self.cita[:6]) + (f" (+{len(self.cita) - 6})"
                                                  if len(self.cita) > 6 else "")
            linea += f"\n      cita: {muestra}"
        if self.motivo:
            linea += f"\n      {self.motivo}"
        return linea


@dataclass
class Situacion:
    hechos: list[Entrada] = field(default_factory=list)
    indicios: list[Entrada] = field(default_factory=list)
    desconocidos: list[Entrada] = field(default_factory=list)

    @property
    def sujetos_comprometidos(self) -> set[str]:
        """Sujetos sobre los que hay al menos un hecho establecido."""
        return {e.afirmacion.split()[0] for e in self.hechos if e.afirmacion}


def desde_hallazgos(ruta: Path, eventos: list[Evento]) -> Situacion:
    """Construye el estado de conocimiento a partir de un archivo de hallazgos.

    Cada hallazgo pasa por el verificador. Lo verificado es hecho; lo que no pasa queda
    como indicio **con el motivo del rechazo escrito al lado**, no se descarta en silencio:
    que una afirmacion no se pueda sostener es informacion sobre la investigacion.
    """
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    hallazgos = datos["hallazgos"] if isinstance(datos, dict) else datos

    sit = Situacion()
    for h in hallazgos:
        try:
            af = Afirmacion.desde_dict(h.get("afirmacion", {}))
        except (ValueError, TypeError) as err:
            sit.indicios.append(Entrada(INDICIO, str(h.get("resumen", "?")),
                                        motivo=f"no expresable en el DSL: {err}"))
            continue
        r = verificar(af, h.get("cita", []), eventos)
        if r.admitido:
            sit.hechos.append(Entrada(HECHO, str(af), r.citas_validas))
        else:
            sit.indicios.append(Entrada(INDICIO, str(af), h.get("cita", []),
                                        f"{r.veredicto}: {r.motivo}"))
    return sit


def huecos(eventos: list[Evento], sit: Situacion, desde: str, hasta: str,
           evid=None) -> list[Entrada]:
    """Donde no hay hechos establecidos, habiendo cobertura para tenerlos.

    Barre el producto **fuente x accion** derivado de `ACCIONES_POR_FUENTE`, no una lista
    escrita a mano: enumerar a mano las zonas a revisar elige justo las que no incomodan, y
    es como se colaron los cinco defectos del proyecto anterior.
    """
    cubiertas = set()
    for e in sit.hechos:
        for palabra in e.afirmacion.split():
            cubiertas.add(palabra)

    out: list[Entrada] = []
    for fuente, acciones in sorted(ACCIONES_POR_FUENTE.items()):
        if not FUENTES[fuente].cubre(desde, hasta):
            out.append(Entrada(DESCONOCIDO, f"{fuente}: toda la ventana",
                               motivo=f"la fuente no cubre {desde} .. {hasta}"))
            continue
        for accion in sorted(acciones):
            if accion in cubiertas:
                continue
            obs = observable(accion, "-", desde, hasta)
            if not obs.informa_la_ausencia:
                continue
            mirado = False
            if evid is not None:
                import bitacora
                mirado = bitacora.toco(evid, fuente, accion, desde, hasta)
            if mirado:
                out.append(Entrada(
                    DESCONOCIDO, f"{fuente}: '{accion}' MIRADO Y VACIO",
                    motivo="se consulto esta zona y no quedo ningun hecho establecido: "
                           "es una zona descartada, no un hueco"))
            else:
                out.append(Entrada(
                    DESCONOCIDO, f"{fuente}: '{accion}' SIN MIRAR",
                    motivo="la fuente cubre la ventana y registra esta accion, y ninguna "
                           "consulta la alcanzo: es un hueco de investigacion"))
    return out


def resumen(sit: Situacion, eventos: list[Evento], desde: str, hasta: str,
            evid=None) -> list[str]:
    sit.desconocidos = huecos(eventos, sit, desde, hasta, evid)
    lineas = [f"HECHOS ({len(sit.hechos)})", "-" * 78]
    lineas += [str(e) for e in sit.hechos] or ["  (ninguno)"]
    lineas += ["", f"INDICIOS ({len(sit.indicios)})", "-" * 78]
    lineas += [str(e) for e in sit.indicios] or ["  (ninguno)"]
    lineas += ["", f"SIN ESTABLECER ({len(sit.desconocidos)})", "-" * 78]
    lineas += ["  Zonas con cobertura demostrada y sin hechos. SIN MIRAR es un hueco de",
               "  investigacion; MIRADO Y VACIO es una zona descartada.", ""]
    lineas += [str(e) for e in sit.desconocidos] or ["  (ninguna)"]
    return lineas
