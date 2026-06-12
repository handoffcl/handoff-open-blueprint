---
name: homologate
description: Homologate an existing project to the handoff-open-blueprint. Installs the full harness — WORKING-AGREEMENT, HANDOFF, roles, docs structure, OAS contracts, git hooks — and the DCDD multi-agent layer (module.yaml manifests, locks/worktrees, semantic validator, pre-push + central gate) without losing existing information.
version: 3.0
---

# Homologate — Existing Project

> **Cuándo usar esto:** el proyecto ya existe pero no tiene la estructura del blueprint, o la tuvo pero quedó desactualizada.
>
> **No uses esto para proyectos nuevos** — usa `commands/bootstrap.md`.
>
> **Principio guía:** cero pérdida de información. Toda la información que ya existe en el proyecto se preserva o migra. Nada se borra sin aprobación explícita del humano.

---

## Estado final garantizado

Al terminar la homologación, el proyecto tendrá **exactamente** la misma estructura que un proyecto nuevo creado con bootstrap. Ni más, ni menos.

```
[proyecto]/
├── CONTEXT.md                         ← existe o se crea
├── HANDOFF.md                         ← existe o se crea — siempre con formato harness
├── WORKING-AGREEMENT.md               ← siempre se crea (es el contrato del harness)
├── CLAUDE.md                          ← si existe, se convierte en bridge delgado
├── .blueprint                         ← existe o se crea (BLUEPRINT_LANG=es)
├── Makefile                           ← existe o se crea desde template
├── roles/
│   ├── routing.md
│   ├── senior-backend.md              ← con stack real del proyecto
│   ├── senior-frontend.md             ← con stack real del proyecto
│   ├── senior-design.md
│   └── security-review.md            ← con zonas críticas del proyecto
├── docs/
│   ├── constitution/constitution.md   ← existe o se crea con contenido real
│   ├── clarify/assumptions.md         ← existe o se crea con contenido real
│   ├── vision/product-vision.md       ← existe o se crea con contenido real
│   ├── plan/v1-mvp.md                 ← existe o se crea con contenido real
│   ├── modular/modules.md             ← existe o se crea con contenido real
│   ├── sdd/arquitectura.md            ← existe o se crea con contenido real
│   ├── architecture/contracts/
│   │   ├── _contract.template.yaml    ← template de referencia
│   │   └── [modulo].yaml              ← un contrato OAS por módulo con API
│   ├── modular/
│   │   ├── modules.md                 ← prosa (humanos)
│   │   └── [modulo]/module.yaml       ← manifiesto machine-readable (DCDD)
│   ├── DCDD.md                        ← referencia de la capa multi-agente
│   └── specs/                         ← se respeta si ya tiene specs
├── .context/                          ← coordinación DCDD
│   ├── locks.json                     ← locks compartidos (commiteado, arranca vacío)
│   ├── agents/registry.local.yaml.template
│   └── tasks/_task.template.yaml
├── scripts/
│   ├── update_docs.py                 ← existe o se copia desde blueprint
│   ├── install_hooks.sh               ← existe o se copia desde blueprint
│   ├── semantic_validator.py          ← motor semántico (DCDD)
│   ├── scope_guard.py                 ← guard de scope + locks (DCDD)
│   └── worktree.sh                    ← worktree + lock + registry (DCDD)
├── .github/workflows/
│   └── semantic-validation.yml        ← gate central (DCDD)
└── .git/hooks/
    ├── pre-commit                     ← siempre instalado
    ├── post-commit                    ← siempre instalado
    └── pre-push                       ← scope_guard + validador local (DCDD)
```

**Lo que se preserva siempre:**
- Código fuente (`src/`, `frontend/`, `tests/`, etc.) — nunca se toca
- Specs existentes en `docs/specs/` — se respetan tal cual
- Notas de sesión en `HANDOFF.md` — migran al final del archivo bajo `## Última sesión`
- Decisiones documentadas en docs existentes — se fusionan, no se reemplazan
- Historial de git — intacto

---

## Antes de empezar

