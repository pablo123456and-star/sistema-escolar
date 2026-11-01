/** Llamadas al backend del paquete reportes (/api/v1/reportes). */
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '@/nucleo/api'
import type {
  DatosReporteDinamico,
  FuenteReporte,
  OpcionesReportes,
  ParametrosEstatico,
  Reporte,
  ReporteEstaticoInfo,
} from './schemas'

export function useOpcionesReportes() {
  return useQuery({ queryKey: ['reportes', 'opciones'], queryFn: () => api<OpcionesReportes>('/reportes/opciones') })
}

export function useCatalogoReportes() {
  return useQuery({ queryKey: ['reportes', 'estaticos'], queryFn: () => api<ReporteEstaticoInfo[]>('/reportes/estaticos') })
}

export function useReporteEstatico(clave: string | null, params: ParametrosEstatico, listo: boolean) {
  return useQuery({
    queryKey: ['reportes', 'estatico', clave, params],
    queryFn: () => api<Reporte>(`/reportes/estaticos/${clave}`, { params }),
    enabled: !!clave && listo,
  })
}

export function useFuentesReporte() {
  return useQuery({ queryKey: ['reportes', 'fuentes'], queryFn: () => api<FuenteReporte[]>('/reportes/dinamico/fuentes') })
}

export function useVistaPreviaDinamica() {
  return useMutation({
    mutationFn: (datos: DatosReporteDinamico) => api<Reporte>('/reportes/dinamico', { metodo: 'POST', cuerpo: datos }),
  })
}
