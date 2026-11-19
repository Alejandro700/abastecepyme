import { ChangeDetectionStrategy, Component, effect, inject, output, signal, untracked } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { RedStore } from '../../core/red.store';
import { CatalogService } from '../../Graph/services/catalog.service';

export interface RiesgoProveedor {
  id: string;
  productos: string[];
  total: number;
  /** Otros proveedores que detienen la misma cantidad de productos. */
  empatados: string[];
}

/**
 * Ranking de proveedores según cuántos productos se detienen si fallan. Responde la pregunta
 * de negocio "¿de quién dependo más?". Se recalcula cada vez que cambia la red.
 */
@Component({
  selector: 'app-riesgo-proveedores',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (ranking().length) {
      <ol class="ranking">
        @for (r of ranking(); track r.id; let i = $index) {
          <li>
            <button type="button" (click)="elegir.emit(r.id)" [attr.aria-label]="r.id + ': detiene ' + r.productos.length + ' productos. Simular su falla'">
              <span class="fila">
                <strong>{{ r.id }}</strong>
                <span [class.critico]="i === 0 && r.productos.length">
                  {{ r.productos.length }} {{ r.productos.length === 1 ? 'producto' : 'productos' }}
                </span>
              </span>
              <span class="barra" aria-hidden="true">
                <span [style.width.%]="porcentaje(r)" [class.critico]="i === 0 && r.productos.length"></span>
              </span>
              @if (r.productos.length) {
                <small class="texto-suave">{{ r.productos.join(', ') }}</small>
              } @else {
                <small class="texto-suave">Ningún producto depende de él</small>
              }
            </button>
          </li>
        }
      </ol>
    } @else {
      <p class="texto-suave">Registra proveedores para ver de cuál dependes más.</p>
    }
  `,
  styles: `
    .ranking { display: grid; gap: 4px; margin: 0; padding: 0; list-style: none; }
    button {
      display: grid; gap: 6px; width: 100%; padding: 10px 12px; border: 0;
      border-radius: var(--radio-sm); background: none; font: inherit; color: inherit;
      text-align: left; cursor: pointer;
    }
    button:hover { background: var(--marca-suave); }
    .fila { display: flex; justify-content: space-between; gap: 12px; }
    .fila span { font-weight: 600; color: var(--texto-suave); }
    .fila .critico { color: var(--falla); }
    .barra { height: 8px; border-radius: 99px; background: var(--fondo); overflow: hidden; }
    .barra span { display: block; height: 100%; border-radius: inherit; background: var(--proveedor); }
    .barra .critico { background: var(--falla); }
  `,
})
export class RiesgoProveedores {
  private readonly store = inject(RedStore);
  private readonly api = inject(CatalogService);

  readonly elegir = output<string>();
  protected readonly ranking = signal<RiesgoProveedor[]>([]);
  /** El más crítico, para mostrarlo en las cifras del tablero. */
  readonly calculado = output<RiesgoProveedor | null>();
  /** Productos que detiene cada proveedor, para marcarlo en la planta 3D. */
  readonly mapa = output<Map<string, number>>();

  private totalProductos = 0;

  constructor() {
    effect(() => {
      const red = this.store.red();
      untracked(() => void this.calcular(red.elementos.filter((e) => e.tipo === 'PROVEEDOR').map((e) => e.id), red.elementos.filter((e) => e.tipo === 'PRODUCTO').length));
    });
  }

  protected porcentaje(r: RiesgoProveedor): number {
    return this.totalProductos ? (r.productos.length / this.totalProductos) * 100 : 0;
  }

  private async calcular(proveedores: string[], totalProductos: number): Promise<void> {
    try {
      const impactos = await Promise.all(proveedores.map((id) => firstValueFrom(this.api.consultarImpacto(id))));
      const ranking = impactos
        .map((a) => ({
          id: a.consultado.id,
          productos: a.alcanzados.filter((x) => x.tipo === 'PRODUCTO').map((x) => x.id),
          total: a.total,
          empatados: [] as string[],
        }))
        .sort((a, b) => b.productos.length - a.productos.length || b.total - a.total);
      this.totalProductos = totalProductos;
      this.ranking.set(ranking);
      const primero = ranking[0];
      if (primero) {
        primero.empatados = ranking
          .slice(1)
          .filter((r) => r.productos.length === primero.productos.length)
          .map((r) => r.id);
      }
      this.calculado.emit(primero ?? null);
      this.mapa.emit(new Map(ranking.map((r) => [r.id, r.productos.length])));
    } catch {
      this.ranking.set([]);
      this.calculado.emit(null);
      this.mapa.emit(new Map());
    }
  }
}
