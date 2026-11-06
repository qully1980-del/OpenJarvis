<div align="center">

<img src="../extras/windows/app/OpenJarvis.png" width="96" alt="OpenJarvis">

# OpenJarvis · edición en castellano para Windows

**Tu asistente de IA personal y local, en castellano, con un tema oscuro rediseñado,<br>motor opcional Claude Code y lanzador de escritorio para Windows.**

Fork de [open-jarvis/OpenJarvis](https://github.com/open-jarvis/OpenJarvis) · rama `es-aurora` · Apache 2.0

</div>

---

## ¿Qué añade este fork?

| | Función | Dónde |
|---|---|---|
| 🇪🇸 | **Interfaz en castellano**: unas 670 traducciones aplicadas sin tocar los componentes originales | `frontend/src/i18n/es.ts` |
| 🎨 | **Tema oscuro «Aurora»**: índigo profundo, aurora animada, cristal y degradado frambuesa → naranja → azafrán, con tipografía IBM Plex | `frontend/src/styles/aurora.css` |
| ⚡ | **Motor Claude Code (headless)**: usa tu suscripción de Claude Code como motor opcional, sin claves de API ni gasto extra | `src/openjarvis/engine/claude_code.py` |
| 🔀 | **Selector de motor en la barra lateral**: Local (Ollama) ↔ Claude (Sonnet · Opus · Haiku) con un clic | `frontend/src/components/EngineSwitch.tsx` |
| 🪟 | **App de escritorio para Windows**: ventana propia, sin navegador ni consolas; arranca y detiene el servidor solo | `extras/windows/app/` |
| 📚 | **Indexador de documentos de Office**: convierte Word, Excel, PowerPoint y PDF, tapa secretos y prepara una base de conocimiento | `extras/windows/indexar-documentos.py` |
| 📰 | **Fuentes de noticias de seguridad y Microsoft** preconfiguradas | `extras/windows/configurar-noticias.py` |
| 🔁 | **Actualizador** que trae la última versión oficial y vuelve a aplicar estos cambios | `extras/windows/actualizar.ps1` |

Los cambios sobre el código original se reducen a **una o dos líneas** en cuatro archivos (`main.tsx`, `Sidebar.tsx`, `engine/__init__.py`, `server/cloud_router.py`). El resto son archivos nuevos, así que el fork es fácil de mantener al día.

---

## Instalación en Windows

### 1. Requisitos

```powershell
winget install --id astral-sh.uv
winget install --id Rustlang.Rustup
winget install --id Microsoft.VisualStudio.2022.BuildTools --override "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
uv python install 3.13
```

También necesitas **Git**, **Node.js 22 o superior** y **Microsoft Edge** (ya viene con Windows). Ollama lo instala el paso 2.

> **Python:** OpenJarvis necesita Python 3.10–3.13. Si tienes instalado 3.14 o superior, el `uv python install 3.13` anterior lo resuelve sin tocar tus otras versiones.

### 2. Clonar e instalar

Clona **fuera de `AppData`** (por ejemplo, en `%USERPROFILE%\OpenJarvis`):

```powershell
git clone -b es-aurora https://github.com/qully1980-del/OpenJarvis.git "$env:USERPROFILE\OpenJarvis"
cd "$env:USERPROFILE\OpenJarvis"
git remote add upstream https://github.com/open-jarvis/OpenJarvis.git

$env:OPENJARVIS_SKIP_SERVICE = '1'
powershell -ExecutionPolicy Bypass -File deploy\windows\install.ps1 -SkipService
```

El instalador oficial compila la extensión de Rust, instala Ollama y descarga el modelo `qwen3.5:2b`.

> **Si el instalador se queda parado en «Running OllamaSetup.exe /S»** cuando Ollama ya aparece en la bandeja, ciérralo con `Ctrl+C`: el resto lo hacen los pasos 3 y 4.

### 3. Interfaz

```powershell
cd frontend
npx -y npm@11 ci --no-audit --no-fund   # el proyecto exige npm 11 (npm 12 da EBADENGINE)
npm run build
cd ..
```

### 4. Configuración y accesos directos

```powershell
# Configuración en castellano (analítica desactivada, servidor solo en 127.0.0.1)
Copy-Item extras\windows\plantillas\config.example.toml "$env:USERPROFILE\.openjarvis\config.toml"

# Archivos de persona (edítalos con tus datos)
Copy-Item extras\windows\plantillas\SOUL.example.md   "$env:USERPROFILE\.openjarvis\SOUL.md"
Copy-Item extras\windows\plantillas\USER.example.md   "$env:USERPROFILE\.openjarvis\USER.md"
Copy-Item extras\windows\plantillas\MEMORY.example.md "$env:USERPROFILE\.openjarvis\MEMORY.md"

# Fuentes de noticias
uv run python extras\windows\configurar-noticias.py

# Accesos directos en el escritorio y el menú Inicio
powershell -ExecutionPolicy Bypass -File extras\windows\instalar-accesos-directos.ps1
```

Listo: abre **OpenJarvis** desde el escritorio o el menú Inicio.

---

## Uso

### App de escritorio
Al abrir el acceso directo:
1. Se arrancan Ollama y el servidor en segundo plano, sin consolas.
2. Aparece una pantalla de carga mientras arranca el servidor (unos 15–30 s).
3. Se abre la interfaz en una ventana de Edge en modo aplicación, con perfil propio, sin barra de direcciones y con su propio icono en la barra de tareas.
4. Al cerrar la ventana, se detiene el servidor.

Los registros están en `%USERPROFILE%\.openjarvis\logs\app-server.log`.

### Elegir motor: Local o Claude
En la barra lateral, **Motor de IA**:

- **Local**: tu modelo de Ollama. Es privado y funciona sin conexión. Es el modo por defecto.
- **Claude**: ejecuta `claude -p` (Claude Code en modo headless) con tu sesión de Claude Code. Elige **Sonnet** (equilibrado), **Opus** (máxima calidad) o **Haiku** (el más rápido).

El motor Claude está aislado:
- No tiene herramientas ni MCP (`--tools ""`, `--strict-mcp-config`): solo genera texto.
- No carga tus ajustes ni tu CLAUDE.md (`--setting-sources ""`) y se ejecuta en una carpeta vacía propia.
- No guarda sesiones.
- Elimina `ANTHROPIC_API_KEY` del entorno para que **nunca facture contra una clave de API**.

> ⚠️ Con Claude, tus mensajes y los fragmentos de documentos que se añadan a la pregunta **se envían a Anthropic** y consumen el límite de tu plan. Requiere tener [Claude Code](https://docs.claude.com/en/docs/claude-code) instalado y con la sesión iniciada.

### Base de conocimiento con tus documentos
El indexador original no entiende Word, Excel ni PowerPoint. Este script los convierte antes:

```powershell
uv run --no-project --python 3.13 --with "markitdown[docx,xlsx,pptx,pdf]" `
    python extras\windows\indexar-documentos.py "C:\ruta\a\tus\documentos" --nombre trabajo

jarvis memory index "$env:USERPROFILE\.openjarvis\knowledge\trabajo"
```

- Cada subcarpeta de primer nivel cuenta como un **proyecto**, y su nombre se repite en cada fragmento para que la búsqueda acierte.
- **Tapa secretos**: contraseñas, secretos de cliente de Entra ID, tokens, JWT, bloques PEM y base64 largos (por ejemplo, certificados PFX incrustados en scripts).
- **Excluye** certificados, comprimidos, imágenes y perfiles `.mobileconfig`.
- **Omite versiones antiguas**: subcarpetas `Archivo`, copias `.BAK` y archivos `_tmp`.

Para preguntas sobre tus documentos, **usa el motor Claude**: los modelos locales pequeños tienden a inventar o a confundir proyectos.

### Archivos de persona
En `%USERPROFILE%\.openjarvis\` hay tres archivos:

| Archivo | Para qué | Límite |
|---|---|---|
| `SOUL.md` | Personalidad, estilo y reglas del asistente | 4.000 caracteres |
| `USER.md` | Quién eres: puesto, especialidad, preferencias | 1.500 caracteres |
| `MEMORY.md` | Datos duraderos: proyectos, fuentes, convenciones | 2.500 caracteres |

### Actualizar
**No uses `jarvis self-update`**: en esta rama falla, porque solo hace `git pull --ff-only`. En su lugar, con OpenJarvis cerrado:

```powershell
powershell -ExecutionPolicy Bypass -File extras\windows\actualizar.ps1
```

Descarga la versión oficial, vuelve a aplicar estos cambios encima, reinstala dependencias y recompila la interfaz. Si hay conflictos, se detiene sin perder nada.

---

## Notas y problemas conocidos en Windows

- **Instalar fuera de `AppData`.** Algunas apps empaquetadas (MSIX) redirigen las escrituras en `AppData\Local` a su propia carpeta. Eso rompe la compilación de la extensión de Rust con `C1083: No se puede abrir el archivo origen`.
- **npm 12.** El frontend exige npm 11. Usa `npx -y npm@11 ci`; no hace falta cambiar tu npm global.
- **Errores `ECONNREFUSED 127.0.0.1:8000` al arrancar `jarvis gui`.** Son normales durante los 20–30 s que tarda la API. Recarga la página con `F5`.
- **Conector de Outlook.** Usa IMAP con contraseña de aplicación, y Exchange Online tiene desactivada la autenticación básica. No funciona con cuentas de Microsoft 365 de empresa.
- **Modelos `claudecode/…`.** `server/cloud_router.py` lleva una excepción para que no se traten como modelos de OpenRouter, porque contienen «/».

---

## Créditos y licencias

- **[OpenJarvis](https://github.com/open-jarvis/OpenJarvis)**: Apache License 2.0. Este fork mantiene la licencia y el aviso originales (`LICENSE`, `NOTICE`).
- **IBM Plex Sans / Mono**: SIL Open Font License 1.1 (`frontend/src/styles/fonts/LICENSE`).
- Claude y Claude Code son productos de Anthropic. Este proyecto no está afiliado a Anthropic ni al equipo de OpenJarvis.
