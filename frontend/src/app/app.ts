import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LucideMenu, LucideX } from '@lucide/angular';

/** Estructura común: barra superior fija, la página activa y el pie. */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, LucideMenu, LucideX],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a class="saltar" href="#contenido">Saltar al contenido</a>

    <header class="barra">
      <div class="contenedor barra-interior">
        <a routerLink="/" class="marca" (click)="menuAbierto.set(false)">
          <img src="logo.png" alt="AbastecePyme, inicio" width="180" height="40" />
        </a>

        <button
          class="menu-boton"
          type="button"
          [attr.aria-expanded]="menuAbierto()"
          aria-controls="navegacion"
          (click)="menuAbierto.set(!menuAbierto())"
        >
          @if (menuAbierto()) {
            <svg lucideX></svg>
          } @else {
            <svg lucideMenu></svg>
          }
          <span class="sr-only">Menú</span>
        </button>

        <nav id="navegacion" [class.abierta]="menuAbierto()" aria-label="Principal">
          @for (enlace of enlaces; track enlace.ruta) {
            <a
              [routerLink]="enlace.ruta"
              routerLinkActive="activo"
              ariaCurrentWhenActive="page"
              (click)="menuAbierto.set(false)"
            >
              {{ enlace.texto }}
            </a>
          }
        </nav>
      </div>
    </header>

    <main id="contenido" tabindex="-1">
      <router-outlet />
    </main>

    <footer class="pie">
      <div class="contenedor pie-interior">
        <img src="icon-192.png" alt="" width="28" height="28" />
        <p>
          <strong>AbastecePyme</strong> · Anticipa qué se afecta antes de que falle un proveedor.
        </p>
        <p class="texto-suave">Datos de demostración, sin inventario ni compras.</p>
      </div>
    </footer>
  `,
  styleUrl: './app.css',
})
export class App {
  protected readonly menuAbierto = signal(false);
  protected readonly enlaces = [
    { ruta: '/catalogo', texto: 'Catálogo' },
    { ruta: '/red', texto: 'Red' },
    { ruta: '/impacto', texto: 'Simular falla' },
    { ruta: '/produccion', texto: 'Producción' },
  ];
}
