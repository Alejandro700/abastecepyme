import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import {
  LucideArrowRight,
  LucideChevronDown,
  LucideFactory,
  LucideShoppingCart,
} from '@lucide/angular';

import { RedStore } from '../../core/red.store';
import { TipoElemento } from '../../Graph/models/catalog.models';

type Estado = 'falla' | 'afectado' | 'normal';

/** Segunda mitad del inicio: ejemplo, perfiles, conceptos, preguntas y llamado final. */
@Component({
  selector: 'app-inicio-detalle',
  imports: [RouterLink, LucideArrowRight, LucideChevronDown, LucideFactory, LucideShoppingCart],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './inicio-detalle.html',
  styleUrl: './inicio-detalle.css',
})
export class InicioDetalle {
  protected readonly store = inject(RedStore);
  private readonly router = inject(Router);

  /** Fábrica de muebles del ejemplo, por pisos (los mismos datos de "Cargar datos de ejemplo"). */
  protected readonly ejemplo: { nombre: string; elementos: { id: string; estado: Estado }[] }[] = [
    {
      nombre: 'Productos',
      elementos: [
        { id: 'Silla', estado: 'afectado' },
        { id: 'Mesa', estado: 'afectado' },
      ],
    },
    {
      nombre: 'Insumos',
      elementos: [
        { id: 'Madera', estado: 'afectado' },
        { id: 'Tornillos', estado: 'normal' },
        { id: 'Barniz', estado: 'normal' },
      ],
    },
    {
      nombre: 'Proveedores',
      elementos: [
        { id: 'MaderasDelSur', estado: 'falla' },
        { id: 'FerreteriaCentral', estado: 'normal' },
        { id: 'QuimicosAndinos', estado: 'normal' },
      ],
    },
  ];

  protected readonly perfiles = [
    {
      icono: 'compras',
      rol: 'Responsable de compras',
      texto: 'Mantiene al día la red de proveedores e insumos.',
      beneficios: [
        'Registra proveedores, insumos y productos en un solo lugar.',
        'Sabe qué proveedores son críticos porque de ellos depende más.',
        'Detecta dependencias circulares antes de que causen problemas.',
      ],
    },
    {
      icono: 'produccion',
      rol: 'Coordinador de producción',
      texto: 'Decide qué preparar y cuándo.',
      beneficios: [
        'Ve en segundos qué productos quedan en riesgo ante una falla.',
        'Obtiene el orden de preparación por etapas.',
        'Identifica lo que se puede preparar en paralelo.',
      ],
    },
  ];

  protected readonly conceptos: { termino: string; tipo?: TipoElemento; texto: string }[] = [
    { termino: 'Proveedor', tipo: 'PROVEEDOR', texto: 'Empresa externa que te entrega algo.' },
    {
      termino: 'Insumo',
      tipo: 'INSUMO',
      texto: 'Material que usas para fabricar: madera, tornillos.',
    },
    { termino: 'Producto', tipo: 'PRODUCTO', texto: 'Lo que vendes: una silla, una mesa.' },
    {
      termino: 'Dependencia',
      texto: 'Que algo necesita otra cosa. «Para producir Silla necesito Madera».',
    },
    {
      termino: 'Etapa',
      texto:
        'Grupo de cosas que se pueden preparar al mismo tiempo, una vez listas las anteriores.',
    },
    {
      termino: 'Dependencia circular',
      texto: 'Cuando A necesita B y B termina necesitando A. No hay por dónde empezar.',
    },
  ];

  protected readonly preguntasFrecuentes = [
    {
      pregunta: '¿Necesito saber de tecnología para usarlo?',
      respuesta:
        'No. Solo escribes qué necesita cada producto o insumo, en frases como «Para producir Mesa necesito Barniz». AbastecePyme hace el resto.',
    },
    {
      pregunta: '¿Puedo probarlo sin registrar mis datos?',
      respuesta:
        'Sí. Con «Cargar datos de ejemplo» se registra una pequeña fábrica de muebles con 8 elementos y 7 dependencias para que explores todo.',
    },
    {
      pregunta: '¿Qué es una dependencia circular y por qué importa?',
      respuesta:
        'Es cuando una cadena de necesidades vuelve al punto de partida. Así no existe un orden de producción posible, y AbastecePyme te muestra exactamente qué elementos forman el ciclo para que lo corrijas.',
    },
    {
      pregunta: '¿Mis datos se guardan?',
      respuesta:
        'Esta versión es de demostración: los datos se guardan mientras el servidor está encendido y se borran al reiniciarlo. No incluye inventario, compras ni facturación.',
    },
  ];

  /** Lleva al simulador con el ejemplo; si la red está vacía, carga primero los datos. */
  async probarEjemplo(): Promise<void> {
    if (this.store.vacia()) await this.store.cargarDemo();
    await this.router.navigate(['/impacto'], { queryParams: { id: 'MaderasDelSur' } });
  }

  async empezar(): Promise<void> {
    await this.store.cargarDemo();
    await this.router.navigate(['/red']);
  }
}
