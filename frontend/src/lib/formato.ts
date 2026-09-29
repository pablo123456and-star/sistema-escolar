/** Formatos de fecha y texto usados en todas las pantallas (hora de Bolivia). */
const ZONA = 'America/La_Paz'

export function fecha(valor?: string | null): string {
  if (!valor) return '—'
  // Fechas sin hora ("2026-09-27"): se muestran tal cual, sin conversión de zona
  if (/^\d{4}-\d{2}-\d{2}$/.test(valor)) {
    const [a, m, d] = valor.split('-')
    return `${d}/${m}/${a}`
  }
  return new Intl.DateTimeFormat('es-BO', { timeZone: ZONA, day: '2-digit', month: '2-digit', year: 'numeric' }).format(
    new Date(valor),
  )
}

export function fechaHora(valor?: string | null): string {
  if (!valor) return '—'
  return new Intl.DateTimeFormat('es-BO', {
    timeZone: ZONA,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(valor))
}

export function hora(valor?: string | null): string {
  if (!valor) return ''
  return new Intl.DateTimeFormat('es-BO', { timeZone: ZONA, hour: '2-digit', minute: '2-digit', hour12: false }).format(
    new Date(valor),
  )
}

export function nombreCompleto(p: { nombre_persona?: string; nombres?: string; apellidos: string }): string {
  return `${p.nombre_persona ?? p.nombres ?? ''} ${p.apellidos}`.trim()
}

export function iniciales(nombre: string): string {
  return nombre
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((x) => x[0]?.toUpperCase())
    .join('')
}

/** "Bs 1.550" */
export function bolivianos(monto: number): string {
  return `Bs ${monto.toLocaleString('es-BO')}`
}

/** "1234567 SC" */
export function documento(ci: string, expedido?: string | null): string {
  return expedido ? `${ci} ${expedido}` : ci
}

export const ETIQUETA_ROL: Record<string, string> = {
  administrador: 'Administrador',
  profesor: 'Docente',
  estudiante: 'Estudiante',
  tutor: 'Padre/Tutor',
}
