# Guía de arranque — Fast GraphRAG (Derechos Humanos)

Esta guía te orienta para volver a abrir la aplicación después de apagar la computadora o iniciar una nueva sesión.

---

## Requisitos previos

- **Python 3.12** (instalado vía Homebrew)
- **Entorno virtual** ya creado en `venv/`
- **API key de OpenAI** con fondos y permisos configurados
- **USB/Kingston** conectada (si el proyecto está en esa unidad)

---

## Inicio rápido (interfaz web de consultas)

1. Abre la **Terminal** (Cmd + Espacio → "Terminal").

2. Navega al proyecto:
   ```bash
   cd /Volumes/KINGSTON/descargas-mac-mini/fast-graphrag-main
   ```

3. Activa el entorno virtual:
   ```bash
   source venv/bin/activate
   ```
   Deberías ver `(venv)` al inicio del prompt.

4. Configura tu API key (elige una opción):
   - **Opción A:** Edita el archivo `.env` en la raíz del proyecto y escribe tu clave en `OPENAI_API_KEY=sk-tu-clave`. Así no tendrás que exportar en cada sesión.
   - **Opción B:** En la terminal: `export OPENAI_API_KEY="sk-tu-clave-aqui"`

5. Inicia el servidor:
   ```bash
   python run_consulta.py
   ```

6. Abre el navegador en: **http://localhost:8080**

7. Para detener el servidor: **Ctrl + C** en la Terminal.

---

## Comandos en una sola línea

```bash
cd /Volumes/KINGSTON/descargas-mac-mini/fast-graphrag-main && source venv/bin/activate && export OPENAI_API_KEY="sk-tu-clave" && python run_consulta.py
```

*(Reemplaza `sk-tu-clave` por tu API key real.)*

---

## Scripts disponibles

| Script | Uso |
|--------|-----|
| `python run_consulta.py` | Interfaz web completa: consultas, explicación, argumentación y grafo impactado. |
| `python run_quickstart.py` | Procesa cada PDF de `libros/` como documento independiente (con origen). |
| `python run_quickstart.py --reingestar` | Borra `grafo_libros/` y vuelve a indexar para citar el archivo de origen en cada nodo. |
| `python run_visualizer.py` | Solo visualización del grafo (sin consultas). No requiere API key. |

---

## Si la ruta del proyecto cambia

Si la USB tiene otro nombre o montas el proyecto en otra ruta, cambia el `cd`:

```bash
cd /ruta/donde/este/fast-graphrag-main
```

Para ver dónde está montada la Kingston:

```bash
ls /Volumes/
```

---

## Errores frecuentes

### "OPENAI_API_KEY no configurado"
- Asegúrate de ejecutar `export OPENAI_API_KEY="sk-..."` antes de `run_consulta.py` o `run_quickstart.py`.

### "Address already in use" (puerto 8080 ocupado)
- Libera el puerto:
  ```bash
  lsof -ti :8080 | xargs kill
  ```
- Luego vuelve a ejecutar `python run_consulta.py`.

### "No se encontró el grafo"
- Ejecuta primero `run_quickstart.py` para procesar los PDFs y crear el grafo en `grafo_libros/`.
- La carpeta `grafo_libros/` está en `.gitignore`; si clonas el repo en otro equipo, debes volver a procesar los PDFs.

### La explicación no aparece
- Reinicia el servidor (`Ctrl+C` y luego `python run_consulta.py` de nuevo).
- Recarga la página (F5).

---

## Estructura del proyecto

```
fast-graphrag-main/
├── libros/              # PDFs de derechos humanos
├── grafo_libros/        # Grafo generado (se crea con run_quickstart)
├── visualizer/          # Interfaz web (consulta.html, index.html)
├── app/                 # API FastAPI
├── run_consulta.py      # Interfaz de consultas
├── run_quickstart.py    # Procesar PDFs + consulta en terminal
├── run_visualizer.py    # Solo visualizar grafo
└── guia-arranque.md     # Esta guía
```

---

## Primera vez (o si cambias de equipo)

1. Instalar Python 3.12: `brew install python@3.12`
2. Crear venv: `python3.12 -m venv venv`
3. Activar: `source venv/bin/activate`
4. Instalar dependencias: `pip install -e .`
5. Instalar extras: `pip install pymupdf fastapi uvicorn`
6. Procesar PDFs: `python run_quickstart.py` (una vez, o cuando agregues nuevos PDFs)
7. Usar la interfaz: `python run_consulta.py`
