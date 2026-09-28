/**
 * Campos de datos personales (compartidos por CU06 estudiantes y CU08 tutores).
 * Al registrar, busca el C.I.: si la persona ya existe, llena sus datos para reutilizarla.
 * Se usa dentro de un <FormProvider> cuyo formulario tiene el objeto "persona".
 */
import { useState } from 'react'
import { Controller, useFormContext } from 'react-hook-form'
import type { z } from 'zod'
import { InfoIcon, Loader2Icon } from 'lucide-react'
import { Campo } from '@/componentes/comunes'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { personasApi } from '../api'
import { EXPEDIDOS, personaAFormulario, type PersonaBuscada, type esquemaPersona } from '../schemas'

type Formulario = { persona: z.infer<typeof esquemaPersona> }

type Props = {
  /** true al editar: el C.I. no se cambia y no se busca */
  edicion?: boolean
  /** Revisa la persona encontrada; devuelve un mensaje de error si no se puede reutilizar */
  validarExistente?: (p: PersonaBuscada) => string | null
}

const NINGUNO = 'ninguno'

export default function CamposPersona({ edicion, validarExistente }: Props) {
  const { register, control, formState, reset, getValues, setError, clearErrors } = useFormContext<Formulario>()
  const [buscando, setBuscando] = useState(false)
  const [aviso, setAviso] = useState<string | null>(null)
  const e = formState.errors.persona

  const buscarCi = async () => {
    const ci = getValues('persona.ci').trim().toUpperCase()
    setAviso(null)
    if (edicion || !/^[0-9]{4,12}(-[0-9][A-Z])?$/.test(ci)) return
    setBuscando(true)
    try {
      const p = await personasApi.buscar(ci)
      const problema = validarExistente?.(p) ?? null
      if (problema) {
        setError('persona.ci', { message: problema })
        return
      }
      if (p.estado_persona !== 'activo') {
        setError('persona.ci', { message: 'La persona con ese C.I. está dada de baja.' })
        return
      }
      clearErrors('persona.ci')
      reset({ ...getValues(), persona: personaAFormulario(p) })
      const papeles = [p.es_estudiante && 'estudiante', p.es_tutor && 'tutor', p.es_profesor && 'docente',
        p.es_administrativo && 'administrativo'].filter(Boolean).join(', ')
      setAviso(`Persona ya registrada${papeles ? ` (${papeles})` : ''}: se reutilizarán sus datos.`)
    } catch {
      // 404: no existe, es una persona nueva (se registra con los datos del formulario)
    } finally {
      setBuscando(false)
    }
  }

  return (
    <div className="grid gap-3 sm:grid-cols-6">
      <Campo etiqueta="C.I." error={e?.ci?.message} className="sm:col-span-2" htmlFor="persona-ci">
        <div className="relative">
          <Input id="persona-ci" disabled={edicion} placeholder="1234567" {...register('persona.ci', { onBlur: buscarCi })} />
          {buscando && <Loader2Icon className="absolute top-1/2 right-2 size-4 -translate-y-1/2 animate-spin text-slate-400" />}
        </div>
      </Campo>
      <Campo etiqueta="Expedido" className="sm:col-span-1">
        <Controller
          control={control}
          name="persona.expedido"
          render={({ field }) => (
            <Select value={field.value || NINGUNO} onValueChange={(v) => field.onChange(v === NINGUNO ? '' : v)}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={NINGUNO}>—</SelectItem>
                {EXPEDIDOS.map((x) => <SelectItem key={x} value={x}>{x}</SelectItem>)}
              </SelectContent>
            </Select>
          )}
        />
      </Campo>
      <Campo etiqueta="Sexo" className="sm:col-span-1">
        <Controller
          control={control}
          name="persona.sexo"
          render={({ field }) => (
            <Select value={field.value || NINGUNO} onValueChange={(v) => field.onChange(v === NINGUNO ? '' : v)}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={NINGUNO}>—</SelectItem>
                <SelectItem value="F">Femenino</SelectItem>
                <SelectItem value="M">Masculino</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
      </Campo>
      <Campo etiqueta="Fecha de nacimiento" error={e?.fecha_nacimiento?.message} className="sm:col-span-2" htmlFor="persona-nac">
        <Input id="persona-nac" type="date" {...register('persona.fecha_nacimiento')} />
      </Campo>
      {aviso && (
        <p className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-xs text-blue-700 sm:col-span-6">
          <InfoIcon className="size-4" /> {aviso}
        </p>
      )}
      <Campo etiqueta="Nombres" error={e?.nombre_persona?.message} className="sm:col-span-3" htmlFor="persona-nombres">
        <Input id="persona-nombres" {...register('persona.nombre_persona')} />
      </Campo>
      <Campo etiqueta="Apellidos" error={e?.apellidos?.message} className="sm:col-span-3" htmlFor="persona-apellidos">
        <Input id="persona-apellidos" {...register('persona.apellidos')} />
      </Campo>
      <Campo etiqueta="Teléfono" error={e?.telefono?.message} className="sm:col-span-2" htmlFor="persona-tel">
        <Input id="persona-tel" inputMode="tel" {...register('persona.telefono')} />
      </Campo>
      <Campo etiqueta="Correo electrónico" error={e?.email?.message} className="sm:col-span-4" htmlFor="persona-email">
        <Input id="persona-email" type="email" {...register('persona.email')} />
      </Campo>
      <Campo etiqueta="Dirección" error={e?.direccion?.message} className="sm:col-span-6" htmlFor="persona-dir">
        <Input id="persona-dir" {...register('persona.direccion')} />
      </Campo>
    </div>
  )
}
