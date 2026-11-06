# Política de seguridad

## Comunicar una vulnerabilidad

**No abras un issue público** para comunicar una vulnerabilidad.

- **Vulnerabilidades de este fork**, como el motor Claude Code, el lanzador de Windows, el indexador de documentos o los scripts de `extras/windows/`: comunícalas de forma privada desde la pestaña **Security → Report a vulnerability** de este repositorio.
- **Vulnerabilidades del resto de OpenJarvis**: comunícalas al [proyecto oficial](https://github.com/open-jarvis/OpenJarvis/security).

Incluye, si puedes:
- Una descripción del problema y de su impacto.
- Los pasos para reproducirlo.
- La versión o el commit afectado.

Responderemos lo antes posible y te mantendremos al tanto de la corrección.

## Versiones con soporte

Solo recibe correcciones la última versión de la rama `es-aurora`.

## Consideraciones de seguridad de esta edición

- **Servidor local.** La configuración de ejemplo escucha solo en `127.0.0.1` y usa el perfil de seguridad `personal`. No lo expongas a la red sin una clave de API (`jarvis auth generate-key`).
- **Motor Claude Code.** Se ejecuta sin herramientas ni servidores MCP, sin cargar los ajustes ni el `CLAUDE.md` del usuario y en una carpeta vacía propia. Elimina `ANTHROPIC_API_KEY` del entorno. Aun así, **los mensajes y los fragmentos de documentos que se añaden a la pregunta se envían a Anthropic**.
- **Indexador de documentos.** Tapa los patrones de secretos más habituales y excluye certificados, comprimidos e imágenes, pero **no garantiza detectarlo todo**. Revisa la carpeta de salida antes de usar el motor Claude con documentos sensibles.
- **Datos personales.** Tu índice, tu configuración y tus archivos de persona se guardan en `%USERPROFILE%\.openjarvis` y nunca forman parte del repositorio. No los subas.
