
export type TipoElemento = 'PRODUCTO' | 'INSUMO' | 'PROVEEDOR';

export const TIPOS_ELEMENTO: readonly TipoElemento[] = [
  'PRODUCTO',
  'INSUMO',
  'PROVEEDOR',
];

export interface Elemento {
  id: string;
  tipo: TipoElemento;
}

export interface Dependencia {
  origen_id: string;
  destino_id: string;
  frase: string;
}

export interface Red {
  elementos: Elemento[];
  dependencias: Dependencia[];
  total_elementos: number;
  total_dependencias: number;
}


export interface ApiError {
  error_code: string;
  message: string;
  details: Record<string, unknown>;
}
