'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { TimelineResponse, TimelineDayGroup, TimelineMemoryItem } from '@/types'

export default function TimelinePage() {
  const { data: timelineData, isLoading } = useQuery<TimelineResponse>({
    queryKey: ['timeline'],
    queryFn: () => dashboardApi.getTimeline(100),
  })

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-[#8B5CF6] animate-pulse" />
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8B5CF6]">
              Chronological Flow
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#171725]">
            Memory Timeline
          </h1>
          <p className="text-xs sm:text-sm text-[#77788A] mt-0.5">
            A chronological journey tracing the evolution of your captured knowledge
          </p>
        </div>
        <Link href="/memories/new">
          <Button
            size="sm"
            className="rounded-full text-xs h-9 px-5 bg-gradient-companion text-white font-semibold shadow-pearl-sm hover:shadow-pearl-hover hover:opacity-95 transition-all"
          >
            + New Memory
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-xs text-[#A1A1B3] animate-pulse">
          Synthesizing chronological timeline...
        </div>
      ) : !timelineData || timelineData.groups.length === 0 ? (
        <div className="p-12 text-center rounded-3xl glass-pearl border border-dashed border-[rgba(30,30,60,0.1)] space-y-3">
          <div className="text-4xl">⏳</div>
          <h3 className="font-bold text-sm text-[#171725]">Timeline is Empty</h3>
          <p className="text-xs text-[#77788A]">
            Capture memories or documents to visualize your ideas chronologically.
          </p>
        </div>
      ) : (
        <div className="relative pl-8 space-y-10 border-l-2 border-[#8B5CF6]/30 ml-4">
          {timelineData.groups.map((group: TimelineDayGroup) => (
            <div key={group.date} className="relative space-y-4">
              {/* Timeline Date Pulsing Node */}
              <div className="absolute -left-[41px] top-0 flex items-center justify-center w-6 h-6 rounded-full bg-white border-2 border-[#8B5CF6] shadow-pearl-sm">
                <div className="w-2.5 h-2.5 rounded-full bg-gradient-companion animate-pulse" />
              </div>

              <div>
                <span className="text-xs font-black uppercase tracking-wider bg-gradient-companion bg-clip-text text-transparent">
                  {group.formatted_date}
                </span>
                <span className="text-[11px] text-[#A1A1B3] ml-2">
                  ({group.memories.length} {group.memories.length === 1 ? 'memory' : 'memories'})
                </span>
              </div>

              <div className="space-y-3">
                {group.memories.map((mem: TimelineMemoryItem) => (
                  <Link key={mem.id} href={`/memories/${mem.id}`} className="block group">
                    <motion.div
                      whileHover={{ x: 4, transition: { duration: 0.15 } }}
                      className="p-5 rounded-3xl glass-pearl border border-[rgba(30,30,60,0.06)] shadow-pearl-sm hover:shadow-pearl-hover hover:border-[#8B5CF6]/30 transition-all duration-200"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6]">
                          {mem.memory_type}
                        </span>
                        <span className="text-[11px] text-[#A1A1B3]">
                          {new Date(mem.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>

                      <h4 className="font-bold text-sm text-[#171725] group-hover:text-[#8B5CF6] transition-colors">
                        {mem.title}
                      </h4>

                      <p className="text-xs text-[#77788A] line-clamp-2 mt-1 leading-relaxed">
                        {mem.snippet}
                      </p>

                      {mem.tags && mem.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-3 pt-2.5 border-t border-[rgba(30,30,60,0.04)]">
                          {mem.tags.map((t) => (
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
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
