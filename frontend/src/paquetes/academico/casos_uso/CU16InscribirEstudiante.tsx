/**
 * CU16 - Inscribir estudiante en gestión académica
 * Paquete: academico
 *
 * Actores ........: Administrativo (Secretaría)
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu16_inscribir_estudiante.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Buscar al estudiante (C.I., RUDE o nombre), elegir grado y paralelo de la gestión abierta
 * viendo el cupo, inscribir y emitir la boleta de inscripción (imprimible). La boleta
 * de un estudiante ya inscrito se puede volver a emitir.
 *
 * Precondición:  El estudiante está activo, sin cuotas vencidas previas y no inscrito en esa gestión; la gestión está abierta y el curso tiene cupo.
 * Postcondición: La inscripción queda activa y se emite la boleta de inscripción.
 *
 * Estado: IMPLEMENTADO.
 */
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { ClipboardCheckIcon, FileTextIcon, RotateCcwIcon, SearchIcon, UserPlusIcon } from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import {
  AvatarIniciales,
  BotonAccion,
  Campo,
  EncabezadoPagina,
  FilaMensaje,
  InsigniaEstado,
  Paginacion,
} from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { documento, nombreCompleto } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import { useOpcionesEstudiantes } from '@/paquetes/personas/api'
import { useBoleta, useEstudiantesInscripcion, useInscribir } from '../api'
import BoletaInscripcion from '../componentes/BoletaInscripcion'
import type { EstudianteInscripcion } from '../schemas'

const TAMANO = 10

