---
id: apis
title: "APIs"
nav_title: "APIs"
summary: "Cómo un programa le pide datos a otro por la red: qué es una API, cómo viaja una petición HTTP, qué prometen sus métodos y sus códigos, y qué es (y qué no es) REST."
status: ready
estimated_time: 190m
tags: [apis, http, rest, crud, requests]
prerequisites: [python]
---

# APIs

**Dos secciones por ahora** · 9 páginas · unos 190 min

## En corto

- **Muchas fuentes de datos son APIs**: en vez de bajar un archivo, le pides los datos a un programa que corre en otra máquina, y te contesta por la red.
- **La primera sección enseña el protocolo de esa comunicación**: HTTP, sus métodos, sus códigos de estado, y la diferencia entre HTTP, REST y CRUD.
- **La segunda sección enseña a repartir el trabajo**: esperar, calcular, concurrencia, `asyncio`, procesos y vectorización, medidos contra un servidor local.
- **Las demás secciones se agregan aquí cuando llega su clase.**

## Las secciones

| # | Sección | Qué contesta | Sesión | Páginas | Min |
|---:|---|---|---|---:|---:|
| 1 | [[apis-y-http]] | Qué es una API, qué viaja por la red cuando la llamas y qué promete cada parte del mensaje | martes 20 de octubre, 19:00–20:30 | 4 | 90 |
| 2 | [[computo-y-concurrencia]] | Dónde pasa el tiempo, qué es concurrente, paralelo y asíncrono, y qué estrategia elegir con una medición | martes 27 de octubre, 19:00–20:30 | 5 | 100 |
