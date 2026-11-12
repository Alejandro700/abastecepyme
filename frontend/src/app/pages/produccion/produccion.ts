import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { LucideChevronRight, LucideTriangleAlert } from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import { NOMBRE_TIPO } from '../../core/presentacion';
import { CatalogService, FalloApi } from '../../Graph/services/catalog.service';
import { Ciclo, Orden } from '../../Graph/models/catalog.models';
import { EstadoRed } from '../../shared/estado-red';

@Component({
  selector: 'app-produccion',
  imports: [RouterLink, EstadoRed, LucideChevronRight, LucideTriangleAlert],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './produccion.html',
  styleUrl: './produccion.css',
})
export class Produccion {
  protected readonly store = inject(RedStore);
  private readonly api = inject(CatalogService);
  protected readonly nombreTipo = NOMBRE_TIPO;

  /** '' = toda la red; si no, el elemento objetivo. */
  protected readonly objetivo = signal('');
  private readonly ordenObjetivo = signal<Orden | null>(null);
  private readonly cicloObjetivo = signal<Ciclo | null>(null);
  protected readonly consultando = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly productos = computed(() =>
    this.store.red().elementos.filter((e) => e.tipo === 'PRODUCTO'),
  );
  protected readonly orden = computed(() =>
    this.objetivo() ? this.ordenObjetivo() : this.store.orden(),
  );
  protected readonly ciclo = computed(() =>
    this.objetivo() ? this.cicloObjetivo() : this.store.ciclo(),
  );

  async elegir(id: string): Promise<void> {
    this.objetivo.set(id);
    this.ordenObjetivo.set(null);
    this.cicloObjetivo.set(null);
    this.error.set(null);
    if (!id) return;
    this.consultando.set(true);
    try {
      this.ordenObjetivo.set(await firstValueFrom(this.api.obtenerOrden(id)));
    } catch (e) {
      if (e instanceof FalloApi && e.codigo === 'CICLO_DETECTADO') {
        this.cicloObjetivo.set(e.detalles as unknown as Ciclo);
      } else {
        this.error.set((e as Error).message);
      }
    } finally {
      this.consultando.set(false);
    }
  }

  /** Eslabones consecutivos de un ciclo cerrado: [A, B, C, A] → A→B, B→C, C→A. */
  protected pares(ciclo: string[]): [string, string][] {
    return ciclo.slice(1).map((id, i) => [ciclo[i], id]);
  }

  async quitar(origen: string, destino: string): Promise<void> {
    await this.store.quitarDependencia(origen, destino);
    if (this.objetivo()) await this.elegir(this.objetivo());
  }

  protected valor(evento: Event): string {
    return (evento.target as HTMLSelectElement).value;
  }
}
