# Role Routing — cuándo activar cada rol

> Lee este archivo antes de decidir con qué rol trabajar.
> La complejidad del task determina el rol. El rol determina el nivel de modelo recomendado.

---

## Tabla de routing

| Complejidad | Ejemplos | Rol | Modelo mínimo |
|---|---|---|---|
| **Pregunta / explicación** | "¿qué hace este código?", debug puntual | Sin rol | 128k |
| **Cambio pequeño** | typo, rename, config, 1-5 líneas | Sin rol | 128k |
| **Feature backend** | nuevo endpoint, migración, servicio | `senior-backend.md` | 128k |
| **Feature frontend** | nuevo componente, página, estado | `senior-frontend.md` | 128k |
| **UI / flujos / conversión** | diseño de pantalla, UX, onboarding | `senior-design.md` | 128k |
| **Decisión de arquitectura** | ADR, cambio estructural, módulo nuevo | `senior-backend.md` | ≥ 200k recomendado |
| **Cualquier cambio de seguridad** | auth, permisos, datos sensibles, API keys | `security-review.md` | 128k (obligatorio) |
| **Refactor amplio** | múltiples archivos, cambio de contrato | `senior-backend.md` | ≥ 200k recomendado |

---

## Reglas

1. **Un rol por sesión** — no mezcles roles en el mismo contexto
2. **Seguridad es siempre obligatoria** — cualquier cambio que toque auth, permisos o datos sensibles activa `security-review.md`, sin excepción
3. **Arquitectura prefiere contexto amplio** — si el modelo disponible tiene < 200k y el task es arquitectural, divide en sesiones más pequeñas
4. **Sin rol no significa sin protocolo** — el `WORKING-AGREEMENT.md` aplica siempre

---

## Cómo activar un rol

```
# En cualquier agente:
"Lee roles/senior-backend.md y trabaja desde ese rol para esta tarea."
```

El rol define:
- Cómo analiza antes de responder
- Qué preguntas hace antes de codear
- Cuándo propone vs cuándo actúa directo
- Qué verifica al terminar

---

## Señales de que necesitas subir de complejidad

- El task toca más de 3 archivos → sube un nivel
- El task cambia contratos entre módulos → arquitectura
- El task afecta datos de usuarios → seguridad obligatoria
- El task tiene dependencias no documentadas → pide contexto antes de actuar
