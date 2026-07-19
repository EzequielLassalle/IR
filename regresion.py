"""Suite de regresion del motor de decision. Cada prueba declara su `esperado`.

**No se llama "casos" a proposito.** En respuesta a incidentes un caso es la unidad de
trabajo -- tiene duenio, severidad, estado y SLA -- y usar la palabra para una suite de
tests garantiza que alguien abra la opcion esperando su cola y encuentre otra cosa.

Son decisiones donde **el veredicto no coincide con la intuicion**. Ese es el criterio de
admision: un caso cuyo resultado se adivina sin correr el motor no ejercita nada.

Estan escritos contra el escenario A. Correrlos contra B con el mismo `esperado` **no tiene
sentido** -- son otro incidente -- y por eso el catalogo declara su escenario.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from acciones import FUNDADA, INAPLICABLE, INFUNDADA, NO_ADJUDICABLE, adjudicar
from eventos import cargar

# Ventana del incidente y momento en que el analista decide, para el escenario A.
DESDE = "2026-03-09T20:00:00Z"
HASTA = "2026-03-10T04:00:00Z"
CIERRE = "2026-03-10T04:00:00Z"


@dataclass
class Prueba:
    numero: int
    titulo: str
    accion: str
    objetivo: str
    en: str
    esperado: str
    concepto: str


PRUEBAS = [
    Prueba(1, "Apagar el host esta fundado, y aun asi es la peor opcion",
         "apagar-host", "WKS-04", CIERRE, FUNDADA,
         "Fundada no quiere decir recomendable. Los requisitos se cumplen igual que para "
         "aislar, pero apagar destruye la memoria volatil y aislar consigue la misma "
         "contencion sin ese costo. Por eso el motor la funda y la recomendacion la ordena "
         "ultima: el veredicto es sobre la evidencia, el orden es sobre el costo."),

    Prueba(2, "La misma accion, dos horas antes, no estaba fundada",
         "deshabilitar-cuenta", "WKS-04\\soporte_it", "2026-03-09T22:00:00Z", INFUNDADA,
         "La cuenta se crea a las 00:34 del dia 10. A las 22:00 del dia 9 no existia y "
         "nada la sostenia. Una decision se juzga con lo que se sabia en su momento, no "
         "con lo que se supo despues."),

    Prueba(3, "La misma accion, al cierre, si lo esta",
         "deshabilitar-cuenta", "WKS-04\\soporte_it", CIERRE, FUNDADA,
         "El par con el caso 2. Lo unico que cambia es el instante de la decision."),

    Prueba(4, "Bloquear la IP interna del servidor de facturacion no esta fundado",
         "bloquear-ip", "10.20.4.201", CIERRE, INFUNDADA,
         "Esa direccion produce 648 fallos de autenticacion: la firma exacta de una fuerza "
         "bruta, y es una aplicacion con la contrasenia vencida. El requisito exige fallos "
         "Y un acceso exitoso desde el mismo origen. Nunca lo consigue, porque nunca "
         "adivina la contrasenia. Volumen no es compromiso."),

    Prueba(5, "Bloquear la IP del ataque si lo esta",
         "bloquear-ip", "198.51.100.77", CIERRE, FUNDADA,
         "El par con el caso 4. La misma regla que descarta la interna funda esta, y no "
         "por el volumen -- la interna tiene cinco veces mas eventos -- sino por la "
         "conjuncion de fallos con un acceso que funciono."),

    Prueba(6, "Actuar sobre un host que no aparece en la evidencia",
         "aislar-host", "DC-01", CIERRE, INAPLICABLE,
         "No hay nada sobre lo que actuar. INAPLICABLE no es lo mismo que INFUNDADA: no es "
         "que la evidencia no respalde la accion, es que el objetivo no existe en el caso. "
         "Confundirlos haria que 'no encontre nada sobre X' se lea como 'X esta limpio'."),

    Prueba(7, "Rotar claves SSH en la estacion Windows",
         "rotar-clave-ssh", "WKS-04", CIERRE, INFUNDADA,
         "WKS-04 tiene un acceso remoto confirmado, y aun asi la accion no se funda: el "
         "requisito esta acotado a sshd, y un logon RDP de Windows no es una autenticacion "
         "por clave publica. Sin ese acotamiento el DSL matchearia por nombre de host y el "
         "motor recomendaria rotar claves en una maquina que no tiene ninguna."),

    Prueba(8, "Adjudicar no es recomendar, y confundirlos costo un motor entero",
         "revocar-credencial", "AKIA7QYCVN4RBUXWK3PD", CIERRE, FUNDADA,
         "Es la credencial legitima de la automatizacion, con 95 usos en la ventana. "
         "Adjudicar la accion sobre ella da FUNDADA, **y esta bien que lo de**: adjudicar "
         "responde 'un humano eligio este objetivo, ¿la evidencia respaldaba la accion?', "
         "y la sospecha la aporto el humano al elegirlo. || Este caso existia antes con "
         "otro texto, que lo presentaba como una leccion sobre 'fundada no es "
         "recomendable'. Era una racionalizacion de un defecto: `recomendar()` era "
         "`adjudicar()` en un bucle sobre el inventario, y por eso proponia revocar esta "
         "credencial. Al recomendar, **nadie aporta sospecha, asi que la precondicion "
         "tiene que cargarla**. El caso 9 es el que prueba que se corrigio."),

    Prueba(9, "Adjudicable no implica recomendable: la misma credencial no se propone",
         "revocar-credencial", "AKIA7QYCVN4RBUXWK3PD", CIERRE, FUNDADA,
         "Mismo veredicto que el caso 8 y distinto comportamiento del recomendador: en la "
         "ventana del incidente esta credencial **no aparece** entre las acciones "
         "propuestas, porque ningun hallazgo la seniala. La verificacion de esto no es el "
         "veredicto sino `test_el_recomendador_discrimina_el_ataque`, que corre el motor "
         "sobre una ventana anterior al incidente y exige que proponga sustancialmente "
         "menos que sobre la ventana del incidente. Un recomendador cuya salida es "
         "invariante a que el ataque haya ocurrido no esta recomendando: esta listando el "
         "inventario cruzado con verbos."),
]


def correr(escenario_dir: Path | None = None) -> list[tuple[Caso, str, bool]]:
    eventos = cargar(escenario_dir) if escenario_dir else cargar()
    out = []
    for c in PRUEBAS:
        v = adjudicar(c.accion, c.objetivo, eventos, c.en, DESDE, HASTA)
        out.append((c, v.veredicto, v.veredicto == c.esperado))
    return out


def resumen(escenario_dir: Path | None = None, detalle: bool = False) -> list[str]:
    lineas = []
    resultados = correr(escenario_dir)
    for c, obtenido, ok in resultados:
        marca = "ok" if ok else "!! NO COINCIDE"
        lineas.append(f"  {c.numero}) {c.titulo}")
        lineas.append(f"     {c.accion} {c.objetivo}  @ {c.en}")
        lineas.append(f"     esperado: {c.esperado:<16} obtenido: {obtenido:<16} {marca}")
        if detalle:
            lineas.append(f"     {c.concepto}")
        lineas.append("")
    fallan = sum(1 for _, _, ok in resultados if not ok)
    lineas.append(f"  {len(resultados) - fallan} de {len(resultados)} coinciden")
    if fallan:
        lineas.append("  !! Con la evidencia intacta, un caso que no coincide es un bug "
                      "del motor.")
    return lineas
