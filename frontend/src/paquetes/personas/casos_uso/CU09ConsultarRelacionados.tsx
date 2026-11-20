/**
 * CU09 - Consultar estudiantes/tutores relacionados
 * Paquete: personas
 *
 * Actores ........: Tutor, Administrativo
 * Rol del sistema : tutor, administrador, estudiante, profesor
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu09_consultar_relacionados.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Cada rol tiene su vista:
 *   - Administrador: busca por C.I. los tutores de un estudiante o los estudiantes de un tutor.
 *   - Tutor: ve directamente a sus estudiantes.
 *   - Estudiante: ve directamente a sus tutores.
 *   - Profesor: elige a un estudiante de sus clases y ve sus padres o tutores (para contactarlos).
 *
 * Precondición:  Sesión iniciada.
 * Postcondición: Se muestra la lista de estudiantes del tutor (o de tutores del estudiante). No se modifica nada.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState, type FormEvent } from 'react'
import { SearchIcon, UserIcon } from 'lucide-react'
import { AvatarIniciales, Campo, EncabezadoPagina, FilaMensaje, InsigniaEstado, Paginacion } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { documento, nombreCompleto } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { cn } from 'cn'
import { ErrorApi, mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { useEstudiantesSeguimiento, useRelacionados } from '../api'
import type { TipoRelacionado } from '../schemas'

const OTRO_TIPO: Record<TipoRelacionado, TipoRelacionado> = { estudiante: 'tutor', tutor: 'estudiante' }

export default function CU09ConsultarRelacionados() {
  const { usuario } = useSesion()
  if (!usuario) return null
  if (usuario.rol === 'administrador') return <VistaAdministrador />
  if (usuario.rol === 'profesor') return <VistaProfesor />
  if (usuario.rol === 'tutor') {
    return (
      <div className="space-y-5">
        <EncabezadoPagina titulo="Mis estudiantes" descripcion="Estudiantes a su cargo registrados en el colegio, con su curso actual." />
        <Relacionados ci={usuario.ci} tipo="tutor" />
      </div>
    )
  }
  return (
    <div className="space-y-5">
      <EncabezadoPagina titulo="Mis tutores" descripcion="Padres o tutores que el colegio tiene registrados para usted." />
      <Relacionados ci={usuario.ci} tipo="estudiante" />
    </div>
  )
}

// ---- Administrador: búsqueda por C.I. --------------------------------------------------
function VistaAdministrador() {
  const [ci, setCi] = useState('')
  const [tipo, setTipo] = useState<TipoRelacionado>('estudiante')
  const [consulta, setConsulta] = useState<{ ci: string; tipo: TipoRelacionado } | null>(null)

  const consultar = (e: FormEvent) => {
    e.preventDefault()
    if (ci.trim()) setConsulta({ ci: ci.trim(), tipo })
  }
  const cambiarTipo = () => {
    if (!consulta) return
    const nuevo = OTRO_TIPO[consulta.tipo]
    setTipo(nuevo)
    setConsulta({ ...consulta, tipo: nuevo })
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Consultar relacionados"
        descripcion="Busque a un estudiante para ver sus tutores, o a un tutor para ver los estudiantes a su cargo."
      />
      <form onSubmit={consultar} className="flex flex-col gap-3 rounded-xl border bg-white p-4 shadow-sm sm:flex-row sm:items-end">
        <Campo etiqueta="C.I." htmlFor="cu09-ci" className="sm:flex-1">
          <div className="relative">
            <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
            <Input id="cu09-ci" value={ci} onChange={(e) => setCi(e.target.value)} placeholder="Ej. 4500001" className="pl-9" />
          </div>
        </Campo>
        <Campo etiqueta="Qué desea ver" className="sm:w-72">
          <Select value={tipo} onValueChange={(v) => setTipo(v as TipoRelacionado)}>
            <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="estudiante">Los tutores de este estudiante</SelectItem>
              <SelectItem value="tutor">Los estudiantes de este tutor</SelectItem>
            </SelectContent>
          </Select>
        </Campo>
        <Button type="submit" disabled={!ci.trim()}>
          <SearchIcon /> Consultar
        </Button>
      </form>
      {consulta && <Relacionados ci={consulta.ci} tipo={consulta.tipo} mostrarPersona onCambiarTipo={cambiarTipo} />}
    </div>
  )
}

// ---- Profesor: elige a un estudiante de sus clases -------------------------------------
const TAMANO = 8

function VistaProfesor() {
  const [busqueda, setBusqueda] = useState('')
  const [pagina, setPagina] = useState(1)
  const [elegido, setElegido] = useState<string | null>(null)
  const lista = useEstudiantesSeguimiento({ q: useRetardo(busqueda), pagina, tamano: TAMANO })

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Mis estudiantes"
        descripcion="Elija a un estudiante de sus cursos para ver a sus padres o tutores y cómo contactarlos."
      />
      <div className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)] lg:items-start">
        <div className="rounded-xl border bg-white shadow-sm">
          <div className="border-b p-3">
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={busqueda}
                onChange={(e) => { setBusqueda(e.target.value); setPagina(1) }}
                placeholder="Buscar por nombre o C.I..."
                className="pl-9"
                aria-label="Buscar estudiante"
              />
            </div>
          </div>
          <ul className="divide-y">
            {lista.isLoading ? (
              <li className="p-6 text-center text-sm text-slate-500">Cargando...</li>
            ) : lista.isError ? (
              <li className="p-6 text-center text-sm text-rose-600">{mensajeError(lista.error)}</li>
            ) : !lista.data?.items.length ? (
              <li className="p-6 text-center text-sm text-slate-500">No tiene estudiantes en sus cursos de la gestión actual.</li>
            ) : (
              lista.data.items.map((e) => (
                <li key={e.ci}>
                  <button
                    type="button"
                    onClick={() => setElegido(e.ci)}
                    aria-current={e.ci === elegido}
                    className={cn(
                      'flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-slate-50',
                      e.ci === elegido && 'bg-blue-50 hover:bg-blue-50',
                    )}
                  >
                    <AvatarIniciales nombre={nombreCompleto(e)} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{e.apellidos}, {e.nombre_persona}</p>
                      <p className="truncate text-xs text-slate-500">{e.curso ?? 'Sin curso'}</p>
                    </div>
                  </button>
                </li>
              ))
            )}
          </ul>
          {(lista.data?.total ?? 0) > TAMANO && (
            <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="estudiantes" onCambiar={setPagina} />
          )}
        </div>
        {elegido ? (
          <Relacionados key={elegido} ci={elegido} tipo="estudiante" mostrarPersona />
        ) : (
          <div className="flex min-h-48 flex-col items-center justify-center gap-2 rounded-xl border border-dashed bg-white p-8 text-center text-slate-500">
            <UserIcon className="size-8 text-slate-300" />
            <p className="font-medium text-slate-700">Elija un estudiante</p>
            <p className="text-sm">Verá a sus padres o tutores con su teléfono.</p>
          </div>
        )}
      </div>
    </div>
  )
}

// ---- Tabla de relacionados (común a todos los roles) -----------------------------------
function Relacionados({
  ci,
  tipo,
  mostrarPersona,
  onCambiarTipo,
}: {
  ci: string
  tipo: TipoRelacionado
  mostrarPersona?: boolean
  onCambiarTipo?: () => void
}) {
  const consulta = useRelacionados(ci, tipo)
  const datos = consulta.data
  const verTutores = tipo === 'estudiante'
  const tipoIncorrecto = consulta.error instanceof ErrorApi && consulta.error.codigo === 'tipo_incorrecto'

  return (
    <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
      {mostrarPersona && datos && (
        <div className="border-b bg-slate-50 px-4 py-3">
          <p className="font-semibold text-slate-800">
            {verTutores ? 'Tutores de' : 'Estudiantes a cargo de'} {datos.nombre_completo}
          </p>
          <p className="text-xs text-slate-500">C.I. {documento(datos.ci)}</p>
        </div>
      )}
      {tipoIncorrecto && onCambiarTipo && (
        <div className="flex flex-col gap-2 border-b bg-amber-50 px-4 py-3 text-sm text-amber-800 sm:flex-row sm:items-center sm:justify-between">
          <span>{mensajeError(consulta.error)}</span>
          <Button size="sm" variant="outline" onClick={onCambiarTipo}>
            Ver {verTutores ? 'sus estudiantes' : 'sus tutores'}
          </Button>
        </div>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="pl-4">{verTutores ? 'Tutor' : 'Estudiante'}</TableHead>
            <TableHead>Parentesco</TableHead>
            <TableHead>{verTutores ? 'Teléfono' : 'Curso'}</TableHead>
            <TableHead className="text-center">Tutor principal</TableHead>
            <TableHead className="text-center">Responsable de pago</TableHead>
            <TableHead className="text-center">Puede recoger</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {consulta.isLoading ? (
            <FilaMensaje columnas={6} cargando />
          ) : consulta.isError ? (
            <FilaMensaje columnas={6} mensaje={tipoIncorrecto && onCambiarTipo ? 'Sin resultados.' : mensajeError(consulta.error)} />
          ) : !datos?.relacionados.length ? (
            <FilaMensaje columnas={6} mensaje={verTutores ? 'No tiene tutores registrados.' : 'No tiene estudiantes a su cargo.'} />
          ) : (
            datos.relacionados.map((r) => (
              <TableRow key={r.ci}>
                <TableCell className="pl-4">
                  <div className="flex items-center gap-3">
                    <AvatarIniciales nombre={r.nombre_completo} />
                    <div className="min-w-0">
                      <p className="font-medium">{r.nombre_completo}</p>
                      <p className="text-xs text-slate-500">C.I. {documento(r.ci)}</p>
                    </div>
                    {r.estado && r.estado !== 'activo' && <InsigniaEstado estado={r.estado} />}
                  </div>
                </TableCell>
                <TableCell className="capitalize">{r.parentesco}</TableCell>
                <TableCell>{(verTutores ? r.telefono : r.curso) ?? '—'}</TableCell>
                <TableCell className="text-center"><SiNo valor={r.es_principal} /></TableCell>
                <TableCell className="text-center"><SiNo valor={r.es_responsable_pago} /></TableCell>
                <TableCell className="text-center"><SiNo valor={r.autorizado_recoger} /></TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}

function SiNo({ valor }: { valor: boolean }) {
  return valor ? (
    <span className="inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">Sí</span>
  ) : (
    <span className="text-slate-400">No</span>
  )
}
