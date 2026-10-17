"""Estados posibles de una capacidad del router.

Se distingue 'no detectada' (no hay evidencia de que exista) de
'no verificada' (hay indicios, pero HERMES no lo ha comprobado).
HERMES nunca afirma una capacidad sin evidencia.
"""
CONFIRMADA = "confirmada"
NO_VERIFICADA = "no_verificada"
NO_DETECTADA = "no_detectada"

# Funciones que requieren evidencia adicional (no basta con que haya una web).
FUNCIONES_POR_VERIFICAR = (
    "obtener_clientes", "cambiar_canal_wifi", "bloquear_cliente", "configurar_qos",
)
