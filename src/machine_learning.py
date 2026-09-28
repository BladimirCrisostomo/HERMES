#esto es el archivo para entrenar el modelo de aprendizaje automático para diagnosticar problemas de conectividad, latencia y perdida de paquetes
import pandas as pd#libreria para manejar datos en forma de tablas

from sklearn.tree import DecisionTreeClassifier#libreria para crear el modelo de árbol de decisión


def entrenar_modelo():#funcion para entrenar el modelo de aprendizaje automático basado en los datos del dataset

    datos = pd.read_csv("data/dataset.csv")#lectura de los datos del dataset

    X = datos[["latencia", "perdida", "conexion"]]

    y = datos["problema"]

    modelo = DecisionTreeClassifier()#creamos el modelo de árbol de decisión
    modelo.fit(X, y)

    return modelo

def predecir_problema(modelo, latencia, perdida, conexion):#funcion para predecir el problema de la red basado en los resultados obtenidos de la red y el modelo entrenado

    datos = [[latencia, perdida, conexion]]

    prediccion = modelo.predict(datos)

    return prediccion[0]