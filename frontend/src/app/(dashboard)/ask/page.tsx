'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { askApi } from '@/lib/api/client'
import { SmritixCompanion } from '@/components/smritix-companion'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ConversationItem, ConversationMessage, SourceAttributionItem } from '@/types'

const STARTER_PROMPTS = [
  'What notes do I have on neural architectures and memory?',
  'Summarize the database technologies I am currently using.',
  'What are my latest notes on FastAPI and data validation?',
]

export default function AskPage() {
  const queryClient = useQueryClient()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [streamingSources, setStreamingSources] = useState<SourceAttributionItem[]>([])
  const abortStreamRef = useRef<(() => void) | null>(null)

  // Query past conversations
  const { data: conversations = [], isLoading: loadingConversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => askApi.getConversations(),
  })

  // Load conversation details when selecting from sidebar
  const { data: conversationDetail, isFetching: loadingDetail } = useQuery({
    queryKey: ['conversation', selectedConversationId],
    queryFn: () => (selectedConversationId ? askApi.getConversation(selectedConversationId) : null),
    enabled: !!selectedConversationId,
  })

  useEffect(() => {
    if (conversationDetail && conversationDetail.messages) {
      setMessages(conversationDetail.messages)
    }
  }, [conversationDetail])

  // Scroll to bottom on new messages or streaming tokens
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  // Delete conversation mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => askApi.deleteConversation(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      if (selectedConversationId === deletedId) {
        handleNewChat()
      }
    },
  })

  const handleNewChat = () => {
    if (isStreaming && abortStreamRef.current) {
      abortStreamRef.current()
    }
    setSelectedConversationId(null)
    setMessages([])
    setStreamingText('')
    setStreamingSources([])
    setIsStreaming(false)
    inputRef.current?.focus()
  }

  const handleSendMessage = (textToSend?: string) => {
    const prompt = (textToSend || input).trim()
    if (!prompt || isStreaming) return

    // Optimistically add user message
    const tempUserMsg: ConversationMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: prompt,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMsg])
    setInput('')
    setIsStreaming(true)
    setStreamingText('')
    setStreamingSources([])

    let activeConvId = selectedConversationId
    let accumulatedText = ''
    let collectedSources: SourceAttributionItem[] = []

    const abortFn = askApi.askStream(
      {
        query: prompt,
        conversation_id: activeConvId || undefined,
      },
      {
        onMetadata: (meta) => {
          if (!activeConvId && meta.conversation_id) {
            activeConvId = meta.conversation_id
            setSelectedConversationId(meta.conversation_id)
          }
          if (meta.sources) {
            collectedSources = meta.sources
            setStreamingSources(meta.sources)
          }
        },
        onToken: (token) => {
          accumulatedText += token
          setStreamingText(accumulatedText)
        },
        onDone: (done) => {
          setIsStreaming(false)
          abortStreamRef.current = null

          const finalSources = done.sources || collectedSources
          const assistantMsg: ConversationMessage = {
            id: `asst-${Date.now()}`,
            role: 'assistant',
            content: accumulatedText,
            sources: finalSources,
            created_at: new Date().toISOString(),
          }
          setMessages((prev) => [...prev, assistantMsg])
          setStreamingText('')
          setStreamingSources([])

          queryClient.invalidateQueries({ queryKey: ['conversations'] })
          if (activeConvId) {
            queryClient.invalidateQueries({ queryKey: ['conversation', activeConvId] })
          }
        },
        onError: (err) => {
          console.error('Ask stream failed:', err)
          setIsStreaming(false)
          abortStreamRef.current = null
          const errorMsg: ConversationMessage = {
            id: `err-${Date.now()}`,
            role: 'assistant',
            content: `Error generating response: ${err.message || 'Unknown error occurred.'}`,
            created_at: new Date().toISOString(),
          }
          setMessages((prev) => [...prev, errorMsg])
          setStreamingText('')
        },
      }
    )

    abortStreamRef.current = abortFn
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleStopStreaming = () => {
    if (abortStreamRef.current) {
      abortStreamRef.current()
      abortStreamRef.current = null
      setIsStreaming(false)
      if (streamingText) {
        setMessages((prev) => [
          ...prev,
          {
            id: `partial-${Date.now()}`,
            role: 'assistant',
            content: streamingText,
            sources: streamingSources,
            created_at: new Date().toISOString(),
          },
        ])
      }
      setStreamingText('')
      setStreamingSources([])
    }
  }

  return (
    <div className="max-w-6xl mx-auto pb-12 h-[calc(100vh-6.5rem)] flex flex-col">
      {/* Ask SMRITIX Header Strip */}
      <div className="flex items-center justify-between pb-4 border-b border-[rgba(30,30,60,0.06)] shrink-0">
        <div className="flex items-center gap-3">
          <SmritixCompanion
            size="sm"
            state={isStreaming ? 'thinking' : 'idle'}
          />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-extrabold text-[#171725] tracking-tight">
                Ask SMRITIX
              </h1>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6]">
                Neural RAG
              </span>
            </div>
            <p className="text-xs text-[#77788A]">
              Conversational synthesis grounded in your verified memories
            </p>
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={handleNewChat}
          className="rounded-full text-xs h-9 px-4 bg-white border border-[rgba(30,30,60,0.08)] shadow-pearl-sm hover:shadow-pearl-hover transition-all"
        >
          + New Thread
        </Button>
      </div>

      {/* Main Chat Interface: Sidebar + Dialogue Window */}
      <div className="flex-1 flex gap-5 overflow-hidden pt-4">
        {/* Past Threads Sidebar (Collapsible on smaller screens) */}
        <aside className="w-64 hidden md:flex flex-col rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm p-3 overflow-hidden shrink-0">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#77788A] px-3 py-2">
            Recent Conversations
          </span>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {loadingConversations ? (
              <div className="p-4 text-xs text-center text-[#A1A1B3]">Loading threads...</div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-xs text-center text-[#A1A1B3]">No previous threads</div>
            ) : (
              conversations.map((c: ConversationItem) => {
                const isSelected = selectedConversationId === c.id
                return (
                  <div
                    key={c.id}
                    onClick={() => setSelectedConversationId(c.id)}
                    className={`group flex items-center justify-between p-2.5 rounded-2xl cursor-pointer text-xs transition-all ${
                      isSelected
                        ? 'bg-gradient-companion text-white shadow-sm font-semibold'
                        : 'text-[#77788A] hover:bg-white/80 hover:text-[#171725]'
                    }`}
                  >
                    <span className="truncate flex-1 pr-2">{c.title || 'Untitled Thread'}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteMutation.mutate(c.id)
                      }}
                      className={`opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 transition-opacity ${
                        isSelected ? 'text-white/80 hover:text-white' : 'text-[#A1A1B3]'
                      }`}
                    >
                      ×
                    </button>
                  </div>
                )
              })
            )}
          </div>
        </aside>

        {/* Central Chat Dialogue Stream */}
        <div className="flex-1 flex flex-col rounded-3xl glass-pearl-elevated border border-[rgba(30,30,60,0.08)] shadow-pearl-md overflow-hidden relative">
          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
            {messages.length === 0 && !isStreaming ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-5">
                <SmritixCompanion size="md" state="idle" />
                <div className="space-y-1.5 max-w-md">
                  <h3 className="text-lg font-bold text-[#171725]">
                    Ask anything about your memories
                  </h3>
                  <p className="text-xs text-[#77788A] leading-relaxed">
                    SMRITIX retrieves semantic passages via hybrid vector search and synthesizes answers with source citations.
                  </p>
                </div>

                <div className="flex flex-col gap-2 w-full max-w-md pt-2">
                  {STARTER_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => handleSendMessage(prompt)}
                      className="text-left text-xs p-3 rounded-2xl bg-white/80 border border-[rgba(30,30,60,0.06)] text-[#171725] hover:border-[#8B5CF6]/40 hover:shadow-pearl-sm transition-all"
                    >
                      ✦ {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg) => {
                  const isUser = msg.role === 'user'
                  return (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-3xl p-4 text-xs sm:text-sm leading-relaxed ${
                          isUser
                            ? 'bg-gradient-companion text-white shadow-pearl-sm rounded-tr-sm'
                            : 'bg-white border border-[rgba(30,30,60,0.08)] text-[#171725] shadow-pearl-sm rounded-tl-sm'
                        }`}
                      >
                        <div className="whitespace-pre-wrap">{msg.content}</div>

                        {/* Grounded Source Citations */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-[rgba(30,30,60,0.06)] space-y-1.5">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-[#8B5CF6]">
                              Cited Sources:
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {msg.sources.map((s, idx) => (
                                <Link
                                  key={s.memory_id}
                                  href={`/memories/${s.memory_id}`}
                                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F0F1F7] hover:bg-[#8B5CF6]/15 text-[#171725] text-[11px] font-medium transition-colors"
                                >
                                  <span className="font-bold text-[#8B5CF6]">[{idx + 1}]</span>
                                  <span className="truncate max-w-[140px]">
                                    {s.title || 'Note Reference'}
                                  </span>
                                </Link>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )
                })}

                {/* Live Streaming Response Bubble */}
                {isStreaming && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col items-start"
                  >
                    <div className="max-w-[85%] rounded-3xl p-4 text-xs sm:text-sm leading-relaxed bg-white border border-[#8B5CF6]/30 text-[#171725] shadow-pearl-sm rounded-tl-sm">
                      <div className="whitespace-pre-wrap">
                        {streamingText || 'Thinking and synthesizing memory passages...'}
                        <span className="inline-block w-1.5 h-4 ml-1 bg-[#8B5CF6] animate-pulse align-middle" />
                      </div>

                      {streamingSources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-[rgba(30,30,60,0.06)] space-y-1.5">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8B5CF6]">
                            Retrieving Citations...
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {streamingSources.map((s, idx) => (
                              <span
                                key={s.memory_id}
                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F0F1F7] text-[#171725] text-[11px]"
                              >
                                <span className="font-bold text-[#8B5CF6]">[{idx + 1}]</span>
                                <span className="truncate max-w-[140px]">{s.title || 'Note'}</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Interactive Input Bar */}
          <div className="p-3 sm:p-4 bg-white/70 border-t border-[rgba(30,30,60,0.06)]">
            <div className="flex items-center gap-2 p-1.5 rounded-full glass-pearl border border-[rgba(30,30,60,0.08)] shadow-pearl-sm">
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask SMRITIX a question about your knowledge..."
                disabled={isStreaming}
                className="flex-1 bg-transparent border-0 px-4 py-2 text-xs sm:text-sm text-[#171725] placeholder:text-[#A1A1B3] focus:outline-none focus:ring-0 resize-none max-h-24"
              />

              {isStreaming ? (
                <Button
                  size="sm"
                  onClick={handleStopStreaming}
                  className="rounded-full text-xs h-9 px-4 bg-red-500 text-white font-semibold hover:bg-red-600 transition-colors"
                >
                  Stop
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => handleSendMessage()}
                  disabled={!input.trim()}
                  className="rounded-full text-xs h-9 px-5 bg-gradient-companion text-white font-semibold shadow-pearl-sm hover:opacity-95 transition-opacity"
                >
                  Send
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
