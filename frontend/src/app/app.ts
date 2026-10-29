import { Component, computed, inject, signal } from '@angular/core';
import { GraphView } from './Graph/graphView';
import { ImpactoResultado } from './Impacto/impactoResultado';
import { CatalogService } from './Graph/services/catalog.service';
import {
  Alcance,
  Red,
  Resaltado,
  SentidoConsulta,
  TipoElemento,
  TIPOS_ELEMENTO,
} from './Graph/models/catalog.models';

const RED_VACIA: Red = {
  elementos: [],
  dependencias: [],
  total_elementos: 0,
  total_dependencias: 0,
};

@Component({
  selector: 'app-root',
  imports: [GraphView, ImpactoResultado],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly catalogo = inject(CatalogService);

  readonly tipos = TIPOS_ELEMENTO;

  readonly red = signal<Red>(RED_VACIA);
  readonly error = signal<string | null>(null);
  readonly aviso = signal<string | null>(null);
  readonly cargando = signal(false);

  readonly nuevoId = signal('');
  readonly nuevoTipo = signal<TipoElemento>('PRODUCTO');

  readonly origenId = signal('');
  readonly destinoId = signal('');

  readonly consultaId = signal('');
  readonly consulta = signal<Alcance | null>(null);

  readonly resaltado = computed<Resaltado | null>(() => {
    const alcance = this.consulta();
    if (!alcance) {
      return null;
    }

    const aristas = new Set<string>();
    for (const alcanzado of alcance.alcanzados) {
      for (let i = 0; i < alcanzado.cadena.length - 1; i++) {
        aristas.add(`${alcanzado.cadena[i]}->${alcanzado.cadena[i + 1]}`);
      }
    }

    return {
      sentido: alcance.sentido,
      foco: alcance.consultado.id,
      elementos: alcance.alcanzados.map((alcanzado) => alcanzado.id),
      aristas: [...aristas],
    };
  });

  constructor() {
    this.recargar();
  }

  recargar(): void {
    this.cargando.set(true);
    this.catalogo.obtenerRed().subscribe({
      next: (red) => {
        this.red.set(red);
        this.error.set(null);
        this.cargando.set(false);
      },
      error: (fallo: Error) => {
        this.error.set(fallo.message);
        this.cargando.set(false);
      },
    });
  }

  crearElemento(): void {
    const id = this.nuevoId().trim();
    if (!id) {
      this.error.set('Escribe un identificador.');
      return;
    }

    this.catalogo.crearElemento(id, this.nuevoTipo()).subscribe({
      next: (elemento) => {
        this.nuevoId.set('');
        this.consulta.set(null);
        this.mostrarAviso(`Se registró ${elemento.tipo} "${elemento.id}".`);
        this.recargar();
      },
      error: (fallo: Error) => this.mostrarError(fallo.message),
    });
  }

  crearDependencia(): void {
    const origen = this.origenId().trim();
    const destino = this.destinoId().trim();
    if (!origen || !destino) {
      this.error.set('Elige los dos elementos.');
      return;
    }

    this.catalogo.crearDependencia(origen, destino).subscribe({
      next: (dependencia) => {
        this.origenId.set('');
        this.destinoId.set('');
        this.consulta.set(null);
        this.mostrarAviso(dependencia.frase);
        this.recargar();
      },
      error: (fallo: Error) => this.mostrarError(fallo.message),
    });
  }

  consultar(sentido: SentidoConsulta): void {
    const id = this.consultaId().trim();
    if (!id) {
      this.mostrarError('Elige el elemento que quieres consultar.');
      return;
    }

    const consulta =
      sentido === 'IMPACTO'
        ? this.catalogo.consultarImpacto(id)
        : this.catalogo.consultarRequisitos(id);

    consulta.subscribe({
      next: (alcance) => {
        this.consulta.set(alcance);
        this.error.set(null);
        this.aviso.set(null);
      },
      error: (fallo: Error) => this.mostrarError(fallo.message),
    });
  }

  capturar(evento: Event): string {
    return (evento.target as HTMLInputElement | HTMLSelectElement).value;
  }

  private mostrarAviso(texto: string): void {
    this.aviso.set(texto);
    this.error.set(null);
  }

  private mostrarError(texto: string): void {
    this.error.set(texto);
    this.aviso.set(null);
  }
}
