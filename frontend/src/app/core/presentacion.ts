import { Alcance, Resaltado, TipoElemento } from '../Graph/models/catalog.models';

/** Nombres de los tipos para la interfaz, en singular y en plural. */
export const NOMBRE_TIPO: Record<TipoElemento, string> = {
  PRODUCTO: 'Producto',
  INSUMO: 'Insumo',
  PROVEEDOR: 'Proveedor',
};
export const NOMBRE_TIPO_PLURAL: Record<TipoElemento, string> = {
  PRODUCTO: 'Productos',
  INSUMO: 'Insumos',
  PROVEEDOR: 'Proveedores',
};

/** Colores por tipo para la red (deben coincidir con las variables de styles.css). */
export const COLOR_TIPO: Record<TipoElemento, string> = {
  PRODUCTO: '#6a45e6',
  INSUMO: '#16a34a',
  PROVEEDOR: '#ea580c',
};
export const COLOR_FALLA = '#dc2626';
export const COLOR_AFECTADO = '#f59e0b';
export const COLOR_REQUISITO = '#0f1c6b';

/**
 * Convierte una consulta de impacto o requisitos en lo que hay que resaltar en la red: el
 * elemento consultado, los alcanzados y las dependencias de sus cadenas ("{a}->{b}").
 */
export function resaltadoDesde(alcance: Alcance): Resaltado {
  const aristas = new Set<string>();
  for (const alcanzado of alcance.alcanzados) {
    for (let i = 0; i < alcanzado.cadena.length - 1; i++) {
      aristas.add(`${alcanzado.cadena[i]}->${alcanzado.cadena[i + 1]}`);
    }
  }
  return {
    sentido: alcance.sentido,
    foco: alcance.consultado.id,
    elementos: alcance.alcanzados.map((a) => a.id),
    aristas: [...aristas],
  };
}

/** Las dependencias de un ciclo cerrado [A, B, C, A] como "{a}->{b}". */
export function aristasDeCiclo(ciclo: string[]): string[] {
  return ciclo.slice(0, -1).map((a, i) => `${a}->${ciclo[i + 1]}`);
}
