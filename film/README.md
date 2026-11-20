# Scroll film

`bay_scene.py` builds the landing page's scroll film in Blender: dusk over the
bay, a lit skyline with a SPIKECLIP rooftop sign, the pink-lit causeway, a
speedboat in SpikeClip colours, then the phone playing a clip rising out of the
water in a burst of gold coins. It renders 180 WebP frames. The sky (HDRI
`belfast_sunset_puresky`), the shore tree (`island_tree_01`) and the buoy
(`lateral_sea_marker`) are CC0 assets from polyhaven.com; set `ASSETS` to
where they were downloaded. `vice_scene.py` is the first, simpler version. The site scrubs those frames with the scroll
(`frontend/src/renderer/src/components/landing/Scene3D.tsx`).

Render (Blender 5.x, Eevee, about 4 minutes on a GTX 1060):

```
blender -b --factory-startup -P vice_scene.py -- preview 1,75,150 50   # quick stills
blender -b --factory-startup -P vice_scene.py -- render                 # all frames
```

Set `OUT` (where frames go) and `CLIP` (the video on the phone) at the top of
the script, then copy `f_0001.webp` … `f_0150.webp` to
`frontend/src/renderer/public/media/film/`.
