'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { memoriesApi, tagsApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'

const MEMORY_TYPES = [
  { value: 'note', label: 'Note / Thought' },
  { value: 'document', label: 'Document' },
  { value: 'snippet', label: 'Code Snippet' },
  { value: 'code', label: 'Code' },
  { value: 'conversation', label: 'Conversation' },
  { value: 'web_clip', label: 'Web Clip' },
  { value: 'annotation', label: 'Annotation' },
]

export default function MemoryDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const memoryId = params.id as string

  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editType, setEditType] = useState('note')
  const [editTags, setEditTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Fetch memory detail
  const { data: memory, isLoading, error } = useQuery({
    queryKey: ['memory', memoryId],
    queryFn: () => memoriesApi.get(memoryId),
    enabled: !!memoryId,
  })

  // Fetch tags for suggestions
  const { data: existingTags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list(),
  })

  // Fetch knowledge graph connections
  const { data: connectionsData } = useQuery({
    queryKey: ['memoryConnections', memoryId],
    queryFn: () => memoriesApi.getConnections(memoryId),
    enabled: !!memoryId,
  })

  // Fetch similar memories via vector similarity
  const { data: similarMemories = [] } = useQuery({
    queryKey: ['memorySimilar', memoryId],
    queryFn: () => memoriesApi.getSimilar(memoryId, 4),
    enabled: !!memoryId,
  })

  // Start editing
  const startEditing = () => {
    if (memory) {
      setEditTitle(memory.title || '')
      setEditContent(memory.content)
      setEditType(memory.memory_type)
      setEditTags([...memory.tags])
      setTagInput('')
      setErrorMessage(null)
      setIsEditing(true)
    }
  }

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: { title?: string; content?: string; memory_type?: string; tags?: string[] }) =>
      memoriesApi.update(memoryId, data),
    onSuccess: (updated) => {
      queryClient.setQueryData(['memory', memoryId], updated)
      queryClient.invalidateQueries({ queryKey: ['memories'] })
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      setIsEditing(false)
    },
    onError: (err: any) => {
      setErrorMessage(err.message || 'Failed to update memory')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => memoriesApi.delete(memoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] })
      router.push('/memories')
    },
  })

  // Archive mutation
  const toggleArchiveMutation = useMutation({
    mutationFn: (isArchived: boolean) =>
      isArchived ? memoriesApi.restore(memoryId) : memoriesApi.archive(memoryId),
    onSuccess: (updated) => {
      queryClient.setQueryData(['memory', memoryId], updated)
      queryClient.invalidateQueries({ queryKey: ['memories'] })
    },
  })

  const handleAddTag = (tagName: string) => {
    const cleaned = tagName.trim().replace(/^#/, '').toLowerCase()
    if (cleaned && !editTags.includes(cleaned)) {
      setEditTags([...editTags, cleaned])
    }
    setTagInput('')
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setEditTags(editTags.filter((t) => t !== tagToRemove))
  }

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!editContent.trim()) {
      setErrorMessage('Content is required')
      return
    }

    let finalTags = [...editTags]
    if (tagInput.trim()) {
      const pending = tagInput.trim().replace(/^#/, '').toLowerCase()
      if (!finalTags.includes(pending)) {
        finalTags.push(pending)
      }
    }

    updateMutation.mutate({
      title: editTitle.trim() || undefined,
      content: editContent.trim(),
      memory_type: editType,
      tags: finalTags,
    })
  }

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-pulse">
        <div className="h-9 w-40 bg-white/70 rounded-full border border-black/[0.04]" />
        <div className="h-64 bg-white/70 rounded-3xl border border-black/[0.04]" />
        <div className="h-96 bg-white/70 rounded-3xl border border-black/[0.04]" />
      </div>
    )
  }

  if (error || !memory) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-2xl mx-auto text-center py-20 px-6 glass-pearl-elevated rounded-3xl border border-white/80 shadow-pearl-soft space-y-4"
      >
        <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-50 border border-amber-200/60 flex items-center justify-center text-amber-600 text-2xl">
          ⚠️
        </div>
        <h2 className="text-2xl font-semibold tracking-tight text-[#171725]">Memory Not Found</h2>
        <p className="text-sm text-[#77788A] max-w-md mx-auto">
          The requested memory does not exist or has been permanently removed from your sovereign store.
        </p>
        <div className="pt-2">
          <Link href="/memories">
            <Button className="rounded-xl px-5 bg-gradient-companion text-white shadow-sm hover:opacity-95">
              ← Return to Memories
            </Button>
          </Link>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="max-w-4xl mx-auto space-y-6 pb-12"
    >
      {/* Top Action & Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link href="/memories">
          <button className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium text-[#77788A] hover:text-[#171725] bg-white/80 hover:bg-white border border-black/[0.06] shadow-xs transition-all">
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m12 19-7-7 7-7" />
              <path d="M19 12H5" />
            </svg>
            Back to Memories
          </button>
        </Link>

        {!isEditing && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => toggleArchiveMutation.mutate(memory.is_archived)}
              disabled={toggleArchiveMutation.isPending}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium text-[#171725] bg-white/80 hover:bg-white border border-black/[0.06] shadow-xs transition-all"
            >
              {memory.is_archived ? (
                <>
                  <span className="text-purple-600">↺</span>
                  Restore
                </>
              ) : (
                <>
                  <span className="text-[#77788A]">📦</span>
                  Archive
                </>
              )}
            </button>
            <button
              onClick={startEditing}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium text-white bg-gradient-companion shadow-xs hover:opacity-95 transition-all"
            >
              <span>✏️</span>
              Edit
            </button>
            <button
              onClick={() => {
                if (confirm('Are you sure you want to permanently delete this memory? This action cannot be undone.')) {
                  deleteMutation.mutate()
                }
              }}
              disabled={deleteMutation.isPending}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium text-rose-600 hover:text-rose-700 bg-rose-50/70 hover:bg-rose-100/70 border border-rose-200/60 shadow-xs transition-all"
            >
              <span>🗑️</span>
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Editing Form */}
      <AnimatePresence mode="wait">
        {isEditing ? (
          <motion.div
            key="edit-form"
            initial={{ opacity: 0, scale: 0.99 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.99 }}
            className="glass-pearl-elevated rounded-3xl p-6 sm:p-8 border border-white/80 shadow-pearl-soft"
          >
            <form onSubmit={handleSaveEdit} className="space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-black/[0.06]">
                <h2 className="text-xl font-semibold text-[#171725] tracking-tight">Edit Memory</h2>
                <span className="text-xs text-[#77788A]">Editing Mode</span>
              </div>

              {errorMessage && (
                <div className="p-3.5 text-xs text-rose-700 bg-rose-50 border border-rose-200/80 rounded-2xl flex items-center gap-2">
                  <span>⚠️</span>
                  {errorMessage}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[#77788A]">Title</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder="Memory Title..."
                  className="w-full h-11 px-4 text-base font-medium rounded-2xl bg-white border border-black/[0.08] shadow-xs text-[#171725] placeholder:text-[#A1A1B3] focus:outline-none focus:ring-2 focus:ring-purple-400/40"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[#77788A]">Memory Type</label>
                <select
                  value={editType}
                  onChange={(e) => setEditType(e.target.value)}
                  className="w-full h-10 px-3.5 rounded-2xl bg-white border border-black/[0.08] text-xs font-medium text-[#171725] focus:outline-none focus:ring-2 focus:ring-purple-400/40"
                >
                  {MEMORY_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[#77788A]">Content *</label>
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  required
                  rows={12}
                  className="w-full p-4 rounded-2xl bg-white border border-black/[0.08] text-sm text-[#171725] leading-relaxed focus:outline-none focus:ring-2 focus:ring-purple-400/40 font-mono"
                />
              </div>

              {/* Tags Editor */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-[#77788A]">Tags</label>
                <div className="flex flex-wrap items-center gap-1.5 mb-2">
                  {editTags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 bg-purple-50 text-purple-700 border border-purple-200/60 text-xs px-2.5 py-1 rounded-xl font-medium"
                    >
                      #{tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="hover:text-rose-600 text-purple-400 ml-0.5"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Add tag and press Enter..."
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ',') {
                        e.preventDefault()
                        handleAddTag(tagInput)
                      }
                    }}
                    className="flex-1 h-10 px-3.5 rounded-2xl bg-white border border-black/[0.08] text-xs text-[#171725] focus:outline-none focus:ring-2 focus:ring-purple-400/40"
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => handleAddTag(tagInput)}
                    className="rounded-2xl px-4 text-xs font-medium"
                  >
                    Add
                  </Button>
                </div>

                {existingTags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-2 text-xs text-[#77788A] items-center">
                    <span className="text-[11px]">Suggestions:</span>
                    {existingTags
                      .filter((t) => !editTags.includes(t.name.toLowerCase()))
                      .slice(0, 8)
                      .map((t) => (
                        <button
                          type="button"
                          key={t.id}
                          onClick={() => handleAddTag(t.name)}
                          className="px-2 py-0.5 rounded-lg bg-black/[0.03] hover:bg-purple-50 hover:text-purple-700 border border-black/[0.05] text-[11px] font-medium transition-colors"
                        >
                          +{t.name}
                        </button>
                      ))}
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-black/[0.06]">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-[#77788A] hover:text-[#171725] hover:bg-black/[0.04] transition-all"
                >
                  Cancel
                </button>
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="rounded-xl px-5 text-xs font-medium bg-gradient-companion text-white shadow-sm hover:opacity-95"
                >
                  {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </form>
          </motion.div>
        ) : (
          /* View Mode */
          <motion.div
            key="view-content"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Header Card */}
            <div className="glass-pearl-elevated rounded-3xl p-6 sm:p-8 border border-white/80 shadow-pearl-soft space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] uppercase tracking-wider font-semibold text-purple-700 bg-purple-50 border border-purple-200/60 px-3 py-1 rounded-full">
                  {memory.memory_type}
                </span>
                {memory.is_archived && (
                  <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-3 py-1 rounded-full border border-amber-200/60 flex items-center gap-1">
                    📦 Archived
                  </span>
                )}
                <span className="text-[11px] font-medium text-[#77788A] bg-black/[0.03] px-3 py-1 rounded-full border border-black/[0.05]">
                  Source: {memory.source_type}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-[#171725] leading-snug">
                {memory.title || 'Untitled Memory'}
              </h1>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[#77788A] pt-1">
                <span className="inline-flex items-center gap-1.5">
                  📅 Created {formatDate(memory.created_at)}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  ⏱️ Updated {formatDate(memory.updated_at)}
                </span>
              </div>

              {memory.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-2">
                  {memory.tags.map((tag) => (
                    <Link
                      key={tag}
                      href={`/memories?tag=${encodeURIComponent(tag)}`}
                      className="inline-flex items-center gap-1 text-xs font-medium bg-purple-50/70 hover:bg-purple-100/70 text-purple-700 border border-purple-200/50 px-3 py-1 rounded-xl transition-all"
                    >
                      #{tag}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Content Card */}
            <div className="glass-pearl-elevated rounded-3xl p-6 sm:p-8 border border-white/80 shadow-pearl-soft space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-black/[0.05]">
                <div className="text-xs uppercase font-semibold tracking-wider text-[#77788A]">
                  Memory Content
                </div>
                <div className="text-xs text-[#A1A1B3]">
                  {memory.content.length} characters
                </div>
              </div>
              <div className="prose max-w-none whitespace-pre-wrap font-sans text-sm sm:text-base text-[#171725] leading-relaxed">
                {memory.content}
              </div>
            </div>

            {/* Indexed Chunks Breakdown */}
            {memory.chunks && memory.chunks.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">📚</span>
                    <h3 className="text-xs font-semibold tracking-wider uppercase text-[#77788A]">
                      Vector Indexed Chunks ({memory.chunks.length})
                    </h3>
                  </div>
                  <span className="text-xs text-[#A1A1B3]">
                    Ready for AI retrieval
                  </span>
                </div>
                <div className="space-y-2.5">
                  {memory.chunks.map((chunk) => (
                    <div
                      key={chunk.id}
                      className="p-4 bg-white/75 rounded-2xl border border-black/[0.06] shadow-xs text-xs text-[#171725] font-mono leading-relaxed"
                    >
                      <div className="flex items-center justify-between text-[11px] text-purple-700 font-semibold mb-2">
                        <span>Chunk #{chunk.chunk_index + 1}</span>
                        {chunk.token_count && (
                          <span className="text-[#77788A] font-normal">{chunk.token_count} tokens</span>
                        )}
                      </div>
                      <div className="text-[#171725]/90 whitespace-pre-wrap">{chunk.content}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sources Section */}
            {memory.sources && memory.sources.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2 px-1">
                  <span className="text-sm">🔗</span>
                  <h3 className="text-xs font-semibold tracking-wider uppercase text-[#77788A]">
                    Source Attribution ({memory.sources.length})
                  </h3>
                </div>
                <div className="space-y-2">
                  {memory.sources.map((src) => (
                    <div
                      key={src.id}
                      className="p-3.5 bg-white/75 rounded-2xl border border-black/[0.06] shadow-xs text-xs flex items-center justify-between"
                    >
                      <div>
                        <span className="font-medium text-[#171725]">
                          {src.source_title || src.source_uri}
                        </span>
                        <span className="text-[#77788A] ml-2 text-[11px]">
                          ({src.source_type})
                        </span>
                      </div>
                      {src.source_uri && (
                        <a
                          href={src.source_uri}
                          target="_blank"
                          rel="noreferrer"
                          className="text-purple-600 hover:text-purple-700 font-medium inline-flex items-center gap-1 text-[11px]"
                        >
                          Visit link ↗
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Knowledge Graph Connections */}
            <div className="space-y-3">
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm">🕸️</span>
                  <h3 className="text-xs font-semibold tracking-wider uppercase text-[#77788A]">
                    Knowledge Graph Connections ({connectionsData?.total_connections || 0})
                  </h3>
                </div>
                <Link
                  href="/graph"
                  className="text-xs font-medium text-purple-600 hover:text-purple-700 inline-flex items-center gap-1"
                >
                  Explore in Graph →
                </Link>
              </div>

              {!connectionsData || connectionsData.edges.length === 0 ? (
                <div className="p-4 bg-white/60 rounded-2xl border border-black/[0.05] text-xs text-[#77788A] text-center">
                  No explicit graph connections yet. Connect memories directly in the Knowledge Graph or create additional memories to reveal emergent links.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {connectionsData.edges.map((edge) => {
                    const otherId = edge.source === memory.id ? edge.target : edge.source
                    const otherNode = connectionsData.nodes.find((n) => n.id === otherId)
                    const isOutgoing = edge.source === memory.id

                    return (
                      <Link
                        key={edge.id}
                        href={`/memories/${otherId}`}
                        className="p-3.5 bg-white/80 hover:bg-white rounded-2xl border border-black/[0.06] hover:border-purple-300/60 shadow-xs hover:shadow-pearl-soft transition-all text-xs flex flex-col justify-between group"
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-medium text-[#171725] group-hover:text-purple-700 transition-colors truncate max-w-[180px]">
                            {otherNode?.title || 'Connected Memory'}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 font-mono font-medium border border-purple-200/50">
                            {isOutgoing ? '→' : '←'} {edge.relation_type}
                          </span>
                        </div>
                        <p className="text-[#77788A] line-clamp-1 text-[11px] mb-2 font-sans">
                          {otherNode?.snippet}
                        </p>
                        <div className="text-[10px] text-[#A1A1B3] flex items-center justify-between">
                          <span>Confidence: {Math.round(edge.confidence * 100)}%</span>
                          <span className="capitalize">{edge.created_by}</span>
                        </div>
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Semantically Similar Memories */}
            {similarMemories.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2 px-1">
                  <span className="text-sm">✨</span>
                  <h3 className="text-xs font-semibold tracking-wider uppercase text-[#77788A]">
                    Semantically Similar Memories ({similarMemories.length})
                  </h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {similarMemories.map((sim) => (
                    <Link
                      key={sim.memory_id}
                      href={`/memories/${sim.memory_id}`}
                      className="p-3.5 bg-white/80 hover:bg-white rounded-2xl border border-black/[0.06] hover:border-cyan-300/60 shadow-xs hover:shadow-pearl-soft transition-all text-xs flex flex-col justify-between group"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-medium text-[#171725] group-hover:text-cyan-700 transition-colors truncate max-w-[180px]">
                          {sim.title || 'Untitled'}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-700 font-mono font-medium border border-cyan-200/60">
                          {Math.round(sim.score * 100)}% match
                        </span>
                      </div>
                      <p className="text-[#77788A] line-clamp-2 text-[11px] font-sans">
                        {sim.snippet}
                      </p>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
