# insight-commerce-recsys
Sistema de recomendación de próxima compra - Proyecto Final Data Science 


## 🔀 Git Workflow — Ramas y Pull Requests

Este documento describe el flujo de trabajo oficial del equipo para gestión de ramas, integración de código y revisión mediante Pull Requests.

---

### 📐 Estructura de Ramas

```
main
 └── develop
        ├── feature/eda-exploratorio
        ├── feature/feature-engineering
        ├── feature/modelo-baseline
        ├── feature/modelo-lightgbm
        ├── feature/api-fastapi
        ├── feature/demo-streamlit
        ├── feature/dashboard-metricas
        └── hotfix/descripcion-del-fix
        └── ...
```

| Rama | Propósito | Desplegada en |
|------|-----------|---------------|
| `main` | Código en producción, siempre estable | 🟢 Producción |
| `develop` | Integración continua, base de trabajo | 🔵 Staging / QA |
| `feature/*` | Desarrollo de funcionalidades individuales | Local / Dev |

---

### 🔄 Flujo de Trabajo

#### 1. Crear una rama de feature

Siempre parte desde `develop`:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-descriptivo
```

**Convención de commits:**

```
tipo(scope): descripción breve en imperativo

Ejemplos:
feat(eda): agregar análisis de distribución de recompra por categoría
fix(features): corregir data leakage en variable days_since_last_order
docs(readme): actualizar instrucciones de instalación
refactor(model): separar pipeline de features en módulo independiente
test(api): agregar test de endpoint /recommend
chore(deps): actualizar lightgbm a versión 4.1

Tipos válidos: feat, fix, docs, refactor, test, chore, style, perf
```

### 2. Desarrollar y hacer commits

```bash
git add .
git commit -m "feat: descripción clara del cambio"
git push origin feature/nombre-descriptivo
```

### 3. Abrir un Pull Request hacia `develop`

- Ir al repositorio en GitHub / GitLab
- Crear un PR desde `feature/*` → `develop`
- Completar la plantilla de PR (ver sección abajo)
- Asignar al menos **un revisor** del equipo

### 4. Revisión de código

- El revisor analiza el código, deja comentarios y aprueba o solicita cambios
- El autor responde los comentarios y realiza las correcciones necesarias
- **No se puede hacer merge sin al menos 1 aprobación**

### 5. Merge a `develop`

Una vez aprobado:

```bash
# Se realiza desde la interfaz del repositorio (squash merge recomendado)
# o desde CLI:
git checkout develop
git merge --no-ff feature/nombre-descriptivo
git push origin develop
```

### 6. Release a `main`

Cuando `develop` está estable y validado en QA:

```bash
git checkout main
git pull origin main
git merge --no-ff develop
git tag -a v1.x.x -m "Release v1.x.x"
git push origin main --tags
```

---

## ✅ Reglas de Pull Requests

### Obligatorio para todo PR

- [ ] **Al menos 1 aprobación** de un miembro del equipo antes del merge
- [ ] Los checks de CI deben pasar (tests, lint, build)
- [ ] Sin conflictos con la rama base
- [ ] Descripción clara de los cambios realizados

### Protecciones de ramas

| Rama | Merge directo | PR requerido | Aprobaciones mínimas |
|------|:---:|:---:|:---:|
| `main` | ❌ | ✅ | 1 |
| `develop` | ❌ | ✅ | 1 |
| `feature/*` | ✅ | — | — |

> ⚙️ Estas reglas deben configurarse en **Settings → Branches → Branch protection rules** del repositorio.

---

## 📝 Plantilla de Pull Request

Al abrir un PR, usar esta estructura:

```markdown
## 📋 Descripción
Breve resumen de los cambios y el contexto del problema que resuelven.

## 🔗 Issue relacionado
Closes #NRO_ISSUE

## 🧪 Tipo de cambio
- [ ] Nueva funcionalidad
- [ ] Corrección de bug
- [ ] Refactor
- [ ] Documentación
- [ ] Configuración / chore

## ✅ Checklist
- [ ] El código sigue los estándares del proyecto
- [ ] He añadido/actualizado tests necesarios
- [ ] He actualizado la documentación si aplica
- [ ] He probado los cambios localmente
- [ ] No hay conflictos con la rama base
```