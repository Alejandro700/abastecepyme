import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { catchError, Observable, throwError } from 'rxjs';

import { ApiError, Dependencia, Elemento, Red, TipoElemento } from '../models/catalog.models';

@Injectable({ providedIn: 'root' })
export class CatalogService {
  private readonly http = inject(HttpClient);

  private readonly base = 'http://localhost:8000/api';

  obtenerRed(): Observable<Red> {
    return this.http.get<Red>(`${this.base}/red`).pipe(catchError(this.traducirError));
  }

  crearElemento(id: string, tipo: TipoElemento): Observable<Elemento> {
    return this.http
      .post<Elemento>(`${this.base}/elementos`, { id, tipo })
      .pipe(catchError(this.traducirError));
  }

  crearDependencia(origenId: string, destinoId: string): Observable<Dependencia> {
    return this.http
      .post<Dependencia>(`${this.base}/dependencias`, {
        origen_id: origenId,
        destino_id: destinoId,
      })
      .pipe(catchError(this.traducirError));
  }

  private traducirError(respuesta: HttpErrorResponse) {
    const cuerpo = respuesta.error as ApiError | null;

    if (respuesta.status === 0) {
      return throwError(
        () => new Error('No se pudo contactar al servidor. ¿Está corriendo en localhost:8000?'),
      );
    }

    const mensaje = cuerpo?.message ?? 'Ocurrió un error inesperado.';
    return throwError(() => new Error(mensaje));
  }
}
