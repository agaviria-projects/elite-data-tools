
### 1. Objetivo

El sistema **Enrutamiento Operativo por Cuadrillas (Control ANS)** está diseñado para apoyar la operación diaria de **Elite Ingenieros**, permitiendo **planificar, distribuir y enrutar pedidos** a cuadrillas de campo usando información proveniente de la extracción (Fénix/ANS) en un archivo Excel con coordenadas **lat/lng**.

**¿Qué hace el sistema?**
- Carga el Excel de extracción y valida datos clave (incluye control de filas con **lat/lng inválidos**).
- Permite filtrar el universo de trabajo por **CONCEPTO, ESTADO, ACTIVIDAD, ZONA y REPORTE TÉCNICO**.
- Genera rutas por cuadrilla (módulo **GENERAL**) y las muestra en **mapa** para validación visual.(Opcional)
- Construye el **Plan Diario ANS (8×15)** priorizando pedidos críticos por estado (**VENCIDO → ALERTA_0 → ALERTA → A TIEMPO → SIN FECHA**).
- Entrega salidas listas para operación: **links de Google Maps (por tramos)**, **exportación a Excel** y **guía de visita para WhatsApp**.

**¿Para quién es?**
- Coordinación operativa, supervisión de campo y personal que asigna y controla la ejecución de pedidos por cuadrillas.

**Alcance y consideraciones**
- El sistema sirve para **planificación y control operativo**.
- La calidad del resultado depende de que el Excel conserve nombres de columnas y coordenadas correctas.

### 2. Requisitos

### 2.1 Archivo de entrada
- **Formato:** Excel `.xlsx` (no CSV).
- **Origen recomendado:** archivo de extracción (FENIX_ANS.xlsx) sin ediciones manuales.
- **Una sola hoja** o la hoja principal con los pedidos (si hay varias, mantener la de pedidos como primera o claramente identificada).

### 2.2 Columnas mínimas requeridas (obligatorias)
> Sin estas columnas el mapa/ruteo no puede operar correctamente:

- **pedido** — identificador único del caso.
- **lat** y **lng** — coordenadas numéricas.
- **direccion** — texto de dirección (para referencia operativa).
- **estado** — estado ANS (VENCIDO / ALERTA_0 / ALERTA / A TIEMPO / SIN FECHA).
- **actividad** — tipo de actividad del pedido.
- **zona** — zona operativa (para filtros).

### 2.3 Columnas recomendadas (mejoran el plan y la operación)
- **fecha_limite_ans** — priorización por vencimiento.
- **nombre_cliente** — para búsqueda y comunicación.
- **celular_contacto** — para guías WhatsApp.
- **reporte_tecnico** — para filtrar “SIN DATOS” vs reportados.
- **municipio / subzona** — para análisis y segmentación.

### 2.4 Recomendaciones de formato (para evitar errores)
- **No cambiar nombres de columnas** (ni tildes, ni espacios, ni mayúsculas/minúsculas si ya vienen estandarizadas).
- **lat/lng deben ser números** (no texto). Evitar comas como separador decimal si te genera errores.
- Evitar **celdas combinadas**, encabezados duplicados o filas “de resumen” dentro de la tabla.
- Mantener **una fila de encabezados** y datos debajo (estructura tipo tabla).
- Si hay valores vacíos, usar vacío real (no “NA”, “null”, “.”) especialmente en lat/lng.

### 2.5 Tamaño y rendimiento
- Recomendado: hasta **10.000 registros** por carga (más es posible, pero puede tardar más en mapa y dashboard).
- Para mejor velocidad: filtra primero (ZONA/ACTIVIDAD/ESTADO) y luego genera rutas/plan.

### 2.6 Validación rápida antes de cargar (checklist)
- [ ] El archivo abre sin errores y está en `.xlsx`
- [ ] Existe columna **pedido**
- [ ] Existe **lat** y **lng** con valores numéricos
- [ ] Existe **estado** y **actividad**
- [ ] Existe **fecha_limite_ans** (recomendado para priorización ANS)

