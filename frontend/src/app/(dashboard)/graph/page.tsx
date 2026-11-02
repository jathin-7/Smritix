'use client'

import { useState, useRef, useEffect, useMemo, useCallback } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { graphApi, tagsApi, memoriesApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { GraphNodeItem, GraphEdgeItem, ClusterItem } from '@/types'

const TYPE_COLORS: Record<string, string> = {
  note: '#8B5CF6',        // Electric Purple
  document: '#38BDF8',    // Electric Cyan
  code: '#7045DB',        // Deep Violet
  snippet: '#A78BFA',     // Soft Violet
  conversation: '#7DD3FC',// Soft Blue
  web_clip: '#06B6D4',    // Cyan
  annotation: '#EC4899',  // Pink
}

interface SimNode extends GraphNodeItem {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

export default function KnowledgeGraphPage() {
  const queryClient = useQueryClient()
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // View & Filter States
  const [activeTab, setActiveTab] = useState<'graph' | 'clusters'>('graph')
  const [selectedTag, setSelectedTag] = useState('')
  const [selectedType, setSelectedType] = useState('')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)

  // Manual Edge Creation Modal / State
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false)
  const [sourceMemoryId, setSourceMemoryId] = useState('')
  const [targetMemoryId, setTargetMemoryId] = useState('')
  const [edgeRelation, setEdgeRelation] = useState('related_to')
  const [edgeError, setEdgeError] = useState<string | null>(null)

  // Canvas Pan & Zoom State
  const transformRef = useRef({ x: 0, y: 0, k: 1 })
  const isDraggingCanvasRef = useRef(false)
  const dragStartRef = useRef({ x: 0, y: 0 })
  const draggedNodeRef = useRef<SimNode | null>(null)

  // Simulation Nodes & Edges
  const simNodesRef = useRef<SimNode[]>([])
  const animFrameRef = useRef<number | null>(null)

  // Fetch Graph Data
  const { data: graphData, isLoading: loadingGraph } = useQuery({
    queryKey: ['graph', selectedTag, selectedType],
    queryFn: () => graphApi.getGraph({
      tag: selectedTag || undefined,
      memory_type: selectedType || undefined,
      limit: 200,
    }),
  })

  // Fetch Clusters Data
  const { data: clustersData, isLoading: loadingClusters } = useQuery({
    queryKey: ['clusters'],
    queryFn: () => graphApi.getClusters(),
  })

  // Fetch Tags for filter
  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list(),
  })

  // Fetch All Memories for manual edge selection
  const { data: allMemoriesData } = useQuery({
    queryKey: ['memoriesListForGraph'],
    queryFn: () => memoriesApi.list({ limit: 100 }),
    enabled: isConnectModalOpen,
  })

  // Create Edge Mutation
  const createEdgeMutation = useMutation({
    mutationFn: (data: { source_memory_id: string; target_memory_id: string; relation_type: string }) =>
      graphApi.createEdge(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['graph'] })
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      setIsConnectModalOpen(false)
      setSourceMemoryId('')
      setTargetMemoryId('')
      setEdgeError(null)
    },
    onError: (err: any) => {
      setEdgeError(err.message || 'Failed to create connection')
    },
  })

  // Delete Edge Mutation
  const deleteEdgeMutation = useMutation({
    mutationFn: (edgeId: string) => graphApi.deleteEdge(edgeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['graph'] })
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
    },
  })

  // Initialize Force Simulation Nodes
  useEffect(() => {
    if (!graphData || !canvasRef.current) return

    const canvas = canvasRef.current
    const width = canvas.clientWidth || 800
    const height = canvas.clientHeight || 600

    const existingMap = new Map(simNodesRef.current.map((n) => [n.id, n]))

    simNodesRef.current = graphData.nodes.map((node, i) => {
      const existing = existingMap.get(node.id)
      if (existing) {
        return {
          ...node,
          x: existing.x,
          y: existing.y,
          vx: existing.vx,
          vy: existing.vy,
          radius: Math.max(7, Math.min(18, 7 + (node.connection_count || 0) * 2)),
          color: TYPE_COLORS[node.memory_type] || '#64748b',
        }
      }

      // Initial circular layout around center
      const angle = (i / Math.max(graphData.nodes.length, 1)) * 2 * Math.PI
      const dist = 100 + Math.random() * 150
      return {
        ...node,
        x: width / 2 + Math.cos(angle) * dist,
        y: height / 2 + Math.sin(angle) * dist,
        vx: 0,
        vy: 0,
        radius: Math.max(7, Math.min(18, 7 + (node.connection_count || 0) * 2)),
        color: TYPE_COLORS[node.memory_type] || '#64748b',
      }
    })
  }, [graphData])

  // Simulation & Canvas Render Loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let isRunning = true

    const runPhysicsStep = () => {
      const nodes = simNodesRef.current
      if (!nodes || nodes.length === 0) return

      const width = canvas.width
      const height = canvas.height
      const centerX = width / 2
      const centerY = height / 2

      // Node map for fast edge lookup
      const nodeMap = new Map(nodes.map((n) => [n.id, n]))
      const edges = graphData?.edges || []

      // 1. Repulsion between all node pairs
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const n1 = nodes[i]
          const n2 = nodes[j]
          const dx = n2.x - n1.x
          const dy = n2.y - n1.y
          const distSq = dx * dx + dy * dy || 1
          const dist = Math.sqrt(distSq)
          if (dist < 260) {
            const force = (260 - dist) / dist * 0.08
            n1.vx -= dx * force
            n1.vy -= dy * force
            n2.vx += dx * force
            n2.vy += dy * force
          }
        }
      }

      // 2. Attraction along edges (Spring force)
      for (const edge of edges) {
        const sourceNode = nodeMap.get(edge.source)
        const targetNode = nodeMap.get(edge.target)
        if (sourceNode && targetNode) {
          const dx = targetNode.x - sourceNode.x
          const dy = targetNode.y - sourceNode.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const desiredDist = 110
          const force = (dist - desiredDist) * 0.005 * (edge.confidence || 0.8)
          sourceNode.vx += dx * force
          sourceNode.vy += dy * force
          targetNode.vx -= dx * force
          targetNode.vy -= dy * force
        }
      }

      // 3. Center gravity & velocity dampening
      for (const node of nodes) {
        if (draggedNodeRef.current === node) continue
        node.vx += (centerX - node.x) * 0.0006
        node.vy += (centerY - node.y) * 0.0006
        node.vx *= 0.88
        node.vy *= 0.88
        node.x += node.vx
        node.y += node.vy
      }
    }

    const render = () => {
      if (!canvas || !ctx) return

      const dpr = window.devicePixelRatio || 1
      const rect = canvas.getBoundingClientRect()
      if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
        canvas.width = rect.width * dpr
        canvas.height = rect.height * dpr
      }

      ctx.save()
      ctx.scale(dpr, dpr)
      ctx.clearRect(0, 0, rect.width, rect.height)

      const { x: panX, y: panY, k: zoom } = transformRef.current
      ctx.translate(panX, panY)
      ctx.scale(zoom, zoom)

      runPhysicsStep()

      const nodes = simNodesRef.current
      const nodeMap = new Map(nodes.map((n) => [n.id, n]))
      const edges = graphData?.edges || []

      // Identify selected node's neighbors
      const neighborIds = new Set<string>()
      if (selectedNodeId) {
        neighborIds.add(selectedNodeId)
        for (const e of edges) {
          if (e.source === selectedNodeId) neighborIds.add(e.target)
          if (e.target === selectedNodeId) neighborIds.add(e.source)
        }
      }

      // Draw Edges
      for (const edge of edges) {
        const s = nodeMap.get(edge.source)
        const t = nodeMap.get(edge.target)
        if (!s || !t) continue

        const isHighlighted =
          selectedNodeId && (edge.source === selectedNodeId || edge.target === selectedNodeId)

        ctx.beginPath()
        ctx.moveTo(s.x, s.y)
        ctx.lineTo(t.x, t.y)

        if (isHighlighted) {
          ctx.strokeStyle = '#8B5CF6' // Highlight purple
          ctx.lineWidth = 2.5
        } else if (selectedNodeId) {
          ctx.strokeStyle = 'rgba(30, 30, 60, 0.05)'
          ctx.lineWidth = 1
        } else {
          ctx.strokeStyle = 'rgba(139, 92, 246, 0.22)' // Soft connection lines
          ctx.lineWidth = 1.2
        }
        ctx.stroke()
      }

      // Draw Nodes
      for (const node of nodes) {
        const isSelected = node.id === selectedNodeId
        const isHovered = node.id === hoveredNodeId
        const isNeighbor = neighborIds.has(node.id)
        const isDimmed = selectedNodeId && !isNeighbor

        ctx.beginPath()
        ctx.arc(node.x, node.y, node.radius + (isSelected ? 3 : 0), 0, Math.PI * 2)

        if (isDimmed) {
          ctx.fillStyle = 'rgba(200, 204, 222, 0.4)'
          ctx.fill()
        } else {
          ctx.fillStyle = node.color
          ctx.fill()
          if (isSelected || isHovered) {
            ctx.lineWidth = isSelected ? 3 : 2
            ctx.strokeStyle = isSelected ? '#7045DB' : '#38BDF8'
            ctx.stroke()
          }
        }

        // Draw node title label
        if (!isDimmed || isSelected) {
          ctx.font = isSelected ? 'bold 11px system-ui' : '10px system-ui'
          ctx.fillStyle = isSelected ? '#7045DB' : '#171725'
          ctx.textAlign = 'center'
          const label = node.title.length > 20 ? node.title.slice(0, 18) + '...' : node.title
          ctx.fillText(label, node.x, node.y + node.radius + 13)
        }
      }

      ctx.restore()

      if (isRunning) {
        animFrameRef.current = requestAnimationFrame(render)
      }
    }

    render()

    return () => {
      isRunning = false
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
      }
    }
  }, [graphData, selectedNodeId, hoveredNodeId])

  // Mouse Interaction Handlers (Pan, Zoom, Node Click, Node Drag)
  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0, clientX: 0, clientY: 0 }
    const rect = canvas.getBoundingClientRect()
    const { x: panX, y: panY, k: zoom } = transformRef.current
    const clientX = e.clientX - rect.left
    const clientY = e.clientY - rect.top
    const graphX = (clientX - panX) / zoom
    const graphY = (clientY - panY) / zoom
    return { x: graphX, y: graphY, clientX, clientY }
  }

  const findNodeAtCoords = (x: number, y: number): SimNode | null => {
    const nodes = simNodesRef.current
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i]
      const dx = n.x - x
      const dy = n.y - y
      if (dx * dx + dy * dy <= (n.radius + 4) * (n.radius + 4)) {
        return n
      }
    }
    return null
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y, clientX, clientY } = getCanvasCoords(e)
    const hitNode = findNodeAtCoords(x, y)

    if (hitNode) {
      draggedNodeRef.current = hitNode
      setSelectedNodeId(hitNode.id)
    } else {
      isDraggingCanvasRef.current = true
      dragStartRef.current = { x: clientX - transformRef.current.x, y: clientY - transformRef.current.y }
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y, clientX, clientY } = getCanvasCoords(e)

    if (draggedNodeRef.current) {
      draggedNodeRef.current.x = x
      draggedNodeRef.current.y = y
      draggedNodeRef.current.vx = 0
      draggedNodeRef.current.vy = 0
    } else if (isDraggingCanvasRef.current) {
      transformRef.current.x = clientX - dragStartRef.current.x
      transformRef.current.y = clientY - dragStartRef.current.y
    } else {
      const hovered = findNodeAtCoords(x, y)
      setHoveredNodeId(hovered ? hovered.id : null)
    }
  }

  const handleMouseUp = () => {
    draggedNodeRef.current = null
    isDraggingCanvasRef.current = false
  }

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault()
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9
    const newZoom = Math.max(0.2, Math.min(3.0, transformRef.current.k * zoomFactor))

    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top

    transformRef.current.x = mouseX - (mouseX - transformRef.current.x) * (newZoom / transformRef.current.k)
    transformRef.current.y = mouseY - (mouseY - transformRef.current.y) * (newZoom / transformRef.current.k)
    transformRef.current.k = newZoom
  }

  const handleResetZoom = () => {
    transformRef.current = { x: 0, y: 0, k: 1 }
  }

  // Selected Node Details & Connected Edges
  const selectedNode = useMemo(
    () => graphData?.nodes.find((n) => n.id === selectedNodeId) || null,
    [graphData, selectedNodeId]
  )

  const selectedNodeEdges = useMemo(() => {
    if (!selectedNodeId || !graphData) return []
    return graphData.edges.filter(
      (e) => e.source === selectedNodeId || e.target === selectedNodeId
    )
  }, [graphData, selectedNodeId])

  const nodeMap = useMemo(
    () => new Map(graphData?.nodes.map((n) => [n.id, n]) || []),
    [graphData]
  )

  const handleCreateEdgeSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!sourceMemoryId || !targetMemoryId) {
      setEdgeError('Please select both memories to link')
      return
    }
    if (sourceMemoryId === targetMemoryId) {
      setEdgeError('Source and target memory cannot be identical')
      return
    }
    setEdgeError(null)
    createEdgeMutation.mutate({
      source_memory_id: sourceMemoryId,
      target_memory_id: targetMemoryId,
      relation_type: edgeRelation,
    })
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6.5rem)] space-y-4">
      {/* Top Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 glass-pearl-elevated p-4 rounded-3xl border border-[rgba(30,30,60,0.08)] shadow-pearl-sm">
        <div>
          <h1 className="text-xl font-extrabold tracking-tight text-[#171725] flex items-center gap-2">
            <span>Knowledge Graph</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6] font-semibold">
              {graphData?.total_nodes || 0} nodes • {graphData?.total_edges || 0} edges
            </span>
          </h1>
          <p className="text-xs text-[#77788A] mt-0.5">
            Semantic associations, auto-discovered connections, and topical clusters
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Tab Switcher */}
          <div className="flex p-1 bg-[#F0F1F7] rounded-full border border-[rgba(30,30,60,0.06)] text-xs">
            <button
              onClick={() => setActiveTab('graph')}
              className={`px-3.5 py-1 rounded-full font-semibold transition ${
                activeTab === 'graph' ? 'bg-gradient-companion text-white shadow-sm' : 'text-[#77788A] hover:text-[#171725]'
              }`}
            >
              2D Graph
            </button>
            <button
              onClick={() => setActiveTab('clusters')}
              className={`px-3.5 py-1 rounded-full font-semibold transition ${
                activeTab === 'clusters' ? 'bg-gradient-companion text-white shadow-sm' : 'text-[#77788A] hover:text-[#171725]'
              }`}
            >
              Topic Clusters ({clustersData?.total_clusters || 0})
            </button>
          </div>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="h-9 rounded-2xl border border-[rgba(30,30,60,0.08)] bg-white px-3 text-xs text-[#171725] shadow-sm focus:outline-none focus:border-[#8B5CF6]"
          >
            <option value="">All Types</option>
            <option value="note">Notes</option>
            <option value="document">Documents</option>
            <option value="code">Code</option>
            <option value="snippet">Snippets</option>
            <option value="conversation">Conversations</option>
          </select>

          {/* Tag Filter */}
          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="h-9 rounded-2xl border border-[rgba(30,30,60,0.08)] bg-white px-3 text-xs text-[#171725] shadow-sm focus:outline-none focus:border-[#8B5CF6]"
          >
            <option value="">All Tags</option>
            {tags.map((t) => (
              <option key={t.id} value={t.name}>
                #{t.name}
              </option>
            ))}
          </select>

          {/* Manual Connect Button */}
          <Button
            size="sm"
            onClick={() => {
              if (selectedNodeId) {
                setSourceMemoryId(selectedNodeId)
              }
              setIsConnectModalOpen(true)
            }}
            className="h-9 rounded-full text-xs gap-1.5 bg-gradient-companion text-white font-semibold shadow-pearl-sm hover:opacity-95"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            Connect Memories
          </Button>
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab === 'graph' ? (
        <div className="flex-1 relative border border-[rgba(30,30,60,0.08)] rounded-3xl glass-pearl-elevated shadow-pearl-md overflow-hidden flex bg-white/40">
          {/* Interactive HTML5 Canvas */}
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
            className="flex-1 h-full w-full cursor-grab active:cursor-grabbing"
          />

          {/* Canvas Floating Legend & Controls */}
          <div className="absolute bottom-4 left-4 flex flex-col gap-2 pointer-events-none">
            <div className="bg-card/80 border border-border/40 backdrop-blur rounded-lg p-2.5 shadow-md flex items-center gap-3 text-[11px] pointer-events-auto">
              <span className="text-muted-foreground font-medium">Legend:</span>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" />
                <span className="text-foreground">Note</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" />
                <span className="text-foreground">Document</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8b5cf6]" />
                <span className="text-foreground">Code</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]" />
                <span className="text-foreground">Chat</span>
              </div>
            </div>

            <div className="flex items-center gap-1 pointer-events-auto">
              <button
                onClick={handleResetZoom}
                className="px-2.5 py-1 text-[11px] rounded bg-card/80 border border-border/40 hover:bg-card text-muted-foreground hover:text-foreground backdrop-blur"
              >
                Reset View
              </button>
            </div>
          </div>

          {/* Node Detail Slide-over Panel */}
          {selectedNode && (
            <div className="w-96 border-l border-border/40 bg-card/95 backdrop-blur flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
              <div className="p-4 border-b border-border/40 flex items-start justify-between">
                <div>
                  <span
                    className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: `${TYPE_COLORS[selectedNode.memory_type] || '#64748b'}20`,
                      color: TYPE_COLORS[selectedNode.memory_type] || '#94a3b8',
                    }}
                  >
                    {selectedNode.memory_type}
                  </span>
                  <h3 className="font-semibold text-sm text-foreground mt-1.5">
                    {selectedNode.title}
                  </h3>
                  <p className="text-[11px] text-muted-foreground">
                    Created {new Date(selectedNode.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedNodeId(null)}
                  className="p-1 text-muted-foreground hover:text-foreground rounded"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
                <div>
                  <h4 className="font-medium text-foreground mb-1">Snippet Preview</h4>
                  <p className="p-2.5 rounded-lg bg-muted/40 text-muted-foreground leading-relaxed">
                    {selectedNode.snippet}
                  </p>
                </div>

                {selectedNode.tags.length > 0 && (
                  <div>
                    <h4 className="font-medium text-foreground mb-1.5">Tags</h4>
                    <div className="flex flex-wrap gap-1">
                      {selectedNode.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 text-[11px]"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-foreground">
                      Connections ({selectedNodeEdges.length})
                    </h4>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSourceMemoryId(selectedNode.id)
                        setIsConnectModalOpen(true)
                      }}
                      className="h-6 text-[11px] px-2 text-primary"
                    >
                      + Add Link
                    </Button>
                  </div>

                  {selectedNodeEdges.length === 0 ? (
                    <p className="text-muted-foreground italic text-[11px]">
                      No connections yet. Click &ldquo;+ Add Link&rdquo; to connect with other memories.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {selectedNodeEdges.map((edge) => {
                        const otherId = edge.source === selectedNode.id ? edge.target : edge.source
                        const otherNode = nodeMap.get(otherId)
                        const isOutgoing = edge.source === selectedNode.id

                        return (
                          <div
                            key={edge.id}
                            className="p-2.5 rounded-lg border border-border/40 bg-accent/20 flex items-start justify-between gap-2"
                          >
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-1.5 mb-1">
                                <span className="font-semibold text-primary truncate">
                                  {otherNode?.title || 'Memory'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                <span className="px-1.5 py-0.2 rounded bg-muted font-mono">
                                  {isOutgoing ? '→' : '←'} {edge.relation_type}
                                </span>
                                <span>{Math.round(edge.confidence * 100)}% conf</span>
                                <span>• {edge.created_by}</span>
                              </div>
                            </div>

                            <button
                              title="Delete Edge"
                              onClick={() => deleteEdgeMutation.mutate(edge.id)}
                              className="text-muted-foreground hover:text-destructive p-1 rounded transition"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>

                <div className="pt-2">
                  <Link href={`/memories/${selectedNode.id}`}>
                    <Button variant="secondary" className="w-full text-xs">
                      Open Memory Detail Page →
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Clusters View */
        <div className="flex-1 border border-border/40 rounded-xl bg-card/40 p-6 overflow-y-auto">
          {loadingClusters ? (
            <div className="p-8 text-center text-xs text-muted-foreground animate-pulse">
              Computing semantic clusters and community components...
            </div>
          ) : !clustersData || clustersData.clusters.length === 0 ? (
            <div className="text-center p-12 text-muted-foreground text-xs">
              No clusters discovered yet. Add memories and connections to form clusters.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {clustersData.clusters.map((cluster: ClusterItem) => (
                <Card
                  key={cluster.id}
                  className="p-5 border-border/50 bg-card hover:border-primary/40 transition flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-sm text-foreground">{cluster.name}</h3>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                        {cluster.size} memories
                      </span>
                    </div>

                    <p className="text-xs text-muted-foreground mb-3">{cluster.description}</p>

                    {cluster.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-4">
                        {cluster.tags.map((t) => (
                          <span
                            key={t}
                            className="text-[10px] px-2 py-0.5 rounded bg-muted text-muted-foreground font-mono"
                          >
                            #{t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="border-t border-border/30 pt-3">
                    <div className="space-y-1">
                      {cluster.node_ids.slice(0, 3).map((nid) => {
                        const n = nodeMap.get(nid)
                        return (
                          <div
                            key={nid}
                            onClick={() => {
                              setSelectedNodeId(nid)
                              setActiveTab('graph')
                            }}
                            className="text-[11px] text-muted-foreground hover:text-primary truncate cursor-pointer flex items-center gap-1.5"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-primary/70" />
                            <span>{n?.title || `Memory #${nid.slice(0, 8)}`}</span>
                          </div>
                        )
                      })}
                      {cluster.size > 3 && (
                        <p className="text-[10px] text-muted-foreground/70 italic pl-3">
                          + {cluster.size - 3} more memories in this cluster
                        </p>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Manual Connection Modal */}
      {isConnectModalOpen && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/60 rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-base text-foreground">Connect Two Memories</h3>
              <button
                onClick={() => setIsConnectModalOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                ✕
              </button>
            </div>

            {edgeError && (
              <div className="p-2.5 rounded bg-destructive/10 text-destructive text-xs">
                {edgeError}
              </div>
            )}

            <form onSubmit={handleCreateEdgeSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="font-medium text-foreground block mb-1">Source Memory</label>
                <select
                  value={sourceMemoryId}
                  onChange={(e) => setSourceMemoryId(e.target.value)}
                  className="w-full h-9 rounded-lg border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  required
                >
                  <option value="">Select source memory...</option>
                  {allMemoriesData?.items.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.title || 'Untitled'} ({m.memory_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Target Memory</label>
                <select
                  value={targetMemoryId}
                  onChange={(e) => setTargetMemoryId(e.target.value)}
                  className="w-full h-9 rounded-lg border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  required
                >
                  <option value="">Select target memory...</option>
                  {allMemoriesData?.items.map((m) => (
                    <option key={m.id} value={m.id} disabled={m.id === sourceMemoryId}>
                      {m.title || 'Untitled'} ({m.memory_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Relation Type</label>
                <select
                  value={edgeRelation}
                  onChange={(e) => setEdgeRelation(e.target.value)}
                  className="w-full h-9 rounded-lg border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="related_to">related_to</option>
                  <option value="similar_to">similar_to</option>
                  <option value="references">references</option>
                  <option value="part_of">part_of</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsConnectModalOpen(false)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createEdgeMutation.isPending}
                  className="text-xs"
                >
                  {createEdgeMutation.isPending ? 'Connecting...' : 'Create Connection'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