Lee estos archivos del blueprint antes de actuar:
- `blueprint/WORKING-AGREEMENT.md.template` — estructura que vas a instalar
- `blueprint/HANDOFF.md.template` — formato del archivo de sesión
- `roles/` — los 5 archivos de rol que vas a copiar
- `blueprint/docs/` — las plantillas de docs

Luego lee en el proyecto:
- Todo archivo existente en la raíz (CLAUDE.md, HANDOFF.md, CONTEXT.md, README.md, Makefile, etc.)
- `src/` o el directorio equivalente del código fuente — para identificar módulos y endpoints
- Cualquier config de deploy (railway.toml, Dockerfile, vercel.json, etc.) — para extraer stack y URLs

**Después del análisis, presenta al humano el reporte de auditoría (Step 0) y espera OK antes de tocar cualquier archivo.**

---

## Step 0 — Auditoría: reporta el estado actual

Genera este reporte y preséntalo al humano antes de hacer cualquier cambio:

```
AUDITORÍA DE HOMOLOGACIÓN — [nombre del proyecto]
==================================================

ARCHIVOS RAÍZ
  ✅ existe    CONTEXT.md
  ❌ falta     WORKING-AGREEMENT.md        → se creará desde template
  ⚠️  reescribir HANDOFF.md               → tiene [notas de sesión / estructura vieja / nada]
  ✅ existe    CLAUDE.md                   → se convertirá en bridge delgado
  ...

ROLES
  ❌ falta     roles/                      → se creará con 5 archivos

DOCS
  ✅ existe    docs/specs/                 → [N] specs encontrados
  ❌ falta     docs/architecture/contracts/ → se creará con [N] contratos OAS
  ⚠️  incompleto docs/modular/             → existe pero le falta sección de contratos
  ...

SCRIPTS Y HOOKS
  ✅ existe    scripts/update_docs.py
  ✅ existe    scripts/install_hooks.sh
  ❌ no activo post-commit hook            → se instalará

DCDD — capa multi-agente
  ❌ falta     docs/modular/[modulo]/module.yaml → se creará uno por módulo
  ❌ falta     .context/                  → se creará (locks/registry/tasks)
  ❌ falta     scripts/semantic_validator.py → se copiará
  ❌ falta     scripts/scope_guard.py     → se copiará
  ❌ falta     scripts/worktree.sh        → se copiará
  ❌ no activo pre-push hook              → se instalará
  ❌ falta     .github/workflows/semantic-validation.yml → se creará

STACK DETECTADO
  Backend: [lo que encontraste]
  Frontend: [lo que encontraste]
  DB: [lo que encontraste]
  Auth: [lo que encontraste]
  Deploy: [lo que encontraste]

MÓDULOS (para contratos OAS y manifiestos module.yaml)
  - [módulo 1] → [N] endpoints | owns: [path] | provides: [símbolos públicos] | consumes: [otros módulos]
  - [módulo 2] → [N] endpoints | owns: [path] | provides: [símbolos públicos] | consumes: [otros módulos]

ADVERTENCIAS
  ⚠️  [cualquier cosa que encontraste que sea rara, contradictoria o riesgosa]

¿Procedo con la homologación?
```

**Espera confirmación. No avances sin ella.**

---

## Step 1 — WORKING-AGREEMENT.md

**Este archivo no existe en el proyecto → créalo.**
**Si ya existe → compáralo con el template y agrega las secciones faltantes sin tocar lo que el humano escribió.**

Crea `WORKING-AGREEMENT.md` desde `blueprint/WORKING-AGREEMENT.md.template`. Completa con información real del proyecto:

- **Sección "Qué puede tocar la IA"** → incluye los directorios reales del proyecto (`frontend/`, `vscode-extension/`, etc.)
- **Sección "Roles disponibles"** → adapta la tabla al stack real
- **Sección "Reglas de código"** → extrae las convenciones que ya existan en `CLAUDE.md` u otro archivo de reglas
- **Sección "Zonas sensibles"** → identifica los archivos/tablas críticos del proyecto (auth, pagos, modelos sensibles)

