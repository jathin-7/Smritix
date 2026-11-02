'use client'

import { PearlHexBackground } from '@/components/pearl-hex-background'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#F8F9FC] p-4 text-[#11121C] overflow-hidden font-sans">
      <PearlHexBackground />
      <div className="relative z-10 w-full max-w-md">
        {children}
      </div>
    </div>
  )
}