### 3. Flujo rápido (5 pasos)
1) Cargar Excel  
2) Configurar filtros  
3) Aplicar filtros  
4) Generar rutas / Plan diario  
5) Exportar / Abrir en Google Maps

### Esquema General de Operación

El siguiente diagrama representa el flujo completo del sistema desde la carga del archivo hasta la salida operativa final.

Interpretación del flujo:

1. El usuario carga el Excel.
2. Configura y aplica filtros.
3. Puede generar rutas en modo GENERAL (opcional).
4. El paso obligatorio para operación diaria es generar el Plan Diario ANS (8×15).
5. Finalmente se exporta la información para ejecución en campo.

Importante:
El módulo GENERAL es un módulo de simulación y análisis territorial.
El Plan Diario ANS (8×15) es el plan oficial de ejecución.
[[IMAGEN_FLUJO]]

### 4. Carga del archivo

La carga del archivo es el primer paso obligatorio del sistema.  
Desde el panel lateral, el usuario selecciona el archivo Excel de extracción para iniciar el proceso.

---

### 4.1 Formato del Excel

Para que el sistema funcione correctamente, el archivo debe cumplir con las siguientes condiciones:

- **Formato:** `.xlsx` (no CSV).
- **Origen recomendado:** archivo de extracción oficial (FENIX_ANS.xlsx).
- **Estructura:** una sola hoja principal con:
  - Encabezados en la primera fila.
  - Datos debajo (estructura tipo tabla).
- No debe contener:
  - Filas de totales dentro de la tabla.
  - Celdas combinadas.
  - Encabezados duplicados.

> ⚠️ Si se modifica manualmente el archivo (columnas, nombres, formatos), pueden generarse errores en filtros, mapa o plan diario.

---

### 4.2 Errores comunes (lat/lng, columnas, tipos)

Los errores más frecuentes al cargar el archivo son:

#### 🔹 Coordenadas (lat/lng)
- Valores vacíos.
- Coordenadas fuera de rango.
- Valores iguales a 0.

Si las coordenadas no son numéricas válidas, el pedido no podrá ubicarse en el mapa.

#### 🔹 Nombres de columnas modificados
Cambiar:
- mayúsculas/minúsculas,
- tildes,
- espacios,
- guiones,

puede impedir que el sistema reconozca las columnas obligatorias.

#### 🔹 Tipos de datos incorrectos
- `fecha_limite_ans` en texto.
- `estado` con valores distintos a los esperados.
- `zona` con valores inconsistentes, diferencias en mayúsculas/minúsculas ejemplo:  Metropolitana, METROPOLITANA,metropolitana.
### ¿Por qué esto es un problema?

El sistema construye los filtros y agrupaciones a partir de los valores exactos de la columna.

---

### 4.3 Mensajes del sistema (filas inválidas)

Al cargar el archivo, el sistema realiza validaciones automáticas:

- Verifica columnas obligatorias.
- Identifica filas con lat/lng inválidos.
- Separa registros no aptos para mapa.
- Muestra advertencias si algo no cumple el formato esperado.

Ejemplos de mensajes:

- ✅ Archivo cargado correctamente.
- ⚠️ Se encontraron X filas con coordenadas inválidas.
- ❌ Falta columna obligatoria.

> Recomendación: si hay filas inválidas, corregir la fuente antes de planificar el día.

---

### 5. Filtros

Los filtros definen el universo de trabajo antes de generar rutas o plan diario.

Después de seleccionar filtros, es obligatorio presionar:

**Aplicar filtros**

Si no se presiona, el sistema seguirá mostrando el conjunto anterior.

---

### 5.1 CONCEPTO

Permite filtrar por Concepto PPRG ó PROG.

---

### 5.2 ESTADO

