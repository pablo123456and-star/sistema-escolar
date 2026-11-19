/**
 * Tipos del paquete asistente (CU28). Espejo de backend/app/paquetes/asistente/schemas.py.
 */

export type EstadoAsistente = { habilitado: boolean }

export type TurnoAnterior = { pregunta: string; respuesta: string }

export type ConsultaEntrada = { pregunta: string; historial: TurnoAnterior[] }

export type RespuestaAsistente = { pregunta: string; respuesta: string; consultas: string[] }

/** El backend acepta como máximo 6 turnos anteriores y preguntas de 2 a 500 caracteres. */
export const MAX_HISTORIAL = 6
export const MAX_PREGUNTA = 500
