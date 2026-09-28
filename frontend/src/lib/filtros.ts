/** Valor usado en los Select de filtros para "Todos" (Radix no admite valores vacíos). */
export const TODOS = 'todos'

/** Convierte "Todos" en "sin filtro" para enviarlo al backend. */
export const sinTodos = (v: string) => (v === TODOS ? undefined : v)
