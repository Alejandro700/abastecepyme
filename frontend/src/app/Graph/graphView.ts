import {
  Component,
  ElementRef,
  effect,
  input,
  OnDestroy,
  viewChild,
} from '@angular/core';
import cytoscape from 'cytoscape';
import { Red, TipoElemento } from './models/catalog.models';


const COLOR_POR_TIPO: Record<TipoElemento, string> = {
  PRODUCTO: '#2563eb',
  INSUMO: '#16a34a',
  PROVEEDOR: '#ea580c',
};


@Component({
  selector: 'app-graph-view',
  template: `<div #lienzo class="lienzo"></div>`,
  styles: [
    `
      .lienzo {
        width: 100%;
        height: 480px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
      }
    `,
  ],
})
export class GraphView implements OnDestroy {
  readonly red = input.required<Red>();

  private readonly lienzo = viewChild.required<ElementRef<HTMLDivElement>>('lienzo');
  private cy?: cytoscape.Core;

  constructor() {

    effect(() => {
      const red = this.red();
      const contenedor = this.lienzo().nativeElement;
      this.dibujar(contenedor, red);
    });
  }

  private dibujar(contenedor: HTMLElement, red: Red): void {

    this.cy?.destroy();

    this.cy = cytoscape({
      container: contenedor,
      elements: [
        ...red.elementos.map((elemento) => ({
          data: { id: elemento.id, etiqueta: elemento.id, tipo: elemento.tipo },
        })),
        ...red.dependencias.map((dependencia) => ({
          data: {
            id: `${dependencia.origen_id}->${dependencia.destino_id}`,
            source: dependencia.origen_id,
            target: dependencia.destino_id,
          },
        })),
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (nodo: cytoscape.NodeSingular) =>
              COLOR_POR_TIPO[nodo.data('tipo') as TipoElemento] ?? '#64748b',
            label: 'data(etiqueta)',
            color: '#ffffff',
            'font-size': '11px',
            'font-weight': 'bold',
            'text-valign': 'center',
            'text-halign': 'center',
            width: 'label',
            height: 28,
            padding: '10px',
            shape: 'round-rectangle',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#94a3b8',
            'target-arrow-color': '#94a3b8',
            // La flecha apunta al destino: se lee "el origen requiere al
            // destino", igual que en el backend.
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
      ],
      layout: {
        name: 'breadthfirst',
        directed: true,
        padding: 24,
        spacingFactor: 1.4,
      },
      minZoom: 0.3,
      maxZoom: 2.5,
    });
  }

  ngOnDestroy(): void {
    this.cy?.destroy();
  }
}
