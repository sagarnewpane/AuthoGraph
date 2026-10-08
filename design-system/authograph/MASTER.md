# AuthoGraph studio workspace

Audience: photographers and creative teams sharing private images with clients.
Job: upload, apply protection, share with recipients, and inspect access activity.

UI/UX Pro Max search: `creative image sharing SaaS --design-system`; Svelte guidance: `forms async accessibility --stack svelte`.
Applied: content-first hero, visible focus, accessible form errors, semantic controls, reduced motion, 44px targets. Refined the suggested glassmorphism into quiet solid surfaces so image content remains the focal point.

Palette: paper #F6F7FB, white #FFFFFF, ink #20212D, secondary ink #656779, studio indigo #5145CD, pale indigo #EEECFC, success #247454, danger #B73642, border #E5E5EE.
Type: Plus Jakarta Sans for body and controls; original Poppins for workspace headings/navigation; Georgia display serif used sparingly for editorial headings. 14–16px body, 12px minimum labels, 32px workspace headings, 64–80px landing heading.
Layout: 248px persistent sidebar, 64px top bar, max 1440px content, 32px desktop/20px mobile gutters. 4px spacing rhythm. 12px cards, 8px controls. Thin neutral borders, one subtle shadow on floating imagery.
Brand: original `LOGOV2 (1).png` wordmark/shield, recolored toward indigo with a CSS hue rotation.
Signature: photographic contact-sheet frames, small image indexes, proof-copy stamps, and indigo permission indicators. Never fake customer counts or activity.
Motion: 160ms color/opacity transitions; no ambient animation. Reduced motion supported.
States: explicit loading, empty, inline error, disabled, focus and success states. No unimplemented controls.

Generated asset: `frontend/static/images/studio-arch.png`, built-in image_gen.
Prompt: Premium editorial architectural photograph, wide 3:2; pale ivory modern building with rounded arch framing cobalt sea, Mediterranean afternoon sunlight, limestone textures, one olive branch, photographic grain; no people, text, logos or UI.
