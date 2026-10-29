export type TipoElemento = 'PRODUCTO' | 'INSUMO' | 'PROVEEDOR';

export const TIPOS_ELEMENTO: readonly TipoElemento[] = ['PRODUCTO', 'INSUMO', 'PROVEEDOR'];

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

export type SentidoConsulta = 'IMPACTO' | 'REQUISITOS';

export interface ElementoAlcanzado {
  id: string;
  tipo: TipoElemento;
  nivel: number;
  cadena: string[];
  explicacion: string;
}

export interface Alcance {
  consultado: Elemento;
  sentido: SentidoConsulta;
  estado: 'CON_IMPACTO' | 'SIN_IMPACTO' | 'CON_REQUISITOS' | 'SIN_REQUISITOS';
  mensaje: string;
  total: number;
  alcanzados: ElementoAlcanzado[];
}

export interface Resaltado {
  sentido: SentidoConsulta;
  foco: string;
  elementos: string[];
  aristas: string[];
}