Permite priorizar pedidos según criticidad ANS:

- VENCIDO
- ALERTA_0
- ALERTA
- A TIEMPO
- SIN FECHA

Para operación diaria se recomienda incluir como mínimo:

**VENCIDO + ALERTA_0**

---

### 5.3 ACTIVIDAD

Filtra por tipo de actividad en caso de ser requerido.

-ACAMN, ACREV, AEJDO,ALECA, ALEGA, ALEGN, AMRTR, APLIN, ARTER, DIPRE, INPRE, REEQU.

---

### 5.4 ZONA

Define la zona operativa oficial.

Ejemplo:
- Metropolitana
- Suroeste
- Occidente
- Nordeste
- Oriente

Se recomienda construir el plan diario por zona; en el dia a dia sera METROPOLITANA.

---

### 5.5 REPORTE TÉCNICO (SIN DATOS)

Permite separar pedidos:

- SIN DATOS
- Con reporte técnico

---

### 6. Módulo Mapa (GENERAL)

Este módulo es de simulación y análisis territorial.

No es el flujo oficial obligatorio del día.

---

### 6.1 Bodega / Origen (punto de partida)

Este módulo define el **punto de inicio del recorrido** para el ruteo y los cálculos de distancia (KM).  
Por defecto, el sistema utiliza las **coordenadas oficiales de la bodega**, que sirven como referencia para iniciar la visita hacia los pedidos asignados.

**📍 Dirección de la bodega (referencia):**  
**Cl 12 Sur # 51B-29, San Fernando, Medellín**

**¿Qué puedes hacer aquí?**
- Ver la **Latitud** y **Longitud** de la bodega (valores predeterminados).
- (Opcional) Activar **“Editar coordenadas manualmente”** para **cambiar temporalmente** el origen si la operación lo requiere.

**¿Cuándo conviene editar el origen?**
- Cuando el punto de salida real no es la bodega (ej. salida desde una base alterna, punto de encuentro, o inicio en campo).
- Cuando se desea simular rutas desde otra ubicación para validar tiempos/recorridos.

**Importante**
- Si no activas el toggle, el sistema toma siempre la bodega como origen.
- Cambiar el origen afecta: **KM estimados**, **secuencia sugerida** y **rutas en Google Maps** (porque el recorrido se calcula desde ese punto).

---

### 6.2 Toggle “No mezclar zona_geo ”

Este toggle controla **si el sistema puede mezclar o no los pedidos entre las Zonas GEO** al momento de generar rutas en el **Mapa General (GENERAL)**.

#### ✅ ¿Qué es “zona_geo”?
Es una **macro-zona geográfica** (clasificación territorial) que agrupa los pedidos por sectores amplios, por ejemplo:
- **NORTE**
- **SUR**
- **ORIENTE**
- **OCCIDENTE**
- **CENTRO**

> En pocas palabras: **zona** = zona operativa: METROPOLITANA SUR, ORIENTE,OCCIDENTE,NORDESTE,SUROESTE.  
> **zona_geo** = sector geográfico grande (macro-zona)

---

### 🟢 Si el toggle está en ON (Activado): “No mezclar zona_geo”
**El sistema NO mezcla pedidos de diferentes zonas_geo.**

- Si estás trabajando **ORIENTE**, las rutas se arman **solo con pedidos ORIENTE**.
- Si estás trabajando **SUR**, las rutas se arman **solo con pedidos SUR**.
- Así sucesivamente (NORTE / OCCIDENTE / CENTRO).

✅ **Ventaja:** rutas más coherentes territorialmente (menos saltos entre puntas de la ciudad).  
✅ **Recomendado para:** operación diaria y cuadrillas asignadas por sector.

---

### ⚪ Si el toggle está en OFF (Desactivado): “Se permite mezclar zona_geo”
**El sistema SÍ puede mezclar pedidos entre zonas_geo.**

