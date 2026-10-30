"""Qué empresas salen en la página y por qué.

Cada entrada: (símbolo en el ranking de companiesmarketcap, símbolo en Yahoo para las cuentas,
ticker que se muestra, nombre que se muestra).
"""

MAG7 = [
    ("AAPL", "AAPL", "AAPL", "Apple"),
    ("MSFT", "MSFT", "MSFT", "Microsoft"),
    ("GOOG", "GOOGL", "GOOGL", "Alphabet"),
    ("AMZN", "AMZN", "AMZN", "Amazon"),
    ("NVDA", "NVDA", "NVDA", "NVIDIA"),
    ("META", "META", "META", "Meta"),
    ("TSLA", "TSLA", "TSLA", "Tesla"),
]

# Las mayores tecnológicas del mundo por capitalización fuera de las 7 (chips y su maquinaria,
# memoria, nube y software, internet), todas metidas de lleno en el ciclo de la IA.
# TSMC, Micron y Broadcom van siempre: las pidió David.
OTRAS = [
    ("TSM", "TSM", "TSM", "TSMC"),
    ("AVGO", "AVGO", "AVGO", "Broadcom"),
    ("005930.KS", "005930.KS", "005930.KS", "Samsung"),
    ("MU", "MU", "MU", "Micron"),
    ("AMD", "AMD", "AMD", "AMD"),
    ("000660.KS", "000660.KS", "000660.KS", "SK Hynix"),
    ("ASML", "ASML", "ASML", "ASML"),
    ("PLTR", "PLTR", "PLTR", "Palantir"),
    ("TCEHY", "0700.HK", "0700.HK", "Tencent"),
    ("ORCL", "ORCL", "ORCL", "Oracle"),
    ("CSCO", "CSCO", "CSCO", "Cisco"),
    ("INTC", "INTC", "INTC", "Intel"),
    ("AMAT", "AMAT", "AMAT", "Applied Materials"),
    ("LRCX", "LRCX", "LRCX", "Lam Research"),
    ("PANW", "PANW", "PANW", "Palo Alto Networks"),
    ("SAP", "SAP", "SAP", "SAP"),
    ("NFLX", "NFLX", "NFLX", "Netflix"),
    ("BABA", "BABA", "BABA", "Alibaba"),
]

GRUPOS = [("mag7", "Las 7 magníficas", MAG7), ("otras", "Otras tecnológicas", OTRAS)]