> ⚠️ **WARNING para el humano:** `WORKING-AGREEMENT.md` es **inmutable** — solo tú lo cambias, nunca la IA ni los scripts. Revísalo después de la homologación y ajusta lo que no refleje tu proyecto.

No dejes ningún placeholder `{{...}}` sin completar.

---

## Step 2 — HANDOFF.md

`HANDOFF.md` en este blueprint tiene dos roles: **reglas del harness** (header) + **notas de la última sesión** (footer).

### Si HANDOFF.md no existe
Créalo desde `blueprint/HANDOFF.md.template` con el stack y estructura reales del proyecto.

### Si HANDOFF.md existe pero solo tiene notas de sesión
> ⚠️ **WARNING para el humano:** voy a reestructurar `HANDOFF.md`. Tus notas de sesión actuales NO se pierden — las muevo al final bajo `## Última sesión`. El contenido nuevo que agrego arriba son las instrucciones del harness.

Reestructura el archivo:
1. Agrega el header del harness (instrucciones de inicio de sesión, stack, comandos, estructura de carpetas)
2. Mueve el contenido existente al final bajo `## Última sesión — [fecha]`

### Si HANDOFF.md ya tiene estructura de harness
Compara con el template. Actualiza secciones obsoletas (stack, comandos, estructura). No toques `## Última sesión`.

---

## Step 3 — roles/

Crea el directorio `roles/` en la raíz del proyecto y copia los 5 archivos desde el blueprint.

Para cada archivo, completa la sección de stack del proyecto:

**`roles/senior-backend.md`** → completa `## Stack del proyecto`:
```
- Backend: [framework real, versión]
- Base de datos: [DB real + entorno dev vs prod]
- Auth: [mecanismo real]
- Deploy: [plataforma real]
- Testing: [framework de tests]
- Quality: [linters, type checkers]
```

**`roles/senior-frontend.md`** → completa `## Stack del proyecto`:
```
- Framework: [framework real]
- Lenguaje: [JS/TS/etc, versión]
- Estilos: [Tailwind/CSS modules/etc]
- Testing: [framework de tests]
```

**`roles/senior-design.md`** → completa `## Sistema de diseño del proyecto`:
```
- Paleta principal: [colores del proyecto o "ver app.css"]
- Tipografía: [fuente o "ver config"]
- Border radius: [valores o "ver Tailwind config"]
- Espaciado base: [escala]
```

**`roles/security-review.md`** → completa `## Zonas críticas en este proyecto`:
```
- [archivo de auth] — descripción de por qué es sensible
- [campo o tabla sensible] — qué nunca exponer
- [mecanismo de auth] — cómo funciona
```

**`roles/routing.md`** → copia sin cambios, o adapta la tabla de complejidad si el proyecto tiene roles específicos.

> ⚠️ **WARNING para el humano:** revisa los archivos de rol después de la homologación. El agente completó las secciones de stack con lo que detectó, pero puede haber detalles que solo tú conoces.

---

## Step 4 — Estructura de docs

Para cada directorio faltante, crea el stub desde el template correspondiente y complétalo con información real del proyecto. **No dejes placeholders.**

| Directorio | Template | Si ya existe |
|---|---|---|
| `docs/constitution/constitution.md` | `blueprint/docs/constitution/constitution.md.template` | Agrega solo las secciones faltantes |
| `docs/clarify/assumptions.md` | `blueprint/docs/clarify/assumptions.md.template` | Agrega solo las secciones faltantes |
| `docs/vision/product-vision.md` | `blueprint/docs/vision/product-vision.md.template` | Agrega solo las secciones faltantes |
| `docs/plan/v1-mvp.md` | `blueprint/docs/plan/v1-mvp.md.template` | Agrega solo las secciones faltantes |
| `docs/modular/modules.md` | `blueprint/docs/modular/modules.md.template` | Agrega sección de contratos OAS |
| `docs/sdd/arquitectura.md` | `blueprint/docs/sdd/arquitectura.md.template` | Agrega solo las secciones faltantes |
| `docs/architecture/contracts/` | — | Crear directorio |
| `docs/specs/` | — | No tocar si ya existe con specs |

