#archivo temporal para probar el modelo de aprendizaje automático 
from machine_learning import entrenar_modelo, predecir_problema


modelo = entrenar_modelo()

resultado = predecir_problema(
    modelo,
    150,
    1,
    1
)

print("Predicción:", resultado)