import { ChangeDetectionStrategy, Component, computed, inject, output, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import {
  LucideCheck,
  LucideChevronLeft,
  LucideChevronRight,
  LucidePlay,
  LucideX,
} from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import { CatalogService, FalloApi } from '../../Graph/services/catalog.service';
import type { Consulta } from './tablero';

/** Lo que el tablero debe mostrar después de un paso. */
export interface Foco {
  id: string | null;
  consulta: Consulta;
}

interface Paso {
  titulo: string;
  texto: string;
  observa: string;
  boton: string;
  ejecutar: () => Promise<Foco>;
}

/**
 * Recorrido guiado de la Feature 4: cada paso ejecuta una acción real contra la API y deja el
 * tablero mostrando la consulta relevante. Cubre las tres features de punta a punta.
 */
@Component({
  selector: 'app-guia-demo',
  imports: [LucideCheck, LucideChevronLeft, LucideChevronRight, LucidePlay, LucideX],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="guia tarjeta" aria-labelledby="titulo-guia">
      <header>
        <span class="antetitulo">Demostración guiada · paso {{ indice() + 1 }} de {{ pasos.length }}</span>
        <button class="cerrar" type="button" (click)="cerrar.emit()">
          <svg lucideX></svg><span class="sr-only">Cerrar la guía</span>
        </button>
      </header>
      <ol class="progreso" aria-hidden="true">
        @for (p of pasos; track $index) {
          <li [class.hecho]="hechos().has($index)" [class.actual]="$index === indice()"></li>
        }
      </ol>
      <h2 id="titulo-guia">{{ paso().titulo }}</h2>
      <p class="texto-suave">{{ paso().texto }}</p>
      @if (hechos().has(indice())) {
        <p class="observa" role="status"><svg lucideCheck></svg> <span><strong>Observa:</strong> {{ paso().observa }}</span></p>
      }
      @if (error()) {
        <p class="alerta alerta-error">{{ error() }}</p>
      }
      <div class="botones">
        <button class="boton boton-secundario boton-chico" type="button" [disabled]="indice() === 0" (click)="mover(-1)">
          <svg lucideChevronLeft></svg> Anterior
        </button>
        @if (hechos().has(indice()) && indice() < pasos.length - 1) {
          <button class="boton boton-chico" type="button" [disabled]="ejecutando()" (click)="mover(1)">
            Siguiente <svg lucideChevronRight></svg>
          </button>
        } @else if (!hechos().has(indice())) {
          <button class="boton boton-chico" type="button" [disabled]="ejecutando()" (click)="ejecutar()">
            <svg lucidePlay></svg> {{ ejecutando() ? 'Ejecutando…' : paso().boton }}
          </button>
        } @else {
          <button class="boton boton-chico" type="button" (click)="reiniciar()">Repetir la demostración</button>
        }
      </div>
    </section>
  `,
  styles: `
    .guia { border: 2px solid var(--marca); margin-bottom: 20px; }
    header { display: flex; justify-content: space-between; align-items: center; }
    .cerrar { display: grid; place-items: center; width: 36px; height: 36px; border: 0; border-radius: var(--radio-sm); background: none; color: var(--texto-suave); cursor: pointer; }
    .cerrar:hover { background: var(--fondo); }
    .progreso { display: flex; gap: 6px; margin: 8px 0 16px; padding: 0; list-style: none; }
    .progreso li { flex: 1; height: 6px; border-radius: 99px; background: var(--borde); }
    .progreso .hecho { background: var(--marca); }
    .progreso .actual { outline: 2px solid var(--marca); outline-offset: 1px; }
    h2 { font-size: 1.25rem; margin: 0 0 6px; }
    .observa { display: flex; gap: 8px; align-items: flex-start; padding: 12px 14px; border-radius: var(--radio-sm); background: var(--exito-suave); color: #14532d; }
    .observa svg { flex: none; width: 18px; height: 18px; margin-top: 2px; color: var(--exito); }
    .botones { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
  `,
})
export class GuiaDemo {
  private readonly store = inject(RedStore);
  private readonly api = inject(CatalogService);

  readonly enfocar = output<Foco>();
  readonly cerrar = output<void>();

  protected readonly indice = signal(0);
  protected readonly hechos = signal(new Set<number>());
  protected readonly ejecutando = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly pasos: Paso[] = [
    {
      titulo: '1. Registra una red de ejemplo',
      texto:
        'Una fábrica de muebles: 2 productos (Silla, Mesa), 3 insumos y 3 proveedores, con 8 dependencias. Empezamos desde cero.',
      observa:
        'Las cifras de arriba y la red 3D se llenan. Cada piso de la red es una etapa: proveedores abajo, productos arriba.',
      boton: 'Cargar la fábrica',
      ejecutar: async () => {
        await this.store.vaciar();
        await this.store.cargarDemo();
        return { id: null, consulta: 'IMPACTO' };
      },
    },
    {
      titulo: '2. ¿De quién dependo más?',
      texto: 'El tablero calcula, para cada proveedor, cuántos productos se detendrían si fallara.',
      observa:
        'MaderasDelSur y FerreteriaCentral empatan: si cualquiera falla, se detienen los 2 productos. QuimicosAndinos solo detiene la Mesa (por el Barniz). En la planta, los muelles críticos tienen anillo rojo y su etiqueta dice cuántos productos detienen.',
      boton: 'Ver el riesgo',
      // Sin consulta activa, la planta marca el riesgo de cada proveedor.
      ejecutar: async () => ({ id: null, consulta: 'IMPACTO' }),
    },
    {
      titulo: '3. Simula que MaderasDelSur falla',
      texto: 'Recorremos la red contra las flechas: quién depende de MaderasDelSur, directa o indirectamente.',
      observa:
        'En rojo lo que falla, en ámbar lo que se detiene: Madera (directo), y por ella Silla y Mesa. Tornillos y Barniz siguen igual.',
      boton: 'Simular la falla',
      ejecutar: async () => ({ id: 'MaderasDelSur', consulta: 'IMPACTO' }),
    },
    {
      titulo: '4. ¿Qué necesito para fabricar una Mesa?',
      texto: 'Ahora a favor de las flechas: todo lo que la Mesa requiere, hasta llegar a los proveedores.',
      observa: 'La Mesa necesita 6 elementos y depende de los 3 proveedores: MaderasDelSur, FerreteriaCentral y QuimicosAndinos.',
      boton: 'Ver qué necesita',
      ejecutar: async () => ({ id: 'Mesa', consulta: 'REQUISITOS' }),
    },
    {
      titulo: '5. ¿En qué orden la preparo?',
      texto: 'Orden por etapas: lo que no requiere nada va primero; lo de una misma etapa se hace en paralelo.',
      observa: 'Tres etapas: primero los 3 proveedores; luego Madera, Tornillos y Barniz en paralelo; al final la Mesa.',
      boton: 'Ver el orden',
      ejecutar: async () => ({ id: 'Mesa', consulta: 'ORDEN' }),
    },
    {
      titulo: '6. Cambia la red en vivo',
      texto: 'Registramos una dependencia nueva: «Para producir Silla necesito Barniz» (ahora la silla va barnizada).',
      observa:
        'Si QuimicosAndinos falla, ahora se detienen los 2 productos: la Silla también depende de él a través del Barniz. El ranking de riesgo y las cifras se recalculan solos.',
      boton: 'Registrar Silla → Barniz',
      ejecutar: async () => {
        await this.registrar('Silla', 'Barniz');
        return { id: 'QuimicosAndinos', consulta: 'IMPACTO' };
      },
    },
    {
      titulo: '7. Provoca un ciclo',
      texto:
        'Registramos un error de datos: «MaderasDelSur necesita Silla». Ahora Silla → Madera → MaderasDelSur → Silla.',
      observa:
        'Aparece la alerta roja: no existe un orden posible. El ciclo se marca en rojo en la red y la producción queda bloqueada.',
      boton: 'Registrar MaderasDelSur → Silla',
      ejecutar: async () => {
        await this.registrar('MaderasDelSur', 'Silla');
        return { id: 'Silla', consulta: 'ORDEN' };
      },
    },
    {
      titulo: '8. Resuelve el ciclo',
      texto: 'Quitamos la dependencia que no corresponde a la realidad, desde el propio tablero.',
      observa: 'La alerta desaparece, vuelve el orden por etapas y el estado pasa a "Red lista para producir".',
      boton: 'Quitar MaderasDelSur → Silla',
      ejecutar: async () => {
        await this.store.quitarDependencia('MaderasDelSur', 'Silla');
        return { id: 'Silla', consulta: 'ORDEN' };
      },
    },
  ];

  protected readonly paso = computed(() => this.pasos[this.indice()]);

  /** Lo que mostró cada paso ya ejecutado, para volver a mostrarlo con "Anterior". */
  private readonly focos = new Map<number, Foco>();

  async ejecutar(): Promise<void> {
    const indice = this.indice();
    this.ejecutando.set(true);
    this.error.set(null);
    try {
      const foco = await this.pasos[indice].ejecutar();
      this.focos.set(indice, foco);
      this.enfocar.emit(foco);
      this.hechos.update((h) => new Set(h).add(indice));
    } catch (e) {
      this.error.set((e as Error).message);
    } finally {
      this.ejecutando.set(false);
    }
  }

  /**
   * "Siguiente" avanza y ejecuta el paso de inmediato, así el tablero cambia con un solo clic.
   * "Anterior" vuelve a mostrar lo de ese paso sin repetir sus acciones (registrar, quitar…).
   */
  async mover(delta: number): Promise<void> {
    if (this.ejecutando()) return;
    this.error.set(null);
    this.indice.update((i) => Math.min(Math.max(i + delta, 0), this.pasos.length - 1));
    const indice = this.indice();
    const foco = this.focos.get(indice);
    if (foco) this.enfocar.emit(foco);
    else if (delta > 0) await this.ejecutar();
  }

  reiniciar(): void {
    this.hechos.set(new Set());
    this.focos.clear();
    this.indice.set(0);
  }

  /** Registra una dependencia; si ya existía, sigue (la demo se puede repetir). */
  private async registrar(origen: string, destino: string): Promise<void> {
    try {
      await firstValueFrom(this.api.crearDependencia(origen, destino));
    } catch (e) {
      if (!(e instanceof FalloApi && e.codigo === 'DEPENDENCIA_DUPLICADA')) throw e;
    }
    await this.store.recargar();
  }
}
