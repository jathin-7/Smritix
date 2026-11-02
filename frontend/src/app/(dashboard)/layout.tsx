'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '@/stores/auth-store'
import { PearlHexBackground } from '@/components/pearl-hex-background'
import { Button } from '@/components/ui/button'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '✦' },
  { href: '/memories', label: 'Memories', icon: '🧠' },
  { href: '/ask', label: 'Ask SMRITIX', icon: '💬' },
  { href: '/graph', label: 'Knowledge Graph', icon: '🕸️' },
  { href: '/search', label: 'Search', icon: '🔍' },
  { href: '/timeline', label: 'Timeline', icon: '⏳' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, isAuthenticated, isLoading, checkAuth, logout } = useAuthStore()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  const initial = user?.display_name
    ? user.display_name[0].toUpperCase()
    : user?.email
    ? user.email[0].toUpperCase()
    : 'S'

  const isNavActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard' || pathname === '/'
    }
    return pathname === href || pathname.startsWith(href + '/')
  }

  return (
    <div className="relative min-h-screen bg-[#F8F9FC] text-[#11121C] font-sans antialiased overflow-x-hidden">
      {/* Signature Embossed Pearl-White Hexagonal Background */}
      <PearlHexBackground />

      {/* Floating Translucent Top Navigation Bar */}
      <header className="sticky top-0 z-40 w-full px-4 sm:px-8 pt-4 pb-2 pointer-events-none">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 pointer-events-auto">
          {/* SMRITIX Brand Emblem */}
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="relative w-9 h-9 rounded-2xl bg-gradient-companion p-[1.5px] shadow-pearl-sm group-hover:shadow-pearl-hover transition-all duration-300">
              <div className="w-full h-full rounded-[14px] bg-white flex items-center justify-center">
                <span className="text-base font-black bg-gradient-to-tr from-[#7045DB] to-[#38BDF8] bg-clip-text text-transparent">
                  S
                </span>
              </div>
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-[#171725] group-hover:text-primary transition-colors">
                SMRITIX
              </span>
              <div className="flex items-center gap-1.5 -mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[#77788A]">
                  Memory Core
                </span>
              </div>
            </div>
          </Link>

          {/* Centered Minimalist Navigation Dock (Desktop) */}
          <nav className="hidden lg:flex items-center gap-1 p-1.5 rounded-full glass-pearl shadow-pearl-sm border border-[rgba(30,30,60,0.06)]">
            {navItems.map((item) => {
              const active = isNavActive(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative px-4 py-2 rounded-full text-xs font-semibold tracking-wide transition-all duration-200 flex items-center gap-2 ${
                    active
                      ? 'text-white shadow-sm'
                      : 'text-[#77788A] hover:text-[#171725] hover:bg-white/70'
                  }`}
                >
                  {active && (
                    <motion.div
                      layoutId="activeNavIndicator"
                      className="absolute inset-0 rounded-full bg-gradient-companion -z-10 shadow-pearl-sm"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  <span className="text-xs">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>

          {/* Right Control Strip: Companion Pulse & User Profile */}
          <div className="flex items-center gap-3">
            {/* Quick Memory Action Button */}
            <Link href="/memories/new" className="hidden sm:inline-flex">
              <Button
                size="sm"
                className="h-9 px-4 rounded-full text-xs font-semibold gap-1.5 bg-gradient-companion text-white shadow-pearl-sm hover:shadow-pearl-hover hover:opacity-95 transition-all"
              >
                <span>+</span>
                <span>New Memory</span>
              </Button>
            </Link>

            {/* User Profile Pill */}
            {isAuthenticated ? (
              <div className="flex items-center gap-2 p-1.5 pr-2 rounded-full glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm">
                <div className="w-7 h-7 rounded-full bg-gradient-companion text-white font-bold text-xs flex items-center justify-center shadow-sm">
                  {initial}
                </div>
                <span className="text-xs font-medium text-[#171725] hidden md:inline max-w-[120px] truncate">
                  {user?.display_name || user?.email?.split('@')[0]}
                </span>
                <button
                  onClick={handleLogout}
                  title="Sign Out"
                  className="w-6 h-6 rounded-full hover:bg-black/5 flex items-center justify-center text-[#77788A] hover:text-red-500 transition-colors ml-1"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>
              </div>
            ) : null}

            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-2xl glass-pearl border border-[rgba(30,30,60,0.06)] text-[#171725]"
              aria-label="Toggle navigation menu"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Dropdown Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="lg:hidden mt-2 p-3 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] pointer-events-auto shadow-pearl-lg space-y-1"
            >
              {navItems.map((item) => {
                const active = isNavActive(item.href)
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-2xl text-xs font-semibold transition-all ${
                      active
                        ? 'bg-gradient-companion text-white shadow-sm'
                        : 'text-[#77788A] hover:bg-white/80 hover:text-[#171725]'
                    }`}
                  >
                    <span className="text-base">{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                )
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Main Content Area */}
      <main className="relative z-10 px-4 sm:px-8 py-6 max-w-7xl mx-auto">
        {children}
      </main>
    </div>
  )
}
