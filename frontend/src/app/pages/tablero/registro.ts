import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { LucidePlus } from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import { NOMBRE_TIPO } from '../../core/presentacion';
import { CatalogService } from '../../Graph/services/catalog.service';
import { TIPOS_ELEMENTO, TipoElemento } from '../../Graph/models/catalog.models';

/** Registro rápido desde el tablero: un elemento o una dependencia, sin cambiar de página. */
@Component({
  selector: 'app-registro-rapido',
  imports: [LucidePlus],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form (submit)="agregarDependencia($event)">
      <p class="frase">
        <span>Para producir</span>
        <select aria-label="Elemento que necesita" [value]="origen()" (change)="origen.set(valor($event))">
          <option value="">elige…</option>
          @for (e of store.red().elementos; track e.id) {
            <option [value]="e.id">{{ e.id }}</option>
          }
        </select>
        <span>necesito</span>
        <select aria-label="Elemento necesario" [value]="destino()" (change)="destino.set(valor($event))">
          <option value="">elige…</option>
          @for (e of store.red().elementos; track e.id) {
            @if (e.id !== origen()) {
              <option [value]="e.id">{{ e.id }}</option>
            }
          }
        </select>
      </p>
      <button class="boton boton-chico" type="submit" [disabled]="guardando()">
        <svg lucidePlus></svg> Agregar dependencia
      </button>
    </form>

    <form (submit)="agregarElemento($event)">
      <p class="frase">
        <input aria-label="Nombre del nuevo elemento" placeholder="Nuevo elemento" [value]="nuevo()" (input)="nuevo.set(valor($event))" />
        <select aria-label="Tipo" [value]="tipo()" (change)="tipo.set($any(valor($event)))">
          @for (t of tipos; track t) {
            <option [value]="t">{{ nombreTipo[t] }}</option>
          }
        </select>
      </p>
      <button class="boton boton-secundario boton-chico" type="submit" [disabled]="guardando()">
        <svg lucidePlus></svg> Agregar elemento
      </button>
    </form>

    @if (aviso(); as a) {
      <p class="aviso" [class.mal]="a.mal" role="status">{{ a.texto }}</p>
    }
  `,
  styles: `
    form { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; padding: 12px 0; border-bottom: 1px solid var(--borde); }
    .frase { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin: 0; flex: 1 1 260px; }
    select, input { min-height: 36px; padding: 0 10px; border: 1px solid var(--borde); border-radius: var(--radio-sm); background: var(--superficie); font: inherit; font-size: 0.9375rem; }
    input { flex: 1; min-width: 140px; }
    select:focus-visible, input:focus-visible { outline: 3px solid var(--marca); outline-offset: 1px; }
    .aviso { margin: 12px 0 0; font-size: 0.875rem; color: #166534; }
    .aviso.mal { color: var(--falla); }
  `,
})
export class RegistroRapido {
  protected readonly store = inject(RedStore);
  private readonly api = inject(CatalogService);
  protected readonly tipos = TIPOS_ELEMENTO;
  protected readonly nombreTipo = NOMBRE_TIPO;

  protected readonly origen = signal('');
  protected readonly destino = signal('');
  protected readonly nuevo = signal('');
  protected readonly tipo = signal<TipoElemento>('INSUMO');
  protected readonly guardando = signal(false);
  protected readonly aviso = signal<{ texto: string; mal: boolean } | null>(null);

  async agregarDependencia(evento: Event): Promise<void> {
    evento.preventDefault();
    if (!this.origen() || !this.destino()) {
      this.aviso.set({ texto: 'Elige los dos elementos.', mal: true });
      return;
    }
    await this.guardar(async () => {
      const d = await firstValueFrom(this.api.crearDependencia(this.origen(), this.destino()));
      this.destino.set('');
      return `Registrado: ${d.frase}.`;
    });
    if (this.store.ciclo() && !this.aviso()?.mal) {
      this.aviso.set({ texto: 'Registrado, pero se formó una dependencia circular. Mira la alerta de arriba.', mal: true });
    }
  }

  async agregarElemento(evento: Event): Promise<void> {
    evento.preventDefault();
    const id = this.nuevo().trim();
    if (!id) {
      this.aviso.set({ texto: 'Escribe el nombre del elemento.', mal: true });
      return;
    }
    await this.guardar(async () => {
      const e = await firstValueFrom(this.api.crearElemento(id, this.tipo()));
      this.nuevo.set('');
      return `${NOMBRE_TIPO[e.tipo]} «${e.id}» registrado.`;
    });
  }

  private async guardar(accion: () => Promise<string>): Promise<void> {
    this.guardando.set(true);
    try {
      const texto = await accion();
      await this.store.recargar();
      this.aviso.set({ texto, mal: false });
    } catch (e) {
      this.aviso.set({ texto: (e as Error).message, mal: true });
    } finally {
      this.guardando.set(false);
    }
  }

  protected valor(evento: Event): string {
    return (evento.target as HTMLInputElement | HTMLSelectElement).value;
  }
}
