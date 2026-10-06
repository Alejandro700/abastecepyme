import { Component, inject, signal } from '@angular/core';
import { GraphView } from './Graph/graphView';
import { CatalogService } from './Graph/services/catalog.service';
import { Red, TipoElemento, TIPOS_ELEMENTO } from './Graph/models/catalog.models';

const RED_VACIA: Red = {
  elementos: [],
  dependencias: [],
  total_elementos: 0,
  total_dependencias: 0,
};

@Component({
  selector: 'app-root',
  imports: [GraphView],
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
        this.mostrarAviso(dependencia.frase);
        this.recargar();
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