export default function CU16InscribirEstudiante() {
  const [busqueda, setBusqueda] = useState('')
  const [pagina, setPagina] = useState(1)
  const q = useRetardo(busqueda)
  const lista = useEstudiantesInscripcion({ q, pagina, tamano: TAMANO })

  const [aInscribir, setAInscribir] = useState<EstudianteInscripcion | null>(null)
  const [idBoleta, setIdBoleta] = useState<number | null>(null)
  const boleta = useBoleta(idBoleta)

  if (idBoleta !== null) {
    return boleta.data ? (
      <BoletaInscripcion boleta={boleta.data} onVolver={() => setIdBoleta(null)} />
    ) : (
      <div className="space-y-4">
        <p className="py-10 text-center text-slate-500">{boleta.isError ? mensajeError(boleta.error) : 'Cargando boleta...'}</p>
        <div className="text-center">
          <Button variant="outline" onClick={() => setIdBoleta(null)}>Volver a la búsqueda</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Inscripción de estudiantes"
        descripcion="Inscriba a los estudiantes en la gestión abierta y emita su boleta de inscripción."
      />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 md:grid-cols-[1fr_auto] md:items-end">
          <Campo etiqueta="Buscar estudiante">
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={busqueda}
                onChange={(e) => {
                  setBusqueda(e.target.value)
                  setPagina(1)
                }}
                placeholder="Nombre, cédula o código RUDE..."
                className="pl-9"
              />
            </div>
          </Campo>
          <Button
            variant="outline"
            onClick={() => {
              setBusqueda('')
              setPagina(1)
            }}
          >
            <RotateCcwIcon /> Limpiar
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="w-10 pl-4">#</TableHead>
              <TableHead>Foto</TableHead>
              <TableHead>Nombre completo</TableHead>
              <TableHead>Código RUDE</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Inscripción en la gestión</TableHead>
              <TableHead className="pr-4 text-center">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lista.isLoading ? (
              <FilaMensaje columnas={7} cargando />
            ) : lista.isError ? (
              <FilaMensaje columnas={7} mensaje={mensajeError(lista.error)} />
            ) : !lista.data?.items.length ? (
              <FilaMensaje columnas={7} mensaje="No se encontraron estudiantes." />
            ) : (
              lista.data.items.map((est, i) => (
                <TableRow key={est.ci}>
                  <TableCell className="pl-4 text-slate-500">{(pagina - 1) * TAMANO + i + 1}</TableCell>
                  <TableCell><AvatarIniciales nombre={nombreCompleto(est)} /></TableCell>
                  <TableCell>
                    <p className="font-medium">{est.apellidos}, {est.nombre_persona}</p>
                    <p className="text-xs text-slate-500">C.I. {documento(est.ci, est.expedido)}</p>
                  </TableCell>
                  <TableCell>{est.rude ?? '—'}</TableCell>
                  <TableCell><InsigniaEstado estado={est.estado_persona} /></TableCell>
                  <TableCell>
                    {est.id_inscripcion ? (
                      <div className="flex flex-col items-start gap-1">
                        <span>{est.curso}</span>
                        {est.estado_inscripcion !== 'activa' && <InsigniaEstado estado={est.estado_inscripcion ?? ''} />}
                      </div>
                    ) : (
                      <span className="text-slate-400">Sin inscripción</span>
                    )}
                  </TableCell>
                  <TableCell className="pr-4">
                    <div className="flex justify-center gap-1.5">
                      {est.id_inscripcion ? (
                        <BotonAccion etiqueta="Ver boleta" tono="azul" onClick={() => setIdBoleta(est.id_inscripcion)}>
                          <FileTextIcon />
                        </BotonAccion>
                      ) : (
                        <BotonAccion
                          etiqueta={est.estado_persona === 'activo' ? 'Inscribir' : 'Estudiante inactivo'}
                          tono="verde"
                          disabled={est.estado_persona !== 'activo'}
                          onClick={() => setAInscribir(est)}
                        >
                          <UserPlusIcon />
                        </BotonAccion>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="estudiantes" onCambiar={setPagina} />
      </div>

      {aInscribir && (
        <DialogoInscribir
          estudiante={aInscribir}
          onCerrar={() => setAInscribir(null)}
          onInscrito={(id) => {
            setAInscribir(null)
            setIdBoleta(id)
          }}
        />
      )}
    </div>
  )
}

function DialogoInscribir({
  estudiante,
  onCerrar,
  onInscrito,
}: {
  estudiante: EstudianteInscripcion
  onCerrar: () => void
  onInscrito: (id_inscripcion: number) => void
}) {
  const opciones = useOpcionesEstudiantes()
  const inscribir = useInscribir()
  const [grado, setGrado] = useState('')
  const [idCurso, setIdCurso] = useState('')
  const [confirmando, setConfirmando] = useState(false)

  const grados = useMemo(() => {
    const vistos = new Map<number, string>()
    for (const c of opciones.data?.cursos ?? []) vistos.set(c.id_grado, `${c.nombre_grado} - ${c.nivel}`)
    return [...vistos.entries()]
  }, [opciones.data])
  const paralelos = (opciones.data?.cursos ?? []).filter((c) => String(c.id_grado) === grado)
  const curso = paralelos.find((c) => String(c.id_curso) === idCurso)

  const confirmar = async () => {
    if (!curso) return
    try {
      const b = await inscribir.mutateAsync({ ci_estudiante: estudiante.ci, id_curso: curso.id_curso })
      toast.success(`${nombreCompleto(estudiante)} inscrito en ${b.curso}.`)
      onInscrito(b.id_inscripcion)
    } catch (e) {
      setConfirmando(false)
      toast.error(mensajeError(e))
    }
  }

  return (
    <>
      <Dialog open={!confirmando} onOpenChange={(v) => !v && onCerrar()}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Inscribir estudiante</DialogTitle>
            <DialogDescription>
              {estudiante.apellidos}, {estudiante.nombre_persona} — C.I. {documento(estudiante.ci, estudiante.expedido)}
            </DialogDescription>
          </DialogHeader>
          {opciones.isLoading ? (
            <p className="py-6 text-center text-slate-500">Cargando...</p>
          ) : !opciones.data?.gestion ? (
            <p className="py-6 text-center text-slate-500">No hay una gestión abierta para inscribir.</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              <p className="text-sm text-slate-600 sm:col-span-2">Gestión {opciones.data.gestion}</p>
              <Campo etiqueta="Grado">
                <Select
                  value={grado}
                  onValueChange={(v) => {
                    setGrado(v)
                    setIdCurso('')
                  }}
                >
                  <SelectTrigger className="w-full"><SelectValue placeholder="Seleccione" /></SelectTrigger>
                  <SelectContent>
                    {grados.map(([id, nombre]) => <SelectItem key={id} value={String(id)}>{nombre}</SelectItem>)}
                  </SelectContent>
                </Select>
              </Campo>
              <Campo etiqueta="Paralelo (inscritos / cupo)">
                <Select value={idCurso} onValueChange={setIdCurso} disabled={!grado}>
                  <SelectTrigger className="w-full"><SelectValue placeholder="Seleccione" /></SelectTrigger>
                  <SelectContent>
                    {paralelos.map((c) => (
                      <SelectItem key={c.id_curso} value={String(c.id_curso)} disabled={c.inscritos >= c.cupo_maximo}>
                        “{c.paralelo}” ({c.inscritos}/{c.cupo_maximo}){c.inscritos >= c.cupo_maximo ? ' — sin cupo' : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Campo>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
            <Button disabled={!curso} onClick={() => setConfirmando(true)}>
              <ClipboardCheckIcon /> Inscribir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Confirmar
        abierto={confirmando}
        onCambiar={(v) => !v && setConfirmando(false)}
        titulo="Confirmar inscripción"
        descripcion={`${nombreCompleto(estudiante)} quedará inscrito en ${curso?.nombre_curso ?? ''} para la gestión ${opciones.data?.gestion ?? ''}.`}
        textoConfirmar="Inscribir"
        icono={<ClipboardCheckIcon />}
        ocupado={inscribir.isPending}
        onConfirmar={confirmar}
      />
    </>
  )
}
