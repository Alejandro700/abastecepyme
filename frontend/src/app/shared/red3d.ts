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
import type * as THREE from 'three';
import type { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import type {
  CSS2DObject,
  CSS2DRenderer,
} from 'three/examples/jsm/renderers/CSS2DRenderer.js';

import { GraphView } from '../Graph/graphView';
import { Red, Resaltado, TipoElemento } from '../Graph/models/catalog.models';
import {
  COLOR_AFECTADO,
  COLOR_FALLA,
  COLOR_REQUISITO,
  COLOR_TIPO,
  NOMBRE_TIPO_PLURAL,
  aristasDeCiclo,
} from '../core/presentacion';

type Three = typeof THREE;

/** Separación entre estaciones (eje X) y entre franjas de etapa (eje Z). */
const SEP_X = 16;
const SEP_Z = 18;
const ALTO_BANDA = 0.8;
const GRIS = '#c9cbd6';
const COLOR_BANDA = '#3f4659';
const COLOR_MARCO = '#cbd2de';
const COLOR_ANDON_VERDE = '#16a34a';
const FILA_POR_TIPO: Record<TipoElemento, number> = { PROVEEDOR: 1, INSUMO: 2, PRODUCTO: 3 };

type EstadoEstacion = 'normal' | 'falla' | 'afectado' | 'foco' | 'requisito' | 'apagado' | 'ciclo';

interface Tinte {
  mat: THREE.MeshStandardMaterial;
  base: THREE.Color;
}

interface Estacion {
  id: string;
  tipo: TipoElemento;
  grupo: THREE.Group;
  tintes: Tinte[];
  andon: { rojo: THREE.MeshStandardMaterial; ambar: THREE.MeshStandardMaterial; verde: THREE.MeshStandardMaterial };
  anillo: THREE.Mesh<THREE.RingGeometry, THREE.MeshBasicMaterial>;
  brazo?: THREE.Group;
  etiqueta: CSS2DObject;
  estado: EstadoEstacion;
  opera: boolean;
}

interface Banda {
  clave: string;
  puntos: THREE.Vector3[];
  largos: number[];
  total: number;
  cuerpo: THREE.MeshStandardMaterial;
  cinta: THREE.MeshStandardMaterial;
  cajas: THREE.Mesh[];
  avance: number;
  mueve: boolean;
  visible: boolean;
}

/**
 * La red como una planta de producción en 3D (three.js, cargado de forma perezosa).
 *
 * - Cada franja del piso es una etapa de preparación: la etapa 1 al frente, los productos al
 *   fondo. Con un ciclo no hay etapas y las franjas se ordenan por tipo.
 * - Proveedor = muelle de recepción, insumo = estantería, producto = estación de ensamble.
 * - Dependencia A → B (A necesita B) = banda transportadora: el material va de B hacia A.
 * - Torre de luces por estación: verde opera, ámbar se detiene, rojo falla.
 * - Al simular una falla, las bandas de la cadena se paran y los brazos de ensamble también.
 * - Los signals solo cambian al interactuar; el bucle de animación no toca Angular.
 * - Respaldo 2D (Cytoscape) si no hay WebGL o el usuario prefiere menos movimiento.
 */
@Component({
  selector: 'app-red-3d',
  imports: [GraphView],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (modo2d()) {
      <app-graph-view [red]="red()" [resaltado]="resaltado()" />
      @if (motivo2d(); as m) {
        <p class="motivo">
          Vista simplificada: {{ m }}
          @if (puedeForzar()) {
            <button type="button" (click)="forzar3d()">Ver en 3D</button>
          }
        </p>
      }
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
      touch-action: none;
    }
    .motivo {
      position: absolute;
      top: 10px;
      left: 10px;
      right: 10px;
      margin: 0;
      padding: 6px 10px;
      border-radius: var(--radio-sm);
      background: rgb(255 255 255 / 0.95);
      border: 1px solid var(--borde);
      font-size: 0.8125rem;
      color: var(--texto-suave);
    }
    .motivo button {
      margin-left: 6px;
      padding: 2px 10px;
      border: 1px solid var(--marca);
      border-radius: var(--radio-sm);
      background: var(--marca-suave);
      color: var(--marca);
      font: inherit;
      font-weight: 600;
      cursor: pointer;
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
  /** false para vistas previas: sin controles, girando sola. */
  readonly interactivo = input(true);
  /** Se conserva por compatibilidad; la planta usa su propio fondo. */
  readonly fondo = input('#ffffff');

  readonly seleccionar = output<string | null>();

  protected readonly modo2d = signal(!webglDisponible() || prefiereMenosMovimiento());
  /** Por qué se muestra la vista 2D, para que el usuario sepa qué pasa. */
  protected readonly motivo2d = signal<string | null>(
    !webglDisponible()
      ? 'tu navegador no tiene WebGL activo (activa la aceleración por hardware y reinicia el navegador).'
      : prefiereMenosMovimiento()
        ? 'tu sistema pide reducir el movimiento.'
        : null,
  );
  /** Solo se puede forzar el 3D si el motivo es la preferencia de movimiento. */
  protected readonly puedeForzar = signal(webglDisponible() && prefiereMenosMovimiento());
  protected readonly cargando = signal(true);
  protected readonly descripcion = signal('Planta de producción en 3D');

  private readonly lienzo = viewChild<ElementRef<HTMLDivElement>>('lienzo');

  private T?: Three;
  private CSS2D?: typeof CSS2DObject;
  private renderer?: THREE.WebGLRenderer;
  private etiquetador?: CSS2DRenderer;
  private escena?: THREE.Scene;
  private camara?: THREE.PerspectiveCamera;
  private controles?: OrbitControls;
  private sol?: THREE.DirectionalLight;
  private planta?: THREE.Group;
  private reloj?: THREE.Clock;
  private raycaster?: THREE.Raycaster;

  private estaciones = new Map<string, Estacion>();
  private bandas: Banda[] = [];
  private firmaEncuadre = '';
  private visible = true;
  private destruido = false;
  private limpiezas: (() => void)[] = [];

  constructor() {
    afterNextRender(() => {
      if (!this.modo2d()) void this.iniciar();
    });

    // Datos: la planta se reconstruye cuando cambia la red o las etapas.
    effect(() => {
      const red = this.red();
      const etapas = this.etapas();
      if (this.cargando()) return;
      untracked(() => this.construir(red, etapas));
    });

    // Estado visual: se recalcula cuando cambia el resaltado, el ciclo o la selección.
    effect(() => {
      this.resaltado();
      this.ciclo();
      this.seleccionado();
      if (this.cargando()) return;
      untracked(() => this.pintar());
    });
  }

  // ---------------------------------------------------------------- Inicio

  private async iniciar(): Promise<void> {
    const div = this.lienzo()?.nativeElement;
    if (!div) return;
    try {
      const [T, { OrbitControls }, { CSS2DRenderer, CSS2DObject }] = await Promise.all([
        import('three'),
        import('three/examples/jsm/controls/OrbitControls.js'),
        import('three/examples/jsm/renderers/CSS2DRenderer.js'),
      ]);
      if (this.destruido) return;
      this.T = T;
      this.CSS2D = CSS2DObject;

      const renderer = new T.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
      renderer.setSize(div.clientWidth, div.clientHeight);
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = T.PCFSoftShadowMap;
      renderer.toneMapping = T.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.05;
      div.appendChild(renderer.domElement);
      this.renderer = renderer;

      const etiquetador = new CSS2DRenderer();
      etiquetador.setSize(div.clientWidth, div.clientHeight);
      Object.assign(etiquetador.domElement.style, {
        position: 'absolute',
        inset: '0',
        pointerEvents: 'none',
      });
      div.appendChild(etiquetador.domElement);
      this.etiquetador = etiquetador;

      const escena = new T.Scene();
      escena.background = new T.Color('#eceaf5');
      escena.fog = new T.Fog('#eceaf5', 220, 520);
      this.escena = escena;

      escena.add(new T.HemisphereLight('#ffffff', '#cfc8e8', 1.1));
      const sol = new T.DirectionalLight('#fff6ea', 2.2);
      sol.position.set(-40, 80, 50);
      sol.castShadow = true;
      sol.shadow.mapSize.set(2048, 2048);
      sol.shadow.bias = -0.0004;
      sol.shadow.normalBias = 0.04;
      escena.add(sol, sol.target);
      this.sol = sol;

      // Piso exterior.
      const exterior = new T.Mesh(
        new T.PlaneGeometry(1200, 1200),
        new T.MeshStandardMaterial({ color: '#e3e0ee', roughness: 1 }),
      );
      exterior.rotation.x = -Math.PI / 2;
      exterior.position.y = -0.02;
      exterior.receiveShadow = true;
      escena.add(exterior);

      const camara = new T.PerspectiveCamera(38, div.clientWidth / div.clientHeight, 0.5, 1500);
      camara.position.set(0, 70, 90);
      this.camara = camara;

      const interactivo = this.interactivo();
      const controles = new OrbitControls(camara, renderer.domElement);
      controles.enableDamping = true;
      controles.dampingFactor = 0.08;
      controles.maxPolarAngle = Math.PI * 0.44;
      controles.minDistance = 18;
      controles.maxDistance = 320;
      controles.enabled = interactivo;
      if (!interactivo) {
        controles.autoRotate = true;
        controles.autoRotateSpeed = 0.8;
      }
      this.controles = controles;

      this.reloj = new T.Clock();
      this.raycaster = new T.Raycaster();
      if (interactivo) this.escucharPuntero(renderer.domElement);

      const observador = new ResizeObserver(() => this.ajustarTamano(div));
      observador.observe(div);
      const visibilidad = new IntersectionObserver(([e]) => (this.visible = e.isIntersecting));
      visibilidad.observe(div);
      this.limpiezas.push(() => observador.disconnect(), () => visibilidad.disconnect());

      renderer.setAnimationLoop(() => this.cuadro());
      this.cargando.set(false);
    } catch (e) {
      console.error('No se pudo iniciar la planta 3D; se usa la vista 2D.', e);
      this.motivo2d.set(`la vista 3D no pudo iniciar (${(e as Error).message}).`);
      this.puedeForzar.set(false);
      this.modo2d.set(true);
    }
  }

  /** El usuario prefiere menos movimiento pero pide ver el 3D igual. */
  protected forzar3d(): void {
    this.modo2d.set(false);
    this.motivo2d.set(null);
    // Espera a que el lienzo exista en la plantilla antes de iniciar.
    setTimeout(() => void this.iniciar());
  }

  private ajustarTamano(div: HTMLDivElement): void {
    if (!this.renderer || !this.camara || !div.clientWidth || !div.clientHeight) return;
    this.renderer.setSize(div.clientWidth, div.clientHeight);
    this.etiquetador?.setSize(div.clientWidth, div.clientHeight);
    this.camara.aspect = div.clientWidth / div.clientHeight;
    this.camara.updateProjectionMatrix();
  }

  /** Clic (sin arrastre) para seleccionar y cursor de mano sobre una estación. */
  private escucharPuntero(lienzo: HTMLCanvasElement): void {
    let inicio: { x: number; y: number } | null = null;
    const abajo = (e: PointerEvent) => (inicio = { x: e.clientX, y: e.clientY });
    const arriba = (e: PointerEvent) => {
      if (!inicio || Math.hypot(e.clientX - inicio.x, e.clientY - inicio.y) > 6) return;
      this.seleccionar.emit(this.estacionBajo(e, lienzo));
    };
    const mover = (e: PointerEvent) => {
      lienzo.style.cursor = this.estacionBajo(e, lienzo) ? 'pointer' : '';
    };
    lienzo.addEventListener('pointerdown', abajo);
    lienzo.addEventListener('pointerup', arriba);
    lienzo.addEventListener('pointermove', mover);
    this.limpiezas.push(() => {
      lienzo.removeEventListener('pointerdown', abajo);
      lienzo.removeEventListener('pointerup', arriba);
      lienzo.removeEventListener('pointermove', mover);
    });
  }

  private estacionBajo(e: PointerEvent, lienzo: HTMLCanvasElement): string | null {
    const T = this.T;
    if (!T || !this.camara || !this.raycaster || !this.planta) return null;
    const r = lienzo.getBoundingClientRect();
    const ndc = new T.Vector2(
      ((e.clientX - r.left) / r.width) * 2 - 1,
      -((e.clientY - r.top) / r.height) * 2 + 1,
    );
    this.raycaster.setFromCamera(ndc, this.camara);
    const grupos = [...this.estaciones.values()].map((s) => s.grupo);
    const golpe = this.raycaster.intersectObjects(grupos, true)[0];
    let objeto: THREE.Object3D | null = golpe?.object ?? null;
    while (objeto && !objeto.userData['id']) objeto = objeto.parent;
    return (objeto?.userData['id'] as string | undefined) ?? null;
  }

  // ---------------------------------------------------------------- Construcción

  private construir(red: Red, etapas: Map<string, number>): void {
    const T = this.T;
    if (!T || !this.escena) return;
    this.desmontarPlanta();

    const planta = new T.Group();
    this.planta = planta;
    this.escena.add(planta);

    // Filas: la etapa de cada elemento; si hay un ciclo (sin etapas), su tipo.
    const porEtapa = etapas.size > 0;
    const filaDe = (id: string, tipo: TipoElemento) =>
      porEtapa ? (etapas.get(id) ?? 1) : FILA_POR_TIPO[tipo];
    const numerosFila = [...new Set(red.elementos.map((e) => filaDe(e.id, e.tipo)))].sort(
      (a, b) => a - b,
    );
    const filas = numerosFila.map((n) => red.elementos.filter((e) => filaDe(e.id, e.tipo) === n));
    const columnas = Math.max(1, ...filas.map((f) => f.length));
    const ancho = columnas * SEP_X;
    const fondo = Math.max(1, filas.length) * SEP_Z;

    // Posiciones en una cuadrícula: las filas más cortas quedan centradas en sus casillas, así
    // los pasillos entre casillas siempre están libres para las bandas.
    const posicion = new Map<string, THREE.Vector3>();
    filas.forEach((fila, k) => {
      const z = ((filas.length - 1) / 2 - k) * SEP_Z;
      const desfase = Math.floor((columnas - fila.length) / 2);
      fila.forEach((e, i) => {
        posicion.set(e.id, new T.Vector3((desfase + i - (columnas - 1) / 2) * SEP_X, 0, z));
      });
    });

    this.construirNave(planta, ancho, fondo, numerosFila, porEtapa);

    for (const e of red.elementos) {
      const estacion = this.construirEstacion(e.id, e.tipo);
      estacion.grupo.position.copy(posicion.get(e.id)!);
      planta.add(estacion.grupo);
      this.estaciones.set(e.id, estacion);
    }

    red.dependencias.forEach((d, k) => {
      const a = posicion.get(d.origen_id);
      const b = posicion.get(d.destino_id);
      if (a && b) this.bandas.push(this.construirBanda(planta, `${d.origen_id}->${d.destino_id}`, b, a, k));
    });

    this.ajustarSombras(ancho, fondo);
    this.descripcion.set(
      `Planta con ${red.total_elementos} elementos y ${red.total_dependencias} dependencias` +
        (porEtapa ? ` en ${numerosFila.length} etapas.` : '.'),
    );

    // Encuadra solo si cambió el tamaño de la planta; si no, respeta la cámara del usuario.
    const firma = `${columnas}x${filas.length}`;
    if (firma !== this.firmaEncuadre) {
      this.firmaEncuadre = firma;
      this.encuadrar(ancho, fondo);
    }
    this.pintar();
  }

  /** Piso de la nave, franjas de etapa con su rótulo, líneas de seguridad y muros bajos. */
  private construirNave(
    planta: THREE.Group,
    ancho: number,
    fondo: number,
    numerosFila: number[],
    porEtapa: boolean,
  ): void {
    const T = this.T!;
    const margen = 10;
    const w = ancho + margen * 2;
    const d = fondo + margen;

    const piso = new T.Mesh(
      new T.BoxGeometry(w, 0.3, d),
      new T.MeshStandardMaterial({ color: '#f7f7fb', roughness: 0.85 }),
    );
    piso.position.y = -0.15;
    piso.receiveShadow = true;
    planta.add(piso);

    numerosFila.forEach((n, k) => {
      const z = ((numerosFila.length - 1) / 2 - k) * SEP_Z;
      const franja = new T.Mesh(
        new T.PlaneGeometry(w - 2, SEP_Z - 2),
        new T.MeshStandardMaterial({ color: k % 2 ? '#ffffff' : '#f1edfd', roughness: 0.9 }),
      );
      franja.rotation.x = -Math.PI / 2;
      franja.position.set(0, 0.01, z);
      franja.receiveShadow = true;
      planta.add(franja);

      // Líneas amarillas de seguridad entre franjas.
      for (const borde of [-1, 1]) {
        const linea = new T.Mesh(
          new T.PlaneGeometry(w - 2, 0.35),
          new T.MeshStandardMaterial({ color: '#f5c518', roughness: 0.6 }),
        );
        linea.rotation.x = -Math.PI / 2;
        linea.position.set(0, 0.02, z + borde * (SEP_Z / 2 - 1));
        planta.add(linea);
      }

      const texto = porEtapa
        ? `ETAPA ${n}`
        : NOMBRE_TIPO_PLURAL[(Object.keys(FILA_POR_TIPO) as TipoElemento[]).find((t) => FILA_POR_TIPO[t] === n)!].toUpperCase();
      const rotulo = this.rotuloPiso(texto);
      rotulo.position.set(-w / 2 + 6.5, 0.03, z + SEP_Z / 2 - 3);
      planta.add(rotulo);
    });

    // Muros bajos al fondo y a los lados; el frente queda abierto hacia los muelles.
    const muro = new T.MeshStandardMaterial({ color: '#dcd8ea', roughness: 0.9 });
    const fondoMuro = new T.Mesh(new T.BoxGeometry(w, 2.2, 0.6), muro);
    fondoMuro.position.set(0, 1.1, -d / 2);
    const izq = new T.Mesh(new T.BoxGeometry(0.6, 2.2, d), muro);
    izq.position.set(-w / 2, 1.1, 0);
    const der = izq.clone();
    der.position.x = w / 2;
    for (const m of [fondoMuro, izq, der]) {
      m.castShadow = m.receiveShadow = true;
      planta.add(m);
    }
  }

  /** Texto pintado en el piso (CanvasTexture). */
  private rotuloPiso(texto: string): THREE.Mesh {
    const T = this.T!;
    const lienzo = document.createElement('canvas');
    lienzo.width = 512;
    lienzo.height = 128;
    const ctx = lienzo.getContext('2d')!;
    ctx.fillStyle = 'rgba(15, 28, 107, 0.55)';
    ctx.font = '800 72px system-ui, Segoe UI, Arial, sans-serif';
    ctx.textBaseline = 'middle';
    ctx.fillText(texto, 8, 64);
    const textura = new T.CanvasTexture(lienzo);
    textura.anisotropy = 4;
    const malla = new T.Mesh(
      new T.PlaneGeometry(12, 3),
      new T.MeshBasicMaterial({ map: textura, transparent: true, depthWrite: false }),
    );
    malla.rotation.x = -Math.PI / 2;
    return malla;
  }

  private construirEstacion(id: string, tipo: TipoElemento): Estacion {
    const T = this.T!;
    const grupo = new T.Group();
    grupo.userData['id'] = id;
    const tintes: Tinte[] = [];

    const caja = (w: number, h: number, d: number, color: string, x: number, y: number, z: number) => {
      const mat = new T.MeshStandardMaterial({ color, roughness: 0.7, metalness: 0.05 });
      tintes.push({ mat, base: new T.Color(color) });
      const m = new T.Mesh(new T.BoxGeometry(w, h, d), mat);
      m.position.set(x, y, z);
      m.castShadow = m.receiveShadow = true;
      grupo.add(m);
      return m;
    };
    const cilindro = (r: number, h: number, color: string, x: number, y: number, z: number) => {
      const mat = new T.MeshStandardMaterial({ color, roughness: 0.5, metalness: 0.2 });
      tintes.push({ mat, base: new T.Color(color) });
      const m = new T.Mesh(new T.CylinderGeometry(r, r, h, 20), mat);
      m.position.set(x, y, z);
      m.castShadow = true;
      grupo.add(m);
      return m;
    };

    let alto = 4;
    let brazo: THREE.Group | undefined;
    const color = COLOR_TIPO[tipo];

    if (tipo === 'PROVEEDOR') {
      // Muelle de recepción: plataforma, portón naranja con marco, toldo y pallets.
      caja(8, 1.2, 6, '#b8bccb', 0, 0.6, 0);
      caja(8, 5, 0.6, '#eceaf3', 0, 3.7, -2.7);
      caja(5.2, 3.6, 0.2, color, 0, 3, -2.3);
      for (let i = 0; i < 4; i++) caja(5.2, 0.12, 0.25, '#c2410c', 0, 1.6 + i * 0.9, -2.15);
      caja(8.6, 0.3, 2.6, color, 0, 6.3, -1.6);
      caja(1.8, 0.3, 1.8, '#c8a06a', 2.6, 1.35, 1.6);
      caja(1.6, 1.2, 1.6, '#e7c58e', 2.6, 2.1, 1.6);
      caja(1.8, 0.3, 1.8, '#c8a06a', -2.4, 1.35, 1.8);
      alto = 6.5;
    } else if (tipo === 'INSUMO') {
      // Estantería con cajas de material.
      for (const x of [-3.4, 3.4]) for (const z of [-1.2, 1.2]) caja(0.3, 6, 0.3, '#334155', x, 3, z);
      for (const y of [0.4, 2.4, 4.4]) caja(7.2, 0.18, 2.8, '#f59e0b', 0, y, 0);
      const tonos = [color, '#22c55e', '#e7c58e', '#15803d', '#d6b98a'];
      let t = 0;
      for (const y of [0.95, 2.95, 4.95])
        for (const x of [-2.3, 0, 2.3]) {
          if ((t * 7) % 5 === 3) {
            t++;
            continue;
          }
          caja(1.9, 1, 2.2, tonos[t++ % tonos.length], x, y, 0);
        }
      alto = 6.4;
    } else {
      // Estación de ensamble: base, mesa, producto terminado y brazo robótico.
      caja(8, 0.25, 6, '#e4e1f0', 0, 0.12, 0);
      caja(5, 0.35, 3, '#d4d0e6', 1, 2.2, 0.4);
      for (const x of [-1.2, 3.2]) for (const z of [-0.8, 1.6]) caja(0.25, 2, 0.25, '#64748b', x, 1.1, z);
      caja(1.6, 1.2, 1.4, color, 1.6, 3, 0.4);
      caja(2.4, 2.8, 2, color, -2.6, 1.4, -1.6);
      caja(2.42, 0.5, 2.02, '#4f2fc4', -2.6, 2.4, -1.6);

      brazo = new T.Group();
      brazo.position.set(-1.6, 0.25, 1.8);
      const base = cilindro(0.8, 0.6, '#475569', 0, 0.3, 0);
      grupo.remove(base);
      brazo.add(base);
      const hombro = new T.Group();
      hombro.position.y = 0.6;
      brazo.add(hombro);
      const segmento = (largo: number) => {
        const mat = new T.MeshStandardMaterial({ color: '#f97316', roughness: 0.5 });
        tintes.push({ mat, base: new T.Color('#f97316') });
        const m = new T.Mesh(new T.BoxGeometry(0.5, largo, 0.5), mat);
        m.position.y = largo / 2;
        m.castShadow = true;
        return m;
      };
      const tramo1 = segmento(3);
      hombro.add(tramo1);
      hombro.rotation.z = -0.5;
      const codo = new T.Group();
      codo.position.y = 3;
      codo.rotation.z = 1.4;
      hombro.add(codo);
      codo.add(segmento(2.4));
      grupo.add(brazo);
      alto = 5;
    }

    // Torre de luces (andon): rojo, ámbar y verde.
    const luz = (c: string) =>
      new T.MeshStandardMaterial({ color: '#d7d9e0', emissive: new T.Color(c), emissiveIntensity: 0, roughness: 0.3 });
    const andon = { rojo: luz(COLOR_FALLA), ambar: luz(COLOR_AFECTADO), verde: luz(COLOR_ANDON_VERDE) };
    const poste = new T.Mesh(
      new T.CylinderGeometry(0.12, 0.12, alto + 1, 8),
      new T.MeshStandardMaterial({ color: '#475569' }),
    );
    poste.position.set(3.6, (alto + 1) / 2, -2.4);
    grupo.add(poste);
    [andon.verde, andon.ambar, andon.rojo].forEach((mat, i) => {
      const m = new T.Mesh(new T.CylinderGeometry(0.42, 0.42, 0.6, 16), mat);
      m.position.set(3.6, alto + 1.3 + i * 0.64, -2.4);
      grupo.add(m);
    });

    // Anillo en el piso para destacar la estación.
    const anillo = new T.Mesh(
      new T.RingGeometry(5.6, 6.3, 48),
      new T.MeshBasicMaterial({ color: COLOR_FALLA, transparent: true, opacity: 0.9, depthWrite: false }),
    );
    anillo.rotation.x = -Math.PI / 2;
    anillo.position.y = 0.05;
    anillo.visible = false;
    grupo.add(anillo);

    // Etiqueta (CSS2DRenderer escribe el transform del div exterior; el estilo va en el span).
    const div = document.createElement('div');
    const texto = document.createElement('span');
    texto.className = 'etiqueta-nodo';
    texto.textContent = id;
    div.appendChild(texto);
    const etiqueta = new this.CSS2D!(div);
    etiqueta.position.set(0, alto + 3.6, 0);
    grupo.add(etiqueta);

    return { id, tipo, grupo, tintes, andon, anillo, brazo, etiqueta, estado: 'normal', opera: true };
  }

  /**
   * Banda transportadora de `desde` (lo que se necesita) a `hacia` (quien lo necesita). Recorre
   * los pasillos entre franjas y entre casillas, así nunca atraviesa una estación.
   */
  private construirBanda(
    planta: THREE.Group,
    clave: string,
    desde: THREE.Vector3,
    hacia: THREE.Vector3,
    indice: number,
  ): Banda {
    const T = this.T!;
    const carril = ((indice % 5) - 2) * 1.5;
    const dz = Math.sign(hacia.z - desde.z) || -1;
    const salida = desde.z + dz * (SEP_Z / 2);
    const llegada = hacia.z - dz * (SEP_Z / 2);
    const sx = hacia.x >= desde.x ? 1 : -1;

    const crudos: [number, number][] = [[desde.x, desde.z], [desde.x, salida]];
    if (Math.abs(salida - llegada) < 0.01 || Math.sign(hacia.z - desde.z) === 0) {
      crudos.push([hacia.x, salida]);
    } else {
      const pasillo = desde.x + sx * (SEP_X / 2);
      crudos.push([pasillo, salida], [pasillo, llegada], [hacia.x, llegada]);
    }
    crudos.push([hacia.x, hacia.z]);

    // Carril propio para que las bandas paralelas no se encimen.
    const puntos = crudos.map(([x, z], i) => {
      const interior = i > 0 && i < crudos.length - 1;
      return new T.Vector3(x + carril, ALTO_BANDA, interior ? z + carril : z);
    });
    // Recorta los extremos para que la banda empiece y termine en el borde de la estación.
    recortar(puntos[0], puntos[1], 3.4);
    recortar(puntos[puntos.length - 1], puntos[puntos.length - 2], 3.4);
    const limpios = puntos.filter((p, i) => i === 0 || p.distanceTo(puntos[i - 1]) > 0.05);

    const cuerpo = new T.MeshStandardMaterial({ color: COLOR_MARCO, roughness: 0.6, metalness: 0.3 });
    const cinta = new T.MeshStandardMaterial({ color: COLOR_BANDA, roughness: 0.9 });
    const largos: number[] = [];
    for (let i = 1; i < limpios.length; i++) {
      const a = limpios[i - 1];
      const b = limpios[i];
      const largo = a.distanceTo(b);
      largos.push(largo);
      const medio = a.clone().add(b).multiplyScalar(0.5);
      const angulo = Math.atan2(b.x - a.x, b.z - a.z);

      const base = new T.Mesh(new T.BoxGeometry(1.3, ALTO_BANDA - 0.1, largo + 1.3), cuerpo);
      base.position.set(medio.x, (ALTO_BANDA - 0.1) / 2, medio.z);
      base.rotation.y = angulo;
      base.castShadow = base.receiveShadow = true;
      const tapete = new T.Mesh(new T.BoxGeometry(1.0, 0.12, largo + 1.0), cinta);
      tapete.position.set(medio.x, ALTO_BANDA, medio.z);
      tapete.rotation.y = angulo;
      planta.add(base, tapete);
    }
    const total = largos.reduce((s, l) => s + l, 0);

    const cajas: THREE.Mesh[] = [];
    const cantidad = Math.max(1, Math.round(total / 7));
    const matCaja = new T.MeshStandardMaterial({ color: '#d6b98a', roughness: 0.8 });
    for (let i = 0; i < cantidad; i++) {
      const c = new T.Mesh(new T.BoxGeometry(0.75, 0.6, 0.75), matCaja);
      c.castShadow = true;
      c.userData['fase'] = i / cantidad;
      planta.add(c);
      cajas.push(c);
    }

    return { clave, puntos: limpios, largos, total, cuerpo, cinta, cajas, avance: 0, mueve: true, visible: true };
  }

  private ajustarSombras(ancho: number, fondo: number): void {
    const sol = this.sol;
    if (!sol) return;
    const r = Math.max(ancho, fondo) * 0.75 + 20;
    const cam = sol.shadow.camera;
    cam.left = cam.bottom = -r;
    cam.right = cam.top = r;
    cam.near = 1;
    cam.far = 300;
    cam.updateProjectionMatrix();
  }

  private encuadrar(ancho: number, fondo: number): void {
    const camara = this.camara;
    if (!camara || !this.controles) return;
    const tamano = Math.max(ancho * 0.75 / Math.max(camara.aspect, 0.6), fondo, 30);
    const distancia = tamano * 1.25 + 25;
    camara.position.set(ancho * 0.12, distancia * 0.62, distancia * 0.78);
    this.controles.target.set(0, 0, -2);
    this.controles.update();
  }

  // ---------------------------------------------------------------- Estado visual

  /** Aplica colores, luces y movimiento según el resaltado, el ciclo y la selección. */
  private pintar(): void {
    const T = this.T;
    if (!T) return;
    const resaltado = this.resaltado();
    const seleccionado = this.seleccionado();
    const enCiclo = new Set(this.ciclo());
    const aristasCiclo = new Set(aristasDeCiclo(this.ciclo()));
    const alcanzados = new Set(resaltado?.elementos ?? []);
    const cadena = new Set(resaltado?.aristas ?? []);
    const impacto = resaltado?.sentido === 'IMPACTO';
    const gris = new T.Color(GRIS);

    for (const s of this.estaciones.values()) {
      let estado: EstadoEstacion = 'normal';
      if (resaltado) {
        if (s.id === resaltado.foco) estado = impacto ? 'falla' : 'foco';
        else if (alcanzados.has(s.id)) estado = impacto ? 'afectado' : 'requisito';
        else estado = 'apagado';
      } else if (enCiclo.has(s.id)) {
        estado = 'ciclo';
      }
      s.estado = estado;
      s.opera = estado === 'normal' || estado === 'foco' || estado === 'requisito';

      const emisivo =
        estado === 'falla' || estado === 'ciclo' ? COLOR_FALLA : estado === 'afectado' ? COLOR_AFECTADO : '#000000';
      const intensidad = estado === 'falla' ? 0.35 : estado === 'afectado' ? 0.28 : estado === 'ciclo' ? 0.25 : 0;
      for (const { mat, base } of s.tintes) {
        mat.color.copy(base);
        if (estado === 'apagado') mat.color.lerp(gris, 0.75);
        mat.emissive.set(emisivo);
        mat.emissiveIntensity = intensidad;
      }

      // Torre de luces: rojo falla o ciclo, ámbar detenido, verde opera, apagada si no aplica.
      s.andon.rojo.emissiveIntensity = estado === 'falla' || estado === 'ciclo' ? 2.4 : 0;
      s.andon.ambar.emissiveIntensity = estado === 'afectado' ? 2.4 : 0;
      s.andon.verde.emissiveIntensity = s.opera && estado !== 'apagado' ? 1.6 : 0;

      const conAnillo = estado !== 'normal' && estado !== 'apagado';
      s.anillo.visible = conAnillo || s.id === seleccionado;
      s.anillo.material.color.set(
        estado === 'falla' || estado === 'ciclo'
          ? COLOR_FALLA
          : estado === 'afectado'
            ? COLOR_AFECTADO
            : estado === 'requisito'
              ? COLOR_REQUISITO
              : COLOR_TIPO.PRODUCTO,
      );
      s.anillo.scale.setScalar(1);
      s.etiqueta.element.firstElementChild?.classList.toggle('apagada', estado === 'apagado');
    }

    for (const b of this.bandas) {
      const destacada = resaltado ? cadena.has(b.clave) : aristasCiclo.has(b.clave);
      const color = destacada
        ? resaltado
          ? impacto
            ? COLOR_FALLA
            : COLOR_REQUISITO
          : COLOR_FALLA
        : null;
      b.cinta.color.set(color ?? (resaltado ? '#9ca3af' : COLOR_BANDA));
      b.cinta.emissive.set(color ?? '#000000');
      b.cinta.emissiveIntensity = color ? 0.45 : 0;
      b.cuerpo.color.set(resaltado && !destacada ? '#e2e3ea' : COLOR_MARCO);
      // Una falla corta el suministro: las bandas de su cadena se paran. Un ciclo también.
      b.mueve = !(destacada && (impacto || !resaltado));
      b.visible = !resaltado || destacada;
      for (const c of b.cajas) c.visible = b.visible;
    }
  }

  // ---------------------------------------------------------------- Animación

  private cuadro(): void {
    if (!this.visible || !this.renderer || !this.escena || !this.camara) return;
    const dt = Math.min(this.reloj!.getDelta(), 0.1);
    const t = this.reloj!.elapsedTime;
    this.controles?.update();

    for (const b of this.bandas) {
      if (b.mueve) b.avance = (b.avance + dt * 3.2) % Math.max(b.total, 0.001);
      for (const c of b.cajas) {
        const d = (b.avance + (c.userData['fase'] as number) * b.total) % b.total;
        posicionEn(b, d, c.position);
        c.position.y = ALTO_BANDA + 0.36;
      }
    }

    for (const s of this.estaciones.values()) {
      if (s.brazo && s.opera) s.brazo.rotation.y = Math.sin(t * 1.4 + s.id.length) * 0.9;
      if (s.estado === 'falla' || s.estado === 'foco') s.anillo.scale.setScalar(1 + Math.sin(t * 4) * 0.06);
      if (s.estado === 'falla' || s.estado === 'ciclo') {
        s.andon.rojo.emissiveIntensity = Math.sin(t * 6) > 0 ? 2.6 : 0.4;
      }
    }

    this.renderer.render(this.escena, this.camara);
    this.etiquetador?.render(this.escena, this.camara);
  }

  // ---------------------------------------------------------------- Limpieza

  /** Quita la planta actual liberando geometrías, materiales, texturas y etiquetas. */
  private desmontarPlanta(): void {
    for (const s of this.estaciones.values()) {
      s.etiqueta.removeFromParent();
      s.etiqueta.element.remove();
    }
    this.estaciones.clear();
    this.bandas = [];
    if (!this.planta) return;
    this.planta.traverse((o) => liberar(o));
    this.planta.removeFromParent();
    this.planta = undefined;
  }

  ngOnDestroy(): void {
    this.destruido = true;
    this.renderer?.setAnimationLoop(null);
    this.limpiezas.forEach((f) => f());
    this.desmontarPlanta();
    this.escena?.traverse((o) => liberar(o));
    this.controles?.dispose();
    this.renderer?.dispose();
    this.lienzo()?.nativeElement.replaceChildren();
  }
}

/** Mueve `a` hacia `b` una distancia (sin pasarse). */
function recortar(a: THREE.Vector3, b: THREE.Vector3, distancia: number): void {
  const largo = a.distanceTo(b);
  if (largo < 0.01) return;
  a.lerp(b, Math.min(distancia, largo - 0.5) / largo);
}

/** Posición a distancia `d` sobre el recorrido de una banda. */
function posicionEn(b: Banda, d: number, destino: THREE.Vector3): void {
  let resto = d;
  for (let i = 0; i < b.largos.length; i++) {
    if (resto <= b.largos[i] || i === b.largos.length - 1) {
      destino.lerpVectors(b.puntos[i], b.puntos[i + 1], Math.min(resto / b.largos[i], 1));
      return;
    }
    resto -= b.largos[i];
  }
}

function liberar(objeto: THREE.Object3D): void {
  const malla = objeto as THREE.Mesh;
  malla.geometry?.dispose();
  const materiales = Array.isArray(malla.material) ? malla.material : malla.material ? [malla.material] : [];
  for (const m of materiales) {
    (m as THREE.MeshBasicMaterial).map?.dispose();
    m.dispose();
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
