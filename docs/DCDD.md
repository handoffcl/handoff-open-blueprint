# DCDD — Desarrollo guiado con Contexto Distribuido y Modular

> La capa multi-agente y multi-equipo del blueprint. Lee primero el README;
> esto es la referencia de arquitectura.

## El problema que resuelve

El harness base evita que un agente empiece de cero. DCDD resuelve el siguiente
nivel: que **varios** agentes —distintas sesiones, distintos modelos, distintos
devs en distintos lugares— trabajen sobre el mismo repo sin pisarse y sin
contradecirse.

Hay dos clases de choque, y son problemas distintos:

| Choque | Ejemplo | Capa que lo resuelve |
|---|---|---|
| **Físico** | dos agentes en la misma rama, uno pierde su lugar | Coordinación (worktrees + locks + scope) |
| **Semántico** | turismo cambia `getCafeProfile`, core lo consume, tests verdes | Validador semántico (local + central) |

Mezclarlos es el error. El worktree no detecta un contrato roto; el validador no
evita que dos agentes editen el mismo archivo. Se necesitan ambos.

---

## Capa 1 — Coordinación

### Worktrees: aislamiento físico

Cada agente trabaja en su propio checkout (`git worktree`) sobre su propia rama.
No comparten directorio de trabajo, así que no pueden pisarse archivos a medio
editar.

```bash
bash scripts/worktree.sh start <module> [branch] [holder]
bash scripts/worktree.sh end   <module>
bash scripts/worktree.sh list
```

`start` hace tres cosas atómicamente: crea el worktree+rama, adquiere el lock del
módulo, y registra al agente. `end` revierte las tres.

### Locks: coordinación compartida vía git

`.context/locks.json` está **commiteado**. Es el sustrato de coordinación: git es
el servidor. Un lock declara "estoy en este módulo".

```json
{
  "locks": [
    { "module": "turismo", "holder": "chris-opus", "branch": "feature/turismo",
      "worktree": ".worktrees/turismo", "acquired_at": "2026-06-12T10:00:00Z",
      "ttl_minutes": 240 }
  ]
}
```

- Si dos personas adquieren lock del mismo módulo y pushean, **git produce un
  conflicto** en `locks.json` — ese conflicto *es* la señal de colisión, atrapada
  antes de que el código choque.
- `ttl_minutes` evita locks zombi: pasado el tiempo, `scope_guard` lo ignora.

### Registry: vista local

`.context/agents/registry.local.yaml` está **gitignored**. Es la foto local: qué
agentes corren en tu máquina ahora (posiblemente varios modelos en paralelo). No
se comparte; el estado compartido vive en `locks.json`.

### task.yaml: el scope de una tarea

`.context/tasks/<id>.yaml` declara, *antes* de empezar, qué puede tocar la tarea:

```yaml
id: pricing
intent: "Ajustar precios en el módulo bookings"
module: bookings
allowed:
  - "src/**/modules/bookings/**"
  - "docs/modular/bookings/**"
forbidden:
  - "svelte.config.js"
  - "package.json"
  - "src/hooks.server.*"
acceptance:
  - "El precio con oferta se calcula desde sale_price"
```

`forbidden` es la lección de una caída real en producción: un agente "arregló"
`Cache-Control` y scripts de build que nadie le pidió tocar, y tiró el sitio.
Esos archivos en `forbidden` → el push se bloquea con razón clara.

### scope_guard: enforcement de la coordinación

`scripts/scope_guard.py` corre en `pre-push` y verifica:

1. **Scope** — cada archivo cambiado está en `allowed` y no en `forbidden`.
2. **Locks** — ningún archivo cambiado pertenece a un módulo lockeado por otro
   holder (respetando `ttl`).

La identidad ("quién soy") viene de `DCDD_AGENT` o del `git user.name`. Un lock
tuyo nunca te bloquea a ti.

---

## Capa 2 — Validador semántico

### module.yaml: la fuente machine-readable

`modules.md` es prosa, para humanos. `docs/modular/<módulo>/module.yaml` es el
manifiesto que lee la máquina:

```yaml
module: bookings
owner: team-core
owns:
  - "src/**/modules/bookings/**"
provides:                        # superficie pública que otros pueden consumir
  - name: createBooking
    contract: "docs/architecture/contracts/bookings.yaml#/paths/~1bookings/post"
consumes:                        # lo que depende de OTROS módulos
  - module: clients
    symbols: [getClient, searchClients]
invariants:
  - "no-direct-db-outside-repository"
```

**Disciplina:** cuando cambias la superficie pública de un módulo, actualizas
`provides` en el **mismo commit**. Eso es lo que permite atrapar la ruptura.

### Un motor, dos modos

```
scripts/semantic_validator.py
  ├─ --mode local    pre-push:  valida [módulos tocados + sus consumidores]
  └─ --mode central  CI:        valida [todos los módulos, cross-check]
```

Es el **mismo código**. Solo cambia el scope. Por eso el feedback local predice
exactamente lo que dirá el gate central — no te estrellas en CI con algo que
local no te avisó.

| Check | Severidad | Qué detecta |
|---|---|---|
| consumes resolution | error | consumes un símbolo que el proveedor ya no provee |
| ownership conflict | error | dos módulos reclaman el mismo archivo |
| invariant resolution | error | invariante referenciado no existe en la constitution |
| provides drift | warning | declaras `provides` que no aparece en tu código |

El modo local incluye a los **consumidores** de lo que tocaste: si cambiás
`clients`, valida también `bookings` porque consume de `clients`. Así detecta que
rompiste a alguien aunque solo hayas editado tu propio módulo.

### Por qué local *y* central

El validador local solo ve **tu** trabajo. No sabe qué hicieron los otros dos del
equipo en sus ramas. El gate central, al hacer merge, ve la foto **completa**: es
el único punto donde se detecta que la rama de turismo y la de core, cada una
verde por separado, juntas rompen un contrato.

---

## El flujo completo

```
worktree start  →  lock + aislamiento físico
   ↓
código  →  commit (post-commit: living docs)
   ↓
git push  →  pre-push:  scope_guard           (¿dentro de mi tarea? ¿módulo libre?)
                        semantic_validator local (¿rompí un contrato?)
   ↓
Pull Request  →  CI:  semantic_validator central (grafo completo)
                      → contradicción → bloquea merge a main
   ↓
merge a main  →  deploy
```

`git push --no-verify` salta el gate local cuando hay un falso positivo legítimo
(cambio cosmético, infra con su propia justificación). El gate central no se
salta.

---

## Archivos

```
scripts/
  semantic_validator.py      motor semántico (sin dependencias, parser YAML propio)
  scope_guard.py             enforcement de scope + locks
  worktree.sh                worktree + lock + registry en un comando
  install_hooks.sh           instala pre-commit, post-commit, pre-push
.context/
  locks.json                 locks compartidos (commiteado)
  agents/registry.local.yaml vista local de agentes (gitignored)
  tasks/<id>.yaml            scope por tarea (gitignored salvo el template)
docs/modular/<módulo>/
  module.yaml                manifiesto machine-readable por módulo
.github/workflows/
  semantic-validation.yml    gate central
```

---

## Sin lock-in

Todo es Python de stdlib + Bash + git. Sin pip, sin servicios, sin extensiones.
El validador trae su propio lector de YAML para el subconjunto de `module.yaml`,
así corre donde corra `python3`. Agnóstico al modelo y al lenguaje del proyecto.
