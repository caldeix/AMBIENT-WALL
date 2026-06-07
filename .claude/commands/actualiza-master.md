Analiza todos los cambios pendientes en git del proyecto Financial Wall, actualiza CHANGELOG.md y README.md si es necesario, haz commits organizados por área y sube todo a master en GitHub.

## Pasos a ejecutar

### 1. Inspeccionar cambios

```
git status
git diff --stat HEAD
```

### 2. Actualizar CHANGELOG.md

Lee el `CHANGELOG.md` actual y los cambios pendientes. Si hay funcionalidades, fixes o cambios relevantes que no estén documentados:

- Determina el nuevo número de versión siguiendo semver:
  - `MAJOR.MINOR.PATCH` — nueva funcionalidad → sube MINOR, corrección → sube PATCH
- Añade una nueva entrada al principio (después de la línea `---` inicial) con el formato:

```markdown
## [X.Y.Z] — YYYY-MM-DD

### Título breve de la versión.

#### Añadido
- ...

#### Cambiado
- ...

#### Corregido
- ...
```

- Omite las secciones que no apliquen.
- Muestra la entrada propuesta al usuario y espera confirmación antes de continuar.

### 3. Actualizar README.md (si es necesario)

Revisa si alguno de los cambios pendientes afecta a:
- Instrucciones de instalación o arranque
- Tabla de `config.yaml` o `chart_blocks`
- Descripción de funcionalidades o layout
- Comandos útiles o atajos de teclado

Si hay algo desactualizado, actualiza la sección correspondiente. Muestra los cambios al usuario y espera confirmación antes de continuar.

### 4. Agrupar por área lógica

Clasifica todos los archivos modificados (incluidos CHANGELOG y README si se actualizaron) en estas categorías:

| Categoría | Archivos |
|-----------|---------|
| **theme** | `src/ui/theme.py` |
| **ui** | `src/ui/app.py`, `src/ui/widgets/top_bar.py`, `src/ui/widgets/market_panel.py` |
| **services** | `src/services/coinmarketcap.py`, `src/services/market_data.py`, `src/services/weather.py`, `shared/config_manager.py` |
| **webapp** | cualquier archivo bajo `app-config/` |
| **config/docs** | `config.example.yaml`, `CLAUDE.md`, `README.md`, `CHANGELOG.md`, `requirements.txt`, archivos bajo `scripts/` |
| **other** | cualquier archivo que no encaje en las categorías anteriores |

### 5. Crear un commit por categoría

Para cada categoría con cambios:

```
git add <archivos de la categoría>
git commit -m "<tipo>(<scope>): <descripción en español, imperativo, máx 72 chars>"
```

Tipos: `feat` | `fix` | `refactor` | `chore` | `docs`

**CRÍTICO: NO incluir líneas `Co-Authored-By` ni `Co-authored-by` en ningún commit.**

### 6. Merge a master (si no estás ya en master)

```
git checkout master
git merge <nombre-del-branch> --no-ff -m "Merge branch '<nombre>': <resumen breve>"
```

### 7. Push a GitHub

```
git push origin master
```

### 8. Resumen final

Muestra al usuario:
- Cambios documentados en CHANGELOG y README (si los hubo)
- Lista de commits creados con su mensaje
- Confirmación de que el push fue exitoso
