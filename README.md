# HERMES

### Sistema Inteligente de Administración y Diagnóstico de Redes

## Descripción

HERMES es un proyecto de Inteligencia Artificial desarrollado bajo la metodología de Aprendizaje Basado en Proyectos (ABP).

El objetivo del proyecto es desarrollar un sistema inteligente capaz de analizar información relacionada con una red de computadoras, identificar posibles problemas y proporcionar un diagnóstico utilizando Inteligencia Artificial, aprendizaje automático y procesamiento de lenguaje natural.

El sistema permitirá que el usuario interactúe utilizando lenguaje natural para describir un problema de red. Por ejemplo:

> "Mi Internet está muy lento y algunas páginas tardan demasiado en cargar."

A partir de esta solicitud, el sistema analizará la información proporcionada, identificará la posible intención del usuario y utilizará datos obtenidos de la red para generar un diagnóstico.

Además del diagnóstico, el sistema podrá proporcionar recomendaciones básicas para ayudar al usuario a identificar y solucionar el problema.

---

## Objetivo

Desarrollar un sistema inteligente capaz de interpretar consultas relacionadas con problemas de redes, recopilar información de la conexión, analizar los datos mediante técnicas de aprendizaje automático y generar diagnósticos comprensibles para el usuario.

El sistema busca combinar conceptos de:

* Inteligencia Artificial.
* Aprendizaje automático.
* Procesamiento de lenguaje natural.
* Administración de redes.
* Análisis de datos.
* Automatización.
* Desarrollo de software.

La finalidad es crear un prototipo funcional que demuestre cómo la Inteligencia Artificial puede utilizarse para apoyar tareas de diagnóstico y administración de redes.

---

## Uso de Inteligencia Artificial

La Inteligencia Artificial será utilizada como uno de los componentes principales del sistema.

El sistema podrá:

* Interpretar consultas escritas en lenguaje natural.
* Identificar la intención del usuario.
* Extraer información relevante de las consultas.
* Clasificar posibles problemas de red.
* Analizar datos obtenidos de la conexión.
* Identificar patrones asociados con diferentes problemas.
* Generar un diagnóstico basado en los datos disponibles.
* Proporcionar recomendaciones de solución.
* Generar respuestas en lenguaje natural.

El aprendizaje automático será utilizado para entrenar un modelo capaz de relacionar diferentes características de una red con posibles estados o problemas.

Por ejemplo, características como:

* Latencia.
* Pérdida de paquetes.
* Tiempo de respuesta.
* Disponibilidad de conexión.
* Velocidad de transferencia.
* Estado de determinados servicios.

podrán utilizarse como datos de entrada para el análisis.

La IA no tendrá control ilimitado sobre el equipo o la red. Las acciones que puedan modificar la configuración del sistema deberán estar controladas y validadas por la aplicación.

---

# Arquitectura general

```text
                         USUARIO
                            │
                            ▼
                  ┌─────────────────┐
                  │ Lenguaje Natural│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Procesamiento de│
                  │     consulta    │
                  └────────┬────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │ Sistema de diagnóstico   │
              │        inteligente       │
              └────────────┬─────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      ┌───────────────┐         ┌────────────────┐
      │ Datos de red  │         │ Modelo de      │
      │               │         │ Machine        │
      │ Ping          │         │ Learning       │
      │ Latencia      │         │                │
      │ Paquetes      │         │ Clasificación  │
      │ Conectividad  │         │ de problemas   │
      └───────┬───────┘         └───────┬────────┘
              │                         │
              └────────────┬────────────┘
                           ▼
                  ┌─────────────────┐
                  │   Diagnóstico   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Recomendaciones │
                  └─────────────────┘
```

---

# Componentes principales

### Interfaz de usuario

Permitirá al usuario introducir consultas relacionadas con problemas de red y visualizar los resultados del diagnóstico.

### Procesamiento de lenguaje natural

Será responsable de analizar las consultas escritas por el usuario e identificar la intención y los datos relevantes de cada solicitud.

### Módulo de administración de red

Se encargará de obtener información de la red y realizar diferentes pruebas, como:

* Ping.
* Latencia.
* Pérdida de paquetes.
* Comprobación de conectividad.
* Información básica de la interfaz de red.

### Módulo de Inteligencia Artificial

Analizará los datos obtenidos de la red y utilizará un modelo de aprendizaje automático para identificar posibles problemas.

### Módulo de diagnóstico

Combinará la información obtenida de la red con los resultados del modelo de IA para generar un diagnóstico.

### Módulo de recomendaciones

Generará recomendaciones relacionadas con el problema detectado, explicando de forma sencilla qué podría estar ocurriendo y qué comprobaciones puede realizar el usuario.

---

# Tecnologías

| Área                              | Tecnología                         |
| --------------------------------- | ---------------------------------- |
| Lenguaje principal                | Python                             |
| Inteligencia Artificial           | Scikit-learn                       |
| Procesamiento de datos            | Pandas                             |
| Procesamiento de lenguaje natural | Python + NLP                       |
| Administración de red             | Herramientas y librerías de Python |
| Interfaz                          | Streamlit                          |
| Machine Learning                  | Modelos de clasificación           |
| Control de versiones              | Git + GitHub                       |
| Documentación                     | Markdown                           |

> Las tecnologías podrán modificarse durante el desarrollo si se encuentra una alternativa que se adapte mejor a los requerimientos del proyecto.

---

# Estructura del proyecto

