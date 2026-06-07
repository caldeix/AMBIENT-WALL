Analiza todos los cambios pendientes en git del proyecto Financial Wall, haz commits organizados por área y sube todo a master en GitHub.

## Pasos a ejecutar

### 1. Inspeccionar cambios

Ejecuta estos comandos para ver el estado actual:
```
git status
git diff --stat HEAD
```

### 2. Agrupar por área lógica

Clasifica los archivos modificados en estas categorías (omite las que no tengan cambios):

| Categoría | Archivos |
|-----------|---------|
| **theme** | `src/ui/theme.py` |
| **ui** | `src/ui/app.py`, `src/ui/widgets/top_bar.py`, `src/ui/widgets/market_panel.py` |
| **services** | `src/services/coinmarketcap.py`, `src/services/market_data.py`, `src/services/weather.py`, `shared/config_manager.py` |
| **webapp** | cualquier archivo bajo `app-config/` |
| **config/docs** | `config.example.yaml`, `CLAUDE.md`, `README.md`, `CHANGELOG.md`, `requirements.txt`, archivos bajo `scripts/` |
| **other** | cualquier archivo que no encaje en las categorías anteriores |

### 3. Crear un commit por categoría

Para cada categoría con cambios:

```
git add <archivos de la categoría>
git commit -m "<tipo>(<scope>): <descripción en español, imperativo, máx 72 chars>"
```

Tipos de commit: `feat` (nueva funcionalidad) | `fix` (corrección de bug) | `refactor` | `chore` (mantenimiento) | `docs`

**CRÍTICO: NO incluir líneas `Co-Authored-By` ni `Co-authored-by` en ningún commit bajo ninguna circunstancia.**

Ejemplos de mensajes correctos:
- `feat(ui): añadir precio EUR bajo el header de cada chart block`
- `fix(services): corregir cálculo de rank cuando el símbolo no existe en CMC`
- `refactor(theme): unificar colores de rank badge sin distinción por tier`
- `docs(config): actualizar CLAUDE.md con estructura interna de market_panel`

### 4. Merge a master (si no estás ya en master)

Si el branch actual no es `master`:
```
git checkout master
git merge <nombre-del-branch> --no-ff -m "Merge branch '<nombre>': <resumen de los cambios>"
```

### 5. Push a GitHub

```
git push origin master
```

### 6. Resumen final

Muestra al usuario:
- Lista de commits creados con su mensaje
- Confirmación de que el push fue exitoso
- Branch final (debe ser `master`)