Ejemplo:
- Una misma ruta podría incluir pedidos de **ORIENTE + CENTRO + SUR** si están relativamente cerca o si el algoritmo los agrupa así.

✅ **Ventaja:** puede mejorar el balanceo si hay pocos pedidos en una zona_geo o si están muy dispersos.  
⚠️ **Riesgo:** rutas menos “limpias” y más difíciles de ejecutar (más traslados largos o cruces).

---

### 6.3 Generar rutas (MAPA GENERAL)

Este paso es **opcional**.

Al presionar **“Generar rutas (MAPA GENERAL)”**, el sistema:

- Agrupa pedidos según la cantidad de cuadrillas seleccionadas.
- Los distribuye por cercanía geográfica.
- Muestra en el mapa las rutas simuladas.

Sirve para:

- Ver concentración de pedidos.
- Analizar distribución territorial.
- Evaluar carga aproximada por cuadrilla.

⚠️ Importante:
Este módulo es de **simulación y análisis**.  
No es el plan oficial del día.

---

### 6.4 Vista satelital

La opción **Vista satelital** cambia el tipo de mapa para mostrar imágenes reales del terreno.

Sirve para:

- Validar accesos reales a los pedidos.
- Identificar zonas rurales o de difícil ingreso.
- Ver si los puntos están muy dispersos.

📌 **Cuándo usarla**
- Cuando hay direcciones complejas.
- Cuando los pedidos están en zonas rurales.
- Cuando se quiere confirmar que la ubicación sea coherente.

> Si no es necesario validar terreno, puedes usar el mapa normal.


### 6.5 ¿Cómo funciona la distribución de pedidos en el módulo General?

Cuando seleccionas la cantidad de cuadrillas en el campo **“Cuadrillas (GENERAL)”**, el sistema divide los pedidos filtrados en esa cantidad de grupos.

Ejemplo práctico:

- Total pedidos filtrados: **504**
- Cuadrillas seleccionadas: **8**

El sistema intentará repartirlos en **8 grupos**, buscando que cada cuadrilla tenga una carga similar.

En promedio sería:

504 ÷ 8 = **63 pedidos por cuadrilla (aprox.)**

⚠️ Importante:

- No siempre será exactamente el mismo número para todas.
- La distribución se basa principalmente en **cercanía geográfica**.
- Si está activado “No mezclar zona_geo”, el sistema primero respeta las zonas y luego reparte dentro de cada una.
- Puede haber pequeñas diferencias (ej: 62, 63 o 64 pedidos) dependiendo de cómo estén ubicados los puntos.

---

### ¿Este módulo prioriza por fecha límite ANS?

No.

### 📊 Análisis e interpretación del Mapa General

El resultado que muestra el módulo GENERAL debe interpretarse como una **simulación territorial**.

La distribución depende de:

- Los filtros aplicados (zona, estado, actividad, etc.).
- La cantidad de cuadrillas configuradas.
- La concentración geográfica de los pedidos.

#### 🔎 ¿Por qué en algunas cuadrillas veo más pedidos críticos que en otras?

Esto puede ocurrir porque:

- En una zona específica hay mayor cantidad de pedidos próximos a vencer.
- El listado puede estar ordenado por estado o fecha límite.
- La concentración territorial no es uniforme.

Es importante entender que:

> El módulo GENERAL distribuye por ubicación geográfica.  
> El análisis final depende de cómo el usuario revise la información.

Si el objetivo es garantizar prioridad estricta por ANS  
(VENCIDO → ALERTA_0 → ALERTA → A TIEMPO → SIN FECHA),  
se debe utilizar el módulo **Plan Diario ANS (8×15)**, que sí organiza el plan bajo esa lógica operativa.

---

### ¿Cuándo usar General y cuándo usar Plan Diario ANS?

Usa **GENERAL** cuando:
- Quieres analizar concentración territorial.
- Quieres simular distribución geográfica.
- Estás revisando carga por sector.

