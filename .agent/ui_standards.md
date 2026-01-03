# 🎨 UI & Design Language Standards

Maintaining the "Premium" look and feel of the PacketBuddy dashboard.

## 🌈 Color Palette (CSS Variables)

- **Background**: Deep Dark Space (`#0a0a0c`).
- **Surface**: Translucent Glass (`rgba(255, 255, 255, 0.03)`).
- **Accents**:
  - Primary: Hyper Violet (`#8b5cf6`).
  - Secondary: Electric Indigo (`#6366f1`).
  - Success: Emerald Glow (`#10b981`).
  - Warning: Amber Pulse (`#f59e0b`).

## 🧱 Layout Rules

1. **The 3-Panel Strategy**: The top summary row MUST stay in a 3-column grid (`Live Speed`, `Today`, `Lifetime`).
2. **Glassmorphism**: Use `backdrop-filter: blur(12px)` for all card containers.
3. **No Placeholders**: Never use generic loading text. Use shimmering skeletons if data is pending.
4. **Icons**: Use SVG icons (Lucide/Feather style). Keep stroke-width at 1.5px for a modern, thin look.

## 📈 Chart Styling (Chart.js)

- **Grid Lines**: Dashed and extremely subtle (`rgba(255, 255, 255, 0.05)`).
- **Gradients**: Line charts must use vertical linear gradients from accent color to transparent.
- **Tension**: Use `tension: 0.4` for "smooth" line aesthetics, never use jagged lines.

## 📱 Responsiveness

- **Desktop**: 1200px+ (3 columns).
- **Tablet**: 768px - 1024px (2 columns).
- **Mobile**: < 768px (Single column stack).

## ✨ Micro-interactions

- **Hover**: All cards should have a subtle scale effect (`scale: 1.01`) and a brighter border on hover.
- **Transitions**: Use `cubic-bezier(0.4, 0, 0.2, 1)` for all UI transitions.
- **Progress Bars**: Usage bars should have a "breathing" gradient animation.
