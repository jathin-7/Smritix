'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { memoriesApi, tagsApi, ingestApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { IngestionJob } from '@/types'

const MEMORY_TYPES = [
  { value: 'note', label: 'Note / Thought' },
  { value: 'document', label: 'Document' },
  { value: 'snippet', label: 'Code Snippet' },
  { value: 'code', label: 'Code' },
  { value: 'conversation', label: 'Conversation' },
  { value: 'web_clip', label: 'Web Clip' },
  { value: 'annotation', label: 'Annotation' },
]

export default function NewMemoryPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [activeTab, setActiveTab] = useState<'write' | 'upload'>('write')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [memoryType, setMemoryType] = useState('note')
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Document Upload states
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [activeJob, setActiveJob] = useState<IngestionJob | null>(null)

  // Fetch existing tags
  const { data: existingTags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list(),
  })

  // Poll active ingestion job
  useEffect(() => {
    if (!activeJob || activeJob.status === 'completed' || activeJob.status === 'failed') {
      return
    }

    const interval = setInterval(async () => {
      try {
        const updated = await ingestApi.getJob(activeJob.id)
        setActiveJob(updated)
        if (updated.status === 'completed') {
          queryClient.invalidateQueries({ queryKey: ['memories'] })
          setTimeout(() => {
            router.push('/memories')
          }, 1000)
        }
      } catch (err) {
        console.error('Error polling job:', err)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [activeJob, queryClient, router])

  // Create memory mutation
  const createMutation = useMutation({
    mutationFn: (data: { title?: string; content: string; memory_type: string; tags: string[] }) =>
      memoriesApi.create(data),
    onSuccess: (newMemory) => {
      queryClient.invalidateQueries({ queryKey: ['memories'] })
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      router.push(`/memories/${newMemory.id}`)
    },
    onError: (err: any) => {
      setErrorMessage(err.message || 'Failed to capture memory')
    },
  })

  const handleAddTag = (tagName: string) => {
    const cleaned = tagName.trim().replace(/^#/, '').toLowerCase()
    if (cleaned && !tags.includes(cleaned)) {
      setTags([...tags, cleaned])
    }
    setTagInput('')
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove))
  }

  const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      handleAddTag(tagInput)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!content.trim()) {
      setErrorMessage('Content is required')
      return
    }

    let finalTags = [...tags]
    if (tagInput.trim()) {
      const pending = tagInput.trim().replace(/^#/, '').toLowerCase()
      if (!finalTags.includes(pending)) {
        finalTags.push(pending)
      }
    }

    createMutation.mutate({
      title: title.trim() || undefined,
      content: content.trim(),
      memory_type: memoryType,
      tags: finalTags,
    })
  }

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!selectedFile) {
      setErrorMessage('Please select a file to upload')
      return
    }

    setIsUploading(true)
    try {
      const job = await ingestApi.uploadDocument(selectedFile, tags)
      setActiveJob(job)
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to upload document')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#8B5CF6] animate-pulse" />
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8B5CF6]">
              Knowledge Capture
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#171725]">
            Create New Memory
          </h1>
          <p className="text-xs sm:text-sm text-[#77788A] mt-0.5">
            Record a note, code snippet, or technical document into your sovereign vault
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex p-1 bg-[#F0F1F7] rounded-full border border-[rgba(30,30,60,0.06)] text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('write')}
            className={`px-4 py-1.5 rounded-full font-bold transition-all ${
              activeTab === 'write'
                ? 'bg-gradient-companion text-white shadow-sm'
                : 'text-[#77788A] hover:text-[#171725]'
            }`}
          >
            ✍️ Write Note
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-1.5 rounded-full font-bold transition-all ${
              activeTab === 'upload'
                ? 'bg-gradient-companion text-white shadow-sm'
                : 'text-[#77788A] hover:text-[#171725]'
            }`}
          >
            📄 Upload Document
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200/60 text-xs text-red-600">
          {errorMessage}
        </div>
      )}

      {/* Main Form Container */}
      <div className="p-6 sm:p-8 rounded-[2rem] glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-md">
        {activeTab === 'write' ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="sm:col-span-2 space-y-1.5">
                <label className="text-xs font-bold text-[#171725]">Memory Title (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Quantum Computing Architectural Principles"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full h-11 px-4 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] text-xs sm:text-sm text-[#171725] placeholder:text-[#A1A1B3] shadow-sm focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-[#8B5CF6]/15 transition-all"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-[#171725]">Format Type</label>
                <select
                  value={memoryType}
                  onChange={(e) => setMemoryType(e.target.value)}
                  className="w-full h-11 px-3.5 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] text-xs text-[#171725] shadow-sm focus:outline-none focus:border-[#8B5CF6]"
                >
                  {MEMORY_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[#171725]">Memory Content (Markdown supported)</label>
              <textarea
                rows={10}
                placeholder="Write your notes, copy research excerpts, or paste code snippets..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                className="w-full p-4 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] text-xs sm:text-sm text-[#171725] placeholder:text-[#A1A1B3] shadow-sm focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-[#8B5CF6]/15 transition-all resize-y leading-relaxed"
              />
            </div>

            {/* Tags Input & Active Chips */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-[#171725]">Tags</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {tags.map((t) => (
                  <span
                    key={t}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#F0F1F7] text-[#171725] border border-[rgba(30,30,60,0.06)]"
                  >
                    #{t}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(t)}
                      className="text-[#A1A1B3] hover:text-red-500"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add tag and press Enter (e.g. quantum, physics)..."
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleTagKeyDown}
                  className="flex-1 h-10 px-4 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] text-xs text-[#171725] placeholder:text-[#A1A1B3] shadow-sm focus:outline-none focus:border-[#8B5CF6]"
                />
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => handleAddTag(tagInput)}
                  className="rounded-2xl text-xs px-4 bg-white border border-[rgba(30,30,60,0.08)]"
                >
                  Add Tag
                </Button>
              </div>

              {/* Tag Suggestions */}
              {existingTags.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap pt-1 text-[11px] text-[#77788A]">
                  <span className="font-semibold">Suggested:</span>
                  {existingTags.slice(0, 8).map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => handleAddTag(t.name)}
                      className="px-2 py-0.5 rounded-full bg-[#F0F1F7] hover:bg-[#8B5CF6]/15 hover:text-[#8B5CF6] transition-colors"
                    >
                      +{t.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-[rgba(30,30,60,0.06)]">
              <Button
                type="button"
                variant="secondary"
                onClick={() => router.back()}
                className="rounded-full text-xs h-10 px-5 bg-white border border-[rgba(30,30,60,0.08)]"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending}
                className="rounded-full text-xs h-10 px-7 font-bold bg-gradient-companion text-white shadow-pearl-sm hover:opacity-95"
              >
                {createMutation.isPending ? 'Chunking & Embedding...' : 'Save to Memory'}
              </Button>
            </div>
          </form>
        ) : (
          /* Document Upload Form */
          <form onSubmit={handleFileUpload} className="space-y-6">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[#8B5CF6]/30 hover:border-[#8B5CF6] rounded-3xl p-10 text-center cursor-pointer transition-colors bg-white/50 space-y-3"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.md,.markdown,.txt"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              <div className="text-4xl">📄</div>
              <div className="space-y-1">
                <p className="text-sm font-bold text-[#171725]">
                  {selectedFile ? selectedFile.name : 'Click to select or drag and drop document'}
                </p>
                <p className="text-xs text-[#77788A]">
                  Supported formats: PDF, Markdown (.md), Plain Text (.txt) — max 50 MB
                </p>
              </div>
            </div>

            {/* Ingestion Progress */}
            {activeJob && (
              <div className="p-4 rounded-2xl bg-white border border-[rgba(30,30,60,0.08)] space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#171725]">Status: {activeJob.status}</span>
                  <span className="text-[#77788A]">{activeJob.status === 'completed' ? '100%' : 'Processing...'}</span>
                </div>
                <div className="h-2 rounded-full bg-[#F0F1F7] overflow-hidden">
                  <div
                    className={`h-full bg-gradient-companion transition-all duration-500 ${
                      activeJob.status === 'completed' ? 'w-full' : 'w-2/3 animate-pulse'
                    }`}
                  />
                </div>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-[rgba(30,30,60,0.06)]">
              <Button
                type="submit"
                disabled={isUploading || !selectedFile}
                className="rounded-full text-xs h-10 px-7 font-bold bg-gradient-companion text-white shadow-pearl-sm hover:opacity-95"
              >
                {isUploading ? 'Uploading & Ingesting...' : 'Upload & Extract Knowledge'}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