Usa **Plan Diario ANS (8×15)** cuando:
- Vas a construir el plan oficial del día.
- Necesitas priorizar pedidos críticos.
- Debes limitar cantidad por cuadrilla según capacidad.

### 7. Módulo Cuadrillas (General)

Este módulo muestra el resultado generado en el MAPA GENERAL.

Aquí puedes ver:

- Qué pedidos quedaron asignados a cada cuadrilla.
- Cuántos pedidos tiene cada grupo.
- Cómo quedó distribuida la carga.

---

### 7.1 Tabla por cuadrilla

Permite:
- Ver pedidos asignados.
- Detectar sobrecargas.
- Validar coherencia territorial.

---

### 7.2 Abrir Google Maps

Genera enlaces por cuadrilla o por tramos.

Útil para ejecución en campo.

---

### 7.3 Exportar Excel

Permite descargar:.
- Consolidado general.(Descargar Excel)

---
### 8. Módulo Plan Diario ANS (8×15)

Este es el **paso oficial de ejecución diaria**.

Aquí el sistema ya no simula.  
Aquí se construye el plan real que se enviará a campo.

---

### 8.1 Parámetros (Configuración del plan)

Antes de generar el plan debes definir:

- **Número de cuadrillas**
- **Pedidos por cuadrilla (capacidad)**

Ejemplo común:
8 cuadrillas × 15 pedidos = hasta 120 pedidos asignados.

🔎 Importante:

- Si tienes 504 pedidos y configuras 8 cuadrillas × 15 pedidos:
  → El sistema asignará **los 120 más prioritarios**.
  → Los demás quedarán pendientes para otro plan.

- Si quieres cubrir más pedidos:
  → Aumenta el número de cuadrillas
  → O aumenta la capacidad por cuadrilla

Este módulo **no reparte todo automáticamente**, sino que construye el plan según la capacidad definida.

---

### 8.2 Cómo funciona la prioridad ANS

El sistema asigna en este orden obligatorio:

1. VENCIDO  
2. ALERTA_0  
3. ALERTA  
4. A TIEMPO 

Esto significa:

- Primero llena las cuadrillas con los más críticos.
- Luego continúa con los siguientes estados.
- Siempre respeta ese orden.

📌 Este módulo SÍ prioriza por fecha límite ANS.
No es territorial, es operativo.

---

### 8.3 Resumen del plan generado

Después de generar el plan verás:

- Cuántas cuadrillas se crearon.
- Cuántos pedidos tiene cada una.
- En qué zona están asignados.

---

### 8.4 Detalle por cuadrilla

Puedes seleccionar una cuadrilla y ver:

- Lista completa de pedidos.
- Orden de visita (ORDEN_VISITA).
- Estado ANS.
- Dirección y datos de contacto.

Este es el listado real que usará el técnico.

---

### 8.5 Indicadores de ruta (KM)

Cada cuadrilla muestra:

- Número de paradas.
- Total estimado de KM.
- Promedio por tramo.
- Tramo más largo.
- Distancia desde bodega al primer punto.

📌 Estos kilómetros son estimados en línea recta.
Sirven para validar si la ruta tiene sentido,
pero no reemplazan tiempos reales de tráfico.

### 📏 ¿Cómo se calculan los kilómetros (KM)?

Los kilómetros mostrados en el Plan Diario ANS se calculan con base en:

- Las coordenadas (lat / lng)
- Que vienen directamente desde la extracción del sistema Fénix (archivo Excel cargado)

El sistema usa esas coordenadas para estimar la distancia entre cada punto.

---

### 🔹 KM bajo → Ruta compacta

Significa que los pedidos están cerca entre sí.

Ejemplo:
- Mismo barrio o sector.
- Poco desplazamiento entre paradas.

👉 Generalmente es una ruta más eficiente.

---

### 🔹 KM alto → Ruta dispersa

Significa que los pedidos están más separados geográficamente.

