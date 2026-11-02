'use client'

import { useState, useEffect } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'

interface SmritixCompanionProps {
  state?: 'idle' | 'thinking' | 'searching' | 'speaking';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
}

export function SmritixCompanion({
  state = 'idle',
  size = 'md',
  className = '',
  onClick,
}: SmritixCompanionProps) {
  const [isBlinking, setIsBlinking] = useState(false)

  // Periodic natural blinking
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setIsBlinking(true)
      setTimeout(() => setIsBlinking(false), 180)
    }, 4200)
    return () => clearInterval(blinkInterval)
  }, [])

  // Interactive subtle mouse tracking
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)
  const springX = useSpring(mouseX, { stiffness: 120, damping: 18 })
  const springY = useSpring(mouseY, { stiffness: 120, damping: 18 })

  const eyeOffsetX = useTransform(springX, [-150, 150], [-4, 4])
  const eyeOffsetY = useTransform(springY, [-150, 150], [-3, 3])
  const bodyRotate = useTransform(springX, [-200, 200], [-5, 5])

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left - rect.width / 2
    const y = e.clientY - rect.top - rect.height / 2
    mouseX.set(x)
    mouseY.set(y)
  }

  const handleMouseLeave = () => {
    mouseX.set(0)
    mouseY.set(0)
  }

  // Dimension scaling
  const dimensions = {
    sm: { width: 120, height: 120 },
    md: { width: 180, height: 180 },
    lg: { width: 240, height: 240 },
  }[size]

  return (
    <div
      className={`relative inline-flex items-center justify-center select-none cursor-pointer ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{ width: dimensions.width, height: dimensions.height }}
    >
      {/* 1. Luminous Ambient Halo Glow (Violet & Cyan Aura) */}
      <motion.div
        animate={
          state === 'thinking'
            ? { scale: [1, 1.25, 1], opacity: [0.5, 0.85, 0.5] }
            : state === 'searching'
            ? { rotate: 360, opacity: [0.45, 0.75, 0.45] }
            : { scale: [1, 1.1, 1], opacity: [0.4, 0.65, 0.4] }
        }
        transition={{
          duration: state === 'thinking' ? 1.6 : 4,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute inset-[-14px] rounded-full bg-gradient-to-tr from-[#8B5CF6]/45 via-[#A78BFA]/30 to-[#38BDF8]/45 blur-2xl pointer-events-none"
      />

      {/* 2. Floating Shell with Idle Bob & Responsive Tilt */}
      <motion.div
        animate={{
          y: state === 'thinking' ? [0, -5, 0] : [0, -12, 0],
          rotate: state === 'thinking' ? [0, 1.5, -1.5, 0] : [0, 1.8, -1.8, 0],
        }}
        transition={{
          duration: state === 'thinking' ? 2 : 4.5,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        style={{ rotate: bodyRotate }}
        className="relative w-full h-full flex items-center justify-center"
      >
        {/* Soft Ambient Ground Shadow */}
        <motion.div
          animate={{
            scale: [0.85, 0.7, 0.85],
            opacity: [0.25, 0.12, 0.25],
          }}
          transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -bottom-6 w-3/4 h-4 rounded-full bg-[#11121C]/15 blur-md"
        />

        {/* 3. Sculpted Porcelain White Ceramic Body Shell */}
        <div
          className="relative w-[92%] h-[92%] rounded-[52px] bg-gradient-to-b from-[#FFFFFF] via-[#FAFBFD] to-[#E2E6F2] p-4 flex items-center justify-center border border-white"
          style={{
            boxShadow:
              '0 24px 48px -12px rgba(124, 58, 237, 0.18), 0 10px 20px -5px rgba(17, 18, 28, 0.08), inset 0 2px 5px #FFFFFF, inset 0 -6px 14px rgba(139, 92, 246, 0.12)',
          }}
        >
          {/* Top Ceramic Specular Highlight Arc */}
          <div className="absolute top-2 left-1/4 w-1/2 h-3.5 rounded-full bg-gradient-to-b from-white/95 to-transparent blur-[0.5px] pointer-events-none" />

          {/* Subtly Shaded Shoulder & Edge Illumination */}
          <div className="absolute inset-0 rounded-[50px] border border-transparent bg-gradient-to-tr from-[#8B5CF6]/20 via-transparent to-[#38BDF8]/25 opacity-70 pointer-events-none" />

          {/* 4. Sleek Curved OLED Visor Screen (Centered Horizontal Capsule) */}
          <div
            className="relative w-[68%] h-[42%] rounded-[24px] bg-gradient-to-b from-[#111320] via-[#0B0C16] to-[#07080E] p-2 flex items-center justify-center overflow-hidden border border-[#2B2D44]/70"
            style={{
              boxShadow:
                'inset 0 2px 6px rgba(0, 0, 0, 0.9), 0 4px 12px rgba(0, 0, 0, 0.15)',
            }}
          >
            {/* Top Visor Glass Reflection Curve */}
            <div className="absolute top-0 inset-x-0 h-1/2 bg-gradient-to-b from-white/18 to-transparent rounded-t-[20px] pointer-events-none" />

            {/* 5. Glowing Cyan Expressive Digital Face */}
            <motion.div
              style={{ x: eyeOffsetX, y: eyeOffsetY }}
              className="relative flex items-center justify-center gap-3.5 z-10"
            >
              {/* Left Eye */}
              <motion.div
                animate={
                  isBlinking
                    ? { scaleY: 0.1 }
                    : state === 'thinking'
                    ? { scaleY: [1, 0.35, 1], scaleX: [1, 1.25, 1] }
                    : { scaleY: 1 }
                }
                transition={{ duration: 0.18 }}
                className="w-3.5 h-6 rounded-full bg-[#38BDF8]"
                style={{
                  boxShadow:
                    '0 0 12px #38BDF8, 0 0 22px rgba(139, 92, 246, 0.8), inset 0 0 4px #FFFFFF',
                }}
              />

              {/* Minimal Center Expression Node */}
              <motion.div
                animate={{
                  opacity: state === 'speaking' ? [0.3, 1, 0.3] : 0.6,
                  scale: state === 'speaking' ? [0.8, 1.3, 0.8] : 1,
                }}
                transition={{ duration: 0.8, repeat: Infinity }}
                className="w-1 h-1 rounded-full bg-[#38BDF8]/70"
              />

              {/* Right Eye */}
              <motion.div
                animate={
                  isBlinking
                    ? { scaleY: 0.1 }
                    : state === 'thinking'
                    ? { scaleY: [1, 0.35, 1], scaleX: [1, 1.25, 1] }
                    : { scaleY: 1 }
                }
                transition={{ duration: 0.18 }}
                className="w-3.5 h-6 rounded-full bg-[#38BDF8]"
                style={{
                  boxShadow:
                    '0 0 12px #38BDF8, 0 0 22px rgba(139, 92, 246, 0.8), inset 0 0 4px #FFFFFF',
                }}
              />
            </motion.div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
