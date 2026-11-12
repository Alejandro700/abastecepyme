import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  afterNextRender,
  effect,
  input,
  output,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import type { ForceGraph3DInstance } from '3d-force-graph';
import type { CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';

import { GraphView } from '../Graph/graphView';
import { Red, Resaltado, TipoElemento } from '../Graph/models/catalog.models';
import {
  COLOR_AFECTADO,
  COLOR_FALLA,
  COLOR_REQUISITO,
  COLOR_TIPO,
  NOMBRE_TIPO,
  aristasDeCiclo,
} from '../core/presentacion';

const SEPARACION_ETAPA = 55;
const COLOR_APAGADO = '#d9d5ec';
const COLOR_ENLACE = '#8b80c9';

interface Nodo {
  id: string;
  tipo: TipoElemento;
  fy?: number;
  etiqueta?: CSS2DObject;
}
interface Enlace {
  source: string | Nodo;
  target: string | Nodo;
  clave: string;
}

/**
 * Red de dependencias en 3D (3d-force-graph sobre three.js), cargada de forma perezosa.
 *
 * - Altura por etapa: la etapa de preparación fija la posición vertical (proveedores abajo,
 *   productos arriba). Sin etapas (hay un ciclo) los elementos quedan libres. No se usa el
 *   `dagMode` de la librería, que falla con ciclos.
 * - Resaltado reutilizable: elemento consultado, alcanzados y dependencias de la cadena.
 * - Respaldo 2D (Cytoscape) si no hay WebGL o el usuario prefiere menos movimiento.
 * - Los signals solo cambian al interactuar (clic), nunca en cada frame.
 */
@Component({
  selector: 'app-red-3d',
  imports: [GraphView],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (modo2d()) {
      <app-graph-view [red]="red()" [resaltado]="resaltado()" />
    } @else {
      <div #lienzo class="lienzo" [attr.aria-label]="descripcion()" role="img"></div>
      @if (cargando()) {
        <div class="cargando"><div class="girador"></div></div>
      }
    }
  `,
  styles: `
    :host {
      display: block;
      position: relative;
      height: 100%;
      min-height: 280px;
    }
    .lienzo {
      position: absolute;
      inset: 0;
      overflow: hidden;
      border-radius: inherit;
    }
    .cargando {
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
    }
  `,
})
export class Red3d implements OnDestroy {
  readonly red = input.required<Red>();
  /** Etapa de cada elemento. Vacío cuando hay un ciclo. */
  readonly etapas = input<Map<string, number>>(new Map());
  /** Ciclo cerrado [A, B, A] a marcar en rojo. */
  readonly ciclo = input<string[]>([]);
  readonly resaltado = input<Resaltado | null>(null);
  readonly seleccionado = input<string | null>(null);
  /** false para vistas previas: sin controles, girando solas. */
  readonly interactivo = input(true);
  readonly fondo = input('#ffffff');

  readonly seleccionar = output<string | null>();

  protected readonly modo2d = signal(!webglDisponible() || prefiereMenosMovimiento());
  protected readonly cargando = signal(true);
  protected readonly descripcion = signal('Red de dependencias en 3D');

  private readonly lienzo = viewChild<ElementRef<HTMLDivElement>>('lienzo');
  private grafo?: ForceGraph3DInstance;
  private CSS2D?: typeof CSS2DObject;
  private observador?: ResizeObserver;
  private destruido = false;
  private encuadrar = true;
  private temporizador?: ReturnType<typeof setTimeout>;

  constructor() {
    afterNextRender(() => {
      if (!this.modo2d()) void this.iniciar();
    });

    // Datos: se reconstruyen cuando cambia la red o las etapas.
    effect(() => {
      const red = this.red();
      const etapas = this.etapas();
      if (this.cargando()) return;
      untracked(() => this.cargarDatos(red, etapas));
    });

    // Colores y grosor: se recalculan cuando cambia el resaltado, el ciclo o la selección.
    effect(() => {
      this.resaltado();
      this.ciclo();
      this.seleccionado();
      if (this.cargando()) return;
      untracked(() => this.pintar());
    });
  }

  private async iniciar(): Promise<void> {
    const div = this.lienzo()?.nativeElement;
    if (!div) return;
    try {
      const [{ default: ForceGraph3D }, { CSS2DRenderer, CSS2DObject }] = await Promise.all([
        import('3d-force-graph'),
        import('three/examples/jsm/renderers/CSS2DRenderer.js'),
      ]);
      if (this.destruido) return;
      this.CSS2D = CSS2DObject;

      const interactivo = this.interactivo();
      this.grafo = new ForceGraph3D(div, {
        controlType: 'orbit',
        extraRenderers: [new CSS2DRenderer() as never],
      })
        .width(div.clientWidth)
        .height(div.clientHeight)
        .backgroundColor(this.fondo())
        .showNavInfo(false)
        .nodeRelSize(6)
        .nodeOpacity(1)
        .nodeResolution(24)
        .nodeLabel((n) => `${(n as Nodo).id} · ${NOMBRE_TIPO[(n as Nodo).tipo]}`)
        .nodeThreeObjectExtend(true)
        .nodeThreeObject((n) => (n as Nodo).etiqueta ?? (null as never))
        .linkOpacity(0.85)
        .linkDirectionalArrowLength(7)
        .linkDirectionalArrowRelPos(1)
        .linkDirectionalParticleWidth(2.5)
        .linkDirectionalParticleSpeed(0.012)
        .cooldownTicks(120)
        .cooldownTime(2500)
        .enableNodeDrag(false)
        .enableNavigationControls(interactivo)
        .enablePointerInteraction(interactivo)
        .onNodeClick((n) => this.seleccionar.emit((n as Nodo).id))
        .onBackgroundClick(() => this.seleccionar.emit(null))
        .onNodeHover((n) => (div.style.cursor = n ? 'pointer' : ''))
        .onEngineStop(() => this.encuadrarVista());

      // Más separación horizontal para que los nombres no se encimen.
      (this.grafo.d3Force('charge') as unknown as { strength(v: number): void }).strength(-160);
      (this.grafo.d3Force('link') as unknown as { distance(v: number): void }).distance(50);
      // Atracción suave al eje central para que los elementos sin dependencias no se alejen.
      // En vertical solo se aplica a los que no tienen etapa fija (diseño libre por ciclo).
      type Punto = Partial<Record<'x' | 'y' | 'z' | 'vx' | 'vy' | 'vz', number>> & { fy?: number };
      let nodos: Punto[] = [];
      const centrar = Object.assign(
        (alpha: number) => {
          for (const n of nodos) {
            n.vx = (n.vx ?? 0) - (n.x ?? 0) * 0.06 * alpha;
            n.vz = (n.vz ?? 0) - (n.z ?? 0) * 0.06 * alpha;
            if (n.fy == null) n.vy = (n.vy ?? 0) - (n.y ?? 0) * 0.06 * alpha;
          }
        },
        { initialize: (ns: typeof nodos) => (nodos = ns) },
      );
      this.grafo.d3Force('centrar', centrar as never);

      if (!interactivo) {
        const controles = this.grafo.controls() as { autoRotate: boolean; autoRotateSpeed: number };
        controles.autoRotate = true;
        controles.autoRotateSpeed = 1.2;
      }

      this.observador = new ResizeObserver(() =>
        this.grafo?.width(div.clientWidth).height(div.clientHeight),
      );
      this.observador.observe(div);

      this.cargando.set(false);
    } catch (e) {
      console.error('No se pudo iniciar la red 3D; se usa la vista 2D.', e);
      this.modo2d.set(true);
    }
  }

  private cargarDatos(red: Red, etapas: Map<string, number>): void {
    if (!this.grafo || !this.CSS2D) return;
    const total = Math.max(0, ...etapas.values());
    const centro = (total + 1) / 2;

    const nodos: Nodo[] = red.elementos.map((e) => {
      // CSS2DRenderer escribe el transform del div exterior; el desplazamiento va en el span.
      const div = document.createElement('div');
      const texto = document.createElement('span');
      texto.className = 'etiqueta-nodo';
      texto.textContent = e.id;
      div.appendChild(texto);
      const etapa = etapas.get(e.id);
      return {
        ...e,
        fy: etapa === undefined ? undefined : (etapa - centro) * SEPARACION_ETAPA,
        etiqueta: new this.CSS2D!(div),
      };
    });
    const enlaces: Enlace[] = red.dependencias.map((d) => ({
      source: d.origen_id,
      target: d.destino_id,
      clave: `${d.origen_id}->${d.destino_id}`,
    }));

    this.descripcion.set(
      `Red con ${red.total_elementos} elementos y ${red.total_dependencias} dependencias` +
        (total ? ` en ${total} etapas.` : '.'),
    );
    this.encuadrar = true;
    this.grafo.graphData({ nodes: nodos, links: enlaces });
    this.pintar();
    // Respaldo por si la simulación tarda en detenerse (pestañas en segundo plano, equipos lentos).
    clearTimeout(this.temporizador);
    this.temporizador = setTimeout(() => this.encuadrarVista(false), 1200);
  }

  /**
   * Encuadra la red. El temporizador da un primer encuadre temprano; el definitivo llega cuando
   * la simulación se detiene. Después no se vuelve a mover la cámara del usuario.
   */
  private encuadrarVista(final = true): void {
    if (!this.encuadrar || !this.grafo) return;
    if (final) this.encuadrar = false;
    this.grafo.zoomToFit(prefiereMenosMovimiento() ? 0 : 500, 40);
  }

  /** Aplica colores, grosores y etiquetas según el resaltado, el ciclo y la selección. */
  private pintar(): void {
    const grafo = this.grafo;
    if (!grafo) return;
    const resaltado = this.resaltado();
    const seleccionado = this.seleccionado();
    const enCiclo = new Set(this.ciclo());
    const aristasCiclo = new Set(aristasDeCiclo(this.ciclo()));
    const alcanzados = new Set(resaltado?.elementos ?? []);
    const cadena = new Set(resaltado?.aristas ?? []);
    const impacto = resaltado?.sentido === 'IMPACTO';

    const colorNodo = (n: Nodo): string => {
      if (resaltado) {
        if (n.id === resaltado.foco) return impacto ? COLOR_FALLA : COLOR_TIPO[n.tipo];
        if (alcanzados.has(n.id)) return impacto ? COLOR_AFECTADO : COLOR_REQUISITO;
        return COLOR_APAGADO;
      }
      return enCiclo.has(n.id) ? COLOR_FALLA : COLOR_TIPO[n.tipo];
    };
    const destacada = (l: Enlace) => (resaltado ? cadena.has(l.clave) : aristasCiclo.has(l.clave));
    const colorEnlace = (l: Enlace): string => {
      if (destacada(l)) return resaltado ? (impacto ? COLOR_FALLA : COLOR_REQUISITO) : COLOR_FALLA;
      return resaltado ? COLOR_APAGADO : COLOR_ENLACE;
    };

    grafo
      .nodeColor((n) => colorNodo(n as Nodo))
      .nodeVal((n) =>
        (n as Nodo).id === seleccionado || (n as Nodo).id === resaltado?.foco ? 2.6 : 1,
      )
      .linkColor((l) => colorEnlace(l as unknown as Enlace))
      .linkWidth((l) => (destacada(l as unknown as Enlace) ? 2.2 : 0.8))
      .linkDirectionalArrowColor((l) => colorEnlace(l as unknown as Enlace))
      .linkDirectionalParticles((l) =>
        resaltado && destacada(l as unknown as Enlace) && !prefiereMenosMovimiento() ? 3 : 0,
      );

    for (const n of grafo.graphData().nodes as Nodo[]) {
      const apagado = !!resaltado && n.id !== resaltado.foco && !alcanzados.has(n.id);
      n.etiqueta?.element.firstElementChild?.classList.toggle('apagada', apagado);
    }
  }

  ngOnDestroy(): void {
    this.destruido = true;
    clearTimeout(this.temporizador);
    this.observador?.disconnect();
    this.grafo?.pauseAnimation();
    this.grafo?._destructor();
    this.lienzo()?.nativeElement.replaceChildren();
  }
}

function webglDisponible(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!(canvas.getContext('webgl2') ?? canvas.getContext('webgl'));
  } catch {
    return false;
  }
}

function prefiereMenosMovimiento(): boolean {
  return matchMedia('(prefers-reduced-motion: reduce)').matches;
}
