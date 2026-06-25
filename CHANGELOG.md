# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [1.0.0] - 2026-06-25

### Adicionado

- Script inicial `merge_gtfs.py` para união de dois arquivos GTFS (base e secundário).
- Prevenção de colisão de chaves primárias (IDs de trips, routes, stops, etc.) através do sufixo `_new_gtfs`.
- Filtro inteligente por `route_short_name` para capturar apenas rotas que não existam no GTFS base.
- Filtro em cascata para `trips.txt`, `stop_times.txt`, `stops.txt`, `shapes.txt`, `calendar.txt`, `calendar_dates.txt` e `agency.txt`.
- Adição de arquivos de documentação (`README.md`, `CHANGELOG.md`) e controle de dependências (`requirements.txt`).
