/**
 * frontend/src/paquetes/personas/casos_uso/CU09ConsultarRelacionados.tsx
 * CU09 - Consultar estudiantes/tutores relacionados
 * Paquete: personas
 *
 * Actores ........: Tutor, Administrativo
 * Rol del sistema : tutor, administrador, estudiante, profesor
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu09_consultar_relacionados.py
 *
 * Precondición:  Sesión iniciada.
 * Postcondición: Se muestra la lista de estudiantes del tutor (o de tutores del estudiante). No se modifica nada.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { SearchIcon, UsersIcon, GraduationCapIcon } from 'lucide-react'
import {
  AvatarIniciales,
  Campo,
  EncabezadoPagina,
  FilaMensaje,

} from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Input } from '@/componentes/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { api, mensajeError } from '@/nucleo/api'  
import { documento } from '@/lib/formato'

// Estructura de los datos que devuelve tu backend
interface Relacionado {
  ci_relacionado: string
  nombre_completo: string
  parentesco: string | null
  es_principal: boolean
  es_responsable_pago: boolean
}

export default function CU09ConsultarRelacionados() {
  const [ci, setCi] = useState('')
  const [tipo, setTipo] = useState<'tutor' | 'estudiante'>('estudiante')
  const [resultados, setResultados] = useState<Relacionado[]>([])
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [buscado, setBuscado] = useState(false)

  const consultar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ci.trim()) return

    setCargando(true)
    setError(null)
    setResultados([])
    setBuscado(true)

    try {
      // Usamos la función `api` de tu proyecto que ya maneja el token
      const data = await api<Relacionado[]>(`/personas/relacionados/${ci.trim()}`, {
        params: { tipo }
      })
      setResultados(data)
    } catch (err) {
      setError(mensajeError(err))
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Consultar Relacionados"
        descripcion="Busque a un estudiante para ver sus tutores, o a un tutor para ver sus estudiantes a cargo."
      />

      <div className="rounded-xl border bg-white shadow-sm p-4 md:p-6">
        <form onSubmit={consultar} className="flex flex-col gap-4 md:flex-row md:items-end">
          <Campo etiqueta="Cédula de Identidad (C.I.)" className="flex-1">
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={ci}
                onChange={(e) => setCi(e.target.value)}
                placeholder="Ej. 4500001"
                className="pl-9"
              />
            </div>
          </Campo>

          <Campo etiqueta="¿Qué desea consultar?" className="md:w-64">
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value as 'tutor' | 'estudiante')}
              className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="estudiante">Los tutores de este Estudiante</option>
              <option value="tutor">Los estudiantes de este Tutor</option>
            </select>
          </Campo>

          <Button type="submit" disabled={cargando || !ci.trim()} className="md:mb-0.5">
            {cargando ? 'Buscando...' : <><SearchIcon className="mr-2 size-4" /> Consultar</>}
          </Button>
        </form>
      </div>

      {buscado && (
        <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
          <div className="bg-slate-50 border-b px-4 py-3 flex items-center gap-2">
            {tipo === 'estudiante' ? <UsersIcon className="size-5 text-blue-600" /> : <GraduationCapIcon className="size-5 text-emerald-600" />}
            <h3 className="font-semibold text-slate-800">
              {tipo === 'estudiante' ? 'Tutores relacionados' : 'Estudiantes a cargo'}
            </h3>
          </div>

          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50/50">
                <TableHead className="w-12 pl-4">#</TableHead>
                <TableHead>{tipo === 'estudiante' ? 'Tutor' : 'Estudiante'}</TableHead>
                <TableHead>Parentesco</TableHead>
                <TableHead className="text-center">Tutor Principal</TableHead>
                <TableHead className="text-center">Responsable de Pago</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cargando ? (
                <FilaMensaje columnas={5} cargando />
              ) : error ? (
                <FilaMensaje columnas={5} mensaje={error} />
              ) : resultados.length === 0 ? (
                <FilaMensaje columnas={5} mensaje="No se encontraron personas relacionadas." />
              ) : (
                resultados.map((r, i) => (
                  <TableRow key={r.ci_relacionado}>
                    <TableCell className="pl-4 text-slate-500">{i + 1}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <AvatarIniciales nombre={r.nombre_completo} />
                        <div>
                          <p className="font-medium">{r.nombre_completo}</p>
                          <p className="text-xs text-slate-500">C.I. {documento(r.ci_relacionado)}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{r.parentesco ?? '—'}</TableCell>
                    <TableCell className="text-center">
                      {r.es_principal ? (
                        <span className="inline-flex rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">Sí</span>
                      ) : '—'}
                    </TableCell>
                    <TableCell className="text-center">
                      {r.es_responsable_pago ? (
                        <span className="inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">Sí</span>
                      ) : '—'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}