import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50:  "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
        },
        earth: {
          50:  "#fdf8f0",
          100: "#faefd9",
          200: "#f5dcaf",
          300: "#ecc37a",
          400: "#e2a044",
          500: "#d4851f",
          600: "#b86915",
          700: "#984f13",
          800: "#7c3f15",
          900: "#663414",
        },
        saffron: "#FF9933",
        leaf:    "#228B22",
        soil:    "#8B4513",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
