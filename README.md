# Email Pipeline

Pipeline de clasificación de emails por sentimiento y prioridad.  
Extrae emails, los limpia, los analiza con un LLM local y genera una cola de priorización interactiva.

---

## Estructura del repositorio

```
email-pipeline/
├── main.py                  ← punto de entrada único del pipeline
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── email_api_server.py  ← servidor FastAPI que simula la Gmail API
│   ├── 01_fetch.py          ← fase 1: ingesta de emails
│   ├── 02_clean.py          ← fase 2: limpieza RegEx
│   ├── cleaning.py          ← fase 2: expresiones regulares
│   ├── 03_analyze.py        ← fase 3: análisis LLM
│   ├── scoring.py           ← fase 4: scoring y priorización
│   └── dashboard.py         ← interfaz Streamlit
│
├── data/
│   ├── mock_emails.py       ← emails de prueba (estructura Gmail API)
│   ├── raw/                 ← output fase 1 (generado, no en Git)
│   ├── clean/               ← output fase 2 (generado, no en Git)
│   └── analyzed_emails.json ← output fase 3 (generado, no en Git)
│
└── tests/
    └── test_cleaning.py
```

> Los contenidos de `data/raw/`, `data/clean/` y `data/analyzed_emails.json` no se incluyen en el repositorio — se generan ejecutando el pipeline.

---

## Requisitos

