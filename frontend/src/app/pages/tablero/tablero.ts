import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import {
  LucideArrowRight,
  LucideCircleCheck,
  LucidePresentation,
  LucideTriangleAlert,
  LucideX,
} from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import {
  NOMBRE_TIPO,
  NOMBRE_TIPO_PLURAL,
  eslabonesDeCiclo,
  resaltadoDesde,
} from '../../core/presentacion';
import { CatalogService, FalloApi } from '../../Graph/services/catalog.service';
import { Alcance, Ciclo, Orden, TIPOS_ELEMENTO } from '../../Graph/models/catalog.models';
import { EstadoRed } from '../../shared/estado-red';
import { Red3d } from '../../shared/red3d';
import { Foco, GuiaDemo } from './guia';
import { RegistroRapido } from './registro';
import { RiesgoProveedor, RiesgoProveedores } from './riesgo';

export type Consulta = 'IMPACTO' | 'REQUISITOS' | 'ORDEN';

/**
 * Feature 4: tablero de abastecimiento. Integra en una sola vista el impacto de una falla, lo
 * que necesita cada elemento, el orden de producción y la alerta de ciclo. La consulta activa se
 * destaca en la red 3D (foco, alcanzados y cadenas) y el resto se atenúa.
 */
@Component({
  selector: 'app-tablero',
  imports: [
    RouterLink,
    EstadoRed,
    Red3d,
    RiesgoProveedores,
    GuiaDemo,
    RegistroRapido,
    LucidePresentation,
    LucideArrowRight,
    LucideCircleCheck,
    LucideTriangleAlert,
    LucideX,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './tablero.html',
  styleUrl: './tablero.css',
})
export class Tablero {
  protected readonly store = inject(RedStore);
  private readonly api = inject(CatalogService);

  /** Elemento que llega por la URL (?id=…). */
  readonly id = input<string>();

  protected readonly nombreTipo = NOMBRE_TIPO;
  protected readonly nombreTipoPlural = NOMBRE_TIPO_PLURAL;
  protected readonly tipos = TIPOS_ELEMENTO;
  protected readonly eslabones = eslabonesDeCiclo;

  protected readonly elegido = signal<string | null>(null);
  protected readonly consulta = signal<Consulta>('IMPACTO');
  protected readonly alcance = signal<Alcance | null>(null);
  protected readonly orden = signal<Orden | null>(null);
  protected readonly cicloObjetivo = signal<Ciclo | null>(null);
  protected readonly consultando = signal(false);
  protected readonly error = signal<string | null>(null);
  /** La guía de demostración se muestra al entrar; se puede cerrar y volver a abrir. */
  protected readonly guia = signal(true);
  protected readonly critico = signal<RiesgoProveedor | null>(null);

  protected readonly totalProductos = computed(
    () => this.store.red().elementos.filter((e) => e.tipo === 'PRODUCTO').length,
  );

  protected readonly elemento = computed(() =>
    this.store.red().elementos.find((e) => e.id === this.elegido()),
  );

  /** Lo que se destaca en la red: la consulta activa. */
  protected readonly resaltado = computed(() => {
    const a = this.alcance();
    return a && this.elegido() ? resaltadoDesde(a) : null;
  });

  /** Cifra principal de la consulta, en lenguaje de negocio. */
  protected readonly titular = computed(() => {
    const a = this.alcance();
    const e = this.elemento();
    if (!a || !e) return null;
    const contar = (t: string) => a.alcanzados.filter((x) => x.tipo === t).length;
    switch (this.consulta()) {
      case 'IMPACTO': {
        const p = contar('PRODUCTO');
        if (!a.total) return { cifra: '0', texto: 'No se detiene nada', tono: 'bien' };
        return p
          ? { cifra: String(p), texto: p === 1 ? 'producto se detiene' : 'productos se detienen', tono: 'mal' }
          : { cifra: String(a.total), texto: 'elementos afectados, ningún producto', tono: 'aviso' };
      }
      case 'REQUISITOS': {
        const prov = contar('PROVEEDOR');
        return {
          cifra: String(a.total),
          texto: `elementos necesarios, de ${prov} ${prov === 1 ? 'proveedor' : 'proveedores'}`,
          tono: 'neutro',
        };
      }
      default: {
        if (this.cicloObjetivo()) return { cifra: '!', texto: 'No se puede producir: hay un ciclo', tono: 'mal' };
        const o = this.orden();
        return o
          ? { cifra: String(o.total_etapas), texto: o.total_etapas === 1 ? 'etapa para producirlo' : 'etapas para producirlo', tono: 'neutro' }
          : null;
      }
    }
  });

  /** Agrupa los alcanzados por tipo: "lo que importa" primero (productos). */
  protected readonly porTipo = computed(() =>
    TIPOS_ELEMENTO.map((tipo) => ({
      tipo,
      elementos: this.alcance()?.alcanzados.filter((a) => a.tipo === tipo) ?? [],
    })).filter((g) => g.elementos.length),
  );

  constructor() {
    // Elemento por URL, cuando la red ya cargó.
    effect(() => {
      const id = this.id();
      if (id && this.store.listo()) untracked(() => this.elegir(id));
    });
    // Si la red cambia (por ejemplo, al quitar una dependencia), se repite la consulta.
    effect(() => {
      this.store.red();
      untracked(() => {
        const id = this.elegido();
        if (!id) return;
        if (this.elemento()) void this.consultar();
        else this.limpiar();
      });
    });
  }

  elegir(id: string | null): void {
    if (!id) return this.limpiar();
    this.elegido.set(id);
    void this.consultar();
  }

  /** La guía pide mostrar una consulta concreta. */
  enfocar(foco: Foco): void {
    this.consulta.set(foco.consulta);
    if (foco.id) this.elegir(foco.id);
    else this.limpiar();
  }

  cambiarConsulta(c: Consulta): void {
    this.consulta.set(c);
    if (this.elegido()) void this.consultar();
  }

  limpiar(): void {
    this.elegido.set(null);
    this.alcance.set(null);
    this.orden.set(null);
    this.cicloObjetivo.set(null);
    this.error.set(null);
  }

  async quitar(origen: string, destino: string): Promise<void> {
    await this.store.quitarDependencia(origen, destino);
  }

  private async consultar(): Promise<void> {
    const id = this.elegido()!;
    const consulta = this.consulta();
    this.consultando.set(true);
    this.error.set(null);
    this.orden.set(null);
    this.cicloObjetivo.set(null);
    try {
      const alcance = await firstValueFrom(
        consulta === 'IMPACTO' ? this.api.consultarImpacto(id) : this.api.consultarRequisitos(id),
      );
      if (consulta === 'ORDEN') {
        try {
          this.orden.set(await firstValueFrom(this.api.obtenerOrden(id)));
        } catch (e) {
          if (!(e instanceof FalloApi && e.codigo === 'CICLO_DETECTADO')) throw e;
          this.cicloObjetivo.set(e.detalles as unknown as Ciclo);
        }
      }
      if (this.elegido() !== id || this.consulta() !== consulta) return;
      this.alcance.set(alcance);
    } catch (e) {
      this.alcance.set(null);
      this.error.set((e as Error).message);
    } finally {
      this.consultando.set(false);
    }
  }

  protected valor(evento: Event): string {
    return (evento.target as HTMLSelectElement).value;
  }
}
