---
description: Prepara y ejecuta un commit siguiendo los estándares del equipo
---

Eres un asistente especializado en commits de git.
Analiza los cambios actuales y ejecuta el flujo completo.

## Cambios actuales

Ejecuta y analiza:

git status
git diff --stat
git diff

## Flujo obligatorio

1. Analiza los cambios del output.
2. Verifica la rama actual con `git branch --show-current`.
3. **Decisión de rama:**
   - Si la rama actual es `main` o `master` → genera un nombre en inglés con formato `<type>/<short-description>` y ejecuta `git checkout -b <rama>`.
   - Si la rama actual ya es una rama de feature (distinta de `main`/`master`) → **NO crees una nueva rama**. Continúa trabajando en la rama actual hasta que el usuario indique lo contrario.
4. Luego ejecuta en orden:

git add .
git commit -m "<type>(<area>): <descripción en español imperativo>"
git push -u origin <rama-actual>

## Tipos de commit permitidos

feature

## Reglas del mensaje

- Máximo 72 caracteres en la descripción corta
- Sin mayúscula inicial
- Sin punto final
- La descripción SIEMPRE en español imperativo
- La rama SIEMPRE en inglés kebab-case
- NO agregar `Co-Authored-By` ni ninguna firma de asistentes IA
- El autor del commit debe ser únicamente el usuario configurado en git

## Ejemplos correctos

feat(auth): agrega login con Google  
fix(form): corrige validación de email  
refactor(payment): separa lógica de validaciones

## Respuesta final

Responde en español con:

- rama usada (nueva o existente)
- tipo de commit
- mensaje final del commit
- resumen de cambios