Ejemplo:
- Diferentes barrios o zonas alejadas.
- Mayor desplazamiento entre visitas.

👉 Puede implicar más tiempo en carretera.

---

### 🔎 Importante sobre los KM

- Los kilómetros son **estimados en línea recta** entre coordenadas.
- No consideran tráfico, semáforos ni sentido real de las vías.
- Si una coordenada en el Excel está mal, el cálculo puede verse afectado.

Por eso es clave que el archivo de extracción tenga coordenadas correctas.

---

### 8.6 Auditoría de tramos

Permite revisar:

- Orden real de visita.
- Estado ANS por punto.
- Distancia entre cada parada.

Sirve para validar que:

- Los VENCIDOS estén al inicio.
- La secuencia tenga lógica territorial.
- No haya saltos innecesarios.

---

### 8.7 WhatsApp – Guía de visita

El sistema genera un texto listo para copiar y pegar en WhatsApp:

Incluye:

- Número de pedido
- Nombre del cliente
- Celular Contacto
- Dirección
- Fecha límite ANS
- Enlace directo a Google Maps

Esto facilita enviar la ruta al técnico sin editar manualmente.

---

### 8.8 Descarga de planillas (PLAN 8×15)

En esta sección puedes generar el archivo final que se entregará a operación.

---

#### ✅ Selección de columnas

Antes de descargar, puedes escoger qué columnas deseas incluir en la planilla.

Por ejemplo:

- Pedido
- Cliente
- Celular
- Dirección
- Actividad
- Fecha límite ANS
- Estado
- Zona
- Orden de visita
- Cuadrilla asignada

Esto permite:

- Imprimir solo la información necesaria.
- Adaptar el documento según lo que solicite el coordinador.
- Crear un informe más limpio si se requiere enviar a supervisión.

Si deseas incluir toda la información disponible,
simplemente deja todas las columnas seleccionadas.

---

#### 📄 Opciones de descarga

Puedes generar:

- **Excel consolidado (PLAN COMPLETO 8×15)**  
  → Incluye todas las cuadrillas en un solo archivo.

- **Excel individual por cuadrilla**  
  → Genera un archivo específico para cada cuadrilla.

- **Enlaces de Google Maps por tramos**  
  → Para abrir directamente las rutas organizadas.

---

#### 🎯 ¿Para qué sirve este archivo?

Este Excel es el **soporte oficial de ejecución diaria**.

Puede utilizarse para:

- Entregar al coordinador de cuadrillas.
- Imprimir como guía física.
- Guardar evidencia del plan generado.
- Compartir con supervisión o gerencia.

---

📌 Recomendación:
Antes de descargar, verifica que:

- El número de pedidos por cuadrilla sea correcto.
- Las columnas seleccionadas sean las necesarias.
- El plan generado corresponda al día operativo.

---

### 8.9 Mapa del Plan ANS

Este mapa muestra la ruta generada para cada cuadrilla.

Aquí puedes:

- Ver el orden de visita.
- Confirmar que los puntos estén bien ubicados.
- Validar que la ruta tenga sentido geográfico.

---

#### 🔎 ¿Qué muestra el mapa?

- Los puntos numerados representan el orden de visita.
- Las líneas muestran la secuencia de recorrido.
- Puedes cambiar entre vista normal o satelital.

---

#### 📌 ¿Para qué sirve?

- Confirmar que los pedidos estén en la zona correcta.
- Detectar si hay saltos extraños en la ruta.
- Validar que el recorrido sea lógico antes de enviarlo a campo.

---

#### ⚠️ Recomendación

Si ves puntos muy alejados o ubicaciones incorrectas:

- Revisa las coordenadas en el archivo Excel.
- Verifica que la zona_geo esté correcta.

El mapa es una herramienta de validación visual antes de ejecutar el plan.

---

### 🔴 Diferencia clave frente al módulo General

