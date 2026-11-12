import { Routes } from '@angular/router';

// Cada página se carga de forma perezosa: la red 3D solo se descarga donde se usa.
export const routes: Routes = [
  {
    path: '',
    title: 'AbastecePyme · Anticipa el impacto de una falla de proveedor',
    loadComponent: () => import('./pages/inicio/inicio').then((m) => m.Inicio),
  },
  {
    path: 'catalogo',
    title: 'Catálogo · AbastecePyme',
    loadComponent: () => import('./pages/catalogo/catalogo').then((m) => m.Catalogo),
  },
  {
    path: 'red',
    title: 'Red · AbastecePyme',
    loadComponent: () => import('./pages/red/red').then((m) => m.RedPagina),
  },
  {
    path: 'impacto',
    title: 'Simulador de impacto · AbastecePyme',
    loadComponent: () => import('./pages/impacto/impacto').then((m) => m.Impacto),
  },
  {
    path: 'produccion',
    title: 'Producción · AbastecePyme',
    loadComponent: () => import('./pages/produccion/produccion').then((m) => m.Produccion),
  },
  { path: '**', redirectTo: '' },
];
