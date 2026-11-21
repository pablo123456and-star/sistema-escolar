/**
 * CU28 - Consultar información por comando de voz.
 *
 * Botón flotante (abajo a la derecha) para todos los roles con sesión, solo si el servidor tiene
 * configurado el asistente (GET /asistente/estado). El botón SOLO abre u oculta el panel; al ocultarlo
 * se conserva la conversación. Dentro del panel, junto a la caja de texto, está el micrófono: graba la
 * pregunta (máximo 20 s) con un medidor de nivel en vivo; si no se detectó sonido no se envía nada.
 * La pregunta grabada va a /asistente/voz y la escrita a /asistente/consulta (con los últimos 6 turnos
 * como historial, para preguntas de seguimiento como "¿y en Física?"). La respuesta se lee en voz alta
 * (speechSynthesis) salvo que se silencie. El asistente solo consulta, con los permisos del usuario.
 */
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { cn } from 'cn'
import {
  BotIcon,
  ChevronDownIcon,
  LoaderCircleIcon,
  MicIcon,
  SendHorizontalIcon,
  SquareIcon,
  Trash2Icon,
  Volume2Icon,
  VolumeXIcon,
  XIcon,
} from 'lucide-react'
import { Button } from '@/componentes/ui/button'
import { Input } from '@/componentes/ui/input'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { useConsultarAsistente, useEstadoAsistente, usePreguntarPorVoz } from '../api'
import { MAX_HISTORIAL, MAX_PREGUNTA, type RespuestaAsistente, type TurnoAnterior } from '../schemas'
import { useGrabadora } from '../useGrabadora'

const MAX_SEGUNDOS = 20
const CLAVE_SILENCIO = 'asistente-silenciado'
const BARRAS = 5

function leerSilencio(): boolean {
  try {
    return localStorage.getItem(CLAVE_SILENCIO) === '1'
  } catch {
    return false
  }
}

function guardarSilencio(valor: boolean) {
  try {
    localStorage.setItem(CLAVE_SILENCIO, valor ? '1' : '0')
  } catch {
    // sin almacenamiento (modo privado): la preferencia dura solo esta sesión
  }
}

function hablar(texto: string) {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.cancel()
  const locucion = new SpeechSynthesisUtterance(texto)
  locucion.lang = 'es-ES'
  const voces = window.speechSynthesis.getVoices()
  const voz = voces.find((v) => v.lang.toLowerCase().startsWith('es-bo')) ?? voces.find((v) => v.lang.toLowerCase().startsWith('es'))
  if (voz) {
    locucion.voice = voz
    locucion.lang = voz.lang
  }
  window.speechSynthesis.speak(locucion)
}

function callar() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}

/** Medidor de nivel del micrófono: 5 barras que se encienden según el volumen. */
function Medidor({ nivel }: { nivel: number }) {
  return (
    <span className="flex h-4 items-end gap-0.5" aria-hidden="true">
      {Array.from({ length: BARRAS }, (_, i) => (
        <span
          key={i}
          className={cn(
            'w-1 rounded-sm transition-colors',
            nivel > i / BARRAS + 0.02 ? 'bg-rose-600' : 'bg-rose-200',
          )}
          style={{ height: `${40 + i * 15}%` }}
        />
      ))}
    </span>
  )
}

