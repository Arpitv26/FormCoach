# FormCoach launch video

22-second, 1920×1080 landscape film at 30 fps, with instrumental music and interface SFX. No narration.

- brag.mp4 — final delivery video, including custom first-frame poster
- brag.jpg — standalone cover image
- share-copy.txt — ready-to-use caption
- brag-plan.md / composition-brief.md — creative plan
- composition/ — editable Hyperframes project
- ASSETS.md — source and attribution notes

## Preview and render

With Node.js, Chrome, FFmpeg and FFprobe installed:

```sh
cd brag-output/composition
npm run dev
npm run check
npm run render -- --output ../brag.mp4 --quality delivery --workers 1
```

Open the Studio URL printed by `npm run dev` to preview and edit the composition.
The generated package scripts pin Hyperframes 0.8.80. Runtime JavaScript, font, footage and audio are bundled locally. Re-rendering produces the animated cut; the cover-frame replacement is a separate FFmpeg step recorded in validation.md.

This deliverable lives separately from the app. No application code, API configuration or dependencies were changed. The final video and editable source are included here; local preview caches and QA captures are ignored.
