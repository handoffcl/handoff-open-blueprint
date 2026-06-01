# BOOTSTRAP

> Este archivo es el punto de entrada. Cualquier agente con ≥ 128k de contexto puede ejecutarlo.

---

## Para el agente que lee esto

Lee este archivo completo y ejecuta el flujo en `commands/bootstrap.md`.

No necesitas una extensión, ni un CLI, ni configuración especial.
Solo necesitas un modelo con ventana de contexto suficiente y acceso al sistema de archivos.

---

## Requisito mínimo de contexto

| Ventana | Estado |
|---|---|
| < 128k tokens | ❌ No compatible — el harness no puede garantizar continuidad |
| ≥ 128k tokens | ✅ Compatible |
| ≥ 200k tokens | ✅ Recomendado para proyectos con historial largo |

**Modelos probados:** Claude 3.5+, GPT-4o, Gemini 1.5+, Llama 4 Scout/Maverick, Mistral Large, Qwen 72B+, DeepSeek V3+

---

## Cómo ejecutar

**Con cualquier agente (Copilot, Cursor, Claude, Gemini, lo que sea):**

```
Lee commands/bootstrap.md y ejecútalo paso a paso.
Empieza por el Step 0 — pregúntame la idea.
```

**Con la extensión Handoff (opcional, experiencia completa):**

```
/bootstrap
```

---

## Qué hace el bootstrap

1. Te pregunta tu idea (una sola pregunta)
2. Genera toda la estructura de docs desde esa idea
3. Instala el harness (git hooks que mantienen los docs vivos)
4. Genera specs iniciales por feature
5. Opcional: implementa y levanta el proyecto

Todo en una sesión. Sin re-explicar nada en sesiones futuras.
