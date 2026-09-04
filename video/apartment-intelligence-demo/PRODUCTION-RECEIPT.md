# Production receipt, Apartment Intelligence demo film v1

- Master: `renders/Apartment-Intelligence-Demo-v1.mp4` (the "fast" cut), 2:03, 1920 × 1080, 30 fps, H.264 + AAC 48 kHz, 13.6 MB. Measured -16.1 LUFS integrated, -1.2 dBTP.
- Built 3 September 2026, 21:35 SGT, from `build.py fast` against `footage/product/product.webm` captured by `capture-product.mjs` on the local build that matches commit `03351d4` (nine tools, survey mode, camera and massing by tool).
- Voice: ElevenLabs professional clone "Adib" (`PI7cqzPMpSlJicFtS4WY`), `eleven_v3`, twelve lines generated once each, no time-stretch. Subtitles are the spoken words, timed by silence detection.
- Music: ElevenLabs Music v2, instrumental, 170 s, one generation, mixed at 0.11 under the voice.
- Footage: twelve founder studio photographs (seven used), one founder desk take, the product capture, ten PDF pages rendered at 110 dpi.
- Claim boundary: every number on screen is a real result from the live engine; the agent console prints real tool calls and replies; nothing is mocked. The "Real life demo" box is the founder's own desk recording. Practitioner quotes are three lines from one practitioner, lightly tidied, unnamed by choice.
- Alternates kept: `apartment-intelligence-demo-editorial.mp4` (2:25) and `apartment-intelligence-demo-product-first.mp4` (2:04).
- Upload: founder uploads to YouTube as Unlisted and pastes the link into the Devpost form; anonymous playback to be checked before submitting.

# v2, with coda (4 September 2026)

- Master: `renders/apartment-intelligence-demo-v2-coda.mp4`, 2:42, 1920 × 1080, 30 fps, H.264 + AAC 48 kHz. Measured -16.2 LUFS integrated, -1.2 dBTP. Built by `build-coda.py`: the v1 master untouched for 2:03, then a hard cut into a 39 s coda.
- Coda: paper card "How this was made."; the founder's own desk recording (`footage/founder/desk-take-1.mov`, from 40 s) in the presentation frame with the argument in the left column; the close card "Apartment Intelligence, built for the OpenAI WebMCP Challenge." with the URL. Narration `footage/audio/beats/b13-coda.mp3`, ElevenLabs clone "Adib", `eleven_v3`, one generation, 31.8 s, subtitled phrase by phrase from silence detection. Music: the unused tail of the same v1 track from 2:03, at 0.11, four-second fade.
- Claim boundary: the narration says the project was dictated because the founder could not type much in the two weeks before the close, that agents wrote the code and the founder reviewed outputs; it names no cause and makes no claim about code quality beyond "I can vouch for what it does". Replace the desk clip with a self-recording if the founder records one; the script and timings need no change.
