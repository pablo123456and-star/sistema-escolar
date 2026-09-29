/** Cálculos de los paneles de inicio: día y hora de Bolivia, próximas clases, promedios y asistencia. */
import type { BloqueHorario, Cuota, Dia, NotaMateria, ResumenAsistencia } from './datosEjemplo'

const ZONA = 'America/La_Paz'
const DIAS_SEMANA = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'] as const

export const DIAS_CLASE: { dia: Dia; etiqueta: string; corta: string }[] = [
  { dia: 'lunes', etiqueta: 'Lunes', corta: 'Lun' },
  { dia: 'martes', etiqueta: 'Martes', corta: 'Mar' },
  { dia: 'miercoles', etiqueta: 'Miércoles', corta: 'Mié' },
  { dia: 'jueves', etiqueta: 'Jueves', corta: 'Jue' },
  { dia: 'viernes', etiqueta: 'Viernes', corta: 'Vie' },
]

/** Fecha y hora actuales en Bolivia: fecha a medianoche UTC (para sumar días) y "HH:MM". */
function ahoraEnBolivia(): { hoy: Date; hora: string } {
  const partes = Object.fromEntries(
    new Intl.DateTimeFormat('en-CA', {
      timeZone: ZONA,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
      .formatToParts(new Date())
      .map((p) => [p.type, p.value]),
  )
  return {
    hoy: new Date(`${partes.year}-${partes.month}-${partes.day}T00:00:00Z`),
    hora: `${partes.hour === '24' ? '00' : partes.hour}:${partes.minute}`,
  }
}

export function diaHoy(): Dia | null {
  const dia = DIAS_SEMANA[ahoraEnBolivia().hoy.getUTCDay()]
  return dia === 'domingo' || dia === 'sabado' ? null : dia
}

export type ClaseProgramada = { bloque: BloqueHorario; fecha: string; etiqueta: string; esHoy: boolean }

/** Próximas clases a partir de ahora (las de hoy que ya terminaron no se muestran). */
export function proximasClases(bloques: BloqueHorario[], cantidad = 4): ClaseProgramada[] {
  const { hoy, hora } = ahoraEnBolivia()
  const clases: ClaseProgramada[] = []
  for (let i = 0; i < 14 && clases.length < cantidad; i++) {
    const fecha = new Date(hoy.getTime() + i * 86_400_000)
    const dia = DIAS_SEMANA[fecha.getUTCDay()]
    const info = DIAS_CLASE.find((d) => d.dia === dia)
    if (!info) continue
    const iso = fecha.toISOString().slice(0, 10)
    const [, mes, d] = iso.split('-')
    bloques
      .filter((b) => b.dia === dia && (i > 0 || b.fin > hora))
      .sort((a, b) => a.inicio.localeCompare(b.inicio))
      .forEach((bloque) => {
        if (clases.length < cantidad) {
          clases.push({ bloque, fecha: iso, etiqueta: i === 0 ? 'Hoy' : i === 1 ? 'Mañana' : `${info.corta} ${d}/${mes}`, esHoy: i === 0 })
        }
      })
  }
  return clases
}

export function promedioMateria(n: NotaMateria): number | null {
  const notas = [n.t1, n.t2, n.t3].filter((x): x is number => x !== null)
  return notas.length ? Math.round(notas.reduce((a, b) => a + b, 0) / notas.length) : null
}

export function promedioGeneral(notas: NotaMateria[]): number | null {
  const promedios = notas.map(promedioMateria).filter((x): x is number => x !== null)
  return promedios.length ? Math.round(promedios.reduce((a, b) => a + b, 0) / promedios.length) : null
}

/** Porcentaje de clases asistidas (los atrasos cuentan como asistencia). */
export function porcentajeAsistencia(a: ResumenAsistencia): number {
  const total = a.presentes + a.atrasos + a.faltas + a.licencias
  return total ? Math.round(((a.presentes + a.atrasos) / total) * 100) : 100
}

export function proximaCuota(cuotas: Cuota[]): Cuota | undefined {
  return cuotas.find((c) => c.estado === 'vencida') ?? cuotas.find((c) => c.estado === 'pendiente')
}

/** Color de una nota en escala 1-100: se aprueba con 51. */
export function tonoNota(valor: number): string {
  if (valor < 51) return 'text-rose-600'
  if (valor < 70) return 'text-amber-600'
  return 'text-emerald-600'
}
