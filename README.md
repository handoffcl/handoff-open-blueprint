# Handoff Open Blueprint

> **Para que tu IA no empiece de cero en cada sesión.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## El problema

Cada vez que abres una nueva sesión con tu agente de IA, re-explicas el proyecto desde cero. El agente no sabe qué decisiones se tomaron, qué está hecho, qué está pendiente, ni qué no se debe tocar. Cada sesión es una pizarra en blanco.

## La solución

Un blueprint que hace tu repo **auto-documentado para la IA**. El agente lee los archivos al inicio de cada sesión y arranca en 30 segundos con el contexto completo del proyecto.

**Agnóstico al modelo.** Funciona con Claude, GPT, Gemini, Mistral, Copilot, Cursor, Llama, DeepSeek — cualquier agente con ≥ 128k tokens de contexto.

**Sin lock-in.** Sin extensiones requeridas, sin CLIs, sin suscripciones. Solo archivos Markdown y un script Python.

---

## Inicio rápido

```bash
git clone https://github.com/handoffcl/handoff-open-blueprint
cd handoff-open-blueprint
```

Luego en cualquier chat con tu agente de IA:

```
Lee BOOTSTRAP.md y ejecútalo.
```

El agente te pregunta tu idea, genera toda la estructura del proyecto y arranca.

---

## ¿Qué hace exactamente?

### 1. El bootstrap — una sola vez

Cuando ejecutas el bootstrap, el agente:
- Te hace **una sola pregunta**: ¿qué hace tu app y para quién?
- Genera todos los documentos del proyecto desde esa respuesta
- Instala git hooks que mantienen los docs actualizados automáticamente
- Escribe los specs iniciales por feature (antes de codear)

### 2. El harness — funciona solo después de cada commit

`scripts/update_docs.py` corre automáticamente via git hook después de cada commit:

```
Tu commit
  ↓
update_docs.py actualiza:
  CONTEXT.md      → últimos cambios, estado actual
  constitution.md → fase del proyecto
  assumptions.md  → alerta si lleva mucho sin revisar
  plan/v1-mvp.md  → progreso de features
  specs/*.md      → estado de cada spec
```

**Resultado:** la sesión 50 arranca con el historial completo de las sesiones 1-49. El agente no re-abre decisiones cerradas ni sugiere lo que ya descartaste.

### 3. Los roles — quién hace qué

Antes de trabajar en cada área, el agente activa el rol correspondiente:

| Área | Rol |
|---|---|
| APIs, base de datos, servicios | `roles/senior-backend.md` |
| Componentes, UX, accesibilidad | `roles/senior-frontend.md` |
| Flujos de usuario, diseño visual | `roles/senior-design.md` |
| Auth, permisos, datos sensibles | `roles/security-review.md` |

El archivo `roles/routing.md` explica cuándo activar cada rol según la complejidad del task.

---

## Requisito mínimo

| Contexto | Compatible |
|---|---|
| < 128k tokens | ❌ No recomendado |
| ≥ 128k tokens | ✅ Compatible |
| ≥ 200k tokens | ✅ Ideal para proyectos con historial largo |

> **Ojo:** algunos modelos anuncian 128k pero en la práctica degradan calidad o fallan antes de ese límite. Verifica el comportamiento real de tu modelo en contextos largos antes de usarlo en proyectos extensos.

**Modelos probados por el equipo:** Claude 3.5+, GPT-4o, Gemini 1.5+, Llama 4 Scout, Mistral Large
**Compatibles por diseño** (ventana ≥ 128k, no verificados): Qwen 72B+, DeepSeek V3+, y cualquier modelo que cumpla el mínimo — verifica la ventana de contexto de tu modelo antes de usarlo

---

## Estructura del repo

```
handoff-open-blueprint/
├── BOOTSTRAP.md              ← punto de entrada — "ejecuta bootstrap"
├── WORKING-AGREEMENT.md      ← reglas de trabajo con la IA
├── LICENSE                   ← MIT
│
├── commands/
│   └── bootstrap.md          ← flujo completo de bootstrap
│
├── roles/
│   ├── routing.md            ← cuándo usar cada rol
│   ├── senior-backend.md
│   ├── senior-frontend.md
│   ├── senior-design.md
│   └── security-review.md
│
├── blueprint/                ← plantillas copiadas al proyecto en bootstrap
│   ├── CONTEXT.md.template
│   ├── HANDOFF.md.template
│   ├── WORKING-AGREEMENT.md.template
│   └── docs/
│       ├── specs/            ← un spec por feature, antes de codear
│       ├── vision/           ← qué hace el producto y para quién
│       ├── constitution/     ← principios del proyecto
│       ├── plan/             ← decisiones técnicas y ADRs
│       ├── clarify/          ← supuestos documentados
│       ├── modular/          ← contratos entre módulos
│       └── architecture/     ← diseño del sistema
│
└── scripts/
    ├── update_docs.py        ← harness: auto-actualiza docs después de cada commit
    └── install_hooks.sh      ← instala los git hooks
```

---

## ¿En qué se diferencia de handoff-blueprint?

[handoff-blueprint](https://github.com/handoffcl/handoff-blueprint) está diseñado para usarse con la extensión VS Code de Handoff — tiene slash commands y aprovecha la integración con el editor.

**handoff-open-blueprint** es la versión completamente agnóstica: funciona con cualquier agente, en cualquier editor, sin instalar nada adicional. Si no usas la extensión de Handoff, este es el que necesitas.

---

## Ecosistema Handoff

| Producto | Descripción |
|---|---|
| [Handoff](https://handoff.cl) | Chat multi-LLM con contexto compartido entre modelos |
| [Handoff VS Code Extension](https://handoff.cl/vscode) | El chat dentro de tu editor con herramientas de filesystem |
| [Handoff Blueprint](https://github.com/handoffcl/handoff-blueprint) | Blueprint para la extensión VS Code |
| **Handoff Open Blueprint** | Este repo — blueprint agnóstico para cualquier agente |
| [Handoff Coder](https://github.com/handoffcl/handoff-coder) | Modelfiles open source que convierten cualquier LLM en un ingeniero senior |

---

## Licencia

MIT — úsalo, forkéalo, mejóralo.

---

Hecho en Chile 🇨🇱 · [handoff.cl](https://handoff.cl) · [@handoffcl](https://github.com/handoffcl)
