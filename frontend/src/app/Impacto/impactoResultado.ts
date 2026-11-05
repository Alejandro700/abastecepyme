import { Component, computed, input, output } from '@angular/core';
import { Alcance } from '../Graph/models/catalog.models';

@Component({
  selector: 'app-impacto-resultado',
  template: `
    <div class="encabezado">
      <h2>{{ titulo() }}</h2>
      <button type="button" (click)="cerrar.emit()">Limpiar</button>
    </div>

    <p class="mensaje" [class.mensaje--alerta]="alcance().estado === 'CON_IMPACTO'">
      {{ alcance().mensaje }}
    </p>

    @if (alcance().total > 0) {
      <ol class="lista">
        @for (alcanzado of alcance().alcanzados; track alcanzado.id) {
          <li>
            <span class="punto punto--{{ alcanzado.tipo.toLowerCase() }}"></span>
            <span class="texto">{{ alcanzado.explicacion }}</span>
            <span class="nivel">
              {{ alcanzado.nivel === 1 ? 'Directo' : 'Indirecto (nivel ' + alcanzado.nivel + ')' }}
            </span>
          </li>
        }
      </ol>
    }
  `,
  styles: [
    `
      :host {
        display: block;
      }

      .encabezado {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
      }

      h2 {
        margin: 0;
        font-size: 1.05rem;
        color: #0f1c6b;
      }

      button {
        background: #ffffff;
        color: #6a45e6;
        border: 1px solid #cdc8e6;
        border-radius: 8px;
        padding: 7px 14px;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
      }

      button:hover {
        background: #f1edfd;
      }

      .mensaje {
        margin: 0 0 12px;
        padding: 10px 14px;
        border-radius: 8px;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #15803d;
        font-size: 0.9rem;
      }

      .mensaje--alerta {
        background: #fff7ed;
        border-color: #fed7aa;
        color: #c2410c;
      }

      .lista {
        margin: 0;
        padding: 0;
        list-style: none;
      }

      li {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        border-top: 1px solid #eeeaf8;
        font-size: 0.9rem;
        color: #334155;
      }

      .texto {
        flex: 1;
      }

      .nivel {
        font-size: 0.75rem;
        color: #64748b;
        white-space: nowrap;
      }

      .punto {
        width: 11px;
        height: 11px;
        border-radius: 50%;
        flex-shrink: 0;
      }

      .punto--producto {
        background: #6a45e6;
      }

      .punto--insumo {
        background: #16a34a;
      }

      .punto--proveedor {
        background: #ea580c;
      }
    `,
  ],
})
export class ImpactoResultado {
  readonly alcance = input.required<Alcance>();
  readonly cerrar = output<void>();

  readonly titulo = computed(() => {
    const { sentido, consultado } = this.alcance();
    return sentido === 'IMPACTO'
      ? `Impacto si falla «${consultado.id}»`
      : `Requisitos de «${consultado.id}»`;
  });
}