> ⚠️ **WARNING para el humano:** los docs creados en este paso tienen información extraída del código y de los archivos existentes. Son un punto de partida — necesitan tu revisión para que reflejen las decisiones reales del proyecto, no solo lo que el agente pudo inferir.

---

## Step 5 — Contratos OAS

Crea un contrato OAS por cada módulo con endpoints públicos.

### Cómo identificar los módulos

Busca en el código fuente:
- FastAPI: archivos con `APIRouter` o `@app.get/post/put/delete`
- Express/NestJS: archivos con `router.get/post` o `@Controller`
- Rails: `config/routes.rb`
- Django: `urls.py`
- Otros: busca el patrón de routing del framework

Cada grupo lógico de endpoints → un contrato.

### Estructura de archivos

```
docs/architecture/contracts/
├── _contract.template.yaml    ← copia del template, no modificar
├── auth.yaml                  ← ejemplo
├── threads.yaml               ← ejemplo
└── [modulo].yaml              ← uno por módulo
```

### Cómo llenar cada contrato

1. Copia `blueprint/docs/architecture/contracts/_contract.template.yaml` → `[modulo].yaml`
2. Completa el header con datos reales (title, description, servers.url)
3. Para cada endpoint real encontrado en el código, agrega su path con:
   - Verb correcto (GET/POST/PUT/DELETE)
   - `operationId` en camelCase (`listThreads`, `createThread`)
   - `tags` → nombre del módulo
   - Request body si aplica (POST/PUT)
   - Responses: 200/201 para éxito, 400 para validación, 401 para auth, 404 para not found
4. Define todos los schemas en `components/schemas` — usa los modelos Pydantic/TypeScript/etc existentes como referencia

**Convenciones que debes respetar:**
- Colecciones: `GET /threads`, `POST /threads`
- Singular: `GET /threads/{threadId}`
- Anidado (máx 2 niveles): `GET /threads/{threadId}/messages`
- Campos: camelCase (`userId`, `createdAt`, `totalAmount`)
- Fechas: ISO 8601 (`2026-05-24T10:30:00Z`)
- IDs: UUID v4, siempre string

5. Agrega una referencia al contrato en `docs/modular/modules.md` bajo el módulo correspondiente

> ⚠️ **WARNING para el humano:** los contratos OAS generados documentan el estado actual de la API — lo que existe hoy. No son el diseño ideal, son la realidad actual. Revísalos y corrígelos si hay endpoints que están mal nombrados, mal tipados, o que deberían cambiar. El contrato es el punto de partida para que el agente no invente convenciones en sesiones futuras.

---

## Step 6 — Manifiestos de módulo (`module.yaml`) — capa semántica DCDD

Los contratos OAS describen la API HTTP. Los `module.yaml` describen el **grafo
de dependencias entre módulos** — y son lo que lee el validador semántico. Crea
uno por módulo: `docs/modular/[modulo]/module.yaml`, desde
`blueprint/docs/modular/_module.template.yaml`.

### Cómo derivar cada campo del código

Para cada módulo detectado en la auditoría:

| Campo | Cómo extraerlo del código |
|---|---|
| `module` | nombre del directorio del módulo |
| `owner` | equipo/persona (pregunta al humano si no es obvio; default `unassigned`) |
| `owns` | glob del directorio del módulo (`src/**/modules/[modulo]/**`) |
| `provides` | **superficie pública** — lo exportado en `index.*` / la frontera pública del módulo. Solo lo que otros módulos pueden importar. |
| `consumes` | lo que el módulo **importa de OTROS módulos**. Busca imports cross-módulo en el código y lista `{ module, symbols }`. |
| `invariants` | IDs de invariantes de `docs/constitution/constitution.md` que aplican a este módulo |

### La regla crítica de `provides` / `consumes`

Esto es lo que permite atrapar rupturas de contrato. Para llenarlo bien:

1. Por cada módulo, lista en `provides` SOLO los símbolos que otros módulos
   realmente importan (no internals).
