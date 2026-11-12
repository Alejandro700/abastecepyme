import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { LucideArrowRight, LucideTriangleAlert, LucideX } from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import { NOMBRE_TIPO, NOMBRE_TIPO_PLURAL } from '../../core/presentacion';
import { CatalogService } from '../../Graph/services/catalog.service';
import { Alcance, TIPOS_ELEMENTO } from '../../Graph/models/catalog.models';
import { EstadoRed } from '../../shared/estado-red';
import { Red3d } from '../../shared/red3d';

@Component({
  selector: 'app-red',
  imports: [RouterLink, EstadoRed, Red3d, LucideArrowRight, LucideTriangleAlert, LucideX],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './red.html',
  styleUrl: './red.css',
})
export class RedPagina {
  protected readonly store = inject(RedStore);
  private readonly api = inject(CatalogService);

  protected readonly tipos = TIPOS_ELEMENTO;
  protected readonly nombreTipo = NOMBRE_TIPO;
  protected readonly nombreTipoPlural = NOMBRE_TIPO_PLURAL;

  protected readonly seleccionado = signal<string | null>(null);
  protected readonly impacto = signal<Alcance | null>(null);
  protected readonly requisitos = signal<Alcance | null>(null);
  protected readonly errorPanel = signal<string | null>(null);

  protected readonly elemento = computed(() =>
    this.store.red().elementos.find((e) => e.id === this.seleccionado()),
  );

  async seleccionar(id: string | null): Promise<void> {
    this.seleccionado.set(id);
    this.impacto.set(null);
    this.requisitos.set(null);
    this.errorPanel.set(null);
    if (!id) return;
    try {
      const [impacto, requisitos] = await Promise.all([
        firstValueFrom(this.api.consultarImpacto(id)),
        firstValueFrom(this.api.consultarRequisitos(id)),
      ]);
      if (this.seleccionado() !== id) return;
      this.impacto.set(impacto);
      this.requisitos.set(requisitos);
    } catch (e) {
      this.errorPanel.set((e as Error).message);
    }
  }
}
