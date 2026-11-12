import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { LucideCircleCheck, LucideTriangleAlert } from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import { NOMBRE_TIPO, NOMBRE_TIPO_PLURAL } from '../../core/presentacion';
import { CatalogService } from '../../Graph/services/catalog.service';
import { TIPOS_ELEMENTO, TipoElemento } from '../../Graph/models/catalog.models';
import { EstadoRed } from '../../shared/estado-red';

interface Aviso {
  tipo: 'exito' | 'error';
  texto: string;
}

@Component({
  selector: 'app-catalogo',
  imports: [RouterLink, EstadoRed, LucideCircleCheck, LucideTriangleAlert],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './catalogo.html',
  styleUrl: './catalogo.css',
})
export class Catalogo {
  protected readonly store = inject(RedStore);
  private readonly api = inject(CatalogService);

  protected readonly tipos = TIPOS_ELEMENTO;

  async vaciar(): Promise<void> {
    if (confirm('¿Borrar todos los elementos y dependencias? No se puede deshacer.')) {
      await this.store.vaciar();
    }
  }
  protected readonly nombreTipo = NOMBRE_TIPO;
  protected readonly nombreTipoPlural = NOMBRE_TIPO_PLURAL;

  // Filtro de la tabla
  protected readonly filtro = signal<TipoElemento | null>(null);
  protected readonly filas = computed(() => {
    const { elementos, dependencias } = this.store.red();
    const filtro = this.filtro();
    return elementos
      .filter((e) => !filtro || e.tipo === filtro)
      .map((e) => ({
        ...e,
        necesita: dependencias.filter((d) => d.origen_id === e.id).length,
        loUsan: dependencias.filter((d) => d.destino_id === e.id).length,
      }));
  });
  protected readonly conteo = computed(() => {
    const c: Record<TipoElemento, number> = { PRODUCTO: 0, INSUMO: 0, PROVEEDOR: 0 };
    for (const e of this.store.red().elementos) c[e.tipo]++;
    return c;
  });

  // Formulario de elemento
  protected readonly nuevoId = signal('');
  protected readonly nuevoTipo = signal<TipoElemento>('PRODUCTO');
  protected readonly avisoElemento = signal<Aviso | null>(null);
  protected readonly guardandoElemento = signal(false);

  // Formulario de dependencia
  protected readonly origen = signal('');
  protected readonly destino = signal('');
  protected readonly avisoDependencia = signal<Aviso | null>(null);
  protected readonly guardandoDependencia = signal(false);

  async registrarElemento(evento: Event): Promise<void> {
    evento.preventDefault();
    const id = this.nuevoId().trim();
    if (!id) {
      this.avisoElemento.set({ tipo: 'error', texto: 'Escribe el nombre del elemento.' });
      return;
    }
    this.guardandoElemento.set(true);
    try {
      const creado = await firstValueFrom(this.api.crearElemento(id, this.nuevoTipo()));
      this.avisoElemento.set({
        tipo: 'exito',
        texto: `${NOMBRE_TIPO[creado.tipo]} «${creado.id}» registrado.`,
      });
      this.nuevoId.set('');
      await this.store.recargar();
    } catch (e) {
      this.avisoElemento.set({ tipo: 'error', texto: (e as Error).message });
    } finally {
      this.guardandoElemento.set(false);
    }
  }

  async registrarDependencia(evento: Event): Promise<void> {
    evento.preventDefault();
    if (!this.origen() || !this.destino()) {
      this.avisoDependencia.set({ tipo: 'error', texto: 'Elige los dos elementos.' });
      return;
    }
    this.guardandoDependencia.set(true);
    try {
      const creada = await firstValueFrom(this.api.crearDependencia(this.origen(), this.destino()));
      this.avisoDependencia.set({ tipo: 'exito', texto: `Registrado: ${creada.frase}.` });
      this.destino.set('');
      await this.store.recargar();
      if (this.store.ciclo()) {
        this.avisoDependencia.set({
          tipo: 'error',
          texto: `Registrado, pero ahora hay una dependencia circular: ${this.store.ciclo()!.explicacion}. Revísala en Producción.`,
        });
      }
    } catch (e) {
      this.avisoDependencia.set({ tipo: 'error', texto: (e as Error).message });
    } finally {
      this.guardandoDependencia.set(false);
    }
  }

  protected valor(evento: Event): string {
    return (evento.target as HTMLInputElement | HTMLSelectElement).value;
  }
}
