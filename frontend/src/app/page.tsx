'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/stores/auth-store'
import { PearlHexBackground } from '@/components/pearl-hex-background'
import { SmritixCompanion } from '@/components/smritix-companion'
import { Button } from '@/components/ui/button'

export default function Home() {
  const router = useRouter()
  const { isAuthenticated, checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, router])

  return (
    <main className="relative min-h-screen flex flex-col items-center justify-center px-6 py-20 bg-[#F8F9FC] text-[#11121C] overflow-hidden selection:bg-purple-200 selection:text-purple-900">
      {/* 1. Signature Soft Pearl-White Honeycomb Background */}
      <PearlHexBackground />

      <div className="relative z-10 max-w-3xl mx-auto flex flex-col items-center text-center space-y-8">
        {/* 2. Floating 3D SMRITIX Companion */}
        <motion.div
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="relative pb-2"
        >
          <SmritixCompanion size="lg" />
        </motion.div>

        {/* 3. Hero Identity & Typography */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="space-y-4"
        >
          {/* Subtle Tag Badge */}
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/85 backdrop-blur-md border border-purple-200/60 shadow-[0_2px_10px_rgba(139,92,246,0.08)] text-xs font-semibold text-[#6D28D9]">
            <span className="w-2 h-2 rounded-full bg-[#8B5CF6] shadow-[0_0_8px_#8B5CF6] animate-pulse" />
            <span>Local-First Sovereign AI Memory</span>
          </div>

          {/* Premium Modern Title */}
          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-[#11121C] leading-[1.12]">
            Remember. Interconnect.{' '}
            <span className="bg-gradient-to-r from-[#6D28D9] via-[#8B5CF6] to-[#0284C7] bg-clip-text text-transparent">
              Resurface.
            </span>
          </h1>

          {/* Subtitle with high-legibility balanced gray */}
          <p className="max-w-xl mx-auto text-base sm:text-lg text-[#5A5D75] leading-relaxed font-normal">
            Your personal digital memory companion. Capture thoughts, documents, and code — interconnected through local neural embeddings and an interactive knowledge graph.
          </p>
        </motion.div>

        {/* 4. Refined Call to Actions */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.35 }}
          className="flex flex-col sm:flex-row items-center gap-4 pt-2 w-full sm:w-auto"
        >
          <Link href="/register" className="w-full sm:w-auto">
            <Button
              size="lg"
              className="w-full sm:w-auto h-12 px-8 rounded-full text-sm font-semibold text-white bg-gradient-to-r from-[#7C3AED] via-[#8B5CF6] to-[#0284C7] hover:opacity-95 shadow-[0_8px_25px_rgba(124,58,237,0.28)] hover:shadow-[0_12px_30px_rgba(124,58,237,0.38)] transition-all transform hover:-translate-y-0.5 active:translate-y-0"
            >
              Get Started Free →
            </Button>
          </Link>

          <Link href="/login" className="w-full sm:w-auto">
            <Button
              variant="secondary"
              size="lg"
              className="w-full sm:w-auto h-12 px-8 rounded-full text-sm font-semibold text-[#11121C] bg-white hover:bg-[#F4F5FB] border border-[#DFE2EE] shadow-[0_4px_14px_rgba(20,20,40,0.04)] hover:shadow-[0_6px_20px_rgba(139,92,246,0.12)] hover:border-purple-300 transition-all transform hover:-translate-y-0.5 active:translate-y-0"
            >
              Sign In to Vault
            </Button>
          </Link>
        </motion.div>

        {/* 5. Clean Trust Highlights */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 pt-6 text-xs text-[#5A5D75] font-medium"
        >
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/70 border border-black/[0.04] shadow-xs">
            <span className="text-emerald-600 font-bold">✓</span> 100% On-Device Sovereign Storage
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/70 border border-black/[0.04] shadow-xs">
            <span className="text-emerald-600 font-bold">✓</span> Zero Telemetry or Cloud Egress
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/70 border border-black/[0.04] shadow-xs">
            <span className="text-purple-600 font-bold">✓</span> Dense Neural Vector Search
          </span>
        </motion.div>
      </div>
    </main>
  )
}
