# Handoff Open Blueprint

> **Estructura tu repo para que cualquier agente de IA arranque en 30 segundos — sin re-explicar nada.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ¿Qué es?

Un blueprint de desarrollo con IA que funciona con **cualquier modelo y cualquier editor**.

No necesitas la extensión de Handoff. No necesitas un CLI. Solo necesitas un modelo con ventana de contexto suficiente y este repo clonado.

**Requisito mínimo:** modelo con ≥ 128k tokens de contexto.  
**Recomendado:** ≥ 200k para proyectos con historial largo.

Compatible con: Claude, GPT-4o, Gemini, Mistral Large, Llama 4, Qwen 72B+, DeepSeek V3+, Copilot, Cursor, y cualquier agente que pueda leer archivos.

---

## Inicio en 30 segundos

```bash
git clone https://github.com/handoffcl/handoff-open-blueprint
cd handoff-open-blueprint
```

Luego en cualquier chat con tu agente:

```
Lee BOOTSTRAP.md y ejecútalo.
```

Eso es todo. El agente pregunta tu idea, genera toda la estructura, instala el harness y arranca.

---

## Qué incluye

```
handoff-open-blueprint/
├── BOOTSTRAP.md              ← punto de entrada — "ejecuta bootstrap"
├── WORKING-AGREEMENT.md      ← cómo trabaja la IA en este proyecto
│
├── commands/
│   └── bootstrap.md          ← flujo completo de bootstrap (agnóstico)
│
├── roles/
│   ├── routing.md            ← cuándo usar cada rol según complejidad
│   ├── senior-backend.md
│   ├── senior-frontend.md
│   ├── senior-design.md
│   └── security-review.md
│
├── blueprint/                ← templates copiados al proyecto en bootstrap
│   ├── CONTEXT.md.template
│   ├── HANDOFF.md.template
│   ├── WORKING-AGREEMENT.md.template
│   ├── Makefile.template
│   └── docs/
│       ├── vision/
│       ├── constitution/
│       ├── plan/
│       ├── specs/
│       ├── clarify/
│       ├── modular/
│       └── architecture/
│
└── scripts/
    ├── update_docs.py        ← harness: auto-actualiza docs después de cada commit
    └── install_hooks.sh      ← instala git hooks
```

---

## El harness — qué hace por ti

`scripts/update_docs.py` corre automáticamente después de cada commit (via git hook) y mantiene vivos:

- `CONTEXT.md` → últimos cambios clasificados
- `docs/constitution/constitution.md` → fase del proyecto
- `docs/clarify/assumptions.md` → alerta si lleva mucho sin revisar
- `docs/plan/v1-mvp.md` → progreso de features
- `docs/specs/*.md` → estado de cada spec

**Resultado:** la sesión 50 arranca con el historial completo de las sesiones 1-49. El agente no re-abre decisiones cerradas, no sugiere lo que ya descartaste, no rompe lo que se construyó con intención.

---

## Role routing por complejidad

Antes de trabajar, el agente consulta `roles/routing.md`:

| Complejidad | Rol |
|---|---|
| Pregunta / cambio pequeño | Sin rol |
| Feature backend | `senior-backend.md` |
| Feature frontend | `senior-frontend.md` |
| UI / flujos | `senior-design.md` |
| Arquitectura | `senior-backend.md` + modelo ≥ 200k |
| Seguridad | `security-review.md` (siempre obligatorio) |

---

## Multi-LLM por diseño

El blueprint no te amarra a un modelo ni a un proveedor.

Puedes cambiar de Claude a Gemini a Mistral en la misma sesión — el contexto vive en los archivos, no en el chat. Cualquier agente que lea `HANDOFF.md` + `CONTEXT.md` + `WORKING-AGREEMENT.md` arranca con el estado completo del proyecto.

Esto es lo que hace posible el trabajo distribuido: múltiples agentes, múltiples sesiones, mismo contexto.

---

## Diferencia con handoff-blueprint

| | handoff-blueprint | handoff-open-blueprint |
|---|---|---|
| Requiere extensión VS Code | Recomendado | No |
| Slash commands | `/bootstrap-app` | `"ejecuta bootstrap"` |
| Roles con routing por complejidad | No | ✅ |
| Compatible con Copilot / Cursor / cualquier agente | Con fricción | ✅ nativo |
| Mantenido por | [@handoffcl](https://github.com/handoffcl) | [@handoffcl](https://github.com/handoffcl) |

---

## Filosofía

> El mejor repo es el que se documenta solo.  
> El mejor repo con IA es el que se documenta solo *para la IA*.

→ [Lee la filosofía completa](PHILOSOPHY.md)

---

## Licencia

MIT — úsalo, forkéalo, mejóralo.

---

Hecho con [Handoff](https://handoff.cl) · [@handoffcl](https://github.com/handoffcl)
