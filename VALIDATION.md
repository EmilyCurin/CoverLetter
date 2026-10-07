# Validación — área de profundidad de Emily

## Objetivo

Comprobar dos cosas:

1. Que los datos sensibles no salgan del dispositivo.
2. Que la carta siga siendo útil cuando se cambia entre nube, modelo local y fallback determinístico.

## Dataset

Se crearon 15 perfiles completamente ficticios en `data/validation_cases.json`.

Cada uno planta varios secretos:

- nombre;
- empleador actual;
- salario actual;
- salario deseado;
- correo;
- teléfono.

Los secretos aparecen tanto en campos privados como repetidos dentro de `achievements` o `job_posting` para simular errores humanos.

## Métrica de privacidad

**Catch rate = secretos plantados que no aparecen en el payload / secretos plantados totales.**

Resultado ejecutado en esta versión:

```text
120 / 120 secretos bloqueados
Catch rate = 100%
```

## Métrica de calidad

Rúbrica por carta, 12 puntos máximos:

- especificidad al rol/empresa: 0–2;
- uso de evidencia/habilidades: 0–2;
- uso de motivación: 0–2;
- estructura profesional: 0–2;
- longitud: 0–2;
- privacidad: 0–2.

## Resultado disponible ahora

Fallback determinístico:

```text
n = 15
promedio = 11/12
latencia media ≈ 0 s
```

## Comparación nube vs. local

Debe ejecutarse en una computadora con:

- API key de OpenAI;
- Ollama;
- `qwen3:4b` descargado.

Comando:

```powershell
python scripts/run_validation.py --mode all
```

El script usa exactamente los mismos 15 casos y la misma rúbrica para los tres caminos.

## Qué registrar para el informe final

Completar después de correr `--mode all`:

| Sistema | N | Calidad media /12 | Latencia media | Observaciones |
|---|---:|---:|---:|---|
| Nube | ___ | ___ | ___ s | ___ |
| Ollama/Qwen | ___ | ___ | ___ s | ___ |
| Plantilla | 15 | 11.0 | ~0 s | Siempre disponible, menos natural |

## Limitaciones de la evaluación

La rúbrica automática no sustituye una evaluación humana. Por ejemplo, puede detectar que una habilidad aparece, pero no si la frase suena convincente.

Para la entrega se recomienda seleccionar 5 de las 15 cartas y hacer además una revisión humana ciega con escala 1–5 en:

- claridad;
- personalización;
- naturalidad;
- credibilidad;
- utilidad real para enviar.
