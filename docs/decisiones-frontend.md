# Decisiones del frontend

Registro de las librerías evaluadas para rehacer el frontend de AbastecePyme. Cada decisión
indica la necesidad, las opciones, la elegida, el motivo, las versiones y la fecha.

**Estado:** aprobada el 5 de noviembre de 2026 e implementada en los bloques 1 a 8 (ver
«Resultado» al final). Paquetes instalados con versión fija (`--save-exact`).

- **Fecha de la investigación:** 5 de noviembre de 2026.
- **Base del proyecto:** Angular `^22.1.0` (zoneless, standalone, signals), Node 24.15.0,
  TypeScript ~6.0.
- **Presupuesto:** 500 kB de aviso para el paquete inicial (`angular.json`).

## Cómo se midió

- **Versiones, licencias, fechas y `peerDependencies`:** consultadas con `npm view` en el
  registro oficial de npm.
- **Tamaños:** cada opción se empaquetó y minificó con esbuild, el mismo empaquetador que usa
  Angular, en una carpeta temporal fuera del proyecto. Se reporta el tamaño minificado y el
  comprimido con gzip, que es lo que descarga el navegador. Los tamaños incluyen las
  dependencias de cada librería.
- **Versiones recientes:** se descartaron como versión fija las publicadas hace menos de dos
  semanas (después del 22 de octubre de 2026).

## 1. Red en 3D

| Opción | Qué es | Ventajas | Desventajas | Tamaño (min / gzip) | Angular 22 | Última versión |
|---|---|---|---|---|---|---|
| `3d-force-graph` | Componente completo sobre three.js: escena, cámara, controles, hover, clic, etiquetas y flechas. | Lo más rápido de implementar: hover, clic, flechas direccionales y partículas sobre las aristas ya vienen hechos. Permite fijar la altura de cada nodo (`fy`) para el diseño por etapas. Tipos incluidos. MIT. | Es la opción más pesada, porque trae varios controles y utilidades que no usaremos. Su modo jerárquico (`dagMode`) falla con ciclos, así que no hay que usarlo. | 1437 kB / **393 kB** | Sí. Es JavaScript puro y no depende de Angular ni de zone.js. | 1.80.1 (29-09-2026) |
| `three-forcegraph` + `three` | Solo el objeto del grafo, para montarlo en una escena propia. | La mitad de peso. Mismo motor de fuerzas y mismo `fy` por etapa. Más control de la escena. Tipos incluidos. MIT. | Hay que programar cámara, controles, detección de hover y clic (raycasting) y etiquetas. | 701 kB / **188 kB** | Sí. Es JavaScript puro. | 1.43.6 (30-09-2026) |
| `three` + `OrbitControls` directo | three.js sin librería de grafos. | Lo más liviano y con control total. Como cada nodo ya tiene su etapa, su posición se puede calcular sin simulación de fuerzas. | Todo se programa a mano: posiciones, flechas, etiquetas, hover y clic. Es el camino más largo. | 553 kB / **138 kB** | Sí. Tipos en `@types/three`. | 0.187.0 (30-10-2026) |
| `angular-three` | Renderizador de Angular para three.js. | Escena declarativa en plantillas de Angular. | **Descartada:** su `peerDependencies` exige `@angular/core >=20 <22` y `three <0.183`, es decir, no soporta Angular 22. Además, requiere `ngxtension`. | — | **No** | 4.2.4 (15-07-2026) |

**Recomendación: `3d-force-graph` 1.80.1 con `three` 0.186.1.**

- Es la opción que deja la red funcionando más rápido y con menos código propio. El tiempo
  ahorrado se puede dedicar al resaltado, que es lo que importa para la Feature 4.
- El peso no afecta el paquete inicial, porque se carga de forma perezosa solo en las rutas que
  la usan (`/red` e `/impacto`). En la vista previa de `/` se cargaría con `@defer (on
  viewport)`, es decir, solo cuando la vista previa aparece en pantalla.
- **Diseño por etapas:** a cada nodo se le fija `fy` según su etapa en `/api/orden`.
  Los proveedores quedan abajo y los productos arriba. **No se usa `dagMode`**, así que un
  ciclo nunca rompe la vista. Si `/api/orden` responde 409, los nodos quedan libres y el ciclo
  se colorea en rojo.
- **Versión de `three`:** fijar 0.186.1 (24-09-2026), porque la 0.187.0 tiene menos de dos
  semanas. `3d-force-graph` acepta `three >=0.179 <1`.
- **Alternativa si el peso preocupa:** `three-forcegraph` reduce la descarga a la mitad
  (188 kB) a cambio de programar los controles y el raycasting. La migración es directa, porque
  usa el mismo modelo de datos.

### Respaldo 2D

Se mantienen **Cytoscape + `cytoscape-dagre`**, que ya están instaladas. Se muestran si WebGL
no está disponible o si el usuario prefiere menos movimiento (`prefers-reduced-motion`).
No hace falta ninguna librería nueva.

## 2. Componentes de interfaz

| Opción | Ventajas | Desventajas | Angular 22 |
|---|---|---|---|
| **CSS propio con variables** | Cero dependencias, peso mínimo y marca propia. Encaja con el estilo minimalista. | Los componentes accesibles complejos (menús, diálogos) hay que hacerlos a mano. | — |
| Angular CDK 22.2.6 | Comportamiento accesible sin estilos (overlay, foco, teclado). Es oficial y MIT. | Para lo que pide el proyecto (tabla, formularios, filtro, alertas) casi no hace falta. | Sí (`^22 \|\| ^23`) |
| Angular Material / PrimeNG | Kits completos de componentes. | Imponen su propio estilo y pesan más. Contradicen el principio de pocas dependencias. | No verificado: descartados por el principio de pocas dependencias. |