- Python 3.11 o superior
- [uv](https://github.com/astral-sh/uv) — gestor de paquetes
- [Ollama](https://ollama.com) — servidor LLM local (necesario para la Fase 3)

### Instalar uv

```bash
pip install uv
```

### Instalar y configurar Ollama

Descarga Ollama desde https://ollama.com e instálalo. Luego descarga el modelo:

```bash
ollama pull gemma3:1b
```

---

## Instalación

Clona el repositorio e instala las dependencias:

```bash
git clone https://github.com/tu-usuario/email-pipeline.git
cd email-pipeline
uv sync
```

`uv sync` lee `pyproject.toml` y `uv.lock`, crea `.venv/` e instala exactamente las mismas versiones que el resto del equipo.

---

## Ejecución

El pipeline requiere dos servidores corriendo antes de ejecutar `main.py`.

**Terminal A — servidor FastAPI** (déjala abierta):

```bash
uv run uvicorn src.email_api_server:app --reload
```

**Terminal B — servidor Ollama** (déjala abierta):

```bash
ollama serve
```

**Terminal C — ejecutar el pipeline completo**:

```bash
uv run python main.py
```

Esto ejecuta las 4 fases en orden y genera todos los outputs en `data/`.

### Opciones de ejecución

```bash
uv run python main.py --only fetch     # ejecutar solo la fase 1
uv run python main.py --only clean     # ejecutar solo la fase 2
uv run python main.py --only analyze   # ejecutar solo la fase 3
uv run python main.py --only score     # ejecutar solo la fase 4
uv run python main.py --skip fetch     # todas las fases menos la 1
uv run python main.py --dashboard      # pipeline completo + abre el dashboard al finalizar
```

El flag `--dashboard` es compatible con cualquier combinación — por ejemplo `--only score --dashboard` ejecuta solo el scoring y abre el dashboard al terminar.

Para abrir el dashboard sin reruns del pipeline:

```bash
uv run streamlit run src/dashboard.py
```

---

## Fases del pipeline

### Fase 1 — Ingesta de datos

**Script:** `src/01_fetch.py`  
**Input:** API mock en `http://localhost:8000/emails`  
**Output:** `data/raw/`

Descarga los emails de la API simulada y guarda dos archivos por email:

```
data/raw/
├── msg_001.txt           ← cuerpo bruto (HTML, firmas, hilos, disclaimers)
├── msg_001.meta.json     ← metadatos extraídos
├── msg_002.txt
├── msg_002.meta.json
└── ...
```

Estructura de cada `.meta.json`:

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

Los `.txt` contienen ruido intencionado (HTML, firmas, hilos citados) para que la Fase 2 lo procese.

---

### Fase 2 — Limpieza de datos

**Script:** `src/02_clean.py`  
**Input:** `data/raw/*.txt`  
**Output:** `data/clean/`

Elimina el ruido típico del cuerpo de un email mediante expresiones regulares:

- HTML y entidades (`&nbsp;`, `<div>`, etc.)
- Hilos citados de respuestas anteriores (`> On Mon...`)
- Mensajes reenviados (`---------- Forwarded message`)
- Firmas y cierres automáticos (`-- `, `Sent from my iPhone`)
- Disclaimers legales
- Anonimiza datos sensibles con placeholders: `<EMAIL>`, `<PHONE>`, `<URL>`

Output generado:

```
data/clean/
├── msg_001.txt              ← texto limpio y anonimizado
├── msg_002.txt
├── ...
└── _cleaning_report.json    ← reporte de lo eliminado por archivo
```

Ejemplo de entrada en `_cleaning_report.json`:

```json
{
  "source_file": "msg_001.txt",
  "raw_chars": 914,
  "clean_chars": 222,
  "quoted_blocks_removed": 1,
  "email_redactions": 1,
  "phone_redactions": 1,
  "url_redactions": 1
}
```

---

### Fase 3 — Análisis LLM

**Script:** `src/03_analyze.py`  
**Input:** `data/clean/*.txt` + `data/raw/*.meta.json`  
**Output:** `data/analyzed_emails.json`  
**Requiere:** Ollama corriendo con el modelo `gemma3:1b`

Envía cada email limpio al modelo LLM local y extrae información estructurada:

- Sentimiento (`very_negative`, `negative`, `neutral`, `positive`, `very_positive`)
- Tema principal (`Complaint`, `Bug`, `New Feature Request`, `Sales`, etc.)
- Resumen en una frase
- Nivel de confianza del modelo (0–1)

Ejemplo de entrada en `analyzed_emails.json`:

```json
{
  "id": "msg_001",
  "sentiment": "very_negative",
  "sentiment_score": 0.9,
  "topic": "Complaint",
  "confidence": 0.95,
  "date_parsed": "2026-02-20T09:15:00",
  "subject": "URGENT: REFUND REQUEST - ORDER #998822",
  "from_addr": "angry.customer@example.com",
  "summary": "Cliente exige reembolso tras múltiples solicitudes ignoradas."
}
```

---

### Fase 4 — Scoring y priorización

**Script:** `src/scoring.py`  
**Input:** `data/analyzed_emails.json`  
**Output:** `data/scored_emails.json`

Calcula una puntuación de urgencia para cada email con la fórmula:

```
score = sentiment_w + topic_w + min(age_days × age_mult, max_age) − (1 − confidence) × 5
```

| Componente | Qué mide |
|---|---|
| `sentiment_w` | Tono emocional (`very_negative` = 40 pts, `positive` = 5 pts) |
| `topic_w` | Categoría (`Complaint` = 30 pts, `Bug` = 25 pts, `Feature Request` = 10 pts) |
| `age_bonus` | Días sin respuesta × 0.5, máximo 20 pts |
| `conf_penalty` | Penalización si el LLM tiene baja confianza |

Clasificación por tier según puntuación total:

| Tier | Umbral |
|---|---|
| CRITICAL | ≥ 70 |
| HIGH | ≥ 45 |
| MEDIUM | ≥ 25 |
| LOW | < 25 |

---

## Dashboard

Puedes lanzar el dashboard de dos formas:

```bash
# al terminar el pipeline automáticamente
uv run python main.py --dashboard

# directamente, sin reruns del pipeline
uv run streamlit run src/dashboard.py
```

Muestra métricas resumen por tier, la cola de priorización ordenada por puntuación, y sliders interactivos para modificar los pesos en tiempo real. Al mover los sliders el ranking se recalcula al instante — por ejemplo, subir el peso de "Bug" por encima de "Complaint" reordena la cola en consecuencia.

---

## Añadir emails de prueba

Edita `data/mock_emails.py` y copia el bloque comentado al final del archivo. El servidor recoge los cambios automáticamente gracias a `--reload`. Luego vuelve a ejecutar el pipeline:

```bash
uv run python main.py
```

---

## Tests

```bash
uv run python -m unittest discover -s tests -v
```

---

## Dependencias

| Paquete | Uso |
|---|---|
| `fastapi` | Servidor HTTP que simula la Gmail API |
| `uvicorn` | Servidor ASGI que arranca FastAPI |
| `requests` | Cliente HTTP para la Fase 1 |
| `streamlit` | Dashboard interactivo |
| `pandas` | Manipulación de datos tabulares |
