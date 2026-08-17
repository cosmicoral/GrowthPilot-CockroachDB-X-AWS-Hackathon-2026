interface LogoProps {
  size?: number
  className?: string
}

export default function Logo({ size = 40, className = "" }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Orbit circle ring - main arc (left + top) */}
      <path
        d="M 50 8 A 42 42 0 1 0 92 50"
        stroke="#6aaee0"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />

      {/* Swoosh trail below-left (comet tail) */}
      <path
        d="M 18 72 Q 28 88 48 82 Q 60 78 68 70"
        stroke="#a8d4f0"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.7"
      />
      <path
        d="M 22 78 Q 34 92 52 86"
        stroke="#c4e4f8"
        strokeWidth="1.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.5"
      />

      {/* Paper airplane body (pointing upper-right) */}
      {/* Main wing top */}
      <path
        d="M 24 62 L 72 22 L 58 68 Z"
        fill="#5b9fd5"
      />
      {/* Dark underside fold */}
      <path
        d="M 42 56 L 72 22 L 58 68 Z"
        fill="#3a82bc"
      />
      {/* Tail flap */}
      <path
        d="M 40 58 L 58 68 L 52 74 Z"
        fill="#4a90c8"
      />
      {/* Center crease highlight */}
      <path
        d="M 24 62 L 72 22"
        stroke="#7ab8e0"
        strokeWidth="0.8"
        opacity="0.6"
        strokeLinecap="round"
      />

      {/* 4-point star sparkle top-right */}
      <path
        d="M 80 16 L 81.8 21.2 L 87 23 L 81.8 24.8 L 80 30 L 78.2 24.8 L 73 23 L 78.2 21.2 Z"
        fill="#8bc8f0"
      />
    </svg>
  )
}
