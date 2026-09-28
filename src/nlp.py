# Codigo para identificar la intencion del usuario y determinar el tipo de diagnostico a realizar (temporal)
def identificar_intencion(texto):

    texto = texto.lower()

    # Problemas de conexión
    if (
        "sin conexión" in texto
        or "no tengo internet" in texto
        or "no hay internet" in texto
        or "no tengo conexión" in texto
        or "no funciona internet" in texto
    ):
        return "diagnostico_conectividad"

    # Problemas de velocidad o latencia
    if (
        "lento" in texto
        or "lag" in texto
        or "latencia" in texto
        or "retraso" in texto
        or "tarda mucho" in texto
    ):
        return "diagnostico_latencia"

    # Diagnóstico general
    if (
        "revisar mi red" in texto
        or "diagnóstico" in texto
        or "diagnostico" in texto
        or "revisar internet" in texto
        or "comprobar mi red" in texto
    ):
        return "diagnostico_general"

    return "intencion_desconocida"