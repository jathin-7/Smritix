'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { memoriesApi, tagsApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Memory } from '@/types'

const MEMORY_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'note', label: 'Note' },
  { value: 'document', label: 'Document' },
  { value: 'snippet', label: 'Snippet' },
  { value: 'code', label: 'Code' },
  { value: 'conversation', label: 'Conversation' },
  { value: 'web_clip', label: 'Web Clip' },
]

export default function MemoriesPage() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState('')
  const [selectedTag, setSelectedTag] = useState('')
  const [showArchived, setShowArchived] = useState(false)

  // Fetch memories
  const { data, isLoading, error } = useQuery({
    queryKey: ['memories', { query: searchQuery, tag: selectedTag, memory_type: selectedType, is_archived: showArchived }],
    queryFn: () => memoriesApi.list({
      query: searchQuery || undefined,
      tag: selectedTag || undefined,
      memory_type: selectedType || undefined,
      is_archived: showArchived,
      limit: 50,
      offset: 0
    }),
  })

  // Fetch tags for filtering
  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list(),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => memoriesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] })
      queryClient.invalidateQueries({ queryKey: ['tags'] })
    },
  })

  // Archive/restore mutation
  const toggleArchiveMutation = useMutation({
    mutationFn: ({ id, isArchived }: { id: string; isArchived: boolean }) =>
      isArchived ? memoriesApi.restore(id) : memoriesApi.archive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] })
    },
  })

  const memories: Memory[] = data?.items || []

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#8B5CF6] animate-pulse" />
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8B5CF6]">
              Knowledge Archive
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#171725]">
            Memory Vault
          </h1>
          <p className="text-xs sm:text-sm text-[#77788A] mt-0.5">
            Explore, filter, and organize your stored knowledge and thoughts
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowArchived(!showArchived)}
            className={`rounded-full text-xs h-9 px-4 border border-[rgba(30,30,60,0.06)] transition-all ${
              showArchived
                ? 'bg-gradient-companion text-white shadow-pearl-sm'
                : 'bg-white text-[#171725] shadow-pearl-sm hover:shadow-pearl-hover'
            }`}
          >
            {showArchived ? 'Viewing Archived' : 'Show Archived'}
          </Button>
          <Link href="/memories/new">
            <Button
              size="sm"
              className="rounded-full text-xs h-9 px-5 bg-gradient-companion text-white font-semibold shadow-pearl-sm hover:shadow-pearl-hover hover:opacity-95 transition-all"
            >
              + New Memory
            </Button>
          </Link>
        </div>
      </div>

      {/* Floating Translucent Filter Bar */}
      <div className="p-4 rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-sm flex flex-col md:flex-row gap-3 items-stretch md:items-center">
        <div className="relative flex-1">
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm text-[#8B5CF6]">🔍</span>
          <input
            placeholder="Search title, content, or summary..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-10 pl-9 pr-4 rounded-2xl bg-[#F0F1F7]/70 border border-transparent text-xs sm:text-sm text-[#171725] placeholder:text-[#A1A1B3] focus:bg-white focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-[#8B5CF6]/15 transition-all"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Type filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="h-10 rounded-2xl border border-[rgba(30,30,60,0.08)] bg-white px-3.5 text-xs font-medium text-[#171725] shadow-sm focus:outline-none focus:border-[#8B5CF6]"
          >
            {MEMORY_TYPES.map(t => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>

          {/* Tag filter */}
          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="h-10 rounded-2xl border border-[rgba(30,30,60,0.08)] bg-white px-3.5 text-xs font-medium text-[#171725] shadow-sm focus:outline-none focus:border-[#8B5CF6]"
          >
            <option value="">All Tags</option>
            {tags.map(t => (
              <option key={t.id} value={t.name}>
                #{t.name}
              </option>
            ))}
          </select>

          {(searchQuery || selectedType || selectedTag) && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSearchQuery('')
                setSelectedType('')
                setSelectedTag('')
              }}
              className="text-xs h-10 rounded-2xl text-[#77788A] bg-white border border-[rgba(30,30,60,0.08)] hover:bg-[#F0F1F7]"
            >
              Reset
            </Button>
          )}
        </div>
      </div>

      {/* Popular Tags Quick Strip */}
      {tags.length > 0 && !selectedTag && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <span className="text-[#77788A] font-semibold whitespace-nowrap text-[11px] uppercase tracking-wider">
            Filter Tags:
          </span>
          {tags.slice(0, 10).map((tag) => (
            <button
              key={tag.id}
              onClick={() => setSelectedTag(tag.name)}
              className="px-3 py-1 rounded-full bg-white border border-[rgba(30,30,60,0.06)] text-[#77788A] hover:text-[#8B5CF6] hover:border-[#8B5CF6]/30 shadow-pearl-sm transition-all whitespace-nowrap text-xs font-medium"
            >
              #{tag.name}
            </button>
          ))}
        </div>
      )}

      {/* Memory Cards Grid */}
      {isLoading ? (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="animate-pulse h-48 rounded-3xl bg-[#E5E7F2]/60" />
          ))}
        </div>
      ) : error ? (
        <div className="p-8 text-center glass-pearl rounded-3xl border border-red-200 text-red-600 space-y-2">
          <p className="font-semibold text-sm">Failed to load memories</p>
          <p className="text-xs opacity-80">{(error as Error).message}</p>
        </div>
      ) : memories.length === 0 ? (
        <div className="text-center py-16 rounded-3xl glass-pearl border border-dashed border-[rgba(30,30,60,0.12)] p-8 space-y-3">
          <div className="text-4xl">🧠</div>
          <h3 className="text-base font-bold text-[#171725]">No memories found</h3>
          <p className="text-[#77788A] max-w-md mx-auto text-xs">
            {searchQuery || selectedType || selectedTag
              ? 'No memories match your active filters. Try clearing your search parameters.'
              : 'Your vault is waiting for its first thought. Capture your notes, documents, or links!'}
          </p>
          <div className="pt-2">
            <Link href="/memories/new">
              <Button size="sm" className="rounded-full bg-gradient-companion text-white text-xs px-5">
                Capture First Memory
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {memories.map((memory) => (
            <motion.div
              key={memory.id}
              whileHover={{ y: -4, transition: { duration: 0.15 } }}
              className="p-6 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover transition-all duration-200 flex flex-col justify-between"
            >
              <Link href={`/memories/${memory.id}`} className="block flex-1">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6]">
                    {memory.memory_type}
                  </span>
                  <span className="text-[11px] text-[#A1A1B3]">
                    {formatDate(memory.created_at)}
                  </span>
                </div>

                <h3 className="text-base font-bold text-[#171725] line-clamp-1 hover:text-[#8B5CF6] transition-colors">
                  {memory.title || 'Untitled Memory'}
                </h3>

                <p className="text-xs text-[#77788A] line-clamp-3 mt-1.5 leading-relaxed">
                  {memory.summary || memory.content}
                </p>
              </Link>

              <div className="pt-4 mt-4 border-t border-[rgba(30,30,60,0.05)] flex items-center justify-between">
                <div className="flex flex-wrap gap-1.5 flex-1 mr-2">
                  {memory.tags.slice(0, 3).map((tag) => (
                    <button
                      key={tag}
                      onClick={(e) => {
                        e.preventDefault()
                        setSelectedTag(tag)
                      }}
                      className="text-[10px] font-medium bg-[#F0F1F7] hover:bg-[#8B5CF6]/15 hover:text-[#8B5CF6] text-[#77788A] px-2.5 py-0.5 rounded-full transition-colors"
                    >
                      #{tag}
                    </button>
                  ))}
                  {memory.tags.length > 3 && (
                    <span className="text-[10px] text-[#A1A1B3] self-center">
                      +{memory.tags.length - 3}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    title={memory.is_archived ? 'Restore memory' : 'Archive memory'}
                    onClick={(e) => {
                      e.preventDefault()
                      toggleArchiveMutation.mutate({ id: memory.id, isArchived: memory.is_archived })
                    }}
                    className="p-1.5 rounded-full hover:bg-black/5 text-[#77788A] hover:text-[#171725] transition-colors text-xs"
                  >
                    {memory.is_archived ? '📤' : '📦'}
                  </button>
                  <button
                    title="Delete memory"
                    onClick={(e) => {
                      e.preventDefault()
                      if (confirm('Are you sure you want to delete this memory?')) {
                        deleteMutation.mutate(memory.id)
                      }
                    }}
                    className="p-1.5 rounded-full hover:bg-red-50 text-[#77788A] hover:text-red-500 transition-colors text-xs"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
