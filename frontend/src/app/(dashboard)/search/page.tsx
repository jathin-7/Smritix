'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchApi, tagsApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { SearchResultItem } from '@/types'

const MEMORY_TYPES = [
  { value: '', label: 'All Formats' },
  { value: 'note', label: 'Notes' },
  { value: 'document', label: 'Documents' },
  { value: 'snippet', label: 'Snippets' },
  { value: 'code', label: 'Code' },
  { value: 'conversation', label: 'Conversations' },
]

export default function SearchPage() {
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState<'hybrid' | 'semantic'>('hybrid')
  const [selectedType, setSelectedType] = useState('')
  const [selectedTag, setSelectedTag] = useState('')
  const [activeResults, setActiveResults] = useState<SearchResultItem[] | null>(null)
  const [lastExecutedQuery, setLastExecutedQuery] = useState('')

  // Search history query
  const { data: historyData } = useQuery({
    queryKey: ['searchHistory'],
    queryFn: () => searchApi.getHistory(10),
  })

  // Tags query for filters
  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list(),
  })

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: (searchQuery: string) => {
      const payload = {
        query: searchQuery,
        limit: 20,
        memory_type: selectedType || undefined,
        tag: selectedTag || undefined,
      }
      return searchMode === 'hybrid'
        ? searchApi.hybridSearch(payload)
        : searchApi.semanticSearch(payload)
    },
    onSuccess: (data) => {
      setActiveResults(data.results)
      setLastExecutedQuery(data.query)
      queryClient.invalidateQueries({ queryKey: ['searchHistory'] })
    },
  })

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!query.trim()) return
    searchMutation.mutate(query.trim())
  }

  const handleQuickHistoryClick = (historicalQuery: string) => {
    setQuery(historicalQuery)
    searchMutation.mutate(historicalQuery)
  }

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Title */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm text-xs font-semibold text-[#8B5CF6]">
          <span className="w-2 h-2 rounded-full bg-[#8B5CF6] animate-pulse" />
          <span>Hybrid Reciprocal Rank Fusion</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#171725]">
          Search Memory Vault
        </h1>
        <p className="text-xs sm:text-sm text-[#77788A] max-w-lg mx-auto">
          Dense 384-dimensional semantic similarity combined with full-text keyword ranking
        </p>
      </div>

      {/* Search Input Box */}
      <form onSubmit={handleSearch} className="space-y-4 max-w-2xl mx-auto">
        <div className="relative flex items-center p-1.5 rounded-full glass-pearl-elevated shadow-pearl-md border border-[rgba(30,30,60,0.08)] hover:shadow-pearl-hover transition-all duration-300">
          <span className="pl-4 pr-2 text-base text-[#8B5CF6]">🔍</span>
          <input
            type="search"
            placeholder="Search concepts, thoughts, code, or ideas..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent border-0 text-xs sm:text-sm text-[#171725] placeholder:text-[#A1A1B3] focus:outline-none focus:ring-0"
          />
          <Button
            type="submit"
            size="sm"
            disabled={searchMutation.isPending}
            className="rounded-full px-5 h-9 text-xs font-semibold bg-gradient-companion text-white shadow-pearl-sm hover:opacity-95"
          >
            {searchMutation.isPending ? 'Searching...' : 'Search'}
          </Button>
        </div>

        {/* Search Mode & Filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1 px-2">
          {/* Mode Switch */}
          <div className="flex items-center gap-1 bg-[#F0F1F7] p-1 rounded-full border border-[rgba(30,30,60,0.06)]">
            <button
              type="button"
              onClick={() => setSearchMode('hybrid')}
              className={`px-3.5 py-1 rounded-full transition-all text-xs font-semibold ${
                searchMode === 'hybrid'
                  ? 'bg-gradient-companion text-white shadow-sm'
                  : 'text-[#77788A] hover:text-[#171725]'
              }`}
            >
              ⚡ Hybrid Search
            </button>
            <button
              type="button"
              onClick={() => setSearchMode('semantic')}
              className={`px-3.5 py-1 rounded-full transition-all text-xs font-semibold ${
                searchMode === 'semantic'
                  ? 'bg-gradient-companion text-white shadow-sm'
                  : 'text-[#77788A] hover:text-[#171725]'
              }`}
            >
              🧠 Vector Semantic
            </button>
          </div>

          {/* Type & Tag Filters */}
          <div className="flex items-center gap-2">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="h-8 rounded-full border border-[rgba(30,30,60,0.08)] bg-white px-3 text-xs text-[#171725] shadow-sm focus:outline-none focus:border-[#8B5CF6]"
            >
              {MEMORY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>

            <select
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
              className="h-8 rounded-full border border-[rgba(30,30,60,0.08)] bg-white px-3 text-xs text-[#171725] shadow-sm focus:outline-none focus:border-[#8B5CF6]"
            >
              <option value="">All Tags</option>
              {tags.map((t) => (
                <option key={t.id} value={t.name}>
                  #{t.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Search History Chips */}
        {historyData && historyData.items.length > 0 && (
          <div className="flex items-center gap-2 overflow-x-auto text-xs text-[#77788A] pt-1 px-2">
            <span className="whitespace-nowrap font-semibold text-[11px] uppercase tracking-wider">
              Recent:
            </span>
            {historyData.items.slice(0, 6).map((item) => (
              <button
                type="button"
                key={item.id}
                onClick={() => handleQuickHistoryClick(item.query)}
                className="px-3 py-0.5 rounded-full bg-white border border-[rgba(30,30,60,0.06)] hover:text-[#8B5CF6] hover:border-[#8B5CF6]/30 shadow-pearl-sm transition-all whitespace-nowrap text-xs font-medium"
              >
                🔍 {item.query}
              </button>
            ))}
          </div>
        )}
      </form>

      {/* Results Section */}
      <div className="pt-2">
        {searchMutation.isPending ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse h-28 rounded-3xl bg-[#E5E7F2]/60" />
            ))}
          </div>
        ) : activeResults === null ? (
          <div className="text-center py-16 rounded-3xl glass-pearl border border-dashed border-[rgba(30,30,60,0.1)] space-y-2">
            <div className="text-4xl">🔍</div>
            <p className="text-sm font-bold text-[#171725]">Find anything in your memory</p>
            <p className="text-xs text-[#77788A] max-w-sm mx-auto">
              Type concepts or natural questions. Dense vector similarity matches your semantic intent even without exact keyword matches.
            </p>
          </div>
        ) : activeResults.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-[#77788A] pb-1 px-2">
              <span>
                Found {activeResults.length} relevant memories for &ldquo;{lastExecutedQuery}&rdquo;
              </span>
              <span className="uppercase font-semibold text-[#8B5CF6]">
                Mode: {searchMode}
              </span>
            </div>

            {activeResults.map((result) => {
              const matchPercent = Math.round(result.score * 100)
              return (
                <Link key={result.memory_id} href={`/memories/${result.memory_id}`}>
                  <motion.div
                    whileHover={{ y: -3, transition: { duration: 0.15 } }}
                    className="p-5 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover transition-all duration-200 mb-3"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6]">
                          {result.memory_type}
                        </span>
                        <h3 className="text-base font-bold text-[#171725] hover:text-[#8B5CF6] transition-colors">
                          {result.title || 'Untitled Memory'}
                        </h3>
                      </div>
                      <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 whitespace-nowrap">
                        {matchPercent}% match
                      </span>
                    </div>

                    <p className="text-xs text-[#77788A] line-clamp-3 leading-relaxed mb-3">
                      {result.snippet}
                    </p>

                    <div className="flex items-center justify-between text-xs text-[#A1A1B3] pt-2 border-t border-[rgba(30,30,60,0.04)]">
                      <div className="flex flex-wrap gap-1.5">
                        {result.tags.map((tag) => (
                          <span
                            key={tag}
                            className="bg-[#F0F1F7] text-[#77788A] px-2.5 py-0.5 rounded-full text-[10px] font-medium"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                      <span className="text-[11px]">{formatDate(result.created_at)}</span>
                    </div>
                  </motion.div>
                </Link>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-16 rounded-3xl glass-pearl space-y-2">
            <div className="text-3xl">🤷‍♂️</div>
            <p className="font-bold text-sm text-[#171725]">
              No results found for &ldquo;{lastExecutedQuery}&rdquo;
            </p>
            <p className="text-xs text-[#77788A] max-w-sm mx-auto">
              Try broader search terms, selecting &ldquo;All Formats&rdquo;, or switching to Vector Semantic search.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
