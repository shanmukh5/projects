# Terminal action movie feasibility overview

## Core constraints of terminal rendering
- **Cell-based grid**: Most terminals render a fixed grid of character cells. The effective resolution is `columns x rows`, not pixel-perfect. This caps how much detail you can show compared to real video resolutions.  
- **Aspect ratio**: Character cells are typically taller than they are wide, so a “square” image in cells still looks stretched unless you compensate.  
- **Refresh pipeline**: Terminal output is text-based (escape sequences + glyphs). Pushing large full-screen redraws at high FPS can be bottlenecked by the terminal emulator, OS, and font rendering pipeline.  

## Frame rate considerations
- **120 FPS is unrealistic for full-screen, full redraws** in most terminals. Even 30–60 FPS is difficult for dense frames unless you optimize with partial updates, dirty-rects, or minimal diffs.  
- **Animation in terminals** usually targets 15–60 FPS, often lower for large, detailed scenes.  

## Color depth and “all pixels”
- **24-bit color is common** (`truecolor`) in modern terminals, but color depth is only per cell (foreground/background), not per pixel.  
- **Higher “pixel” density is only possible via glyph tricks** (block characters, braille, sextants, etc.), which can effectively provide sub-cell resolution, but still limited by glyph shapes and terminal support.  
- **Graphics protocols** (Kitty graphics, iTerm2 images, Sixel) allow true pixel images inside the terminal, but support is not universal and still has performance limitations for high-FPS full-screen animation.  

## Resolution: how far you can push clarity
- **Baseline grid resolution**: Your effective “canvas” is the terminal’s **columns × rows**. A large full-screen terminal might be ~200×60 (12,000 cells). Smaller or standard windows might be 120×40 (4,800 cells).  
- **Readable action threshold**: If you want **clear silhouettes and action readability**, plan for **20–40 cells tall per character**. That means two samurais plus environment works best in ~120–200 columns × 40–60 rows.  
- **Sub-cell tricks for more detail**:  
  - **Braille**: Each cell encodes 2×4 dots → ~2×4 “pixels” per cell. A 160×50 terminal becomes ~320×200 dot resolution for line art.  
  - **Half/quarter blocks**: Useful for gradients, rain, and shadows, but still limited in detail for complex faces or armor.  
- **True-pixel protocols**: If you can target Kitty/iTerm2/Sixel, you can show actual images at higher pixel resolution. Even then, **full-motion video-like detail is constrained by throughput** and terminal support.  

## Practical detail limits for “two samurais in rain”
- **Character detail**: At standard terminal sizes (e.g., 120x40), each samurai might be a small silhouette with a few highlights. Complex animation (limbs, cloth, sword arcs) is possible but stylized and abstract.  
- **Environment detail**: Rain can be simulated with moving particles or line-dithering. Backgrounds are typically simplified gradients or silhouettes to avoid unreadable noise.  
- **Visual fidelity**: You can achieve *beautiful*, *stylized* visuals, but not film-like fidelity. The best results are impressionistic—clear shapes, motion, and lighting cues rather than fine texture.  

## How far you can push it (realistic ceiling)
- **Full-screen TUI animation**: feasible and can look excellent with carefully designed ASCII/Unicode art and palette use.  
- **120 FPS full-screen**: generally not feasible on typical terminals with cell-based rendering.  
- **“All pixels” full-screen**: only possible if you target a graphics-capable terminal protocol; even then, high-FPS video-like playback is limited by terminal and system throughput.  

## Bottom line
You can build a terminal “action movie” experience with pauses, restarts, and rich animation—but it will be **stylized**, **low-resolution**, and **performance-constrained** compared to real video. The strongest results focus on clear silhouettes, dynamic motion, and clever use of color and glyphs rather than photoreal detail.  
