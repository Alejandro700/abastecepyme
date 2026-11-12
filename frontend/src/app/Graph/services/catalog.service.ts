import { inject, Injectable, InjectionToken } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { catchError, Observable, throwError } from 'rxjs';

import {
  Alcance,
  ApiError,
  Dependencia,
  Elemento,
  Orden,
  Red,
  TipoElemento,
} from '../models/catalog.models';

/** URL base de la API. Se puede reemplazar con un provider en app.config.ts. */
export const API_URL = new InjectionToken<string>('API_URL', {
  providedIn: 'root',
  factory: () => 'http://localhost:8000/api',
});

/** Error de la API con su código y detalles (por ejemplo, el ciclo de CICLO_DETECTADO). */
export class FalloApi extends Error {
  constructor(
    message: string,
    readonly codigo: string,
    readonly detalles: Record<string, unknown> = {},
  ) {
    super(message);
  }
}

@Injectable({ providedIn: 'root' })
export class CatalogService {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_URL);

  obtenerRed(): Observable<Red> {
    return this.http.get<Red>(`${this.base}/red`).pipe(catchError(traducirError));
  }

  crearElemento(id: string, tipo: TipoElemento): Observable<Elemento> {
    return this.http
      .post<Elemento>(`${this.base}/elementos`, { id, tipo })
      .pipe(catchError(traducirError));
  }

  crearDependencia(origenId: string, destinoId: string): Observable<Dependencia> {
    return this.http
      .post<Dependencia>(`${this.base}/dependencias`, {
        origen_id: origenId,
        destino_id: destinoId,
      })
      .pipe(catchError(traducirError));
  }

  eliminarDependencia(origenId: string, destinoId: string): Observable<void> {
    const o = encodeURIComponent(origenId);
    const d = encodeURIComponent(destinoId);
    return this.http
      .delete<void>(`${this.base}/dependencias/${o}/${d}`)
      .pipe(catchError(traducirError));
  }

  /** Borra todos los elementos y dependencias. */
  vaciarRed(): Observable<void> {
    return this.http.delete<void>(`${this.base}/red`).pipe(catchError(traducirError));
  }

  consultarImpacto(id: string): Observable<Alcance> {
    return this.http
      .get<Alcance>(`${this.base}/elementos/${encodeURIComponent(id)}/impacto`)
      .pipe(catchError(traducirError));
  }

  consultarRequisitos(id: string): Observable<Alcance> {
    return this.http
      .get<Alcance>(`${this.base}/elementos/${encodeURIComponent(id)}/requisitos`)
      .pipe(catchError(traducirError));
  }

  /** Orden de toda la red, o solo de lo que necesita `id`. Un ciclo llega como FalloApi. */
  obtenerOrden(id?: string): Observable<Orden> {
    const ruta = id ? `/elementos/${encodeURIComponent(id)}/orden` : '/orden';
    return this.http.get<Orden>(`${this.base}${ruta}`).pipe(catchError(traducirError));
  }
}

function traducirError(respuesta: HttpErrorResponse) {
  if (respuesta.status === 0) {
    return throwError(
      () =>
        new FalloApi(
          'No se pudo contactar al servidor. Revisa que el backend esté corriendo.',
          'SIN_CONEXION',
        ),
    );
  }
  const cuerpo = respuesta.error as ApiError | null;
  return throwError(
    () =>
      new FalloApi(
        cuerpo?.message ?? 'Ocurrió un error inesperado.',
        cuerpo?.error_code ?? 'DESCONOCIDO',
        cuerpo?.details ?? {},
      ),
  );
}
