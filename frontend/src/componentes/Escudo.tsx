/** Escudo de la Unidad Educativa (antorcha, libro y laureles), dibujado en SVG. */
type Props = { className?: string }

export default function Escudo({ className }: Props) {
  return (
    <svg viewBox="0 0 100 116" className={className} role="img" aria-label="Escudo de la Unidad Educativa">
      <path d="M50 3 L94 16 V56 C94 84 74 103 50 113 C26 103 6 84 6 56 V16 Z" fill="#E3B341" />
      <path d="M50 9 L88 20 V56 C88 80 71 97 50 106 C29 97 12 80 12 56 V20 Z" fill="#12306B" />
      {/* laureles */}
      <g fill="none" stroke="#E3B341" strokeWidth="2.4" strokeLinecap="round">
        <path d="M27 84 C18 72 18 55 25 42" />
        <path d="M73 84 C82 72 82 55 75 42" />
      </g>
      <g fill="#E3B341">
        {[48, 56, 64, 72].map((y, i) => (
          <g key={y}>
            <ellipse cx={21 + (i === 0 ? 3 : i === 3 ? 2 : 0)} cy={y} rx="2.6" ry="5" transform={`rotate(-35 ${21} ${y})`} />
            <ellipse cx={79 - (i === 0 ? 3 : i === 3 ? 2 : 0)} cy={y} rx="2.6" ry="5" transform={`rotate(35 ${79} ${y})`} />
          </g>
        ))}
      </g>
      {/* antorcha */}
      <path d="M50 20 C56 27 55 33 50 37 C45 33 44 27 50 20 Z" fill="#F59E0B" />
      <path d="M50 25 C53 29 52 32 50 34 C48 32 47 29 50 25 Z" fill="#FDE68A" />
      <path d="M43 38 H57 L54 44 H46 Z" fill="#E3B341" />
      <rect x="47.5" y="44" width="5" height="16" rx="1.5" fill="#E3B341" />
      {/* libro abierto */}
      <path d="M50 66 C43 61 33 61 26 63 V82 C33 80 43 80 50 85 Z" fill="#FFFFFF" />
      <path d="M50 66 C57 61 67 61 74 63 V82 C67 80 57 80 50 85 Z" fill="#F1F5F9" />
      <g stroke="#94A3B8" strokeWidth="1">
        <path d="M31 68 H45 M31 72 H45 M31 76 H45 M55 68 H69 M55 72 H69 M55 76 H69" />
      </g>
      <path d="M50 66 V85" stroke="#12306B" strokeWidth="1.2" />
    </svg>
  )
}
