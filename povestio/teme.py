"""Povestio - temele de atmosferă. Fiecare temă are o variantă animată (din cod) și poate folosi
clipuri reale din broll/<tema>/*.mp4 (Pexels, Flow/Veo sau filmări proprii)."""

TEME = {
    "iarna_seara": {
        "descriere": "Seară de iarnă: fereastră, ninsoare, luminițe calde.",
        "grad_rece": [(10, 18, 40), (34, 30, 52), (70, 42, 30)],
        "grad_cald": [(28, 20, 26), (74, 44, 30), (120, 72, 38)],
        "particule": "zapada",
        "fereastra": True,
        "ghirlanda": True,
        "bokeh": "cald",
        "text": (255, 246, 232),
    },
    "seara_acasa": {
        "descriere": "Seară liniștită acasă: lumină de veioză, căldură, relaxare.",
        "grad_rece": [(22, 16, 20), (52, 34, 30), (92, 58, 36)],
        "grad_cald": [(34, 22, 20), (88, 54, 32), (140, 88, 44)],
        "particule": "praf",
        "fereastra": False,
        "ghirlanda": False,
        "bokeh": "cald",
        "text": (255, 244, 228),
    },
    "dimineata": {
        "descriere": "Dimineață luminoasă: soare blând, cafea, ordine.",
        "grad_rece": [(70, 78, 96), (150, 132, 120), (214, 170, 128)],
        "grad_cald": [(96, 90, 100), (196, 156, 120), (236, 196, 150)],
        "particule": "praf",
        "fereastra": False,
        "ghirlanda": False,
        "bokeh": "soare",
        "raze": True,
        "text": (255, 252, 244),
    },
    "natura_zori": {
        "descriere": "Natură în zori: ceață, lac, liniște.",
        "grad_rece": [(18, 30, 40), (52, 72, 80), (120, 120, 104)],
        "grad_cald": [(30, 40, 48), (92, 98, 96), (188, 160, 118)],
        "particule": "ceata",
        "fereastra": False,
        "ghirlanda": False,
        "bokeh": "rece",
        "text": (250, 250, 244),
    },
}

BOKEH = {
    "cald": [(255, 196, 120), (255, 170, 90), (255, 220, 160), (250, 150, 80), (255, 236, 200)],
    "soare": [(255, 236, 190), (255, 222, 160), (255, 248, 220), (250, 210, 150)],
    "rece": [(200, 220, 230), (230, 236, 230), (180, 200, 210), (240, 226, 200)],
}
