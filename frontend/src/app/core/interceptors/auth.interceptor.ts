/**
 * Auth interceptor — attaches auth credentials to every outbound HTTP request.
 * Works for all HttpClient calls; SSE streaming uses fetch() with manual headers.
 */
import {
  HttpHandlerFn,
  HttpInterceptorFn,
  HttpRequest,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn,
) => {
  const auth = inject(AuthService);
  const headers = auth.getAuthHeaders();

  if (Object.keys(headers).length === 0) {
    return next(req);
  }

  const cloned = req.clone({ setHeaders: headers });
  return next(cloned);
};
