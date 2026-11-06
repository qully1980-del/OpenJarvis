"""Prepara una carpeta de documentos para la base de conocimiento de OpenJarvis.

El indexador de OpenJarvis (`jarvis memory index`) lee bien Markdown, texto y
PDF, pero no Word/Excel/PowerPoint. Este script:

  1. Convierte cada documento a Markdown (Word, Excel, PowerPoint, PDF y HTML
     con MarkItDown; scripts y texto tal cual).
  2. Tapa posibles secretos (contraseñas, secretos de cliente, tokens, JWT,
     bloques PEM y base64 largos) y excluye certificados, comprimidos e imágenes.
  3. Omite versiones antiguas (subcarpetas «Archivo», copias .BAK, _tmp).
  4. Repite el nombre del proyecto y del documento en cada fragmento para que
     la búsqueda por palabras encuentre el proyecto correcto.

El resultado queda en ~/.openjarvis/knowledge/<nombre>. Después, indexa:
    jarvis memory index "%USERPROFILE%\\.openjarvis\\knowledge\\<nombre>"

Uso:
    uv run --no-project --python 3.13 --with "markitdown[docx,xlsx,pptx,pdf]" ^
        python extras\\windows\\indexar-documentos.py "C:\\ruta\\a\\tus\\documentos" --nombre trabajo

Cada subcarpeta de primer nivel se trata como un «proyecto». Nada sale del
equipo: la conversión es local.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

_args = argparse.ArgumentParser(description=__doc__.splitlines()[0])
_args.add_argument("origen", help="Carpeta con tus documentos")
_args.add_argument("--nombre", default="documentos", help="Nombre de la colección (carpeta de salida)")
_ARGS = _args.parse_args()

ORIGEN = Path(_ARGS.origen).expanduser().resolve()
DESTINO = Path.home() / ".openjarvis" / "knowledge" / _ARGS.nombre
OFFICE = {".docx", ".xlsx", ".pptx", ".pdf", ".html", ".htm"}
TEXTO = {".md", ".txt", ".csv"}
CODIGO = {".ps1", ".psm1", ".sh", ".py", ".json", ".yml", ".yaml", ".xml", ".sql"}
# Nunca se indexan: certificados/claves, comprimidos, imágenes y perfiles MDM.
EXCLUIR = {".pfx", ".p12", ".pem", ".key", ".cer", ".crt", ".zip", ".7z", ".rar",
           ".png", ".jpg", ".jpeg", ".gif", ".mobileconfig", ".exe", ".msi"}
MAX_CHARS = 200_000  # por documento, para no inflar el índice con informes enormes

# Patrones de secretos: se sustituye el valor, se conserva el nombre.
SECRETOS = [
    # clave = "valor" / clave: valor  (secret, password, token, apikey...)
    (re.compile(r'(?i)((?:client_?secret|secret|password|passwd|pwd|api[_-]?key|access[_-]?token|'
                r'refresh[_-]?token|bearer|sas[_-]?token|connection[_-]?string|shared[_-]?secret)'
                r'\s*["\']?\s*[:=]\s*)(["\']?)([^\s"\';,]{4,})(\2)'), r'\1\2[REDACTADO]\4'),
    # ConvertTo-SecureString "texto" -AsPlainText
    (re.compile(r'(?i)(ConvertTo-SecureString\s+(?:-String\s+)?)(["\'])(.+?)(\2)'), r'\1\2[REDACTADO]\4'),
    # Cabeceras Authorization: Bearer xxx
    (re.compile(r'(?i)(Bearer\s+)[A-Za-z0-9\-_\.=]{20,}'), r'\1[REDACTADO]'),
    # Bloques PEM
    (re.compile(r'-----BEGIN [A-Z ]+-----[\s\S]+?-----END [A-Z ]+-----'), '[BLOQUE DE CLAVE/CERTIFICADO REDACTADO]'),
    # JWT
    (re.compile(r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}'), '[JWT REDACTADO]'),
    # URIs data: (imágenes incrustadas) y bloques base64 largos: certificados
    # PFX incrustados en scripts, ficheros comprimidos, logotipos... Nunca aportan
    # al índice y pueden contener claves privadas.
    (re.compile(r'data:[a-z]+/[a-z0-9.+\-]+;base64,[A-Za-z0-9+/=]+'), '[DATOS INCRUSTADOS OMITIDOS]'),
    (re.compile(r'[A-Za-z0-9+/]{120,}={0,2}'), '[BLOQUE BASE64 OMITIDO]'),
    # Secretos de cliente de Entra ID (formato xxx~xxxx...)
    (re.compile(r'\b[A-Za-z0-9_\-\.]{3}\dQ~[A-Za-z0-9_\-\.~]{30,}\b'), '[SECRETO ENTRA REDACTADO]'),
]


def tapar(texto: str) -> tuple[str, int]:
    total = 0
    for patron, reemplazo in SECRETOS:
        texto, n = patron.subn(reemplazo, texto)
        total += n
    return texto, total


def leer_texto(ruta: Path) -> str:
    datos = ruta.read_bytes()
    for cod in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return datos.decode(cod)
        except UnicodeError:
            continue
    return datos.decode("utf-8", errors="replace")


def main() -> int:
    from markitdown import MarkItDown

    md = MarkItDown()
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)

    ok = omitidos = fallos = tapados = 0
    for ruta in sorted(ORIGEN.rglob("*")):
        if not ruta.is_file() or ruta.name.startswith(("~$", ".")):
            continue
        ext = ruta.suffix.lower()
        rel = ruta.relative_to(ORIGEN)
        # Versiones antiguas y temporales: duplican contenido y confunden al
        # buscador (subcarpetas "Archivo", copias .BAK, ficheros _tmp).
        antiguo = any(p.lower() == "archivo" for p in rel.parts[:-1]) or \
            ".bak" in ruta.name.lower() or ruta.name.lower().startswith("_tmp")
        if antiguo or ext in EXCLUIR or ext not in OFFICE | TEXTO | CODIGO:
            omitidos += 1
            continue
        try:
            if ext in OFFICE:
                cuerpo = md.convert(str(ruta)).text_content or ""
            elif ext in CODIGO:
                lang = {".ps1": "powershell", ".psm1": "powershell", ".sh": "bash", ".py": "python"}.get(ext, "")
                cuerpo = f"```{lang}\n{leer_texto(ruta)}\n```"
            else:
                cuerpo = leer_texto(ruta)
        except Exception as exc:  # noqa: BLE001
            print(f"  [fallo] {rel}: {exc.__class__.__name__}: {str(exc)[:120]}")
            fallos += 1
            continue

        cuerpo = cuerpo.strip()
        if len(cuerpo) < 20:
            omitidos += 1
            continue
        cuerpo, n = tapar(cuerpo[:MAX_CHARS])
        tapados += n
        proyecto = rel.parts[0] if len(rel.parts) > 1 else "(raíz)"
        cabecera = (
            f"# {ruta.stem}\n\n"
            f"- Proyecto: {proyecto}\n"
            f"- Archivo original: {ruta}\n"
            f"- Tipo: {ext.lstrip('.')}\n\n"
        )
        # El índice es por palabras y trocea en fragmentos de ~512 tokens: se
        # repite una línea con el proyecto y el archivo cada ~1.400 caracteres
        # para que cada fragmento "sepa" a qué proyecto pertenece.
        etiqueta = f"[Proyecto: {proyecto} · Documento: {ruta.stem}]"
        bloques, actual = [], ""
        for parrafo in cuerpo.split("\n\n"):
            if len(actual) + len(parrafo) > 1400 and actual:
                bloques.append(actual)
                actual = ""
            actual += parrafo + "\n\n"
        if actual:
            bloques.append(actual)
        cuerpo = ("\n" + etiqueta + "\n\n").join(b.rstrip() + "\n" for b in bloques)
        salida = DESTINO / rel.with_suffix(rel.suffix + ".md")
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(cabecera + cuerpo + "\n", encoding="utf-8")
        ok += 1

    print(f"\nConvertidos: {ok}   Omitidos: {omitidos}   Fallos: {fallos}   Secretos tapados: {tapados}")
    print(f"Resultado en: {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