2. Por cada import cross-módulo que encuentres en el código, agrégalo al
   `consumes` del módulo importador, nombrando el módulo proveedor y el símbolo.
3. **Verifica coherencia:** cada símbolo en algún `consumes` debe existir en el
   `provides` del proveedor. Si no, el grafo ya está roto hoy — repórtalo.

### Verifica el grafo antes de seguir

```bash
python3 scripts/semantic_validator.py --mode central --root .
```

Debe pasar (o solo warnings de drift). Si hay errores de `consumes` que no
resuelven, es que los `module.yaml` no reflejan el código real — corrígelos.

> ⚠️ **WARNING para el humano:** los `module.yaml` son la fuente de verdad del
> validador. Si declaran un `provides` que no existe o omiten un `consumes` real,
> el gate da falsos positivos o deja pasar rupturas. Revisa que reflejen la
> realidad del código.

---

## Step 7 — Scripts, coordinación y hooks

### Copia los scripts del harness y de DCDD

```
scripts/update_docs.py          ← harness principal
scripts/install_hooks.sh        ← instalador de hooks
scripts/semantic_validator.py   ← motor semántico (DCDD)
scripts/scope_guard.py          ← guard de scope + locks (DCDD)
scripts/worktree.sh             ← worktree + lock + registry (DCDD)
```

### Crea la coordinación `.context/`

```bash
mkdir -p .context/agents .context/tasks
echo '{"locks": []}' > .context/locks.json   # arranca vacío, se commitea
cp blueprint/.context/agents/registry.local.yaml.template .context/agents/
cp blueprint/.context/tasks/_task.template.yaml .context/tasks/
```

Agrega al `.gitignore` (estado local, nunca se commitea):
```
.worktrees/
.context/agents/registry.local.yaml
.context/tasks/*.yaml
!.context/tasks/_task.template.yaml
```

### Crea el gate central

```bash
mkdir -p .github/workflows
# desde el clone del blueprint: el workflow vive en github/ (raíz), no bajo blueprint/
cp [blueprint]/github/workflows/semantic-validation.yml .github/workflows/
```

### Instala los git hooks

```bash
bash scripts/install_hooks.sh
ls .git/hooks/pre-commit .git/hooks/post-commit .git/hooks/pre-push
```

> ⚠️ **WARNING para el humano — esto cambia tu flujo de trabajo:**
>
> **pre-commit:** si commiteas código en `src/` sin un spec en `docs/specs/`, el
> commit **falla**. Para cambios cosméticos: `git commit --no-verify`.
>
> **post-commit:** después de cada commit, `update_docs.py` actualiza los living
> docs. No edites a mano las secciones auto-generadas.
>
> **pre-push (nuevo, DCDD):** antes de cada push corre `scope_guard` (¿el cambio
> está dentro del scope de tu tarea? ¿el módulo está libre?) y el validador
> semántico local (¿rompiste un contrato?). Si falla por contrato roto,
> **arréglalo** — no uses `--no-verify` para saltarlo. El mismo motor corre en CI
> (`semantic-validation.yml`) antes del merge a main.

---

## Step 8 — Sincroniza los docs

Corre el harness manualmente para que todo quede sincronizado ahora:

```bash
python3 scripts/update_docs.py
```

Resultado esperado:
```
[docs] Updating living docs...
  ✓ CONTEXT.md (N commits)
  ✓ docs/constitution/constitution.md
  ✓ docs/clarify/assumptions.md
  ✓ docs/plan/v1-mvp.md
  ✓ N spec(s) status updated
```

Si el comando falla, reporta el error al humano antes de continuar.

---

## Step 9 — CLAUDE.md (solo si el proyecto usa Claude Code)

Si existe `CLAUDE.md` con reglas detalladas de proyecto:

> ⚠️ **WARNING para el humano:** las reglas que están en `CLAUDE.md` ya están en `WORKING-AGREEMENT.md`. Voy a reducir `CLAUDE.md` a un bridge delgado que apunta a los archivos del harness. No se pierde nada — la información migró a `WORKING-AGREEMENT.md`.