**Recomendación: CSS propio con variables.** Las cinco páginas no necesitan diálogos ni menús
complejos. Si más adelante hace falta uno accesible, se agrega solo **Angular CDK**, que es
oficial y no trae estilos.

## 3. Íconos

| Opción | Estado | Angular 22 |
|---|---|---|
| `@lucide/angular` | Paquete oficial actual de Lucide. Importa solo los íconos usados. Licencia ISC (equivalente a MIT). Tipos incluidos. | **Sí** (`>=17`) |
| `lucide-angular` | Paquete anterior, con nombre casi igual. | **No** (`13.x - 21.x`) |
| SVG en línea propios | Cero dependencias. | — |

**Recomendación: `@lucide/angular` 1.61.0** (21-10-2026). Lucide publica una versión casi a
diario solo para agregar íconos, así que se fija una con dos semanas o más. Ojo con el nombre:
`lucide-angular`, sin arroba, no soporta Angular 22. Si se usan menos de 8 íconos, también
basta con copiar los SVG a mano y evitar la dependencia.

## 4. Gráficos y cifras

| Opción | Tamaño (min / gzip) | Angular 22 | Licencia |
|---|---|---|---|
| ECharts 6.1.0 + `ngx-echarts` 22.0.0 (solo barras) | 435 kB / 150 kB | Sí (`>=22`) | Apache 2.0 / MIT |
| Chart.js 4.6.1 (solo barras) | 131 kB / 46 kB | Sí (JavaScript puro) | MIT |
| HTML y CSS | 0 | — | — |

**Recomendación: ninguna librería.** Las cifras del inicio (elementos, dependencias, etapas)
son números, y las etapas de Producción se dibujan mejor como columnas en HTML y CSS. Si en la
Feature 4 aparece un gráfico real, **Chart.js** es la opción liviana.

## 5. Animaciones

| Opción | Estado |
|---|---|
| `@angular/animations` | **Obsoleto** en Angular 22. npm recomienda `animate.enter` y `animate.leave`. |
| `animate.enter` / `animate.leave` + CSS | Incluido en Angular 22, sin dependencias. |
| GSAP 3.15.1 | Licencia propia ("Standard no-charge"), no MIT. Más de lo que se necesita. |

**Recomendación: CSS + `animate.enter`/`animate.leave` nativos de Angular**, con una regla
global para `prefers-reduced-motion` que desactive las transiciones.

## 6. Tipografía

**Recomendación: fuentes del sistema** (`system-ui, -apple-system, "Segoe UI", Roboto,
sans-serif`). Se ven modernas en todos los dispositivos, no pesan nada y no dependen de un
servicio externo.

## Resumen: lo que se instalaría

| Paquete | Versión | Uso | Carga |
|---|---|---|---|
| `3d-force-graph` | 1.80.1 | Red en 3D | Perezosa (`/red`, `/impacto`, vista previa con `@defer`) |
| `three` | 0.186.1 | Motor 3D (lo exige `3d-force-graph`) | Perezosa |
| `@types/three` | 0.186.x | Tipos (solo desarrollo) | — |
| `@lucide/angular` | 1.61.0 | Íconos (opcional) | Solo los íconos usados |

Todo lo demás se resuelve con lo que ya existe: Angular 22, CSS propio y Cytoscape para el
respaldo 2D.

## Siguiente paso

1. Aprobación de esta propuesta.
2. Prototipo desechable: una página de prueba que dibuje `/api/red` en 3D con la altura por
   etapa, para comprobar que compila con Angular 22 y que un ciclo no rompe la vista.
3. Actualizar este documento con el resultado del prototipo.

## Resultado (bloques 1 a 8)

Implementado el 5 de noviembre de 2026 con las librerías aprobadas.

| Medida | Antes | Después |
|---|---|---|
| Paquete inicial | 669 kB (superaba el presupuesto de 500 kB) | **329 kB** (82 kB transferidos) |
| Red 3D (`3d-force-graph` + `three`) | — | Chunk perezoso de 846 kB (200 kB transferidos), solo en `/`, `/red` e `/impacto` |
| Cytoscape (respaldo 2D) | En el paquete inicial | Chunk perezoso, solo si no hay WebGL o con `prefers-reduced-motion` |

Decisiones tomadas al implementar:

- **Altura por etapa sin `dagMode`:** cada elemento recibe `fy = (etapa − centro) × 55`. Con un
  ciclo (409) no hay etapas, la red queda libre y el ciclo se pinta en rojo. Una fuerza propia
  atrae los elementos al eje central para que los aislados no se alejen.
- **Etiquetas con `CSS2DRenderer`** (incluido en `three`, sin dependencia nueva). El
  renderizador escribe el `transform` del contenedor, así que el desplazamiento va en un `span`
  interior.
- **Encuadre:** `zoomToFit` temprano con temporizador y definitivo al detenerse la simulación;
  después no se mueve la cámara del usuario.
- **Signals solo al interactuar:** el bucle de animación no escribe signals. Clic → `seleccionar`.
- **Animaciones:** CSS y `@defer (on viewport)` para la vista previa del inicio; regla global para
  `prefers-reduced-motion`. No se usó `@angular/animations` (obsoleto).
- **`allowedCommonJsDependencies`:** se agregaron los paquetes `ngraph.*` (dependencias internas
  de `three-forcegraph`) para silenciar el aviso de CommonJS. No afecta el funcionamiento.

Verificación: `ng build` sin errores ni avisos; revisión en Chrome a 1440 px y 390 px de todas
las páginas, con red vacía, con datos de ejemplo y con un ciclo, sin errores en la consola.
Capturas en `docs/capturas/`.
