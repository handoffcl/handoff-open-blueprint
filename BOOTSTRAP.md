# BOOTSTRAP

> **Punto de entrada.** Cualquier agente de IA con ≥ 128k de contexto puede ejecutar este archivo.

---

## Para el agente que lee esto

Eres el arquitecto de este proyecto. Lee este archivo completo y ejecuta el flujo en `commands/bootstrap.md`.

No necesitas una extensión, ni un CLI, ni configuración especial. Solo necesitas acceso al sistema de archivos del proyecto.

---

## Requisito mínimo de contexto

| Ventana | Estado |
|---|---|
| < 128k tokens | ❌ No compatible — el harness no puede garantizar continuidad |
| ≥ 128k tokens | ✅ Compatible |
| ≥ 200k tokens | ✅ Recomendado para proyectos con historial largo |

**Modelos compatibles:** Claude 3.5+, GPT-4o, Gemini 1.5+, Llama 4, Mistral Large, Qwen 72B+, DeepSeek V3+, y cualquier modelo que cumpla el mínimo de contexto.

---

## Cómo ejecutar

**Con cualquier agente (Copilot, Cursor, Claude, Gemini, Mistral, lo que sea):**

Pega esto en el chat:

```
Lee el archivo BOOTSTRAP.md de este repo y ejecútalo.
Empieza por el Step 0 — hazme una sola pregunta sobre mi idea.
```

**Con la extensión Handoff (opcional):**

```
/bootstrap
```

---

## Qué pasa cuando ejecutas el bootstrap

El agente te hace **una sola pregunta** y desde tu respuesta genera todo:

1. **Estructura de documentos** — visión del producto, principios, decisiones técnicas, supuestos, módulos, arquitectura
2. **CONTEXT.md** — el archivo que el agente leerá al inicio de cada sesión futura
3. **HANDOFF.md** — las reglas del proyecto para la IA
4. **Git hooks** — el harness que mantiene los docs actualizados automáticamente después de cada commit
5. **Specs iniciales** — un spec por feature, escritos antes de codear
6. **Opcional** — implementa las features y levanta el proyecto

**Todo en una sesión. Sin re-explicar nada en sesiones futuras.**

---

## Qué pasa después del bootstrap

Después de cada `git commit`, el harness actualiza automáticamente:

- `CONTEXT.md` → últimos cambios clasificados
- `docs/constitution/` → fase del proyecto (Exploratorio → Estable)
- `docs/clarify/` → alerta si llevan mucho tiempo sin revisión
- `docs/plan/` → progreso de features y ADRs
- `docs/specs/` → estado de cada spec

La próxima sesión: el agente lee los docs y arranca con el contexto completo en 30 segundos.