export default function AsistenteVoz() {
  const { usuario } = useSesion()
  const estado = useEstadoAsistente(!!usuario)
  const consultar = useConsultarAsistente()
  const preguntarVoz = usePreguntarPorVoz()

  const [abierto, setAbierto] = useState(false)
  const [pendiente, setPendiente] = useState(false) // llegó una respuesta con el panel oculto
  const [texto, setTexto] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [turnos, setTurnos] = useState<TurnoAnterior[]>([])
  const [silenciado, setSilenciado] = useState(leerSilencio)
  // Las respuestas llegan después: se usan los valores del momento en que llegan.
  const silencioActual = useRef(silenciado)
  const abiertoActual = useRef(abierto)
  const finConversacion = useRef<HTMLDivElement | null>(null)

  const procesando = consultar.isPending || preguntarVoz.isPending

  useEffect(() => {
    abiertoActual.current = abierto
  }, [abierto])

  const mostrar = (r: RespuestaAsistente) => {
    setTurnos((anteriores) => [...anteriores, { pregunta: r.pregunta, respuesta: r.respuesta }].slice(-MAX_HISTORIAL))
    if (!abiertoActual.current) setPendiente(true)
    if (!silencioActual.current) hablar(r.respuesta)
  }

  const alFallar = (e: unknown) => {
    setError(mensajeError(e))
    if (!abiertoActual.current) setPendiente(true)
  }

  const grabadora = useGrabadora({
    maxSegundos: MAX_SEGUNDOS,
    alTerminar: (audio) =>
      preguntarVoz.mutate({ audio, historial: turnos.slice(-MAX_HISTORIAL) }, { onSuccess: mostrar, onError: alFallar }),
    alFallar: setError,
  })

  // Al desmontar (cerrar sesión, salir): callar (la grabadora suelta el micrófono sola).
  useEffect(() => callar, [])

  useEffect(() => {
    if (abierto) finConversacion.current?.scrollIntoView({ block: 'end' })
  }, [abierto, turnos, procesando, error, grabadora.grabando])

  if (!usuario || !estado.data?.habilitado) return null

  const alternarPanel = () => {
    if (abierto) {
      grabadora.cancelar() // al ocultar, la grabación en curso se descarta
      setAbierto(false)
    } else {
      setPendiente(false)
      setAbierto(true)
    }
  }

  const pulsarMicrofono = () => {
    if (grabadora.grabando) {
      grabadora.terminar()
      return
    }
    if (procesando) return
    setError(null)
    callar()
    void grabadora.iniciar()
  }

  const enviarTexto = (e: FormEvent) => {
    e.preventDefault()
    const pregunta = texto.trim()
    if (pregunta.length < 2 || procesando || grabadora.grabando) return
    setError(null)
    callar()
    consultar.mutate(
      { pregunta, historial: turnos.slice(-MAX_HISTORIAL) },
      {
        onSuccess: (r) => {
          setTexto('')
          mostrar(r)
        },
        onError: alFallar,
      },
    )
  }

  const cambiarSilencio = () => {
    const nuevo = !silenciado
    setSilenciado(nuevo)
    silencioActual.current = nuevo
    guardarSilencio(nuevo)
    if (nuevo) callar()
  }

  const borrarConversacion = () => {
    callar()
    setTurnos([])
    setError(null)
  }

  const botonEncabezado = 'text-white hover:bg-white/10 hover:text-white'

  return (
    <div className="print:hidden">
      {abierto && (
        <section
          aria-label="Asistente por voz"
          className="fixed right-4 bottom-24 z-30 flex max-h-[min(32rem,calc(100dvh-8rem))] w-[calc(100vw-2rem)] max-w-sm flex-col overflow-hidden rounded-xl border bg-white shadow-xl"
        >
          <header className="flex items-center gap-2 border-b bg-[#0B2352] px-3 py-2 text-white">
            <BotIcon className="size-5" />
            <h2 className="text-sm font-semibold">Asistente</h2>
            <div className="ml-auto flex items-center">
              <Button
                size="icon-sm"
                variant="ghost"
                className={botonEncabezado}
                onClick={borrarConversacion}
                disabled={turnos.length === 0 && !error}
                aria-label="Borrar conversación"
                title="Borrar conversación"
              >
                <Trash2Icon />
              </Button>
              <Button
                size="icon-sm"
                variant="ghost"
                className={botonEncabezado}
                onClick={cambiarSilencio}
                aria-label={silenciado ? 'Activar lectura en voz alta' : 'Silenciar lectura en voz alta'}
                aria-pressed={silenciado}
                title={silenciado ? 'Activar voz' : 'Silenciar'}
              >
                {silenciado ? <VolumeXIcon /> : <Volume2Icon />}
              </Button>
              <Button
                size="icon-sm"
                variant="ghost"
                className={botonEncabezado}
                onClick={alternarPanel}
                aria-label="Ocultar asistente"
                title="Ocultar (la conversación se conserva)"
              >
                <ChevronDownIcon />
              </Button>
            </div>
          </header>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3 text-sm" aria-live="polite">
            {turnos.length === 0 && !procesando && !grabadora.grabando && !error && (
              <p className="text-slate-500">
                Pulse el micrófono y haga su pregunta, por ejemplo: “¿Qué clases tengo el lunes?” o “¿Tengo cuotas
                pendientes?”. También puede escribirla abajo.
              </p>
            )}
            {turnos.map((t, i) => (
              <div key={i} className="space-y-2">
                <p className="ml-8 rounded-lg rounded-br-none bg-blue-600 px-3 py-2 text-white">{t.pregunta}</p>
                <p className="mr-8 rounded-lg rounded-bl-none bg-slate-100 px-3 py-2 text-slate-800">{t.respuesta}</p>
              </div>
            ))}
            {grabadora.grabando && (
              <div className="space-y-1">
                <p className="flex items-center gap-2 text-rose-600">
                  <Medidor nivel={grabadora.nivel} />
                  Escuchando… {Math.max(0, MAX_SEGUNDOS - grabadora.segundos)} s
                </p>
                {grabadora.medidorActivo && !grabadora.haySonido && grabadora.segundos >= 3 && (
                  <p className="text-xs text-amber-700">
                    No se detecta sonido: revise que el micrófono correcto esté activo y con volumen.
                  </p>
                )}
              </div>
            )}
            {procesando && (
              <p className="flex items-center gap-2 text-slate-500">
                <LoaderCircleIcon className="size-4 animate-spin" /> Buscando la respuesta…
              </p>
            )}
            {error && (
              <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-rose-700">
                {error}
              </p>
            )}
            <div ref={finConversacion} />
          </div>

          <form onSubmit={enviarTexto} className="flex items-center gap-2 border-t p-2">
            <Input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              maxLength={MAX_PREGUNTA}
              placeholder={grabadora.grabando ? 'Escuchando…' : 'Escriba su pregunta…'}
              aria-label="Pregunta para el asistente"
              disabled={procesando || grabadora.grabando}
            />
            {grabadora.grabando ? (
              <>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  onClick={grabadora.cancelar}
                  aria-label="Cancelar la grabación sin enviar"
                  title="Cancelar"
                >
                  <XIcon />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  className="animate-pulse bg-rose-600 hover:bg-rose-700"
                  onClick={pulsarMicrofono}
                  aria-label="Terminar la grabación y preguntar"
                  title="Terminar y preguntar"
                >
                  <SquareIcon className="fill-current" />
                </Button>
              </>
            ) : (
              <>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  onClick={pulsarMicrofono}
                  disabled={procesando}
                  aria-label="Preguntar por voz"
                  title="Preguntar por voz"
                >
                  <MicIcon />
                </Button>
                <Button
                  type="submit"
                  size="icon"
                  aria-label="Enviar pregunta"
                  disabled={procesando || texto.trim().length < 2}
                >
                  <SendHorizontalIcon />
                </Button>
              </>
            )}
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={alternarPanel}
        aria-label={abierto ? 'Ocultar asistente' : pendiente ? 'Abrir asistente (hay una respuesta nueva)' : 'Abrir asistente'}
        aria-expanded={abierto}
        title={abierto ? 'Ocultar asistente' : 'Asistente'}
        className="fixed right-4 bottom-4 z-30 flex size-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition-colors hover:bg-blue-700 focus-visible:ring-4 focus-visible:ring-blue-300 focus-visible:outline-none"
      >
        {abierto ? <ChevronDownIcon className="size-6" /> : <BotIcon className="size-6" />}
        {!abierto && procesando && (
          <span className="absolute -top-1 -right-1 flex size-5 items-center justify-center rounded-full bg-white text-blue-600 shadow">
            <LoaderCircleIcon className="size-3.5 animate-spin" />
          </span>
        )}
        {!abierto && !procesando && pendiente && (
          <span className="absolute top-0 right-0 size-3.5 rounded-full border-2 border-white bg-rose-500" />
        )}
      </button>
    </div>
  )
}
