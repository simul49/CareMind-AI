import { defineConfig } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  theme: {
    extend: {
      colors: {
        cream: "#FDF7EE",
        ink: "#22333B",
        teal: {
          DEFAULT: "#0E7C7B",
          light: "#E0F2F1",
          dark: "#0B5E5D",
        },
        rose: "#E11D48",
        amber: {
          DEFAULT: "#F59E0B",
          light: "#FEF3C7",
        },
      },
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        soft: "0 8px 30px rgba(34, 51, 59, 0.08)",
        card: "0 2px 16px rgba(34, 51, 59, 0.06)",
        glow: "0 0 40px rgba(14, 124, 123, 0.25)",
      },
    },
  },
  plugins: [],
};
