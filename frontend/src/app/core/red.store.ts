import { computed, inject, Injectable, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { CatalogService, FalloApi } from '../Graph/services/catalog.service';
import { Ciclo, Orden, Red, TipoElemento } from '../Graph/models/catalog.models';

const RED_VACIA: Red = {
  elementos: [],
  dependencias: [],
  total_elementos: 0,
  total_dependencias: 0,
};

/** Los mismos datos de backend/scripts/cargar_demo.py. */
const DEMO_ELEMENTOS: [string, TipoElemento][] = [
  ['Silla', 'PRODUCTO'],
  ['Mesa', 'PRODUCTO'],
  ['Madera', 'INSUMO'],
  ['Tornillos', 'INSUMO'],
  ['Barniz', 'INSUMO'],
  ['MaderasDelSur', 'PROVEEDOR'],
  ['FerreteriaCentral', 'PROVEEDOR'],
  ['QuimicosAndinos', 'PROVEEDOR'],
];
const DEMO_DEPENDENCIAS: [string, string][] = [
  ['Silla', 'Madera'],
  ['Silla', 'Tornillos'],
  ['Mesa', 'Madera'],
  ['Mesa', 'Tornillos'],
  ['Mesa', 'Barniz'],
  ['Madera', 'MaderasDelSur'],
  ['Tornillos', 'FerreteriaCentral'],
];

/**
 * Estado compartido de la red. Todas las páginas leen de aquí, así que al registrar algo y
 * llamar a `recargar()` se actualizan juntas.
 */
@Injectable({ providedIn: 'root' })
export class RedStore {
  private readonly api = inject(CatalogService);

  readonly red = signal<Red>(RED_VACIA);
  /** Orden de toda la red, o null si hay un ciclo o aún no se ha cargado. */
  readonly orden = signal<Orden | null>(null);
  /** Ciclo detectado por /api/orden (409), o null si la red tiene un orden válido. */
  readonly ciclo = signal<Ciclo | null>(null);
  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);
  /** Pasa a true después de la primera carga, con o sin éxito. */
  readonly listo = signal(false);

  readonly vacia = computed(() => this.red().total_elementos === 0);

  /** Etapa de preparación de cada elemento (vacío si hay ciclo). */
  readonly etapas = computed(() => {
    const mapa = new Map<string, number>();
    for (const etapa of this.orden()?.etapas ?? []) {
      for (const el of etapa.elementos) mapa.set(el.id, etapa.numero);
    }
    return mapa;
  });

  constructor() {
    void this.recargar();
  }

  async recargar(): Promise<void> {
    this.cargando.set(true);
    this.error.set(null);
    try {
      this.red.set(await firstValueFrom(this.api.obtenerRed()));
      await this.recargarOrden();
    } catch (e) {
      this.error.set((e as Error).message);
    } finally {
      this.cargando.set(false);
      this.listo.set(true);
    }
  }

  /** Registra los datos de ejemplo. Lo que ya existe se omite. */
  async cargarDemo(): Promise<void> {
    this.cargando.set(true);
    try {
      for (const [id, tipo] of DEMO_ELEMENTOS) {
        await this.ignorarDuplicado(firstValueFrom(this.api.crearElemento(id, tipo)));
      }
      for (const [origen, destino] of DEMO_DEPENDENCIAS) {
        await this.ignorarDuplicado(firstValueFrom(this.api.crearDependencia(origen, destino)));
      }
    } catch (e) {
      this.error.set((e as Error).message);
    }
    await this.recargar();
  }

  /** Quita una dependencia (por ejemplo, la que cierra un ciclo) y recarga. */
  async quitarDependencia(origen: string, destino: string): Promise<void> {
    await this.ejecutar(firstValueFrom(this.api.eliminarDependencia(origen, destino)));
  }

  /** Deja la red vacía y recarga. */
  async vaciar(): Promise<void> {
    await this.ejecutar(firstValueFrom(this.api.vaciarRed()));
  }

  private async ejecutar(peticion: Promise<unknown>): Promise<void> {
    this.cargando.set(true);
    try {
      await peticion;
    } catch (e) {
      this.error.set((e as Error).message);
    }
    await this.recargar();
  }

  private async recargarOrden(): Promise<void> {
    try {
      this.orden.set(await firstValueFrom(this.api.obtenerOrden()));
      this.ciclo.set(null);
    } catch (e) {
      if (e instanceof FalloApi && e.codigo === 'CICLO_DETECTADO') {
        this.orden.set(null);
        this.ciclo.set(e.detalles as unknown as Ciclo);
      } else {
        throw e;
      }
    }
  }

  private async ignorarDuplicado(peticion: Promise<unknown>): Promise<void> {
    try {
      await peticion;
    } catch (e) {
      const duplicado = ['ELEMENTO_DUPLICADO', 'DEPENDENCIA_DUPLICADA'];
      if (!(e instanceof FalloApi && duplicado.includes(e.codigo))) throw e;
    }
  }
}
