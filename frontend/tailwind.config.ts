import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "#8B5CF6",           // Electric Purple
          soft: "#A78BFA",              // Soft Violet
          deep: "#7045DB",              // Deep Violet
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#F0F1F7",           // Soft Pearl Gray
          foreground: "#171725",
        },
        accent: {
          DEFAULT: "#38BDF8",           // Electric Cyan
          soft: "#7DD3FC",              // Soft Blue
          foreground: "#171725",
        },
        muted: {
          DEFAULT: "#F0F1F7",
          foreground: "#77788A",        // Secondary Text
        },
        subtle: "#A1A1B3",              // Muted Text
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        card: {
          DEFAULT: "#FFFFFF",
          foreground: "#171725",
        },
      },
      borderRadius: {
        '2xl': "1.25rem",
        '3xl': "1.75rem",
        '4xl': "2.25rem",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        'pearl-sm': '0 2px 8px -1px rgba(30, 30, 60, 0.04), 0 1px 3px -1px rgba(30, 30, 60, 0.02)',
        'pearl-md': '0 10px 30px -6px rgba(23, 23, 37, 0.05), 0 4px 10px -2px rgba(23, 23, 37, 0.02)',
        'pearl-lg': '0 20px 48px -10px rgba(139, 92, 246, 0.08), 0 8px 24px -4px rgba(23, 23, 37, 0.03)',
        'pearl-glow': '0 0 50px -10px rgba(139, 92, 246, 0.25), 0 0 30px -5px rgba(56, 189, 248, 0.2)',
      },
      animation: {
        'float-slow': 'float 6s ease-in-out infinite',
        'float-gentle': 'floatGentle 4s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 4s ease-in-out infinite',
        'orbit': 'orbit 20s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%': { transform: 'translateY(-12px) rotate(1.5deg)' },
        },
        floatGentle: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%': { opacity: '0.9', transform: 'scale(1.05)' },
        },
        orbit: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
    },
  },
  plugins: [],
};
export default config;
