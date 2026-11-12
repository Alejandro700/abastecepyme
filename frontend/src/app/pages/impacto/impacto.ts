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
import { firstValueFrom } from 'rxjs';
import { LucideCircleCheck, LucideTriangleAlert, LucideZap } from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import { NOMBRE_TIPO, NOMBRE_TIPO_PLURAL, resaltadoDesde } from '../../core/presentacion';
import { CatalogService } from '../../Graph/services/catalog.service';
import {
  Alcance,
  ElementoAlcanzado,
  SentidoConsulta,
  TIPOS_ELEMENTO,
} from '../../Graph/models/catalog.models';
import { EstadoRed } from '../../shared/estado-red';
import { Red3d } from '../../shared/red3d';

@Component({
  selector: 'app-impacto',
  imports: [EstadoRed, Red3d, LucideCircleCheck, LucideTriangleAlert, LucideZap],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './impacto.html',
  styleUrl: './impacto.css',
})
export class Impacto {
  protected readonly store = inject(RedStore);
  private readonly api = inject(CatalogService);

  /** Elemento que llega por la URL (?id=…), por ejemplo desde el catálogo o la red. */
  readonly id = input<string>();

  protected readonly nombreTipo = NOMBRE_TIPO;
  protected readonly nombreTipoPlural = NOMBRE_TIPO_PLURAL;

  protected readonly elegido = signal('');
  protected readonly sentido = signal<SentidoConsulta>('IMPACTO');
  protected readonly resultado = signal<Alcance | null>(null);
  protected readonly consultando = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly resaltado = computed(() => {
    const r = this.resultado();
    return r ? resaltadoDesde(r) : null;
  });

  /** Alcanzados agrupados por nivel (1 = directo). */
  protected readonly niveles = computed(() => {
    const grupos = new Map<number, ElementoAlcanzado[]>();
    for (const a of this.resultado()?.alcanzados ?? []) {
      grupos.set(a.nivel, [...(grupos.get(a.nivel) ?? []), a]);
    }
    return [...grupos.entries()].map(([nivel, elementos]) => ({ nivel, elementos }));
  });

  /** Un proveedor de la red para sugerir en el estado inicial. */
  protected readonly sugerencia = computed(
    () =>
      this.store.red().elementos.find((e) => e.tipo === 'PROVEEDOR')?.id ??
      this.store.red().elementos[0]?.id,
  );

  /** "2 productos, 1 insumo" a partir de los alcanzados. */
  protected readonly resumen = computed(() =>
    TIPOS_ELEMENTO.map((t) => ({
      tipo: t,
      total: this.resultado()?.alcanzados.filter((a) => a.tipo === t).length ?? 0,
    })).filter((r) => r.total),
  );

  constructor() {
    effect(() => {
      const id = this.id();
      if (id && this.store.listo()) {
        untracked(() => {
          this.elegido.set(id);
          void this.consultar();
        });
      }
    });
  }

  cambiarSentido(sentido: SentidoConsulta): void {
    this.sentido.set(sentido);
    if (this.resultado()) void this.consultar();
  }

  async consultar(evento?: Event): Promise<void> {
    evento?.preventDefault();
    const id = this.elegido();
    if (!id) {
      this.error.set('Elige un elemento para simular.');
      return;
    }
    this.consultando.set(true);
    this.error.set(null);
    try {
      const peticion =
        this.sentido() === 'IMPACTO'
          ? this.api.consultarImpacto(id)
          : this.api.consultarRequisitos(id);
      this.resultado.set(await firstValueFrom(peticion));
    } catch (e) {
      this.resultado.set(null);
      this.error.set((e as Error).message);
    } finally {
      this.consultando.set(false);
    }
  }

  limpiar(): void {
    this.resultado.set(null);
    this.error.set(null);
  }

  protected valor(evento: Event): string {
    return (evento.target as HTMLSelectElement).value;
  }
}
