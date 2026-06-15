# Design Context: Storyverse

## Design Direction: "Obsidian Canvas" (Dark Mode Glassmorphism)
The design should feel like a premium, professional AI tool (like Midjourney or RunwayML) crossed with a digital grimoire. We will use absolute blacks, deep charcoals, and vibrant neon accents to make the AI-generated imagery pop.

## Color Palette
- **Background**: Absolute Black `#000000` to Deep Charcoal `#0A0A0A`
- **Surface Panels**: Frosted Glass `rgba(25, 25, 25, 0.6)` with heavy background blur (`backdrop-blur-xl`).
- **Primary Accent**: Neon Violet `#8B5CF6` transitioning to Cyan `#06B6D4` (used for active states, loading glows, and primary buttons).
- **Text (Primary)**: Pure White `#FFFFFF` for headings.
- **Text (Secondary)**: Slate Gray `#94A3B8` for body copy and metadata.

## Typography
- **Headings (The Brand)**: `Outfit` or `Space Grotesk` (Google Fonts) - Geometric, tech-forward, and bold.
- **Body & UI**: `Inter` - Highly legible, neutral, and professional.

## Layout & Components
- **Floating UI**: Cards and navigation bars should float above the background with subtle 1px inner borders (`border-white/10`) to simulate physical glass edges.
- **The Story Card (Redesigned)**: 
  - An asymmetrical split-pane layout. 
  - Left side: 60% width containing the typography (title, tags, story text).
  - Right side: 40% width containing a visually stunning masonry or stacked display of the generated Comic and Meme images.
- **Animations**: Silky smooth micro-interactions. Glow effects that breathe (`animate-pulse`) when generating.

## Anti-References (What to avoid)
- Avoid flat, generic Tailwind defaults (no standard blue buttons).
- Avoid overly cluttered, dense dashboards. Keep the canvas wide and breathable to let the art shine.
- Do not use cartoonish or overly playful fonts; the humor comes from the memes, the UI must remain a sleek framing device.