- GENERAL = análisis territorial (simulación)
- PLAN DIARIO ANS = ejecución oficial con prioridad ANS

Si necesitas garantizar atención a lo más crítico,
siempre usa el Plan Diario ANS.

---

### ✅ Checklist antes de enviar el Plan Diario

Antes de compartir el plan con las cuadrillas, verifica:

- [ ] Se aplicaron los filtros correctos.
- [ ] El número de cuadrillas es el correcto.
- [ ] La capacidad por cuadrilla es adecuada.
- [ ] Los pedidos críticos (VENCIDOS / ALERTA_0) están incluidos.
- [ ] El mapa no presenta saltos extraños.
- [ ] Las columnas necesarias están incluidas en la planilla.
- [ ] El archivo descargado corresponde al día operativo.

Si todo está validado, el plan puede enviarse a ejecución.

---
### 9. Módulo Datos

Esta sección muestra el detalle real de los pedidos después de aplicar los filtros.

Aquí puedes validar qué pedidos están activos antes de generar rutas o plan.

---

### 9.1 Cantidad de registros

El sistema muestra:

**Registros: 504** (ejemplo)

Este número indica cuántos pedidos cumplen con los filtros seleccionados.

📌 Importante:

La cantidad de pedidos también depende de que cada registro tenga:

- Latitud (lat)
- Longitud (lng)

Si un pedido no tiene coordenadas válidas, no podrá visualizarse en mapa ni entrar en el cálculo de rutas.

Por eso el número puede cambiar si:

- Se aplican filtros.
- Hay pedidos sin coordenadas.
- Existen registros incompletos.

---

### 9.2 Buscar pedido (opcional)

La barra "Buscar pedido" permite encontrar rápidamente un caso específico.

Puedes escribir:

- Número de pedido

Esto sirve para:

- Verificar si un pedido quedó incluido.
- Confirmar en qué cuadrilla fue asignado.
- Validar estado y datos antes de enviar el plan.

Ejemplo práctico:

Si un técnico pregunta:
“¿En qué cuadrilla quedó el pedido 23678984?”

Puedes buscarlo aquí y ver inmediatamente:

- Cuadrilla asignada (cuadrilla_plan)
- Estado ANS
- Fecha límite
- Datos del cliente

---

### 🎯 ¿Para qué sirve este módulo?

- Confirmar asignaciones individuales.
- Revisar información detallada sin necesidad de abrir Excel.
- Controlar que el filtro aplicado sea el correcto.

---

### 10. Dashboard Operativo

Esta sección responde una pregunta clave:

📊 **¿Cómo está la operación hoy?**

El dashboard permite entender rápidamente:

- Cuánta carga hay.
- Qué tan crítica es.
- En qué zonas se concentra.
- Qué actividades están generando mayor presión.

Es una vista ejecutiva para tomar decisiones.

En la parte superior del Dashboard encontrarás tres filtros:

- Zona Geo
- Estado
- Actividad

Estos filtros permiten analizar la operación de manera específica.

---

#### 🔎 ¿Qué sucede cuando aplicas un filtro?

Al seleccionar una opción:

- Se actualizan los KPIs.
- Se recalculan los porcentajes.
- Cambian los gráficos.
- Se ajusta el resumen operativo.
- Se modifica la tabla de urgentes.

Es decir:

👉 Todo el Dashboard se adapta a la selección realizada.

---

#### 📍 Ejemplo práctico

Si eliges:

Zona Geo → SUR

El Dashboard mostrará únicamente la información correspondiente a la zona SUR:

- Total de pedidos en SUR.
- Cuántos están vencidos en SUR.
- Porcentaje de riesgo en SUR.
- Actividades más frecuentes en SUR.

---

Si seleccionas:

Estado → VENCIDO

Verás únicamente:

- Pedidos vencidos.
- Su distribución por zona.
- Su actividad dominante.

---

