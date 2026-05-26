---
description: Flujo completo para resolver un issue — planificación, implementación, tests y revisión
---

Resuelve este issue siguiendo el flujo estricto. NO omitas pasos.

**Issue:** $ARGUMENTS

---

### Paso 0 — Issue Snapshot

Antes de hacer cualquier cosa:

1. Si `$ARGUMENTS` es una URL (GitHub, Jira, Linear, etc.), obtén el contenido completo con `WebFetch`. Si no, usa el texto tal cual.
2. Produce el siguiente bloque **Issue Snapshot** en tu respuesta:

```
## Issue Snapshot
**Título/ID:** [título o ID]
**Body:** [body verbatim — no resumir]

**Criterios de aceptación:**
- [ ] AC-1: [criterio 1]
- [ ] AC-2: [criterio 2]
...

**Fuera de alcance:** [qué NO pide el issue explícitamente, o "nada especificado"]
```

3. Si todos los AC vienen literalmente del texto del issue → continuar automáticamente al Paso 1.
4. Si algún criterio fue **inferido** (no está literalmente en el issue) → marcarlo como *(inferido)* y ESPERAR confirmación humana antes de continuar.

Este snapshot es el contrato congelado. Todos los pasos posteriores lo referencian.

---

### Paso 1 — Planificación

Delegar a `issue-planner` pasando el **Issue Snapshot completo** (no solo el texto original).

Instruir al planner para que incluya, además de su output estándar, la sección obligatoria:

```
### Cobertura de criterios de aceptación
- [AC-1: "..."] → cubierto por: cambio backend X, test Y
- [AC-2: "..."] → cubierto por: ...
- [AC-N: "..."] → ⚠️ GAP — no cubierto, razón: [...]
```

Si algún AC tiene GAP:
- NO continuar al Paso 2.
- Mostrar el GAP al humano y ESPERAR resolución (aclaración, cambio de alcance o diferimiento explícito).

Si el planner emite "Riesgos / preguntas abiertas":
- Mostrarlos al humano y ESPERAR respuestas antes de continuar al Paso 2.
- NO asumir respuestas — solo el humano puede desbloquear.

Si el planner dice "no se requiere plan":
- Construir la cobertura de AC inline (trivialmente: 1 archivo, sin contrato) y continuar al Paso 2 sin esperar.

En cualquier otro caso → mostrar el plan completo incluyendo la sección de cobertura y ESPERAR confirmación antes de continuar.

---

### Paso 2 — Implementación

Una vez confirmado el plan (o saltado):

Delegar a `nestjs-dev` pasando:
- El **Issue Snapshot completo**.
- La **Cobertura de criterios de aceptación** del plan.
- El contrato de API exacto (cuando aplique).

Instruir al agente para que incluya en su output:

```
### Criterios de aceptación cubiertos
- AC-1 → archivos: ruta/archivo.ts:42, ruta/otro.ts:10
- AC-2 → archivos: ...
```

Si `nestjs-dev` no puede cubrir un AC por información faltante → debe reportarlo como bloqueador, nunca asumir.

---

### Paso 3 — Tests

**3.a — Generar/completar specs:**

Delegar a `test-unitario` pasando:
- Lista de archivos creados/modificados por `nestjs-dev`.
- Sección "Tests requeridos" del plan.

El agente lee los services/controllers/repositories nuevos o modificados y produce los `.spec.ts` correspondientes siguiendo `academico-testing-standard.md`.

**3.b — Ejecutar specs:**

Delegar a `test-runner`. Capturar el resultado.

**3.c — Verificación de cobertura AC:**

Para cada AC del Issue Snapshot, verificar (vía `Grep` sobre los `.spec.ts` modificados) que al menos un test cubre ese escenario, o que `nestjs-dev` lo declaró cubierto en "Criterios de aceptación cubiertos".

Si algún AC no tiene cobertura de test → volver a `test-unitario` para agregar el spec, luego re-ejecutar `test-runner`.

**3.d — Manejo de failures:**

- Failure causado por el cambio actual → volver a `nestjs-dev` para corregir, luego re-ejecutar `test-runner`.
- Flakes o timeouts preexistentes → marcarlos y continuar.

---

### Paso 4 — Code review

Delegar a `code-reviewer` pasando el **Issue Snapshot** junto con el diff.

Instruir al revisor para que incluya la sección obligatoria:

```
### Cumplimiento del issue
- AC-1: ✅ cubierto en ruta/archivo.ts:42 / test en ruta/archivo.spec.ts:10
- AC-2: ⚠️ parcial — falta caso de error
- AC-3: ❌ no implementado
```

Todo AC marcado ❌ se trata como hallazgo 🔴 blocking.

Si hay hallazgos 🔴 (violación de regla dura o AC no cumplido) → volver al agente responsable (`nestjs-dev` para código, `test-unitario` para tests faltantes) para corregir, luego re-ejecutar `code-reviewer`.

Si solo hay hallazgos 🟡 / 🟢 → mostrarlos sin bloquear.

---

### Paso 5 — Reporte final

```
## Issue Snapshot (estado final)
- [x] AC-1: [criterio] → ruta/archivo.ts:42, test: ruta/archivo.spec.ts:10
- [x] AC-2: [criterio] → ...
- [ ] AC-N: [criterio] → DIFERIDO (razón: [aprobado por humano en paso 1])

## Qué se hizo
**Backend:** [resumen]

## Tests
[resultado de test-runner — counts pass/fail]

## Hallazgos de revisión
[output completo de code-reviewer con sección "Cumplimiento del issue"]

## Confirmación de fuera de alcance
Nada fuera del Issue Snapshot fue modificado.
[O: lo siguiente fue excluido deliberadamente: ...]

## Cómo probar manualmente
- Para verificar AC-1: [pasos concretos]
- Para verificar AC-2: [pasos concretos]
```

NO hacer commit. El commit lo hace el humano.
