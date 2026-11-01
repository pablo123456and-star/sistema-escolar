/** Tipos del paquete reportes (iguales a backend/app/paquetes/reportes/schemas.py). */

export type TipoColumna = 'texto' | 'entero' | 'decimal' | 'porcentaje' | 'fecha'
export type Formato = 'pdf' | 'xlsx'

export type OpcionesReportes = {
  gestiones: { id_gestion: number; anio: number; estado_gestion: string }[]
  niveles: { id_nivel: number; nombre_nivel: string }[]
  cursos: { id_curso: number; nombre_curso: string; id_nivel: number }[]
  periodos: { id_periodo: number; nombre_periodo: string; id_gestion: number; anio: number }[]
  materias: { id_materia: number; nombre_materia: string }[]
}

export type ReporteEstaticoInfo = {
  clave: string
  nombre: string
  descripcion: string
  parametros: ('gestion' | 'curso' | 'periodo')[]
}

export type ColumnaReporte = { clave: string; titulo: string; tipo: TipoColumna }

export type Reporte = {
  titulo: string
  filtros: string[]
  columnas: ColumnaReporte[]
  filas: Record<string, string | number | null>[]
  total: number
  mostradas: number
  resumen: string[]
  generado_en: string
}

export type TipoFiltro = 'gestion' | 'nivel' | 'curso' | 'periodo' | 'materia' | 'opcion' | 'fecha' | 'numero'

export type FuenteReporte = {
  clave: string
  nombre: string
  descripcion: string
  columnas: (ColumnaReporte & { por_defecto: boolean })[]
  filtros: { clave: string; titulo: string; tipo: TipoFiltro; opciones: { valor: string; etiqueta: string }[] }[]
}

export type DatosReporteDinamico = {
  fuente: string
  columnas: string[]
  filtros: Record<string, string>
  orden: string | null
  descendente: boolean
}

export type ParametrosEstatico = { id_gestion?: number; id_curso?: number; id_periodo?: number }