#### 🎯 ¿Para qué sirven estos filtros?

Permiten:

- Analizar una zona específica.
- Revisar un estado en particular.
- Entender qué actividad está generando más presión.
- Tomar decisiones antes de generar el Plan Diario.

---

### 10.1 KPIs – Panorama general

Lo primero que vemos es el resumen numérico:

- **Total pedidos filtrados** → universo actual de trabajo.
- **Vencidos** → atención inmediata.
- **Alerta_0** → prioridad del día.
- **Alerta** → riesgo cercano.
- **A Tiempo** → dentro del ANS.
- **Sin Fecha** → requiere revisión.

📌 Aquí se detecta rápidamente si hay presión operativa.

Ejemplo:
Si los VENCIDOS aumentan, la operación está en riesgo.
Si la mayoría está A TIEMPO, el control es saludable.

---

### 10.2 % por estado (ANS)

Este gráfico muestra la proporción real de la operación.

Pregunta que responde:

👉 ¿Qué porcentaje de mi carga está en riesgo?

No es lo mismo:

- 10 vencidos sobre 50 pedidos (20%)
- Que 10 vencidos sobre 500 pedidos (2%)

Aquí se mide la presión real.

---

### 10.3 Estado (conteo)

Este gráfico muestra cantidades reales por estado.

Sirve para:

- Comparar volumen.
- Detectar si ALERTA está creciendo.
- Revisar comportamiento general.

Es una vista rápida de equilibrio entre estados.

---

### 10.4 Top zonas (zona_geo)

Pregunta clave:

📍 ¿Dónde está concentrada la carga?

Permite identificar:

- Zona más cargada.
- Zonas con mayor presión.
- Necesidad de redistribución.

Ejemplo:
Si CENTRO tiene 38% de la carga,
puede requerir más cuadrillas o revisión territorial.

---

### 10.5 Top actividades

Pregunta clave:

🛠 ¿Qué tipo de actividad está generando más pedidos?

Sirve para:

- Detectar repetitividad.
- Identificar actividad dominante.
- Apoyar decisiones de especialización por cuadrilla.

Ejemplo:
Si ALEGA representa 30%,
podría requerir enfoque técnico específico.

---

### 10.6 Estados por zona

Este gráfico cruza:

Zona + Estado ANS

Permite ver:

- En qué zona hay más vencidos.
- Si una zona específica está en riesgo.
- Si la presión es general o localizada.

Ejemplo:
Si SUR tiene muchos ALERTA_0,
se debe priorizar en el plan diario.

---

### 10.7 Detalle operativo (VENCIDO + ALERTA_0)

Aquí se listan únicamente los pedidos críticos.

Sirve para:

- Validación rápida.
- Confirmar que no se escape ningún vencido.

Este es el control previo a la ejecución.

---

### 🎯 ¿Qué aporta el Dashboard?

No es solo visualización.

Es una herramienta para:

- Tomar decisiones antes de generar el plan.
- Identificar riesgo operativo.
- Ajustar cuadrillas si es necesario.
- Priorizar zonas críticas.

Si el Dashboard muestra presión alta,
el Plan Diario ANS debe construirse con enfoque urgente.

---

### 11. Buenas prácticas

- Siempre presionar **Aplicar filtros** después de cambiar filtros.
- No modificar manualmente nombres de columnas.
- Validar lat/lng antes de generar rutas..
- Guardar exportaciones para trazabilidad.

### 12. Cierre

El sistema **Enrutamiento Operativo por Cuadrillas – Control ANS** es una herramienta de apoyo para:

- Planificar.
- Priorizar.
- Visualizar.
- Ejecutar.
- Controlar la operación diaria.

La calidad del resultado depende de:

- La calidad del archivo de entrada.
- La correcta aplicación de filtros.
- La validación antes de enviar el plan.

Un uso ordenado del sistema reduce riesgos, mejora tiempos de respuesta y fortalece el control operativo.