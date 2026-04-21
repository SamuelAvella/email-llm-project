# Email Pipeline 
Pipeline de clasificación de emails por sentimiento y prioridad.  
---
## Estructura del proyecto
```
email-pipeline/
├── .gitignore
├── README.md
├── pyproject.toml          ← dependencias del proyecto
├── uv.lock                 ← versiones exactas (generado automáticamente)
│
└── src/
    ├── __init__.py
    ├── config.py           ← URLs, rutas y constantes centralizadas
    ├── mock_emails.py      ← base de datos mock (estructura Gmail API)
    ├── email_api_server.py ← servidor FastAPI que simula la Gmail API
    ├── 01_fetch.py         ← cliente que descarga y persiste los emails
    ├── scoring.py          ← fórmula de scoring de urgencia
    └── dashboard.py        ← dashboard Streamlit con cola de priorización
```
> `data/` no se incluye en el repositorio — se genera ejecutando `01_fetch.py`.
---
## Requisitos
- Python 3.11 o superior
- [uv](https://github.com/astral-sh/uv) — gestor de paquetes
Instalar `uv` si no lo tienes:
```bash
pip install uv
```
---
## Instalación
Clona el repositorio e instala las dependencias con un solo comando:
```bash
git clone https://github.com/tu-usuario/email-pipeline.git
cd email-pipeline
uv sync
```
`uv sync` lee `pyproject.toml` y `uv.lock`, crea el entorno virtual `.venv/` e instala exactamente las mismas versiones que el resto del equipo.
---
## Fase 1: Ingesta de datos
Necesitas **dos terminales abiertas** simultáneamente.
### Terminal A — levantar el servidor
```bash
uv run uvicorn src.email_api_server:app --reload
```
El servidor queda bloqueado escuchando en `http://localhost:8000`. No cierres esta terminal.
Puedes verificar que está operativo abriendo en el navegador:
```
http://localhost:8000/health
```
Deberías ver:
```json
{"status": "ok", "emails_available": 10}
```
### Terminal B — ejecutar el fetch
Con el servidor corriendo, abre una segunda terminal y ejecuta:
```bash
uv run python src/01_fetch.py
```
Output esperado:
```
18:22:58  INFO  Directorio de salida: .../data/raw
18:22:58  INFO  GET http://localhost:8000/emails  params={'limit': 50, 'skip': 0}
18:22:58  INFO  Recibidos 10 emails (total: 10)
18:22:58  INFO    ✔  msg_001  →  msg_001.txt  |  msg_001.meta.json
18:22:58  INFO    ✔  msg_002  →  msg_002.txt  |  msg_002.meta.json
...
18:22:58  INFO  Ingesta completada: 10/10 emails guardados en 'data/raw'
```
---
## Output generado
Después de ejecutar el fetch encontrarás en `data/raw/` dos archivos por cada email:
```
data/raw/
├── msg_001.txt           ← cuerpo bruto del email (con HTML, firmas, hilos)
├── msg_001.meta.json     ← metadatos extraídos
├── msg_002.txt
├── msg_002.meta.json
└── ...
```
**Estructura de cada `.meta.json`:**
```json
{
  "id": "msg_001",
  "thread_id": "msg_001",
  "from": "angry.customer@example.com",
  "subject": "URGENT: REFUND REQUEST - ORDER #998822",
  "date": "Thu, 20 Feb 2026 09:15:00 +0000",
  "label_ids": ["INBOX", "UNREAD"],
  "internal_date_ms": 1740038100000
}
```
Los archivos `.txt` contienen el cuerpo sin procesar, incluyendo HTML, firmas, hilos de conversación y disclaimers — ruido intencionado para que la Fase 2 (limpieza RegEx) lo procese.
---
## Añadir emails de prueba
Edita `src/mock_emails.py` y copia el bloque comentado al final del archivo.  
El servidor recoge los cambios automáticamente gracias a `--reload`.  
Vuelve a ejecutar `01_fetch.py` para regenerar `data/raw/`.
---
## Dependencias
| Paquete | Uso |
|---|---|
| `fastapi` | Servidor HTTP que simula la Gmail API |
| `uvicorn` | Servidor ASGI que arranca FastAPI |
| `requests` | Cliente HTTP para hacer el GET desde `01_fetch.py` |
| `streamlit` | Dashboard interactivo para la cola de priorización |
| `pandas` | Manipulación de datos tabulares en el dashboard |
---
## Fase 2: Limpieza de datos
---
## Fase 3: Llamadas a modelo LLM
---
## Fase 4: Scoring + Dashboard

### Fórmula de urgencia

Cada email recibe una puntuación calculada con:

```
score = sentiment_w + topic_w + min(age_days × age_mult, max_age) − (1 − confidence) × 5
```

| Componente | Qué mide | Por qué |
|---|---|---|
| `sentiment_w` | Tono emocional del email | Un cliente enfadado (`very_negative` = 40 pts) necesita atención antes que uno contento (`positive` = 5 pts) |
| `topic_w` | Categoría del email | Una queja (30 pts) o un bug (25 pts) bloquean al usuario; un feature request (10 pts) puede esperar |
| `age_bonus` | Días sin respuesta × 0.5 (máx. 20) | Un email ignorado durante días se vuelve más urgente, pero con tope para que los muy antiguos no dominen |
| `conf_penalty` | Confianza del LLM | Si el modelo no está seguro de su análisis, restamos puntos para no priorizar datos poco fiables |

Según la puntuación total, cada email se clasifica en un tier:

| Tier | Umbral |
|---|---|
| 🔴 CRITICAL | ≥ 70 |
| 🟠 HIGH | ≥ 45 |
| 🟡 MEDIUM | ≥ 25 |
| 🟢 LOW | < 25 |

### Ejecutar el scoring

```bash
python src/scoring.py
```

Genera `data/scored_emails.json` con los emails ordenados por urgencia.

### Lanzar el dashboard

```bash
streamlit run src/dashboard.py
```

El dashboard muestra:
- Métricas resumen por tier (cuántos emails hay en cada nivel)
- Cola de priorización ordenada por puntuación
- Desglose individual de cada email (cómo se compone su score)
- Sliders interactivos en la barra lateral para modificar todos los pesos

**Demo clave:** al mover los sliders, el ranking se recalcula en tiempo real. Por ejemplo, si subes el peso de "Bug" por encima de "Complaint", los emails de bugs suben en la cola. Si pones el multiplicador de edad a 0, los emails antiguos pierden su bonus.