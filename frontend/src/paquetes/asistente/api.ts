/**
 * Llamadas al backend del paquete asistente (/api/v1/asistente/...) y hooks de TanStack Query.
 * CU28 - Consultar información por comando de voz.
 */
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '@/nucleo/api'
import {
  MAX_HISTORIAL,
  type ConsultaEntrada,
  type EstadoAsistente,
  type RespuestaAsistente,
  type TurnoAnterior,
} from './schemas'

const MAX_RESPUESTA_HISTORIAL = 400

/** ¿Está configurado el asistente en el servidor? (si no, no se muestra el botón). */
export function useEstadoAsistente(activo: boolean) {
  return useQuery({
    queryKey: ['asistente', 'estado'],
    queryFn: () => api<EstadoAsistente>('/asistente/estado'),
    enabled: activo,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

/** Pregunta escrita. */
export function useConsultarAsistente() {
  return useMutation({
    mutationFn: (datos: ConsultaEntrada) =>
      api<RespuestaAsistente>('/asistente/consulta', { metodo: 'POST', cuerpo: datos }),
  })
}

/** Turnos anteriores en base64 (JSON en UTF-8): una cabecera HTTP no admite tildes ni ñ. */
function codificarHistorial(historial: TurnoAnterior[]): string {
  const recortado = historial.slice(-MAX_HISTORIAL).map((t) => ({
    pregunta: t.pregunta.slice(0, 500),
    respuesta: t.respuesta.slice(0, MAX_RESPUESTA_HISTORIAL),
  }))
  let binario = ''
  for (const byte of new TextEncoder().encode(JSON.stringify(recortado))) binario += String.fromCharCode(byte)
  return btoa(binario)
}

/**
 * Pregunta grabada: el cuerpo es el audio tal cual (audio/webm, audio/ogg, audio/mp4...) y los turnos
 * anteriores van en la cabecera X-Historial, para entender preguntas de seguimiento.
 */
export function usePreguntarPorVoz() {
  return useMutation({
    mutationFn: ({ audio, historial }: { audio: Blob; historial: TurnoAnterior[] }) =>
      api<RespuestaAsistente>('/asistente/voz', {
        metodo: 'POST',
        cuerpo: audio,
        cabeceras: historial.length ? { 'X-Historial': codificarHistorial(historial) } : undefined,
      }),
  })
}
