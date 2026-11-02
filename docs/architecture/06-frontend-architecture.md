# Frontend Architecture

## Tech Stack
- **Framework:** Next.js 14+ (App Router)
- **UI Library:** React, Tailwind CSS
- **Language:** TypeScript
- **Animations:** Framer Motion, GSAP, Lenis
- **3D/Visualization:** Three.js, React Three Fiber, Drei

## App Structure (Next.js App Router)
The frontend relies on the Next.js App Router to structure routing organically.

```text
app/
  (auth)/
    login/page.tsx
    register/page.tsx
  (dashboard)/
    layout.tsx
    page.tsx              — Dashboard home
    memories/
      page.tsx            — Memory list/grid
      [id]/page.tsx       — Memory detail
      new/page.tsx        — Create memory
    search/page.tsx       — Semantic search
    ask/page.tsx          — Ask SMRITIX (chat)
    graph/page.tsx        — Knowledge graph visualization
    projects/
      page.tsx
      [id]/page.tsx
    timeline/page.tsx
    voice/page.tsx
    settings/
      page.tsx
      privacy/page.tsx
      ai/page.tsx
  api/                    — Next.js API routes (proxy to FastAPI if needed)
```

## State Management
To keep the application highly responsive and reduce boilerplate, state management is broken into distinct concerns:
- **Server State:** TanStack Query (React Query) handles all data fetching, caching, and synchronization with the FastAPI backend.
- **Client State:** Zustand is used for lightweight, fast UI state such as managing sidebar toggles, modal visibility, and theme selection.
- **Form State:** React Hook Form combined with Zod handles complex form validation seamlessly.
- *Decision: No Redux.* Redux introduces unnecessary boilerplate for this scale; Zustand and React Query provide a simpler and cleaner separation.

## Component Architecture
Components are structured using a modified atomic design methodology to ensure reusability and clarity.
- **Shared UI:** Located in `components/ui/` (atoms, molecules, UI primitives like Buttons, Cards).
- **Features:** Located in `components/features/` (complex organisms mapped to domain features like search, memories).
- **Layouts:** Located in `components/layouts/` (templates).

### Key UI Components
- **MemoryCard:** Displays a memory with type icon, tags, and summary.
- **MemoryEditor:** A rich text editor for creating/editing memories (using TipTap).
- **SearchBar:** Semantic search with advanced filtering options.
- **ChatInterface:** The conversational UI for "Ask SMRITIX".
- **KnowledgeGraph3D:** Three.js force-directed graph visualization of connections.
- **Timeline:** A chronological display of the memory timeline.
- **VoiceRecorder:** An audio recording component for voice ingestion.
- **Dashboard:** An overview featuring stats, recent memories, and identified knowledge gaps.

## Animation Strategy
Animations are used to enhance the user experience without hindering productivity.
- **Framer Motion:** Handles page transitions, component mount/unmount animations, and layout shifts.
- **GSAP:** Reserved for complex scroll-based sequences, particularly on landing or showcase pages.
- **Lenis:** Provides smooth, native-feeling scrolling across the app.
- **Three.js/R3F:** Powers the 3D Knowledge Graph visualization and interactive elements.
- *Rule of Thumb:* Keep animations subtle and snappy within the core app; be more expressive on the landing page.

## API Client
- **Centralization:** A centralized API client using the standard `fetch` API, wrapped with interceptors.
- **Type Safety:** Automated generation of TypeScript types from the backend OpenAPI specification.
- **Resilience:** Implements automatic token refresh, error handling, and robust retry logic.

## Real-time Capabilities
- **Server-Sent Events (SSE):** Used for streaming AI responses progressively to the ChatInterface.
- **WebSockets:** Power low-latency voice conversations.
- **Job Status:** Initial implementation uses polling for ingestion job status, with a planned upgrade to WebSockets in V2.

## Theming
- **Dark Mode First:** SMRITIX defaults to a dark mode aesthetic, with full light mode support.
- **CSS Variables:** Theming relies on CSS variables injected via Tailwind CSS, providing a scalable and consistent design token system.
