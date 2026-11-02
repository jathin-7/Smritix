'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/stores/auth-store'
import { SmritixCompanion } from '@/components/smritix-companion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function LoginPage() {
  const router = useRouter()
  const { login, error, clearError } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setFormError(null)

    if (!email || !password) {
      setFormError('Please fill in all fields')
      return
    }

    setLoading(true)
    try {
      await login(email, password)
      router.push('/dashboard')
    } catch (err: any) {
      setFormError(err.message || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="p-8 rounded-[2rem] glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-lg space-y-6"
    >
      {/* Mini AI Companion Header */}
      <div className="flex flex-col items-center text-center space-y-2">
        <SmritixCompanion size="sm" />
        <h2 className="text-2xl font-black text-[#171725] tracking-tight">
          Welcome to <span className="text-gradient-companion">SMRITIX</span>
        </h2>
        <p className="text-xs text-[#77788A]">
          Enter your credentials to access your sovereign memory vault
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {(formError || error) && (
          <div className="p-3 text-xs text-red-600 bg-red-50 border border-red-200/60 rounded-2xl">
            {formError || error}
          </div>
        )}

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#171725]">Email</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full h-11 px-4 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] text-xs text-[#171725] placeholder:text-[#A1A1B3] shadow-sm focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-[#8B5CF6]/20 transition-all"
          />
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-[#171725]">Password</label>
          </div>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full h-11 px-4 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] text-xs text-[#171725] placeholder:text-[#A1A1B3] shadow-sm focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-[#8B5CF6]/20 transition-all"
          />
        </div>

        <Button
          type="submit"
          disabled={loading}
          className="w-full h-11 rounded-2xl text-xs font-bold bg-gradient-companion text-white shadow-pearl-sm hover:shadow-pearl-hover hover:opacity-95 transition-all mt-2"
        >
          {loading ? 'Decrypting Vault...' : 'Sign In'}
        </Button>
      </form>

      <div className="text-center pt-2 text-xs text-[#77788A]">
        Don&apos;t have an account?{' '}
        <Link href="/register" className="font-semibold text-[#8B5CF6] hover:underline">
          Create one now
        </Link>
      </div>
    </motion.div>
  )
}
