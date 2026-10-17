import logging

# Evita que los avisos de HERMES ensucien la salida de las pruebas.
logging.getLogger("hermes").addHandler(logging.NullHandler())
