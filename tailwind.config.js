/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: { primary: "var(--bg-primary)", secondary: "var(--bg-secondary)" },
        accent: {
          violet: "var(--accent-violet)",
          cyan: "var(--accent-cyan)",
          magenta: "var(--accent-magenta)"
        },
        border: { subtle: "var(--border-subtle)" },
        text: { primary: "var(--text-primary)", muted: "var(--text-muted)" }
      },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        12: "var(--space-12)",
        16: "var(--space-16)"
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        pill: "var(--radius-pill)"
      },
      transitionDuration: {
        fast: "var(--fast)",
        base: "var(--base)",
        slow: "var(--slow)"
      },
      transitionTimingFunction: {
        out: "var(--ease-out)"
      }
    }
  },
  plugins: []
};
