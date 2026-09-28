/** Marco de las pantallas de acceso (login y recuperar contraseña): panel azul con el escudo + formulario. */
import type { ReactNode } from 'react'
import { GraduationCapIcon } from 'lucide-react'
import Escudo from '@/componentes/Escudo'

export default function MarcoAcceso({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-blue-50 p-4">
      <div className="grid w-full max-w-4xl overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-slate-200 md:grid-cols-[5fr_6fr]">
        <div className="relative flex flex-col items-center justify-center gap-3 overflow-hidden bg-gradient-to-br from-[#0B2352] via-[#123A86] to-[#1A5FD6] px-8 py-6 text-center text-white md:gap-4 md:py-10">
          <div className="pointer-events-none absolute -bottom-16 -left-16 size-56 rounded-full bg-white/10" />
          <div className="pointer-events-none absolute -top-20 -right-10 size-56 rounded-full bg-white/5" />
          <Escudo className="relative h-16 w-auto drop-shadow-lg md:h-28" />
          <div className="relative">
            <p className="text-base text-blue-100 md:text-lg">Unidad Educativa</p>
            <p className="text-xl font-bold md:text-2xl">“Mariscal Sucre G”</p>
          </div>
          <div className="relative hidden h-px w-16 bg-white/60 md:block" />
          <GraduationCapIcon className="relative hidden size-12 md:block" strokeWidth={1.5} />
          <div className="relative hidden md:block">
            <p className="text-lg font-semibold">Sistema de Gestión Académica</p>
            <p className="mt-2 text-sm text-blue-100">
              Accede para gestionar las actividades académicas, administrativas y estudiantiles.
            </p>
          </div>
        </div>
        <div className="flex items-center justify-center px-6 py-10 sm:px-12">{children}</div>
      </div>
    </div>
  )
}
