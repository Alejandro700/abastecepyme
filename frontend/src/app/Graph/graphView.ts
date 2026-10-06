import { Component, ElementRef, effect, input, OnDestroy, viewChild } from '@angular/core';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { Red, TipoElemento } from './models/catalog.models';

cytoscape.use(dagre);

const COLOR_POR_TIPO: Record<TipoElemento, string> = {
  PRODUCTO: '#6a45e6',
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
        border: 1px solid #e2e0f1;
        border-radius: 10px;
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
            'font-size': '12px',
            'font-weight': 'bold',
            'text-valign': 'center',
            'text-halign': 'center',
            width: 'label',
            height: 30,
            padding: '12px',
            shape: 'round-rectangle',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#a9a4cf',
            'target-arrow-color': '#a9a4cf',
            // La flecha apunta al destino: "el origen requiere al destino".
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
      ],
      // Los productos quedan arriba y sus requisitos debajo, siguiendo la dirección de las flechas.
      layout: {
        name: 'dagre',
        rankDir: 'TB',
        nodeSep: 40,
        rankSep: 70,
        padding: 24,
      } as cytoscape.LayoutOptions,
      minZoom: 0.3,
      maxZoom: 2.5,
    });
  }

  ngOnDestroy(): void {
    this.cy?.destroy();
  }
}
