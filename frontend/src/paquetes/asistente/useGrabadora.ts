/**
 * Grabación de la pregunta para el asistente (CU28).
 *
 * MediaRecorder graba el audio y un AnalyserNode mide el nivel (RMS y pico) en vivo para el medidor.
 * El AudioContext se crea dentro del clic (antes de pedir el micrófono): si se crea después de un
 * await, el navegador lo deja suspendido y el medidor solo lee ceros.
 * Si el medidor funcionó y durante toda la grabación no se superó el umbral, el audio NO se envía
 * (el micrófono no está captando). Si el medidor no pudo funcionar, se envía igual y decide el backend.
 * El micrófono y el AudioContext se sueltan siempre: al terminar, al cancelar y al desmontar.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

const TIPOS_AUDIO = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
/** Hubo voz si el RMS llegó a este valor (0 = silencio total, 1 = saturado)... */
export const UMBRAL_SONIDO = 0.01
/** ...o si alguna muestra superó este valor absoluto. */
export const UMBRAL_PICO = 0.05

export const SIN_SONIDO =
  'No se detectó sonido. Revise que el micrófono correcto esté activo y con volumen en Windows/navegador, o escriba su pregunta.'

type Opciones = {
  maxSegundos: number
  alTerminar: (audio: Blob) => void
  alFallar: (mensaje: string) => void
}

export function useGrabadora({ maxSegundos, alTerminar, alFallar }: Opciones) {
  const [grabando, setGrabando] = useState(false)
  const [segundos, setSegundos] = useState(0)
  const [nivel, setNivel] = useState(0) // 0..1 para el medidor
  const [haySonido, setHaySonido] = useState(false)
  const [medidorActivo, setMedidorActivo] = useState(false) // el AudioContext está corriendo y midiendo

  const grabadora = useRef<MediaRecorder | null>(null)
  const flujo = useRef<MediaStream | null>(null)
  const contexto = useRef<AudioContext | null>(null)
  const cuadro = useRef<number | null>(null)
  const intervalo = useRef<number | null>(null)
  const huboSonido = useRef(false)
  const midio = useRef(false) // se tomaron muestras con el contexto en 'running'
  const descartar = useRef(false)
  const avisos = useRef({ alTerminar, alFallar })

  useEffect(() => {
    avisos.current = { alTerminar, alFallar }
  })

  const liberar = useCallback(() => {
    if (intervalo.current) window.clearInterval(intervalo.current)
    intervalo.current = null
    if (cuadro.current) cancelAnimationFrame(cuadro.current)
    cuadro.current = null
    flujo.current?.getTracks().forEach((pista) => pista.stop())
    flujo.current = null
    if (contexto.current && contexto.current.state !== 'closed') void contexto.current.close()
    contexto.current = null
    grabadora.current = null
    setGrabando(false)
    setMedidorActivo(false)
    setNivel(0)
  }, [])

  /** Termina y envía (si hubo sonido). */
  const terminar = useCallback(() => {
    descartar.current = false
    const g = grabadora.current
    if (g && g.state !== 'inactive') g.stop()
  }, [])

  /** Termina sin enviar nada. */
  const cancelar = useCallback(() => {
    descartar.current = true
    const g = grabadora.current
    if (g && g.state !== 'inactive') g.stop()
    else liberar()
  }, [liberar])

  // Al desmontar: soltar el micrófono sin enviar.
  useEffect(() => cancelar, [cancelar])

  const iniciar = useCallback(async () => {
    if (grabadora.current) return
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      avisos.current.alFallar('Este navegador no permite grabar audio. Escriba su pregunta.')
      return
    }
    // El AudioContext se crea ya, dentro del gesto del usuario (antes de cualquier await).
    const ContextoAudio =
      window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    let ctx: AudioContext | null = null
    try {
      ctx = ContextoAudio ? new ContextoAudio() : null
      if (ctx && ctx.state !== 'running') void ctx.resume().catch(() => undefined)
    } catch {
      ctx = null
    }
    contexto.current = ctx

    let pistas: MediaStream
    try {
      pistas = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      })
    } catch {
      if (ctx && ctx.state !== 'closed') void ctx.close()
      contexto.current = null
      avisos.current.alFallar('No se pudo usar el micrófono. Revise el permiso del navegador o escriba su pregunta.')
      return
    }
    flujo.current = pistas
    huboSonido.current = false
    midio.current = false
    descartar.current = false
    setHaySonido(false)
    setMedidorActivo(false)
    setSegundos(0)

    // Medidor de nivel (sin AudioContext se graba igual, sin medidor ni control de silencio).
    if (ctx) {
      try {
        const analizador = ctx.createAnalyser()
        analizador.fftSize = 1024
        ctx.createMediaStreamSource(pistas).connect(analizador)
        if (ctx.state !== 'running') await ctx.resume().catch(() => undefined)
        const muestras = new Float32Array(analizador.fftSize)
        const medir = () => {
          if (contexto.current !== ctx) return
          if (ctx.state === 'running') {
            analizador.getFloatTimeDomainData(muestras)
            let suma = 0
            let maximo = 0
            for (const m of muestras) {
              suma += m * m
              const a = Math.abs(m)
              if (a > maximo) maximo = a
            }
            const rms = Math.sqrt(suma / muestras.length)
            if (!midio.current) {
              midio.current = true
              setMedidorActivo(true)
            }
            if (!huboSonido.current && (rms >= UMBRAL_SONIDO || maximo >= UMBRAL_PICO)) {
              huboSonido.current = true
              setHaySonido(true)
            }
            setNivel(Math.min(1, Math.round(Math.max(rms * 8, maximo * 1.5) * 20) / 20))
          }
          cuadro.current = requestAnimationFrame(medir)
        }
        medir()
      } catch {
        midio.current = false
      }
    }

    const tipo = TIPOS_AUDIO.find((t) => MediaRecorder.isTypeSupported(t))
    const g = new MediaRecorder(pistas, tipo ? { mimeType: tipo } : undefined)
    const partes: Blob[] = []
    g.ondataavailable = (e) => {
      if (e.data.size > 0) partes.push(e.data)
    }
    g.onstop = () => {
      // El control de silencio solo vale si el medidor realmente midió; si no, decide el backend.
      const silencio = midio.current && !huboSonido.current
      liberar()
      if (descartar.current) return
      if (silencio) {
        avisos.current.alFallar(SIN_SONIDO)
        return
      }
      const audio = new Blob(partes, { type: g.mimeType || tipo || 'audio/webm' })
      if (audio.size === 0) {
        avisos.current.alFallar('No se grabó audio. Intente de nuevo.')
        return
      }
      avisos.current.alTerminar(audio)
    }
    grabadora.current = g
    g.start()
    setGrabando(true)
    const inicio = Date.now()
    intervalo.current = window.setInterval(() => {
      const s = Math.floor((Date.now() - inicio) / 1000)
      setSegundos(s)
      if (s >= maxSegundos) terminar()
    }, 250)
  }, [liberar, maxSegundos, terminar])

  return { grabando, segundos, nivel, haySonido, medidorActivo, iniciar, terminar, cancelar }
}
