# Working Agreement

> **Reglas de trabajo con la IA en este proyecto.**
> El agente debe leer este archivo antes de cualquier acción.

---

## La regla fundamental

**Analiza → Resume → Propone → Espera OK → Escribe spec → Solo entonces codea.**

No escribas código sin que exista una spec en `docs/specs/`. Esta regla aplica incluso en sesiones largas o cuando parece obvio qué hacer.

---

## Antes de cualquier tarea

1. Lee `CONTEXT.md` — tiene el estado actual, la arquitectura y los últimos cambios
2. Identifica el tipo de tarea (tabla abajo) y activa el rol correspondiente
3. Si falta contexto, pide el archivo antes de asumir

---

## Tipos de tarea y protocolo

| Tipo | Ejemplos | Protocolo |
|---|---|---|
| **Pregunta / explicación** | "¿qué hace X?", "por qué está así" | Responde directo |
| **Cambio pequeño** | typo, rename, 1-5 líneas | Propón en 1 línea → espera OK |
| **Feature nueva** | endpoint, componente, servicio | Escribe spec → propón → espera OK → implementa |
| **Decisión de arquitectura** | cambio de módulo, ADR | Analiza → escribe ADR → espera OK |
| **Cualquier cambio de seguridad** | auth, permisos, keys | Activa `roles/security-review.md` siempre |

---

## Roles disponibles

Antes de trabajar en cada área, di en el chat:
`"Lee roles/[nombre].md y trabaja desde ese rol."`

| Área | Archivo |
|---|---|
| APIs, base de datos, servicios | `roles/senior-backend.md` |
| Componentes, UX, accesibilidad | `roles/senior-frontend.md` |
| Diseño visual, flujos, conversión | `roles/senior-design.md` |
| Seguridad, auth, datos sensibles | `roles/security-review.md` |

Ver `roles/routing.md` para la guía completa de cuándo usar cada rol.

---

## Reglas de código

- Sin TODOs sin resolver
- Sin implementaciones a medias presentadas como completas
- Tipado estricto según el lenguaje del proyecto
- Edición quirúrgica — toca solo lo necesario
- Sin duplicar lógica si ya existe abstracción clara

---

## Reglas de documentación

- Cada feature nueva: spec en `docs/specs/<nombre>.md` **antes** de codear
- Cada decisión arquitectural importante: ADR en `docs/plan/`
- `CONTEXT.md` se actualiza automáticamente — no lo edites a mano

---

## Quality gate

```bash
make quality   # debe pasar en verde antes de cada commit
```

Sin quality gate verde, sin merge.
