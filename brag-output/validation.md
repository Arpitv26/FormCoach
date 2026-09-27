# Validation

- Hyperframes 0.8.80 full check: passed, zero errors.
- Runtime: zero errors or warnings. Layout: zero issues across 12 sampled times. Motion: zero errors or warnings.
- Text contrast: 74/74 checks passed WCAG AA.
- Six organizational warnings recommend sub-compositions instead of the five compact scenes in one editable timeline. Reviewed; no rendering or layout failures.
- All five scene snapshots visually reviewed. Final encoded upload, review, save and outro frames extracted for review.
- Delivery render: 1920×1080, H.264, yuv420p, 30 fps, 660 frames, exactly 22 seconds; stereo AAC audio.
- Full final MP4 decoded without errors. Audio measured below clipping.
- Poster chosen from settled hook at 1.2 seconds; baked over frame 0 only. Verified duration and frame count unchanged. Audio stream copied without re-encoding in poster pass.
- Local Studio URL returned HTTP 200.

## Poster replacement

```sh
ffmpeg -ss 1.2 -i brag.mp4 -frames:v 1 -q:v 2 brag.jpg
ffmpeg -i brag.mp4 -i brag.jpg -filter_complex "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]" -map "[v]" -map '0:a?' -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a copy -movflags +faststart brag.poster.mp4
```

After successful verification, brag.poster.mp4 replaces brag.mp4.

## Audio measurements

[Parsed_volumedetect_0 @ 0x14c61b830] mean_volume: -23.7 dB
[Parsed_volumedetect_0 @ 0x14c61b830] max_volume: -3.7 dB
