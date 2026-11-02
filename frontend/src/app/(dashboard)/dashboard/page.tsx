'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi, memoriesApi } from '@/lib/api/client'
import { useAuthStore } from '@/stores/auth-store'
import { SmritixCompanion } from '@/components/smritix-companion'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DashboardStatsResponse, Memory, TypeBreakdownItem, ActivityDayItem } from '@/types'

export default function DashboardPage() {
  const router = useRouter()
  const { user } = useAuthStore()
  const [companionState, setCompanionState] = useState<'idle' | 'thinking' | 'searching'>('idle')
  const [quickQuery, setQuickQuery] = useState('')

  // 1. Fetch live aggregate dashboard metrics
  const { data: stats, isLoading: loadingStats } = useQuery<DashboardStatsResponse>({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => dashboardApi.getStats(),
  })

  // 2. Fetch live knowledge gaps & health score
  const { data: healthData, isLoading: loadingHealth } = useQuery({
    queryKey: ['dashboard', 'knowledge-gaps'],
    queryFn: () => dashboardApi.getKnowledgeGaps(),
  })

  // 3. Fetch recent memories
  const { data: memoriesData, isLoading: loadingMemories } = useQuery({
    queryKey: ['memories', 'recent'],
    queryFn: () => memoriesApi.list({ limit: 4, offset: 0 }),
  })

  const handleQuickAsk = (e: React.FormEvent) => {
    e.preventDefault()
    if (!quickQuery.trim()) return
    setCompanionState('thinking')
    setTimeout(() => {
      router.push(`/ask?q=${encodeURIComponent(quickQuery.trim())}`)
    }, 400)
  }

  const healthScore = healthData?.health_score ?? 100
  const circumference = 2 * Math.PI * 38
  const strokeDashoffset = circumference - (healthScore / 100) * circumference

  return (
    <div className="space-y-10 pb-16 max-w-6xl mx-auto">
      {/* SECTION 1: Central AI Companion Showcase & Welcome Header */}
      <section className="relative flex flex-col items-center text-center pt-4 pb-2">
        {/* Ambient Halo behind the Companion */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 rounded-full bg-gradient-to-tr from-[#8B5CF6]/15 via-[#A78BFA]/10 to-[#38BDF8]/15 blur-3xl pointer-events-none" />

        {/* Central Floating SMRITIX 3D Companion */}
        <div className="relative z-10 mb-5">
          <SmritixCompanion
            state={companionState}
            size="md"
            onClick={() => {
              setCompanionState(companionState === 'idle' ? 'thinking' : 'idle')
            }}
          />
        </div>

        {/* Welcome Typography */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10 space-y-2 max-w-2xl px-4"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm text-xs font-semibold text-[#77788A]">
            <span className="w-2 h-2 rounded-full bg-[#8B5CF6] animate-pulse" />
            <span>Digital Memory Companion • Local-First</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-[#171725]">
            Your mind,{' '}
            <span className="text-gradient-companion">
              beautifully organized.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-[#77788A] font-normal leading-relaxed">
            Welcome back,{' '}
            <strong className="text-[#171725] font-semibold">
              {user?.display_name || user?.email?.split('@')[0] || 'Explorer'}
            </strong>
            . Your memories, notes, and dynamic knowledge graph are active and ready to be recalled.
          </p>
        </motion.div>

        {/* Floating Quick Ask Bar */}
        <motion.form
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          onSubmit={handleQuickAsk}
          className="relative z-10 w-full max-w-xl mt-6 px-4"
        >
          <div className="relative flex items-center p-1.5 rounded-full glass-pearl-elevated shadow-pearl-md border border-[rgba(30,30,60,0.08)] hover:shadow-pearl-hover transition-all duration-300">
            <span className="pl-4 pr-2 text-base text-[#8B5CF6]">✦</span>
            <input
              type="text"
              placeholder="Ask SMRITIX anything about your memory vault..."
              value={quickQuery}
              onChange={(e) => setQuickQuery(e.target.value)}
              className="flex-1 bg-transparent border-0 text-xs sm:text-sm text-[#171725] placeholder:text-[#A1A1B3] focus:outline-none focus:ring-0"
            />
            <Button
              type="submit"
              size="sm"
              className="h-9 px-5 rounded-full text-xs font-semibold bg-gradient-companion text-white shadow-pearl-sm hover:opacity-95 transition-opacity"
            >
              Ask
            </Button>
          </div>
        </motion.form>
      </section>

      {/* SECTION 2: Four Floating Memory Metric Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Metric 1: Total Memories */}
        <motion.div
          whileHover={{ y: -4, transition: { duration: 0.2 } }}
          className="p-5 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover transition-all duration-300"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-[#77788A]">Total Memories</span>
            <div className="w-8 h-8 rounded-2xl bg-[#8B5CF6]/10 text-[#8B5CF6] flex items-center justify-center text-sm font-bold">
              🧠
            </div>
          </div>
          <div className="text-3xl font-black text-[#171725] tracking-tight">
            {loadingStats ? '...' : (stats?.total_memories || 0).toLocaleString()}
          </div>
          <p className="text-[11px] text-[#77788A] mt-1">
            +{stats?.new_this_week || 0} recorded this week
          </p>
        </motion.div>

        {/* Metric 2: Interconnected Edges */}
        <motion.div
          whileHover={{ y: -4, transition: { duration: 0.2 } }}
          className="p-5 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover transition-all duration-300"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-[#77788A]">Knowledge Connections</span>
            <div className="w-8 h-8 rounded-2xl bg-[#38BDF8]/10 text-[#38BDF8] flex items-center justify-center text-sm font-bold">
              🕸️
            </div>
          </div>
          <div className="text-3xl font-black text-[#171725] tracking-tight">
            {loadingStats ? '...' : (stats?.total_edges || 0).toLocaleString()}
          </div>
          <p className="text-[11px] text-[#77788A] mt-1">
            Semantic similarity &gt; 0.65
          </p>
        </motion.div>

        {/* Metric 3: AI Conversations */}
        <motion.div
          whileHover={{ y: -4, transition: { duration: 0.2 } }}
          className="p-5 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover transition-all duration-300"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-[#77788A]">Conversations</span>
            <div className="w-8 h-8 rounded-2xl bg-[#A78BFA]/15 text-[#7045DB] flex items-center justify-center text-sm font-bold">
              💬
            </div>
          </div>
          <div className="text-3xl font-black text-[#171725] tracking-tight">
            {loadingStats ? '...' : (stats?.total_conversations || 0).toLocaleString()}
          </div>
          <p className="text-[11px] text-[#77788A] mt-1">
            Grounded memory queries
          </p>
        </motion.div>

        {/* Metric 4: Vector Chunks */}
        <motion.div
          whileHover={{ y: -4, transition: { duration: 0.2 } }}
          className="p-5 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover transition-all duration-300"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-[#77788A]">Vector Chunks</span>
            <div className="w-8 h-8 rounded-2xl bg-[#38BDF8]/10 text-[#38BDF8] flex items-center justify-center text-sm font-bold">
              ✦
            </div>
          </div>
          <div className="text-3xl font-black text-[#171725] tracking-tight">
            {loadingStats ? '...' : (stats?.total_chunks || 0).toLocaleString()}
          </div>
          <p className="text-[11px] text-[#77788A] mt-1">
            384-dimensional dense vectors
          </p>
        </motion.div>
      </section>

      {/* SECTION 3: Visual Analytics — Velocity Chart & Knowledge Health */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 7-Day Memory Activity Velocity (2 cols) */}
        <Card className="lg:col-span-2 p-6 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-bold text-[#171725]">Memory Velocity</h3>
              <p className="text-xs text-[#77788A]">Knowledge creation activity over the past 7 days</p>
            </div>
            <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6]">
              7-Day Sparkline
            </span>
          </div>

          <div className="h-44 flex items-end justify-between gap-2 pt-4 px-2">
            {stats?.activity && stats.activity.length > 0 ? (
              stats.activity.map((day: ActivityDayItem, idx: number) => {
                const maxVal = Math.max(...stats.activity.map((d: ActivityDayItem) => d.count), 1)
                const heightPercent = Math.max((day.count / maxVal) * 100, 8)
                const isToday = idx === stats.activity.length - 1

                return (
                  <div key={day.date} className="flex-1 flex flex-col items-center gap-2 group h-full justify-end">
                    <span className="text-[10px] font-semibold text-[#77788A] opacity-0 group-hover:opacity-100 transition-opacity">
                      {day.count}
                    </span>
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: `${heightPercent}%` }}
                      transition={{ duration: 0.6, delay: idx * 0.05 }}
                      className={`w-full max-w-[38px] rounded-t-xl transition-all duration-300 ${
                        isToday
                          ? 'bg-gradient-companion shadow-pearl-sm'
                          : 'bg-[#E5E7F2] hover:bg-[#8B5CF6]/50'
                      }`}
                    />
                    <span className="text-[10px] font-medium text-[#77788A]">
                      {day.day_name || day.date}
                    </span>
                  </div>
                )
              })
            ) : (
              <div className="w-full h-full flex items-center justify-center text-xs text-[#A1A1B3]">
                No recorded activity yet
              </div>
            )}
          </div>
        </Card>

        {/* Knowledge Base Health Score (1 col) */}
        <Card className="p-6 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-[#171725]">Knowledge Health</h3>
            <p className="text-xs text-[#77788A]">Graph connectivity & completeness</p>
          </div>

          <div className="relative flex items-center justify-center py-6">
            <svg className="w-32 h-32 -rotate-90 transform" viewBox="0 0 96 96">
              {/* Background Track */}
              <circle
                cx="48"
                cy="48"
                r="38"
                stroke="#E5E7F2"
                strokeWidth="7"
                fill="none"
              />
              {/* Gradient Progress Arc */}
              <circle
                cx="48"
                cy="48"
                r="38"
                stroke="url(#healthGradient)"
                strokeWidth="7"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="none"
                className="transition-all duration-1000 ease-out"
              />
              <defs>
                <linearGradient id="healthGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8B5CF6" />
                  <stop offset="100%" stopColor="#38BDF8" />
                </linearGradient>
              </defs>
            </svg>

            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-2xl font-black text-[#171725]">
                {loadingHealth ? '...' : `${healthScore}%`}
              </span>
              <span className="text-[10px] font-semibold text-[#8B5CF6] uppercase tracking-wider">
                Optimal
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-center text-xs pt-2 border-t border-[rgba(30,30,60,0.05)]">
            <div className="p-2 rounded-2xl bg-[#F0F1F7]/70">
              <div className="font-bold text-[#171725]">{healthData?.untagged_count || 0}</div>
              <div className="text-[10px] text-[#77788A]">Untagged</div>
            </div>
            <div className="p-2 rounded-2xl bg-[#F0F1F7]/70">
              <div className="font-bold text-[#171725]">{healthData?.orphaned_count || 0}</div>
              <div className="text-[10px] text-[#77788A]">Orphaned</div>
            </div>
          </div>
        </Card>
      </section>

      {/* SECTION 4: Memory Architecture Breakdown & Quick Action Launchpad */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Memory Format Distribution */}
        <Card className="lg:col-span-2 p-6 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-[#171725]">Format Distribution</h3>
              <p className="text-xs text-[#77788A]">Memory types categorized in your vault</p>
            </div>
          </div>

          {/* Segmented Distribution Bar */}
          <div className="h-4 rounded-full overflow-hidden flex bg-[#E5E7F2] gap-0.5 p-0.5 mb-5">
            {stats?.types && stats.types.length > 0 ? (
              stats.types.map((t: TypeBreakdownItem) => {
                const colors: Record<string, string> = {
                  note: 'bg-[#8B5CF6]',
                  document: 'bg-[#38BDF8]',
                  code: 'bg-[#7045DB]',
                  snippet: 'bg-[#A78BFA]',
                  conversation: 'bg-[#7DD3FC]',
                }
                const pct = (t.count / (stats.total_memories || 1)) * 100
                return (
                  <div
                    key={t.memory_type}
                    style={{ width: `${Math.max(pct, 4)}%` }}
                    className={`${colors[t.memory_type] || 'bg-slate-400'} h-full rounded-full transition-all`}
                    title={`${t.memory_type}: ${t.count}`}
                  />
                )
              })
            ) : (
              <div className="w-full h-full bg-[#E5E7F2] rounded-full" />
            )}
          </div>

          {/* Type Badges */}
          <div className="flex flex-wrap gap-2.5">
            {stats?.types?.map((t: TypeBreakdownItem) => (
              <div
                key={t.memory_type}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F0F1F7] text-xs"
              >
                <span className="font-semibold text-[#171725] capitalize">
                  {t.memory_type}
                </span>
                <span className="text-[11px] font-bold px-1.5 py-0.5 rounded-full bg-white text-[#8B5CF6] shadow-sm">
                  {t.count}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Quick Launchpad */}
        <Card className="p-6 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm">
          <h3 className="text-sm font-bold text-[#171725] mb-4">Quick Launchpad</h3>
          <div className="grid grid-cols-2 gap-2.5">
            <Link href="/memories/new">
              <Button
                variant="secondary"
                className="w-full h-16 rounded-2xl flex-col gap-1 text-xs font-semibold bg-white border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover hover:border-[#8B5CF6]/30 transition-all"
              >
                <span className="text-lg">✍️</span>
                <span>Add Note</span>
              </Button>
            </Link>
            <Link href="/ask">
              <Button
                variant="secondary"
                className="w-full h-16 rounded-2xl flex-col gap-1 text-xs font-semibold bg-white border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover hover:border-[#8B5CF6]/30 transition-all"
              >
                <span className="text-lg">💬</span>
                <span>Ask AI</span>
              </Button>
            </Link>
            <Link href="/graph">
              <Button
                variant="secondary"
                className="w-full h-16 rounded-2xl flex-col gap-1 text-xs font-semibold bg-white border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover hover:border-[#8B5CF6]/30 transition-all"
              >
                <span className="text-lg">🕸️</span>
                <span>Graph</span>
              </Button>
            </Link>
            <Link href="/search">
              <Button
                variant="secondary"
                className="w-full h-16 rounded-2xl flex-col gap-1 text-xs font-semibold bg-white border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover hover:border-[#8B5CF6]/30 transition-all"
              >
                <span className="text-lg">🔍</span>
                <span>Search</span>
              </Button>
            </Link>
          </div>
        </Card>
      </section>

      {/* SECTION 5: Recent Memories Live Stream */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-[#171725]">Recent Memory Entries</h3>
            <p className="text-xs text-[#77788A]">Captured thoughts and interconnected documents</p>
          </div>
          <Link href="/memories" className="text-xs font-semibold text-[#8B5CF6] hover:underline">
            View All Vault →
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {loadingMemories ? (
            <div className="col-span-2 p-8 text-center text-xs text-[#A1A1B3]">
              Loading memory items...
            </div>
          ) : !memoriesData || memoriesData.items.length === 0 ? (
            <Card className="col-span-2 p-8 text-center rounded-3xl glass-pearl">
              <div className="text-3xl mb-2">🧠</div>
              <h4 className="text-sm font-bold text-[#171725]">No Memories Yet</h4>
              <p className="text-xs text-[#77788A] mt-1 mb-4">
                Start capturing your thoughts, technical notes, or documents.
              </p>
              <Link href="/memories/new">
                <Button size="sm" className="rounded-full bg-gradient-companion text-white text-xs">
                  + Create First Memory
                </Button>
              </Link>
            </Card>
          ) : (
            memoriesData.items.map((mem: Memory) => (
              <Link key={mem.id} href={`/memories/${mem.id}`}>
                <motion.div
                  whileHover={{ y: -3, transition: { duration: 0.15 } }}
                  className="p-5 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover transition-all duration-200 h-full flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6]">
                        {mem.memory_type}
                      </span>
                      <span className="text-[11px] text-[#A1A1B3]">
                        {new Date(mem.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-[#171725] line-clamp-1">
                      {mem.title || 'Untitled Memory'}
                    </h4>
                    <p className="text-xs text-[#77788A] line-clamp-2 mt-1 leading-relaxed">
                      {mem.summary || mem.content}
                    </p>
                  </div>

                  {mem.tags && mem.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-[rgba(30,30,60,0.04)]">
                      {mem.tags.slice(0, 3).map((t) => (
                        <span
                          key={t}
                          className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-[#F0F1F7] text-[#77788A]"
                        >
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}
                </motion.div>
              </Link>
            ))
          )}
        </div>
      </section>
    </div>
  )
}
