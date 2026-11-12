import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { LucideDatabase, LucideRotateCcw, LucideTriangleAlert } from '@lucide/angular';

import { RouterLink } from '@angular/router';
import { RedStore } from '../core/red.store';

/**
 * Envuelve el contenido de una página que necesita la red. Muestra el estado de carga, el
 * error o la invitación a cargar datos, y solo deja ver el contenido cuando hay datos.
 */
@Component({
  selector: 'app-estado-red',
  imports: [RouterLink, LucideDatabase, LucideRotateCcw, LucideTriangleAlert],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (!store.listo()) {
      <div class="caja" role="status">
        <div class="girador"></div>
        <p class="texto-suave">Cargando la red…</p>
      </div>
    } @else if (store.error() && store.vacia()) {
      <div class="caja tarjeta" role="alert">
        <svg lucideTriangleAlert class="icono falla"></svg>
        <h2>No pudimos cargar la red</h2>
        <p class="texto-suave">{{ store.error() }}</p>
        <button class="boton boton-secundario" type="button" (click)="store.recargar()">
          <svg lucideRotateCcw></svg> Reintentar
        </button>
      </div>
    } @else if (store.vacia()) {
      <div class="caja tarjeta">
        <svg lucideDatabase class="icono"></svg>
        <h2>Aún no hay datos en tu red</h2>
        <p class="texto-suave">{{ invitacion() }}</p>
        <div class="acciones">
          <button
            class="boton"
            type="button"
            [disabled]="store.cargando()"
            (click)="store.cargarDemo()"
          >
            {{ store.cargando() ? 'Cargando…' : 'Cargar datos de ejemplo' }}
          </button>
          @if (mostrarCatalogo()) {
            <a class="boton boton-secundario" routerLink="/catalogo">Registrar los míos</a>
          }
        </div>
      </div>
    } @else {
      <ng-content />
    }
  `,
  styles: `
    .caja {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 8px;
      padding: 48px 24px;
    }
    .caja p {
      max-width: 46ch;
    }
    .icono {
      width: 40px;
      height: 40px;
      color: var(--marca);
      margin-bottom: 8px;
    }
    .icono.falla {
      color: var(--falla);
    }
    .acciones {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: center;
    }
  `,
})
export class EstadoRed {
  protected readonly store = inject(RedStore);
  readonly invitacion = input(
    'Carga un ejemplo de una fábrica de muebles para ver cómo funciona, o registra tus propios proveedores, insumos y productos.',
  );
  readonly mostrarCatalogo = input(true);
}
