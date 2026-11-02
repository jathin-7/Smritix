'use client'

import { motion } from 'framer-motion'

export function PearlHexBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 bg-[#F8F9FC]" aria-hidden="true">
      {/* 1. Large-scale Soft Hexagonal Honeycomb Canvas */}
      <svg
        className="absolute inset-0 w-full h-full opacity-60"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          maskImage: 'radial-gradient(ellipse at 50% 35%, black 25%, rgba(0, 0, 0, 0.4) 55%, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(ellipse at 50% 35%, black 25%, rgba(0, 0, 0, 0.4) 55%, transparent 80%)',
        }}
      >
        <defs>
          {/* Subtle Seamless Honeycomb Lattice (Width 120, Height 104) */}
          <pattern id="honeycomb-pattern" width="120" height="103.92" patternUnits="userSpaceOnUse">
            {/* Hexagon 1 */}
            <path
              d="M 30,0 L 90,0 L 120,51.96 L 90,103.92 L 30,103.92 L 0,51.96 Z"
              fill="none"
              stroke="rgba(124, 58, 237, 0.045)"
              strokeWidth="1.2"
            />
            {/* Offset Hexagon 2 */}
            <path
              d="M 90,51.96 L 150,51.96 L 180,103.92 L 150,155.88 L 90,155.88 L 60,103.92 Z"
              fill="none"
              stroke="rgba(56, 189, 248, 0.04)"
              strokeWidth="1.2"
            />
          </pattern>
        </defs>

        <rect width="100%" height="100%" fill="url(#honeycomb-pattern)" />
      </svg>

      {/* 2. Primary Ambient Violet Radial Aura (Centered behind Companion) */}
      <motion.div
        animate={{
          scale: [1, 1.12, 1],
          opacity: [0.35, 0.55, 0.35],
          x: [0, 15, -15, 0],
          y: [0, -20, 15, 0],
        }}
        transition={{
          duration: 16,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-[5%] left-1/2 -translate-x-1/2 w-[750px] h-[650px] rounded-full bg-gradient-to-b from-[#8B5CF6]/15 via-[#A78BFA]/10 to-transparent blur-[110px]"
      />

      {/* 3. Secondary Ambient Cyan Aura (Subtle lower-right illumination) */}
      <motion.div
        animate={{
          scale: [1, 1.08, 0.96, 1],
          opacity: [0.3, 0.5, 0.3],
          x: [0, -20, 20, 0],
          y: [0, 15, -15, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-[25%] right-[15%] w-[580px] h-[520px] rounded-full bg-gradient-to-br from-[#38BDF8]/12 via-[#7DD3FC]/8 to-transparent blur-[120px]"
      />

      {/* 4. Ambient Soft Bottom Fill */}
      <div className="absolute bottom-0 inset-x-0 h-[380px] bg-gradient-to-t from-white via-white/70 to-transparent" />

      {/* 5. Minimalist Ambient Particle Accents */}
      <div className="absolute inset-0">
        <motion.span
          animate={{ y: [0, -18, 0], opacity: [0.3, 0.7, 0.3] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-[22%] left-[16%] w-2 h-2 rounded-full bg-[#8B5CF6]/30 blur-[0.5px]"
        />
        <motion.span
          animate={{ y: [0, 16, 0], opacity: [0.25, 0.6, 0.25] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
          className="absolute top-[38%] right-[22%] w-2.5 h-2.5 rounded-full bg-[#38BDF8]/35 blur-[0.5px]"
        />
        <motion.span
          animate={{ y: [0, -12, 0], opacity: [0.2, 0.5, 0.2] }}
          transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut', delay: 2.5 }}
          className="absolute top-[68%] left-[28%] w-1.5 h-1.5 rounded-full bg-[#A78BFA]/30 blur-[0.5px]"
        />
      </div>
    </div>
  )
}
