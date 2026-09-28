#Codigo principal de HERMES solo personal autorizado XD

from src.nlp import identificar_intencion #funcion para identificar la intencion del usuario
from src.network import obtener_datos_red #funcion para obtener los datos de la red con diagnostico de latencia y perdida de paquetes
from src.diagnostico import diagnosticar, recomendar #funciones para diagnosticar y recomendar acciones basadas en los resultados del diagnostico


print("=== HERMES ===")
print("Sistema Inteligente de Administración y Diagnóstico de Redes")
print()

pregunta = input("¿Qué problema tienes con tu red?: ")

intencion = identificar_intencion(pregunta)#esto llama a la funcion identificar_intencion para determinar la intencion del usuario

print()
print("Intención detectada:", intencion)
print()

if intencion == "diagnostico_latencia":
    
    hostname, ip_local, conexion, latencia, perdida = obtener_datos_red()#funcion para obtener los datos de la red con diagnostico de latencia y perdida de paquetes

    resultado = diagnosticar(latencia, perdida, conexion)
    recomendacion = recomendar(latencia, perdida, conexion)

    print("Nombre del equipo:", hostname)
    print("IP local:", ip_local)
    print("Conexión:", "estable" if conexion else "sin conexión")
    print("Latencia promedio:", latencia, "ms")
    print("Pérdida de paquetes:", perdida, "%")
    print()
    print("Diagnóstico:", resultado)
    print("Recomendación:", recomendacion)

elif intencion == "diagnostico_conectividad":

    hostname, ip_local, conexion, latencia, perdida = obtener_datos_red()

    resultado = diagnosticar(latencia, perdida, conexion)
    recomendacion = recomendar(latencia, perdida, conexion)

    print("Nombre del equipo:", hostname)
    print("IP local:", ip_local)
    print("Conexión:", "OK" if conexion else "ERROR")
    print()
    print("Diagnóstico:", resultado)
    print("Recomendación:", recomendacion)

elif intencion == "diagnostico_general":

    hostname, ip_local, conexion, latencia, perdida = obtener_datos_red()#obtener los datos de la red con diagnostico de latencia y perdida de paquetes

    resultado = diagnosticar(latencia, perdida, conexion)
    recomendacion = recomendar(latencia, perdida, conexion)

    print("Nombre del equipo:", hostname)
    print("IP local:", ip_local)
    print("Conexión:", "estable" if conexion else "sin conexión")
    print("Latencia promedio:", latencia, "ms")
    print("Pérdida de paquetes:", perdida, "%")
    print()
    print("Diagnóstico:", resultado)
    print("Recomendación:", recomendacion)

else:

    print("No pude identificar el problema.")
    print("Prueba con frases como:")
    print("- Mi internet está lento")
    print("- No tengo internet")
    print("- Quiero revisar mi red")