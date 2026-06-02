# Spec: Potential Improvements — Ideas to Evaluate
<!-- status: pending | 2026-05-24 -->

> Ideas rescatadas de arquitecturas externas. NO implementar todo — evaluar cada una por separado.
> Criterio: ¿agrega valor real sin engordar el blueprint?

---

## Context

Al revisar arquitecturas de producción AI (ej. production-ai-app), hay patrones interesantes
que podrían sumar al blueprint sin romper su filosofía de mantenerse lean.

**Regla:** el blueprint resuelve "cómo desarrollar con IA hasta MVP". No es un blueprint de operaciones en producción — eso lo cubren herramientas especializadas (SonarQube, Datadog, etc.).

---

## Ideas a evaluar

### 1. Golden dataset para evaluación del agente
**Qué es:** un conjunto de inputs/outputs esperados para testear que el agente produce resultados correctos, no solo que el código compila.

**Por qué podría sumar:** el quality gate actual (`make quality`) valida código, no comportamiento del agente.

**Riesgo:** puede volverse mantenimiento pesado si el dataset crece sin control.

**Decisión pendiente:** ¿vale para el blueprint genérico o solo para proyectos con AI pipelines?

---

### 2. Cost tracker a nivel de sesión de agente
**Qué es:** registrar cuántos tokens/costo consume el agente por sesión o por feature.

**Por qué podría sumar:** Relay ya lo tiene a nivel de chat. Tenerlo en el blueprint ayudaría a detectar sesiones que queman tokens innecesariamente.

**Riesgo:** overhead de instrumentación para proyectos simples.

**Decisión pendiente:** ¿como script opcional o parte del harness por defecto?

---

### 3. Output validator antes del quality gate
**Qué es:** una capa que valida lo que el agente produjo antes de correr `make quality` — verifica que el diff tiene sentido respecto a la spec.

**Por qué podría sumar:** el agente puede pasar el quality gate y aun así haber implementado algo distinto a la spec.

**Riesgo:** requiere que el agente mismo valide su output, lo cual puede ser circular.

**Decisión pendiente:** explorar si esto se puede hacer con una instrucción en WORKING-AGREEMENT.md en lugar de tooling.

---

### 4. Generación automática de contratos OAS al construir arquitectura
**Qué es:** cuando el agente genera la arquitectura del producto, debe generar simultáneamente los contratos OAS (OpenAPI Specification) de cada módulo/integración — no como documentación posterior sino como contrato previo al código.

**Flujo correcto:**
```
idea → constitution → specs → arquitectura → OAS generado → código implementa el contrato
```
No al revés. El código implementa el contrato, no el contrato describe el código.

**Estándar de naming — nivel enterprise:**

Recursos:
- Colecciones en plural: `GET /users`, `GET /orders`, `GET /products`
- Recurso singular: `GET /users/{userId}`, `GET /orders/{orderId}`
- Anidados: `GET /users/{userId}/orders` — máximo 2 niveles

Campos:
- camelCase en JSON: `customerId`, `createdAt`, `totalAmount`
- Fechas: ISO 8601 — `2026-05-24T10:30:00Z`
- IDs: UUID v4, siempre string

Respuestas consistentes:
```yaml
# Éxito colección
data: []
meta:
  total: 0
  page: 1
  pageSize: 20

# Éxito singular
data: {}

# Error
error:
  code: "RESOURCE_NOT_FOUND"
  message: "..."
```

**Integración con quality gate:**
- Spectral valida OAS en CI — si el código rompe el contrato, el commit no pasa
- Los YAMLs viven en `docs/architecture/contracts/` con nombre estándar: `{modulo}-api.yaml`

**Por qué es un diferenciador:** la IA ya conoce la arquitectura cuando genera specs. Generar el OAS en ese momento tiene costo cero adicional — pero produce un contrato versionado que protege las integraciones en equipos.

**Decisión pendiente:** definir el template base del YAML que el agente debe seguir al generarlo.

---

### 5. Coordinación de contexto en equipos — diferenciador clave
**Qué es:** cuando múltiples personas (o agentes) trabajan en paralelo sobre el mismo repo, cada uno tiene su propio contexto de sesión. El código puede divergir y el contexto del agente también diverge — es el problema de git pero con una capa adicional.

**Escenario real:**
- Persona A trabaja módulo auth con Claude
- Persona B trabaja módulo payments con GPT
- Persona C hace un fix en la API con Gemini
- Nadie sabe qué decidió el otro. CONTEXT.md tiene conflictos de merge.

**Por qué es un diferenciador:** nadie lo está resolviendo explícitamente hoy. Los blueprints existentes asumen un solo desarrollador o ignoran el problema.

**Líneas de solución a explorar:**
- Specs por módulo con ownership claro — cada quien tiene su spec, no se pisan
- ADRs como contrato compartido antes de implementar
- CONTEXT.md por módulo en lugar de uno global
- Branch de agente por persona/módulo con merge review de contexto

**Decisión pendiente:** definir si esto va al blueprint base o es un blueprint de equipos separado.

---

### 6. Workflow de equipo y colaboración — diferenciador open source
**Qué es:** definir explícitamente cómo trabajan múltiples personas sobre el mismo repo modular con DDD liviano. El repo ya tiene la estructura correcta — falta documentar el workflow.

**El repo NO es un monolito** — es un repo modular donde cada feature es independiente por diseño. Cualquier persona puede tomar un spec y trabajarlo sin tocar otros módulos.

**Workflow de equipo:**
```
1. Clonas el repo
2. Lees CONTEXT.md → entiendes el estado actual en 30 minutos
3. Tomas un spec existente en docs/specs/ O propones uno nuevo
4. Trabajas en tu branch — tu módulo, tu spec, tu OAS
5. El quality gate valida código + contratos OAS (no rompiste nada)
6. PR → review → merge
```

**Por qué funciona:**
- El contexto ya está en el repo — no hay onboarding de 2 semanas
- Cada módulo tiene su spec, su contrato y su OAS — superficie de conflicto mínima
- CONTEXT.md + modules.md dan el mapa completo antes de tocar una línea

**Lo que falta para activarlo:**
- OAS por módulo generado al momento de crear la arquitectura (ver mejora #4)
- Un comando `/add-component <nombre>` que genere spec + módulo + OAS en un paso
- Documentar este workflow en CONTRIBUTING.md del blueprint

**Por qué es un diferenciador:** ningún blueprint documenta explícitamente cómo trabajan equipos con agentes IA en paralelo. Este workflow resuelve el problema de coordinación de contexto sin reuniones ni onboarding.

---

## Lo que explícitamente NO entra

- RAG, semantic cache, hybrid retrieval — infraestructura de producto, no de desarrollo
- Operaciones en producción — SonarQube, Datadog y similares ya lo cubren mejor
- Agentes multi-capa (document grader, query decomposer) — complejidad de producto, no de blueprint

---

## Criterio para aprobar cualquier mejora

1. ¿La necesita un proyecto en fase MVP? Si no, no entra al blueprint base.
2. ¿Se puede implementar en menos de 1 hora? Si no, va a un blueprint avanzado separado.
3. ¿Engorda CONTEXT.md o CLAUDE.md? Si sí, descartada.