```text
hermes/
│
├── data/
│   └── dataset.csv
│
├── models/
│   └── modelo_diagnostico.pkl
│
├── src/
│   ├── diagnostico.py
│   ├── machine_learning.py
│   ├── network.py
│   └── nlp.py
│
├── tests/
│   └── test_diagnostico.py
│
├── app.py
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

### Descripción de las carpetas

**`data/`**
Contendrá los datos utilizados para entrenar y probar el modelo de aprendizaje automático.

**`models/`**
Contendrá los modelos de Machine Learning entrenados.

**`src/`**
Contendrá los módulos principales del sistema.

**`tests/`**
Contendrá las pruebas utilizadas para verificar el funcionamiento del sistema.

**`app.py`**
Será el punto de entrada de la aplicación.

**`requirements.txt`**
Contendrá las librerías necesarias para ejecutar el proyecto.

**`.env.example`**
Servirá como ejemplo para configurar variables de entorno sin publicar información sensible.

---

# Seguridad

La seguridad será considerada durante todo el desarrollo del proyecto.

Se contemplarán principalmente:

* Validación de entradas del usuario.
* Protección de información sensible.
* Uso de variables de entorno.
* No almacenar credenciales directamente en el código.
* Control de las acciones que puede ejecutar el sistema.
* Evitar la ejecución de comandos arbitrarios introducidos por el usuario.
* Validación de los datos utilizados por el sistema.
* Registro de errores y eventos importantes.
* Separación entre las funciones de diagnóstico y las funciones que puedan modificar la configuración de red.

El sistema estará diseñado principalmente para **observar, analizar y diagnosticar** la red. Las acciones que puedan modificar configuraciones deberán estar controladas explícitamente.

---

# Alcance inicial (MVP)

La primera versión funcional del proyecto permitirá:

1. Recibir consultas del usuario mediante lenguaje natural.
2. Identificar la intención de la consulta.
3. Realizar pruebas básicas de conectividad.
4. Obtener información relacionada con la red.
5. Medir parámetros como latencia y pérdida de paquetes.
6. Procesar los datos obtenidos.
7. Utilizar un modelo de Machine Learning para clasificar posibles problemas.
8. Generar un diagnóstico.
9. Mostrar recomendaciones básicas al usuario.
10. Presentar los resultados mediante una interfaz sencilla.

---

# Ejemplo de funcionamiento

El usuario podría escribir:

```text
Mi Internet está muy lento y tengo mucho lag.
```

El sistema procesará la consulta y realizará las pruebas necesarias.

```text
Consulta del usuario
        ↓
Identificación de intención
        ↓
Pruebas de red
        ↓
Obtención de datos
        ↓
Modelo de Machine Learning
        ↓
Clasificación del problema
        ↓
Diagnóstico
        ↓
Recomendaciones
```

El resultado podría ser:

```text
Diagnóstico:

Se detectó una latencia elevada durante las pruebas
realizadas.

Posible causa:
Problemas de conectividad o congestión de la red.

Recomendaciones:
- Verificar la conexión con el router.
- Realizar una nueva prueba de latencia.
- Comprobar si otros dispositivos presentan el mismo problema.
```

---

# Organización del equipo

El proyecto será desarrollado por dos integrantes. Las responsabilidades se dividirán en dos áreas principales para mantener una distribución equilibrada del trabajo.

| Integrante   | Área principal   | Responsabilidades                                                                                                        |
| ------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------ |
| jose         | IA + Backend     | Machine Learning, procesamiento de lenguaje natural, lógica de diagnóstico y desarrollo de módulos principales en Python |
| V            | Redes + Interfaz | Recolección de datos de red, pruebas de conectividad, interfaz de usuario, integración y pruebas                         |

Aunque cada integrante tendrá un área principal, ambos participarán en:

* Integración de los módulos.
* Pruebas del sistema.
* Documentación.
* Revisión del código.
* Seguridad.
* Control de versiones mediante Git y GitHub.
* Preparación de la presentación del proyecto.

Los nombres y responsabilidades específicas podrán actualizarse posteriormente.

---

# Metodología

El proyecto será desarrollado de manera incremental, comenzando por un MVP funcional y agregando nuevas características conforme avance el desarrollo.

El código será administrado mediante **Git y GitHub**, utilizando repositorios, commits y ramas para mantener un historial organizado del proyecto.

El desarrollo se dividirá en diferentes etapas:

1. Análisis del problema.
2. Diseño del sistema.
3. Preparación de datos.
4. Desarrollo del módulo de red.
5. Desarrollo del procesamiento de lenguaje natural.
6. Entrenamiento del modelo de Machine Learning.
7. Integración de los componentes.
8. Desarrollo de la interfaz.
9. Pruebas.
10. Documentación.
11. Presentación del proyecto.

---

# Propósito académico

HERMES busca demostrar la aplicación práctica de conceptos de Inteligencia Artificial y aprendizaje automático en un problema relacionado con la administración y diagnóstico de redes.

El proyecto integra diferentes áreas de desarrollo de software para construir una solución funcional capaz de interpretar consultas en lenguaje natural, analizar información de una red y utilizar modelos de Inteligencia Artificial para apoyar el proceso de diagnóstico.

Además, el proyecto permitirá aplicar conocimientos de programación en Python, procesamiento de datos, Machine Learning, redes de computadoras, desarrollo de interfaces, pruebas y control de versiones mediante Git y GitHub.
