# Guía corta para Emily — cómo explicar y demostrar el proyecto

## La idea en una frase

> Mi aplicación usa la nube cuando necesita mejor calidad de redacción, pero la privacidad se decide localmente con reglas verificables; si la nube falla, usa Ollama y, si también falla, una plantilla local.

## Qué tecnología usé

- **Python:** lenguaje principal.
- **Streamlit:** interfaz web que corre localmente.
- **OpenAI Responses API:** generación de la carta en la nube.
- **Ollama + Qwen:** modelo local de respaldo.
- **Reglas/regex en Python:** privacidad.
- **Pytest:** pruebas automáticas.

## Por qué esto sí es split brain

No mandé toda la tarea a un solo modelo.

**Local:**
- salario actual;
- salario deseado;
- nombre/contacto;
- empleador actual;
- clasificación de qué puede salir;
- redacción de secretos;
- nota de negociación;
- fallback Ollama;
- último fallback sin modelo.

**Cloud:**
- solo redactar una mejor cover letter a partir del payload sanitizado.

## La parte de Emily

Mi profundidad fue validación y aprendizaje.

Construí 15 perfiles ficticios. En ellos planté 120 valores sensibles, incluso dentro de campos de texto libre. Los tests comprobaron que los 120 fueron detenidos antes del payload de nube.

Además comparo las cartas con una rúbrica común de 12 puntos y mido latencia. El script puede ejecutar la misma evaluación contra cloud, Ollama y la plantilla local.

## Demo de 4 minutos

### Minuto 1 — formulario

Muestra que hay dos bloques:

- 🔒 datos privados;
- datos profesionales que podrían enviarse después de ser filtrados.

Pon un salario ficticio llamativo, por ejemplo `13791`, y vuelve a escribir `Q13,791` dentro de “Achievements”.

### Minuto 2 — generación cloud

Genera la carta.

Abre el audit y muestra que el salario no aparece; debe salir `[REDACTED_MONEY]`.

Luego enseña que la nota privada sí conoce el salario.

Frase para decir:

> La IA no decide qué es privado. Esa decisión ocurre antes de la llamada, con una lista explícita y reglas que puedo probar.

### Minuto 3 — falla de nube

Desmarca cloud o quita temporalmente la API key.

Genera de nuevo con Ollama.

Frase:

> Si la nube falla, la aplicación no deja de servir: degrada a un modelo local.

### Minuto 4 — offline total

Detén Ollama y genera otra vez.

Debe aparecer `local-template`.

Frase:

> Incluso sin internet y sin modelo local, todavía entrego una carta básica. Priorizo disponibilidad sobre quedar completamente inutilizable.

## Preguntas que pueden hacerte

**¿Por qué no mandas el salario a la nube y solo le dices al modelo que no lo mencione?**  
Porque la condición no es “que no lo escriba”; es que no salga del dispositivo. Si ya se envió a la API, la privacidad falló aunque la respuesta no lo muestre.

**¿Por qué regex si tienes IA?**  
Porque una regla para proteger un salario es más predecible, barata y fácil de probar. El modelo se reserva para donde sí aporta calidad.

**¿Por qué Qwen?**  
Porque Ollama permite ejecutar modelos en la computadora y Qwen tiene versiones pequeñas adecuadas para un fallback. El modelo es configurable en `.env`.

**¿Por qué no subiste la app tal cual a Streamlit Cloud?**  
Porque entonces el formulario completo viajaría al servidor de Streamlit. Para defender que el salario queda en el dispositivo, la versión evaluada corre localmente.

**¿Tu 100% significa que nunca habrá una fuga?**  
No. Significa que en mi set de 15 casos y 120 secretos plantados, el sistema atrapó 120/120. La afirmación está limitada al set probado.

## Antes de entregar

- Crea repo público en GitHub.
- Sube el proyecto sin `.env`.
- Crea tu propia API key y no la compartas.
- Instala Ollama + `qwen3:4b`.
- Ejecuta `pytest -q`.
- Ejecuta `python scripts/run_validation.py --mode all`.
- Guarda el resultado final.
- Haz la prueba del README con otra persona y llena `DIDACTIC_TEST.md`.
- Toma capturas reales.
- Publica el artículo.
- Enlaza repo, video/demo y artículo desde el README.
