"""Append the 'how this was made' coda to the v1 master. Usage: .venv/bin/python video/apartment-intelligence-demo/build-coda.py
Output: renders/apartment-intelligence-demo-v2-coda.mp4 (v1 untouched, then a hard cut into the coda)."""
import glob, json, os, re, shlex, subprocess
D = "video/apartment-intelligence-demo"; F = f"{D}/footage"; R = f"{D}/renders/coda"; os.makedirs(R, exist_ok=True)
SERIF = f"{F}/fonts/snba-serif-regular.ttf"; SANS = f"{F}/fonts/snba-sans-serif-medium.ttf"
V1 = f"{D}/renders/apartment-intelligence-demo-fast.mp4"  # the current fast cut; v1 master kept as history
FOUNDER = f"{F}/founder/desk-take-1.mov"
MUSIC = f"{F}/music/music__20260903_191426.mp3"; NARR = f"{F}/audio/beats/b13-coda.mp3"
W, H, FPS = 1920, 1080, 30; PAPER = "0xf5f2e9"; INK = "0x18211d"; MUTED = "0x5f665f"
def run(c): subprocess.run(c, shell=True, check=True)
def alen(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
def esc(t): return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%")
def dt(text, font, size, color, x, y): return f"drawtext=fontfile={font}:text='{esc(text)}':fontsize={size}:fontcolor={color}:x={x}:y={y}"
def card(out, sec, lines, size=64, sub=None, subsize=28):
    gap = int(size * 1.15); subs = sub or []
    total = len(lines) * gap + (len(subs) * (subsize + 12) + 30 if subs else 0); y0 = H / 2 - total / 2
    parts = [dt(l, SERIF, size, INK, "(w-text_w)/2", int(y0 + i * gap)) for i, l in enumerate(lines)]
    for j, s_ in enumerate(subs): parts.append(dt(s_, SANS, subsize, MUTED, "(w-text_w)/2", int(y0 + len(lines) * gap + 30 + j * (subsize + 12))))
    run(f"ffmpeg -v error -y -f lavfi -i color=c={PAPER}:s={W}x{H}:r={FPS}:d={sec} -vf \"{','.join(parts)}\" -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
def founder(out, t0, sec, label, cap_lines):
    # the presentation frame: paper ground, the desk recording in a box on the right with clear paper around it,
    # a short argument in the left column that never reaches the box (column 72..500 px, box from 580 px)
    BW, BH, BX, BY = 1280, 720, 580, 180
    caps = ""; y = BY + 6
    for l in cap_lines: caps += ("," + dt(l, SERIF, 28, INK, 72, y)) if l else ""; y += 40
    fc = (f"color=c={PAPER}:s={W}x{H}:r={FPS}:d={sec:.3f}[bg];[0:v]trim=start={t0}:end={t0+sec},setpts=PTS-STARTPTS,scale={BW}:{BH}:force_original_aspect_ratio=increase,crop={BW}:{BH},fps={FPS},pad=iw+4:ih+4:2:2:{INK}[f];"
          f"[bg][f]overlay={BX-2}:{BY-2}:shortest=0[a];[a]{dt(label, SANS, 22, MUTED, BX, BY - 40)}{caps}[v]")
    run(f"ffmpeg -v error -y -i {FOUNDER} -filter_complex \"{fc}\" -map \"[v]\" -t {sec:.3f} -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
def speech_segments(f):
    out = subprocess.run(f"ffmpeg -v info -i {f} -af silencedetect=noise=-32dB:d=0.22 -f null -", shell=True, capture_output=True, text=True).stderr
    sil = [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([0-9.]+)", out), re.findall(r"silence_end: ([0-9.]+)", out))]
    total = alen(f); segs, cur = [], 0.0
    for a, b in sil:
        if a - cur > 0.15: segs.append((cur, a))
        cur = b
    if total - cur > 0.15: segs.append((cur, total))
    return segs
def phrase_times(f, phrases):
    segs = speech_segments(f)
    if len(segs) == len(phrases): return segs
    start, end = (segs[0][0], segs[-1][1]) if segs else (0.0, alen(f)); span = end - start
    n = sum(len(x) for x in phrases); t, out = start, []
    for x in phrases: d = span * len(x) / n; out.append((t, t + d)); t += d
    return out

SUBS = ["A last word on how this was made.", "Two weeks before the deadline an accident left my wrist too painful to type with,", "so the whole project was dictated.",
        "I spoke the briefs into Codex, Codex wrote the code,", "and we went round and round:", "I reviewed every screen, every number, every export,", "and sent back what was wrong.",
        "That meant letting go.", "Less reading code, more judging results.", "I can vouch for what it does, because that is what I checked.",
        "Speaking lets a thought arrive whole, in a way typing never did.", "And trusting the agent with the code freed me for the decisions only a person can make.",
        "I will keep working this way.", "If you have not tried it, try it."]
CAPS = ["Dictated, not typed.", "", "A wrist too painful to type.", "", "Briefs spoken into Codex.", "Codex wrote the code.", "",
        "I reviewed every screen,", "every number, every export.", "", "Let go of the code.", "Keep the decisions."]
NL = alen(NARR); LEAD = 0.6                    # narration starts 0.6 s into the coda
t_title = 2.8; t_close = 3.6  # whole film must stay under three minutes
t_body = max(6.0, NL + LEAD + 0.4 - t_title)   # the pictures carry the rest of the narration
def still(out, f, sec, push=1.05):
    n = int(sec * FPS)
    vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
          f"zoompan=z='1+({push}-1)*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},eq=saturation=0.92:contrast=1.02")
    run(f"ffmpeg -v error -y -loop 1 -t {sec} -i {shlex.quote(f)} -vf \"{vf}\" -frames:v {n} -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
# Pictures: your own stills in footage/founder/stills/ (jpg or png, sorted by name; suggested: the wrist, the dictation
# setup, a dictated brief in Codex), each with the act-one slow push. Until they exist, the desk recording stands in.
STILLS = sorted(p for p in glob.glob(f"{F}/founder/stills/*") if p.lower().endswith((".jpg", ".jpeg", ".png")))
segs = []
card(f"{R}/c0.mp4", t_title, ["How this was made."], size=72); segs.append(f"{R}/c0.mp4")
DICTATION = next((p for p in glob.glob(f"{F}/founder/dictation.*") if p.lower().endswith((".mov", ".mp4", ".m4v"))), None)
if DICTATION:
    FOUNDER = DICTATION
    founder(f"{R}/c1.mp4", 0.0, t_body, "Working by dictation, September 2026", CAPS); segs.append(f"{R}/c1.mp4")
    print(f"dictation clip: {DICTATION}")
elif STILLS:
    each = t_body / len(STILLS)
    for i, f in enumerate(STILLS): still(f"{R}/s{i}.mp4", f, each); segs.append(f"{R}/s{i}.mp4")
    print(f"stills: {len(STILLS)} x {each:.1f}s")
else:
    founder(f"{R}/c1.mp4", 40.0, t_body, "My desk, 3 September 2026", CAPS); segs.append(f"{R}/c1.mp4")
    print("no stills in footage/founder/stills/; the desk recording stands in")
card(f"{R}/c2.mp4", t_close, ["Apartment Intelligence,", "built for the OpenAI WebMCP Challenge."], size=54, sub=["apartments.senibina.com.sg"], subsize=30); segs.append(f"{R}/c2.mp4")
lst = f"{R}/list.txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
run(f"ffmpeg -v error -y -f concat -safe 0 -i {lst} -c copy {R}/coda_video0.mp4")
total = t_title + t_body + t_close
chain = ",".join(f"drawtext=fontfile={SANS}:text='{esc(txt)}':fontsize=34:fontcolor={INK}:box=1:boxcolor={PAPER}@0.94:boxborderw=16:x=(w-text_w)/2:y=h-96:enable='between(t,{LEAD+a:.2f},{LEAD+z+0.25:.2f})'" for (a, z), txt in zip(phrase_times(NARR, SUBS), SUBS))
run(f"ffmpeg -v error -y -i {R}/coda_video0.mp4 -vf \"{chain}\" -c:v libx264 -crf 18 -pix_fmt yuv420p -r {FPS} {R}/coda_video.mp4")
V1LEN = alen(V1)
music_left = alen(MUSIC) - V1LEN                      # the v1 cut already used the first 123 s of the track
fade_at = max(1.5, min(total, music_left) - 4.0)      # fade out where the music really ends, not where the film does
fc = (f"[1:a]atrim={V1LEN}:{V1LEN+total},asetpts=PTS-STARTPTS,apad=whole_dur={total},afade=t=in:st=0:d=1.5,afade=t=out:st={fade_at}:d=4,volume=0.11[m];"
      f"[2:a]adelay={int(LEAD*1000)}|{int(LEAD*1000)}[n];[m][n]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
run(f"ffmpeg -v error -y -i {R}/coda_video.mp4 -i {MUSIC} -i {NARR} -filter_complex \"{fc}\" -map 0:v -map \"[a]\" -c:v copy -c:a aac -b:a 192k -ar 48000 -t {total} {R}/coda.mp4")
final = f"{D}/renders/apartment-intelligence-demo-v2-coda.mp4"
open(f"{R}/final.txt", "w").write(f"file '{os.path.abspath(V1)}'\nfile '{os.path.abspath(R + '/coda.mp4')}'\n")
run(f"ffmpeg -v error -y -f concat -safe 0 -i {R}/final.txt -c copy -movflags +faststart {final}")
json.dump({"v1_s": V1LEN, "coda_s": total, "total_s": V1LEN + total, "narration_s": NL}, open(f"{R}/cues.json", "w"), indent=1)
print(f"v1 {V1LEN:.1f}s + coda {total:.1f}s = {V1LEN+total:.1f}s -> {final}")
