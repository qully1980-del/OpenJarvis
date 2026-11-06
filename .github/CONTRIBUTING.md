# Cómo contribuir

¡Gracias por tu interés! Este repositorio es un **fork** de [open-jarvis/OpenJarvis](https://github.com/open-jarvis/OpenJarvis) que añade la edición en castellano para Windows. Antes de empezar, conviene saber dónde encaja cada contribución.

---

## ¿Aquí o en el proyecto oficial?

| Tu contribución trata de… | Dónde enviarla |
|---|---|
| Traducción al castellano (`frontend/src/i18n/es.ts`) | **Aquí** |
| Tema oscuro «Aurora» (`frontend/src/styles/aurora.css`) | **Aquí** |
| Motor Claude Code y selector Local/Claude | **Aquí** |
| Extras de Windows: app de escritorio, indexador, noticias, actualizador, plantillas (`extras/windows/`) | **Aquí** |
| Documentación en castellano (`.github/`) | **Aquí** |
| Cualquier otra parte de OpenJarvis: agentes, motores, herramientas, evaluaciones, servidor… | **[Proyecto oficial](https://github.com/open-jarvis/OpenJarvis/blob/main/CONTRIBUTING.md)** |

Mantener este fork cerca del original es una prioridad. Por eso **evitamos modificar archivos del proyecto oficial**: los cambios van en archivos nuevos y, si no hay más remedio, en una o dos líneas bien localizadas.

---

## Buenas primeras contribuciones

- Textos de la interfaz que sigan en inglés: añádelos al diccionario de `es.ts`.
- Correcciones de traducción, erratas o mejoras de la documentación.
- Informes de errores con pasos para reproducirlos en Windows.
- Nuevas fuentes RSS comprobadas para `extras/windows/configurar-noticias.py`.
- Patrones de secretos que el indexador debería tapar y no tapa.

---

## Preparar el entorno

Sigue la [guía de instalación](README.md#instalación-en-windows). En resumen:

```powershell
git clone -b es-aurora https://github.com/qully1980-del/OpenJarvis.git
cd OpenJarvis
git remote add upstream https://github.com/open-jarvis/OpenJarvis.git
uv sync --extra dev
cd frontend; npx -y npm@11 ci; cd ..
```

Para trabajar en la interfaz con recarga en caliente, ejecuta `jarvis serve` en una terminal y `npm run dev` (dentro de `frontend/`) en otra.

### Hooks de pre-commit

```powershell
uv run pre-commit install
```

Ejecutan [Ruff](https://docs.astral.sh/ruff/) en cada commit. Si fallan, corrige los avisos y vuelve a hacer commit.

---

## Proponer cambios

- **Cambios pequeños** (traducciones, erratas, ajustes de estilo, correcciones sencillas): abre directamente una pull request.
- **Cambios mayores** (nuevas funciones, cambios en el motor Claude Code, nuevas dependencias): **abre primero un issue** para comentar el enfoque.

### Antes de enviar una pull request

1. Ejecuta las pruebas:
   ```powershell
   uv run pytest tests/ -v
   ```
2. Ejecuta el linter y el formateador:
   ```powershell
   uv run ruff check src/ tests/
   uv run ruff format --check src/ tests/
   ```
3. Si tocas la interfaz, comprueba que compila:
   ```powershell
   cd frontend; npm run build
   ```
4. Si tocas `extras/windows/`, pruébalo en Windows y describe cómo en la pull request.
5. **Nunca incluyas datos personales, de clientes ni secretos**: ni en el código, ni en capturas, ni en ejemplos.

### Mensajes de commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/es/), con la descripción en castellano:

```
feat(i18n): traducir el panel de agentes
fix(windows): detener el servidor al cerrar la última ventana
docs: aclarar la instalación de Build Tools
style(aurora): mejorar el contraste del texto secundario
```

La primera línea debe tener menos de 72 caracteres. Enlaza los issues relacionados (`fixes #12`).

### Qué hace buena una pull request

- **Centrada**: un cambio por pull request.
- **Probada**: con pruebas si hay código nuevo en Python, o con los pasos que seguiste para probarla.
- **Documentada**: actualiza `.github/README.md` si cambia el uso o la instalación.
- **Fácil de mantener**: no rompe la actualización automática desde el proyecto oficial (`extras/windows/actualizar.ps1`).

---

## Código de conducta

Este proyecto sigue el [Código de conducta del Pacto de Contribuyentes](CODE_OF_CONDUCT.md). Al participar, te comprometes a respetarlo.

## ¿Dudas?

- Para este fork: abre un [issue](https://github.com/qully1980-del/OpenJarvis/issues).
- Para OpenJarvis en general: usa las [Discussions del proyecto oficial](https://github.com/open-jarvis/OpenJarvis/discussions) o su [documentación](https://open-jarvis.github.io/OpenJarvis/).
