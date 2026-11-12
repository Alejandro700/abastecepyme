import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  LucideArrowRight,
  LucideCircleCheck,
  LucideClipboardList,
  LucideClock,
  LucideListOrdered,
  LucideShieldCheck,
  LucideSparkles,
  LucideZap,
} from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import { EstadoRed } from '../../shared/estado-red';
import { Red3d } from '../../shared/red3d';
import { InicioDetalle } from './inicio-detalle';

/** Página de presentación: qué resuelve, cómo funciona y para quién es. */
@Component({
  selector: 'app-inicio',
  imports: [
    RouterLink,
    EstadoRed,
    Red3d,
    InicioDetalle,
    LucideArrowRight,
    LucideCircleCheck,
    LucideClipboardList,
    LucideClock,
    LucideListOrdered,
    LucideShieldCheck,
    LucideSparkles,
    LucideZap,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <!-- Portada -->
    <section class="contenedor portada">
      <div>
        <span class="antetitulo">Para pymes que fabrican</span>
        <h1>Sabe qué se afecta antes de que falle un proveedor.</h1>
        <p class="bajada">
          Registra tus proveedores, insumos y productos. AbastecePyme te muestra en segundos qué se
          detiene si algo falla y en qué orden preparar tu producción.
        </p>
        <div class="acciones">
          <a class="boton" routerLink="/impacto">Simular una falla <svg lucideArrowRight></svg></a>
          <a class="boton boton-secundario" routerLink="/red">Ver la red</a>
        </div>
        <ul class="garantias">
          <li><svg lucideClock></svg> Resultados en segundos</li>
          <li><svg lucideSparkles></svg> Ejemplo listo para probar</li>
          <li><svg lucideShieldCheck></svg> Sin instalar nada</li>
        </ul>
      </div>

      <figure class="vista-previa tarjeta">
        <app-estado-red
          [mostrarCatalogo]="false"
          invitacion="Carga un ejemplo de una fábrica de muebles y mira tu red cobrar vida."
        >
          @defer (on viewport) {
            <app-red-3d
              [red]="store.red()"
              [etapas]="store.etapas()"
              [ciclo]="store.ciclo()?.ciclo ?? []"
              [interactivo]="false"
            />
          } @placeholder {
            <div class="hueco"></div>
          }
        </app-estado-red>
        <figcaption>Tu red de abastecimiento: proveedores abajo, productos arriba.</figcaption>
      </figure>
    </section>

    <!-- Cifras en vivo -->
    <section class="contenedor" aria-label="Tu red en cifras">
      <dl class="cifras">
        <div>
          <dt>Elementos registrados</dt>
          <dd>{{ store.red().total_elementos }}</dd>
        </div>
        <div>
          <dt>Dependencias</dt>
          <dd>{{ store.red().total_dependencias }}</dd>
        </div>
        <div [class.alerta-ciclo]="store.ciclo()">
          <dt>{{ store.ciclo() ? 'Orden bloqueado' : 'Etapas de producción' }}</dt>
          <dd>{{ etapas() }}</dd>
        </div>
      </dl>
    </section>

    <!-- El problema -->
    <section class="contenedor seccion problema">
      <div>
        <span class="antetitulo">El problema</span>
        <h2>Un proveedor falla y nadie sabe qué se detiene.</h2>
        <p class="texto-suave">
          En una pyme, las dependencias viven en la cabeza de alguien o en una hoja de cálculo.
          Cuando un proveedor no entrega, el equipo se entera tarde de qué productos quedan en
          riesgo y prepara las cosas en el orden equivocado.
        </p>
      </div>
      <ul class="preguntas">
        @for (p of preguntas; track p.pregunta) {
          <li>
            <svg lucideCircleCheck></svg>
            <div>
              <strong>{{ p.pregunta }}</strong>
              <span class="texto-suave">{{ p.respuesta }}</span>
            </div>
          </li>
        }
      </ul>
    </section>

    <!-- Cómo funciona -->
    <section class="seccion seccion-alterna">
      <div class="contenedor">
        <header class="seccion-cabecera">
          <span class="antetitulo">Cómo funciona</span>
          <h2>Tres pasos, sin complicaciones</h2>
          <p>No necesitas saber de redes ni de algoritmos: solo qué necesita cada cosa.</p>
        </header>
        <ol class="pasos">
          @for (paso of pasos; track paso.titulo; let i = $index) {
            <li class="tarjeta">
              <span class="numero">{{ i + 1 }}</span>
              @switch (paso.icono) {
                @case ('registra') {
                  <svg lucideClipboardList class="icono"></svg>
                }
                @case ('simula') {
                  <svg lucideZap class="icono"></svg>
                }
                @default {
                  <svg lucideListOrdered class="icono"></svg>
                }
              }
              <h3>{{ paso.titulo }}</h3>
              <p class="texto-suave">{{ paso.texto }}</p>
              <a class="ir" [routerLink]="paso.ruta"
                >{{ paso.accion }} <svg lucideArrowRight></svg
              ></a>
            </li>
          }
        </ol>
      </div>
    </section>

    <app-inicio-detalle />
  `,
  styleUrl: './inicio.css',
})
export class Inicio {
  protected readonly store = inject(RedStore);

  protected readonly etapas = computed(() =>
    this.store.ciclo() ? 'Ciclo' : (this.store.orden()?.total_etapas ?? 0),
  );

  protected readonly preguntas = [
    {
      pregunta: '¿Qué productos se detienen si este proveedor falla?',
      respuesta: 'Lo ves al instante, con la cadena completa de por qué.',
    },
    {
      pregunta: '¿Qué necesito para fabricar este producto?',
      respuesta: 'Todos los insumos y proveedores, directos e indirectos.',
    },
    {
      pregunta: '¿En qué orden preparo todo?',
      respuesta: 'Por etapas, con lo que se puede hacer en paralelo agrupado.',
    },
  ];

  protected readonly pasos = [
    {
      icono: 'registra',
      titulo: 'Registra tu red',
      texto:
        'Anota tus proveedores, insumos y productos, y qué necesita cada uno. Por ejemplo: «Para producir Silla necesito Madera».',
      accion: 'Ir al catálogo',
      ruta: '/catalogo',
    },
    {
      icono: 'simula',
      titulo: 'Simula una falla',
      texto:
        'Elige un proveedor o insumo y mira en rojo lo que falla y en ámbar todo lo que se detiene por eso.',
      accion: 'Simular una falla',
      ruta: '/impacto',
    },
    {
      icono: 'ordena',
      titulo: 'Planifica la producción',
      texto:
        'Obtén el orden de preparación por etapas. Si hay una dependencia circular, te avisamos cuál es.',
      accion: 'Ver el orden',
      ruta: '/produccion',
    },
  ];
}
