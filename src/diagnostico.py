# Diagnóstico de la conexión a Internet


def diagnosticar(latencia, perdida, conexion):#funcion para diagnosticar la conexion a internet basada en los resultados obtenidos de la red

    if not conexion:
        return "No hay conexión a Internet."

    if perdida is None:
        return "No fue posible obtener la pérdida de paquetes."

    if latencia is None:
        return "No fue posible obtener la latencia."

    if perdida > 10:
        return "Se detecta una pérdida de paquetes alta."

    if latencia > 100:
        return "La latencia es alta."

    if latencia > 50:
        return "La conexión funciona, pero presenta una latencia moderada."

    return "La conexión parece estable."


def recomendar(latencia, perdida, conexion): #funcion para dar recomendaciones basadas en los resultados del diagnostico

    if not conexion:
        return "Verifica que el router esté encendido y que tu dispositivo esté conectado a la red."

    if perdida > 10:
        return "Revisa la conexión Wi-Fi, los cables de red y la estabilidad del router."

    if latencia > 100:
        return "Comprueba si hay otros dispositivos utilizando la red y realiza una nueva prueba."

    if latencia > 50:
        return "Si utilizas Wi-Fi, intenta acercarte al router o utilizar una conexión por cable."

    return "No se detectan problemas importantes. Puedes continuar utilizando la conexión."