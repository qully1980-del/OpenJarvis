"""Configura el conector «Noticias / RSS» con fuentes de seguridad y Microsoft.

Uso (desde la raíz del repositorio):
    uv run python extras/windows/configurar-noticias.py

Después, en la interfaz: Fuentes de datos → Noticias / RSS → Sincronizar ahora.
Todas las fuentes se comprobaron con el propio conector de OpenJarvis.
"""

from openjarvis.connectors.news_rss import NewsRSSConnector

FUENTES = [
    ("Microsoft Security Blog", "https://www.microsoft.com/en-us/security/blog/feed/"),
    ("Microsoft 365 Roadmap", "https://www.microsoft.com/releasecommunications/api/v2/m365/rss"),
    ("Azure Updates", "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"),
    ("Intune Customer Success", "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=IntuneCustomerSuccess"),
    ("Microsoft Defender XDR Blog", "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftThreatProtectionBlog"),
    ("Practical 365", "https://practical365.com/feed/"),
    ("INCIBE-CERT Avisos", "https://www.incibe.es/incibe-cert/alerta-temprana/avisos/feed"),
    ("Una al día (Hispasec)", "https://unaaldia.hispasec.com/feed"),
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
]

if __name__ == "__main__":
    conector = NewsRSSConnector()
    conector.configure([{"name": n, "url": u} for n, u in FUENTES])
    print(f"{len(FUENTES)} fuentes configuradas. Conectado: {conector.is_connected()}")
