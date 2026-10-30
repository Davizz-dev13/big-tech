"""Países y sectores en español, con bandera."""

PAISES = {
    "United States": ("Estados Unidos", "🇺🇸"), "Taiwan": ("Taiwán", "🇹🇼"), "South Korea": ("Corea del Sur", "🇰🇷"),
    "Netherlands": ("Países Bajos", "🇳🇱"), "China": ("China", "🇨🇳"), "Germany": ("Alemania", "🇩🇪"),
    "Japan": ("Japón", "🇯🇵"), "United Kingdom": ("Reino Unido", "🇬🇧"), "France": ("Francia", "🇫🇷"),
    "Canada": ("Canadá", "🇨🇦"), "Switzerland": ("Suiza", "🇨🇭"), "India": ("India", "🇮🇳"),
    "Hong Kong": ("Hong Kong", "🇭🇰"), "Ireland": ("Irlanda", "🇮🇪"), "Israel": ("Israel", "🇮🇱"),
}

SECTORES = {
    "Technology": "Tecnología", "Communication Services": "Comunicaciones", "Consumer Cyclical": "Consumo cíclico",
    "Consumer Defensive": "Consumo básico", "Financial Services": "Finanzas", "Healthcare": "Salud",
    "Industrials": "Industria", "Energy": "Energía", "Basic Materials": "Materiales", "Real Estate": "Inmobiliario",
    "Utilities": "Servicios públicos",
}

INDUSTRIAS = {
    "Semiconductors": "Semiconductores", "Semiconductor Equipment & Materials": "Equipos para chips",
    "Software - Infrastructure": "Software e infraestructura", "Software - Application": "Software de aplicaciones",
    "Consumer Electronics": "Electrónica de consumo", "Internet Content & Information": "Internet y contenidos",
    "Internet Retail": "Comercio electrónico", "Auto Manufacturers": "Automóviles",
    "Communication Equipment": "Equipos de comunicaciones", "Entertainment": "Entretenimiento",
    "Electronic Gaming & Multimedia": "Videojuegos y multimedia", "Information Technology Services": "Servicios TI",
    "Computer Hardware": "Hardware",
}


def pais(nombre: str) -> tuple[str, str]:
    return PAISES.get(nombre, (nombre or "—", "🏳️"))


def sector(nombre: str) -> str:
    return SECTORES.get(nombre, nombre or "—")


def industria(nombre: str) -> str:
    return INDUSTRIAS.get(nombre, nombre or "")
