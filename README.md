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
    └── 01_fetch.py         ← cliente que descarga y persiste los emails
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

---
## Fase 2: Limpieza de datos

En esta fase se transforman los emails de `data/raw/` en texto limpio y utilizable para el modelo.

### Objetivo

Eliminar el ruido típico del cuerpo de un email antes de pasarlo al LLM:

- HTML y entidades como `&nbsp;`
- hilos citados de respuestas anteriores
- mensajes reenviados
- firmas y cierres automáticos
- disclaimers legales
- URLs, emails y teléfonos en el cuerpo

El limpiador anonimiza los datos sensibles con placeholders:

- `<EMAIL>`
- `<PHONE>`
- `<URL>`

### Script de la fase

El punto de entrada es:

```bash
uv run python src/02_clean.py
```

Este script:

- lee todos los `*.txt` de `data/raw/`
- aplica las reglas RegEx definidas en `src/cleaning.py`
- escribe el resultado en `data/clean/`
- genera un reporte agregado en JSON

### Ejecución

Cuando ya tengas `data/raw/` generado por la Fase 1, ejecuta:

```bash
uv run python src/02_clean.py
```

También puedes indicar rutas personalizadas:

```bash
uv run python src/02_clean.py --input-dir data/raw --output-dir data/clean
```

Y si quieres guardar el reporte en otra ubicación:

```bash
uv run python src/02_clean.py --report-path data/clean/reporte_step2.json
```

### Output generado

Después de ejecutar la limpieza encontrarás:

```
data/clean/
├── msg_001.txt
├── msg_002.txt
├── ...
└── _cleaning_report.json
```

- `msg_XXX.txt` contiene la versión limpia del email.
- `_cleaning_report.json` resume lo que se eliminó o anonimizó.

Output esperado en consola:

```text
19:05:12  INFO      clean  msg_001.txt -> msg_001.txt (914 -> 222 chars)
19:05:12  INFO      clean  msg_002.txt -> msg_002.txt (462 -> 249 chars)
...
19:05:12  INFO      Cleaning report written to .../data/clean/_cleaning_report.json
19:05:12  INFO      Cleaned 10 email(s): 4623 -> 2431 chars
```

### Qué contiene `_cleaning_report.json`

El reporte guarda, para el total y para cada archivo:

- caracteres antes y después de limpiar
- bloques citados eliminados
- mensajes reenviados eliminados
- firmas o disclaimers cortados
- emails, teléfonos y URLs anonimizados
- motivo de truncado si el contenido se cortó en una firma, hilo citado o forward

Ejemplo de entrada:

```json
{
  "source_file": "msg_001.txt",
  "output_file": "msg_001.txt",
  "raw_chars": 914,
  "clean_chars": 222,
  "chars_removed": 692,
  "quoted_blocks_removed": 1,
  "forwarded_blocks_removed": 0,
  "signature_blocks_removed": 0,
  "disclaimer_blocks_removed": 0,
  "email_redactions": 1,
  "phone_redactions": 1,
  "url_redactions": 1,
  "truncated_by": "quoted_thread"
}
```

### Validación manual recomendada

Antes de seguir a la Fase 3, revisa al menos estos casos:

- `data/clean/msg_001.txt`
- `data/clean/msg_007.txt`
- `data/clean/msg_010.txt`

Comprueba que:

- se mantiene el contenido útil del email
- desaparece el ruido de firmas, hilos y disclaimers
- los datos personales quedan anonimizados
- no se pierden señales importantes como `ORDER #998822`, `ticket #5544` o `HTTP 500`

### Tests

La fase incluye pruebas básicas en:

```bash
tests/test_cleaning.py
```

Para ejecutarlas:

```bash
uv run python -m unittest discover -s tests -v
```

Estas pruebas verifican que:

- se elimina ruido típico
- se anonimizan contactos
- se conserva la estructura útil de un bug report
- se genera el reporte JSON

### Flujo completo de la fase

Si cambias los emails mock o regeneras `data/raw/`, vuelve a ejecutar:

```bash
uv run python src/01_fetch.py
uv run python src/02_clean.py
```

---
## Fase 3: Llamadas a modelo LLM
---
## Fase 4: Visualización con StreamLit
