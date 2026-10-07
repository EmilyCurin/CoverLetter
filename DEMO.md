# Estrategia de demo

## Por qué la demo principal es local

La garantía “el salario actual nunca sale del dispositivo” es verdadera cuando `streamlit run app.py` se ejecuta en la computadora de la persona.

Si esta misma app Python se hospeda en Streamlit Community Cloud, el navegador envía los campos del formulario al servidor donde corre Streamlit. Eso hace que el salario ya haya salido del dispositivo antes de llegar a `src/privacy.py`.

## Opción recomendada para el entregable

1. Repo público en GitHub.
2. Video/GIF de 2–4 minutos ejecutando la app localmente con datos ficticios.
3. Link a ese video en la parte superior del README del repo.
4. Instrucciones reproducibles para ejecutar localmente.

## Si la evaluación exige una URL interactiva

Puedes publicar una versión solo para demostración con datos ficticios, pero etiqueta claramente:

```text
DEMO — USE FAKE DATA ONLY
The privacy guarantee is demonstrated by the local build and automated tests.
```

No uses datos personales reales en esa versión hospedada.
