'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/stores/auth-store'
import { SmritixCompanion } from '@/components/smritix-companion'
import { Button } from '@/components/ui/button'

export default function RegisterPage() {
  const router = useRouter()
  const { register, error, clearError } = useAuthStore()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setFormError(null)

    if (!email || !password) {
      setFormError('Please fill in email and password')
      return
    }

    if (password.length < 8) {
      setFormError('Password must be at least 8 characters')
      return
    }

    setLoading(true)
    try {
      await register(email, password, displayName || undefined)
      router.push('/dashboard')
    } catch (err: any) {
      setFormError(err.message || 'Registration failed')
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
          Create <span className="text-gradient-companion">SMRITIX</span> Vault
        </h2>
        <p className="text-xs text-[#77788A]">
          Initialize your local-first personal AI memory companion
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {(formError || error) && (
          <div className="p-3 text-xs text-red-600 bg-red-50 border border-red-200/60 rounded-2xl">
            {formError || error}
          </div>
        )}

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#171725]">Display Name (Optional)</label>
          <input
            type="text"
            placeholder="Explorer"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full h-11 px-4 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] text-xs text-[#171725] placeholder:text-[#A1A1B3] shadow-sm focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-[#8B5CF6]/20 transition-all"
          />
        </div>

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
          <label className="text-xs font-semibold text-[#171725]">Password (min 8 chars)</label>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="w-full h-11 px-4 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] text-xs text-[#171725] placeholder:text-[#A1A1B3] shadow-sm focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-[#8B5CF6]/20 transition-all"
          />
        </div>

        <Button
          type="submit"
          disabled={loading}
          className="w-full h-11 rounded-2xl text-xs font-bold bg-gradient-companion text-white shadow-pearl-sm hover:shadow-pearl-hover hover:opacity-95 transition-all mt-2"
        >
          {loading ? 'Initializing Vault...' : 'Create Account'}
        </Button>
      </form>

      <div className="text-center pt-2 text-xs text-[#77788A]">
        Already have a vault?{' '}
        <Link href="/login" className="font-semibold text-[#8B5CF6] hover:underline">
          Sign In
        </Link>
      </div>
    </motion.div>
  )
}
