'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { settingsApi } from '@/lib/api/client'
import { useAuthStore } from '@/stores/auth-store'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AISettingsResponse, PrivacySettingsResponse } from '@/types'

export default function SettingsPage() {
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState<'ai' | 'privacy' | 'storage' | 'system'>('ai')

  const {
    data: aiSettings,
    isLoading: loadingAI,
    isRefetching: refetchingAI,
    refetch: refetchAI,
  } = useQuery<AISettingsResponse>({
    queryKey: ['settings', 'ai'],
    queryFn: () => settingsApi.getAISettings(),
  })

  const {
    data: privacySettings,
    isLoading: loadingPrivacy,
  } = useQuery<PrivacySettingsResponse>({
    queryKey: ['settings', 'privacy'],
    queryFn: () => settingsApi.getPrivacySettings(),
  })

  return (
    <div className="space-y-8 pb-16 max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[rgba(30,30,60,0.06)] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#8B5CF6] animate-pulse" />
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8B5CF6]">
              Neural Core & Privacy Boundaries
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#171725]">
            Settings & System Control
          </h1>
          <p className="text-xs sm:text-sm text-[#77788A] mt-0.5">
            Configure your local AI inference, embedding vectors, and sovereign privacy rules
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => refetchAI()}
            disabled={refetchingAI}
            className="rounded-full text-xs h-9 px-4 gap-2 bg-white border border-[rgba(30,30,60,0.08)] shadow-pearl-sm hover:shadow-pearl-hover transition-all"
          >
            <span className={refetchingAI ? 'animate-spin' : ''}>⚙️</span>
            <span>{refetchingAI ? 'Probing Ollama...' : 'Diagnostics Check'}</span>
          </Button>
        </div>
      </div>

      {/* Modern Navigation Tabs */}
      <div className="flex items-center gap-1.5 p-1.5 glass-pearl-elevated rounded-full border border-[rgba(30,30,60,0.08)] w-fit overflow-x-auto max-w-full shadow-pearl-sm">
        <button
          onClick={() => setActiveTab('ai')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold transition-all ${
            activeTab === 'ai'
              ? 'bg-gradient-companion text-white shadow-sm'
              : 'text-[#77788A] hover:text-[#171725] hover:bg-white/70'
          }`}
        >
          <span>✦</span>
          <span>AI & Neural Engine</span>
        </button>

        <button
          onClick={() => setActiveTab('privacy')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold transition-all ${
            activeTab === 'privacy'
              ? 'bg-gradient-companion text-white shadow-sm'
              : 'text-[#77788A] hover:text-[#171725] hover:bg-white/70'
          }`}
        >
          <span>🛡️</span>
          <span>Privacy & Sovereignty</span>
        </button>

        <button
          onClick={() => setActiveTab('storage')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold transition-all ${
            activeTab === 'storage'
              ? 'bg-gradient-companion text-white shadow-sm'
              : 'text-[#77788A] hover:text-[#171725] hover:bg-white/70'
          }`}
        >
          <span>🕸️</span>
          <span>Vectors & Graph</span>
        </button>

        <button
          onClick={() => setActiveTab('system')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold transition-all ${
            activeTab === 'system'
              ? 'bg-gradient-companion text-white shadow-sm'
              : 'text-[#77788A] hover:text-[#171725] hover:bg-white/70'
          }`}
        >
          <span>👤</span>
          <span>Identity & Diagnostics</span>
        </button>
      </div>

      {/* Tab 1: AI & Neural Engine */}
      {activeTab === 'ai' && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="space-y-6"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Ollama Status Card */}
            <div className="p-6 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-[#8B5CF6]/10 text-[#8B5CF6] flex items-center justify-center text-lg">
                    🦙
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#171725]">Ollama LLM Daemon</h3>
                    <p className="text-[11px] text-[#77788A]">Local high-speed inference runtime</p>
                  </div>
                </div>

                {loadingAI ? (
                  <span className="text-xs text-[#A1A1B3]">Checking...</span>
                ) : aiSettings?.ollama_available ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Online & Active
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                    Fallback Standby
                  </span>
                )}
              </div>

              <div className="space-y-2.5 pt-2 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
                  <span className="text-[#77788A]">Endpoint URI</span>
                  <span className="font-mono text-[#171725] font-medium">{aiSettings?.ollama_url || 'http://localhost:11434'}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
                  <span className="text-[#77788A]">Active LLM Provider</span>
                  <span className="font-mono text-[#171725] font-medium">{aiSettings?.llm_provider || 'OllamaProvider'}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
                  <span className="text-[#77788A]">Model Tag</span>
                  <span className="font-mono text-[#8B5CF6] font-bold">{aiSettings?.default_model || 'mistral:latest'}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-[#77788A]">Cloud Egress</span>
                  <span className="text-emerald-600 font-bold">100% On-Device</span>
                </div>
              </div>
            </div>

            {/* Embedding Vector Engine */}
            <div className="p-6 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-[#38BDF8]/10 text-[#38BDF8] flex items-center justify-center text-lg">
                    ✦
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#171725]">Dense Vector Embedder</h3>
                    <p className="text-[11px] text-[#77788A]">Semantic representation pipeline</p>
                  </div>
                </div>

                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Active
                </span>
              </div>

              <div className="space-y-2.5 pt-2 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
                  <span className="text-[#77788A]">Embedding Model</span>
                  <span className="font-mono text-[#171725] font-medium">all-MiniLM-L6-v2</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
                  <span className="text-[#77788A]">Vector Dimensions</span>
                  <span className="font-mono text-[#8B5CF6] font-bold">{aiSettings?.embedding_dimensions || 384} floats</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
                  <span className="text-[#77788A]">Metric Space</span>
                  <span className="font-mono text-[#171725]">Cosine Similarity (HNSW)</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-[#77788A]">Chunking Token Size</span>
                  <span className="text-[#77788A]">500 tokens / 50 stride</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Tab 2: Privacy & Sovereignty */}
      {activeTab === 'privacy' && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          <div className="p-5 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm flex items-start gap-4">
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg font-bold shrink-0">
              ✓
            </div>
            <div>
              <h4 className="text-sm font-bold text-[#171725]">Local-First Architecture</h4>
              <p className="text-xs text-[#77788A] mt-1 leading-relaxed">
                Your memories, documents, and embeddings never leave your local environment.
              </p>
            </div>
          </div>

          <div className="p-5 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm flex items-start gap-4">
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg font-bold shrink-0">
              ✓
            </div>
            <div>
              <h4 className="text-sm font-bold text-[#171725]">Zero Telemetry & Tracking</h4>
              <p className="text-xs text-[#77788A] mt-1 leading-relaxed">
                No tracking cookies, analytics beacons, or remote logging. Completely sovereign.
              </p>
            </div>
          </div>

          <div className="p-5 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm flex items-start gap-4">
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg font-bold shrink-0">
              ✓
            </div>
            <div>
              <h4 className="text-sm font-bold text-[#171725]">Cryptographic Authentication</h4>
              <p className="text-xs text-[#77788A] mt-1 leading-relaxed">
                User passwords hashed with Argon2id; access tokens signed with JWT HS256.
              </p>
            </div>
          </div>

          <div className="p-5 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm flex items-start gap-4">
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg font-bold shrink-0">
              ✓
            </div>
            <div>
              <h4 className="text-sm font-bold text-[#171725]">Zero Recurring Cost</h4>
              <p className="text-xs text-[#77788A] mt-1 leading-relaxed">
                No pay-per-token API bills. Everything runs on your own hardware resources.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Tab 3: Vectors & Graph */}
      {activeTab === 'storage' && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          <div className="p-6 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm space-y-3">
            <h3 className="text-sm font-bold text-[#171725]">Database & Storage</h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-[rgba(30,30,60,0.04)]">
                <span className="text-[#77788A]">Primary Engine</span>
                <span className="font-mono text-[#171725]">PostgreSQL 16 / SQLite async</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-[rgba(30,30,60,0.04)]">
                <span className="text-[#77788A]">Vector Indexing</span>
                <span className="font-mono text-[#8B5CF6] font-bold">pgvector (HNSW)</span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-[#77788A]">Search Engine</span>
                <span className="font-mono text-[#171725]">Reciprocal Rank Fusion (k=60)</span>
              </div>
            </div>
          </div>

          <div className="p-6 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm space-y-3">
            <h3 className="text-sm font-bold text-[#171725]">Knowledge Graph Linkage</h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-[rgba(30,30,60,0.04)]">
                <span className="text-[#77788A]">Auto-Discovery</span>
                <span className="font-mono text-[#8B5CF6] font-bold">cosine &gt; 0.65</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-[rgba(30,30,60,0.04)]">
                <span className="text-[#77788A]">Physics Simulation</span>
                <span className="font-mono text-[#171725]">2D Force-Directed</span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-[#77788A]">Topic Clustering</span>
                <span className="font-mono text-[#171725]">Tag co-occurrence</span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Tab 4: Identity & Diagnostics */}
      {activeTab === 'system' && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="p-6 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm space-y-4 max-w-xl"
        >
          <h3 className="text-sm font-bold text-[#171725]">Current Session Identity</h3>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
              <span className="text-[#77788A]">User ID</span>
              <span className="font-mono text-[#171725]">{user?.id || 'anonymous-local'}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
              <span className="text-[#77788A]">Email</span>
              <span className="text-[#171725] font-medium">{user?.email || 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-[rgba(30,30,60,0.04)]">
              <span className="text-[#77788A]">Display Name</span>
              <span className="text-[#171725] font-semibold">{user?.display_name || 'Explorer'}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-[#77788A]">Privilege</span>
              <span className="text-[#8B5CF6] font-bold uppercase">Local Sovereign Owner</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
