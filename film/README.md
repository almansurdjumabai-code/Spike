# Scroll film

`vice_scene.py` builds the landing page's scroll film in Blender (dusk bay,
ocean, palms, neon skyline, the phone playing a clip, gold coins) and renders
it to 150 WebP frames. The site scrubs those frames with the scroll
(`frontend/src/renderer/src/components/landing/Scene3D.tsx`).

Render (Blender 5.x, Eevee, about 4 minutes on a GTX 1060):

```
blender -b --factory-startup -P vice_scene.py -- preview 1,75,150 50   # quick stills
blender -b --factory-startup -P vice_scene.py -- render                 # all frames
```

Set `OUT` (where frames go) and `CLIP` (the video on the phone) at the top of
the script, then copy `f_0001.webp` … `f_0150.webp` to
`frontend/src/renderer/public/media/film/`.