Reemplaza el contenido de `CLAUDE.md` por:

```markdown
# CLAUDE.md — [Nombre del proyecto] (Claude Code bridge)

## Inicio de cada sesión

1. Lee `CONTEXT.md` → estado actual del proyecto
2. Lee `WORKING-AGREEMENT.md` → reglas del harness (spec antes de código, roles, quality gate)
3. Lee `HANDOFF.md` → contexto de la última sesión y pendientes

## Comandos esenciales

[pega aquí los comandos reales: make quality, make dev, npm run dev, etc.]

## Variables de entorno requeridas

Ver `.env.example` para la lista completa.
```

---

## Checklist de cierre

Antes de terminar la sesión de homologación, verifica cada punto:

- [ ] `WORKING-AGREEMENT.md` existe, sin placeholders, con stack y zonas sensibles del proyecto
- [ ] `HANDOFF.md` tiene header del harness + notas de última sesión al final
- [ ] `roles/` tiene los 5 archivos con stack real completado
- [ ] `docs/architecture/contracts/` tiene al menos un `.yaml` por módulo backend
- [ ] `docs/modular/[modulo]/module.yaml` existe por cada módulo, con `provides`/`consumes` reales
- [ ] `docs/constitution/`, `docs/clarify/`, `docs/plan/`, `docs/modular/`, `docs/sdd/` existen con contenido real
- [ ] `.context/` creado: `locks.json` (vacío, commiteado) + templates de registry/tasks
- [ ] scripts DCDD copiados: `semantic_validator.py`, `scope_guard.py`, `worktree.sh`
- [ ] `.github/workflows/semantic-validation.yml` existe (gate central)
- [ ] `.gitignore` ignora `.worktrees/`, `registry.local.yaml`, `tasks/*.yaml`
- [ ] `scripts/install_hooks.sh` corrió exitosamente
- [ ] `.git/hooks/pre-commit`, `post-commit` y `pre-push` están activos
- [ ] `python3 scripts/semantic_validator.py --mode central` pasa (o solo warnings)
- [ ] `python3 scripts/update_docs.py` corrió sin errores
- [ ] `CLAUDE.md` es un bridge delgado (si usa Claude Code)
- [ ] Cero placeholders `{{...}}` en cualquier archivo del proyecto

Cuando todo esté en verde, presenta al humano el resumen final:

```
HOMOLOGACIÓN COMPLETADA — [nombre del proyecto]
===============================================

Archivos creados:
  + WORKING-AGREEMENT.md
  + HANDOFF.md (reestructurado, notas previas preservadas)
  + roles/ (5 archivos)
  + docs/architecture/contracts/ ([N] contratos OAS)
  + docs/modular/[modulo]/module.yaml ([N] manifiestos)
  + .context/ (locks.json + templates registry/tasks)
  + scripts/ (semantic_validator.py, scope_guard.py, worktree.sh)
  + .github/workflows/semantic-validation.yml
  + [otros archivos creados]

Archivos modificados:
  ~ CLAUDE.md → bridge delgado
  ~ CONTEXT.md → sincronizado
  ~ .gitignore → entradas DCDD
  ~ [otros archivos modificados]

Harness activo:
  ✓ pre-commit: bloquea commits de src/ sin spec
  ✓ post-commit: update_docs.py corre después de cada commit
  ✓ pre-push: scope_guard + validador semántico local
  ✓ CI: semantic-validation.yml (gate central antes de merge a main)

Grafo semántico:
  ✓ semantic_validator --mode central pasa ([N] módulos, [M] warnings)

Próximos pasos para el humano:
  1. Revisar WORKING-AGREEMENT.md — ajusta zonas sensibles y convenciones
  2. Revisar los contratos OAS y los module.yaml — corrige provides/consumes que el agente no pudo inferir
  3. Revisar roles/ — completa los detalles de diseño y sistema pendientes
  4. Asignar owners reales en cada module.yaml y en .context/locks.json
  5. El próximo commit/push activará el harness y los gates automáticamente
```
