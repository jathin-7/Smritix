import type { Metadata, Viewport } from 'next'
import '@/styles/globals.css'
import Providers from './providers'

export const metadata: Metadata = {
  title: 'SMRITIX — Sovereign Personal AI Memory System',
  description: 'Your personal AI memory companion. Capture thoughts, documents, and code with sovereign local AI.',
}

export const viewport: Viewport = {
  themeColor: '#F8F8FC',
  colorScheme: 'light',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="light" style={{ colorScheme: 'light' }}>
      <head>
        <meta name="color-scheme" content="light" />
        <meta name="supported-color-schemes" content="light" />
      </head>
      <body className="font-sans antialiased min-h-screen bg-[#F8F8FC] text-[#11121C]">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
