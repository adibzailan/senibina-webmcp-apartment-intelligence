"""Assemble the demo film from shared footage. Usage: build.py <version>  (editorial | fast | product-first)"""
import json, os, shlex, subprocess, sys
V = sys.argv[1] if len(sys.argv) > 1 else "fast"
D = "video/apartment-intelligence-demo"; F = f"{D}/footage"; R = f"{D}/renders/{V}"; os.makedirs(R, exist_ok=True)
SERIF = f"{F}/fonts/snba-serif-regular.ttf"; SANS = f"{F}/fonts/snba-sans-serif-medium.ttf"
PROD = f"{F}/product/product.webm"; FOUNDER = f"{F}/founder/desk-take-1.mov"; PDF = f"{F}/product/pdf"; PR = f"{F}/practice"
MUSIC = f"{F}/music/music__20260903_191426.mp3"; BEATS = f"{F}/audio/beats"
W, H, FPS = 1920, 1080, 30; PAPER = "0xf5f2e9"; INK = "0x18211d"; MUTED = "0x5f665f"
marks = {m["name"]: m["t"] for m in json.load(open(f"{F}/product/timing.json"))["marks"]}
def esc(t): return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%")
def run(cmd): subprocess.run(cmd, shell=True, check=True)
def dt(text, font, size, color, x, y): return f"drawtext=fontfile={font}:text='{esc(text)}':fontsize={size}:fontcolor={color}:x={x}:y={y}"
def caption(t): return ("," + dt(t, SANS, 34, INK, "(w-text_w)/2", "h-120") + f":box=1:boxcolor={PAPER}@0.94:boxborderw=16") if t else ""

# ---------- clip builders: each writes a silent 1920x1080 clip of `sec` seconds ----------
def still(out, f, sec, cap=None, push=1.04):
    n = int(sec * FPS)
    vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
          f"zoompan=z='1+({push}-1)*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},eq=saturation=0.92:contrast=1.02{caption(cap)}")
    run(f"ffmpeg -v error -y -loop 1 -t {sec} -i {shlex.quote(f)} -vf \"{vf}\" -frames:v {n} -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
def card(out, sec, lines, size=84, sub=None, fade=True, gap=None, subsize=26):
    gap = gap or int(size * 1.12); subs = [sub] if isinstance(sub, str) else (sub or [])
    total = len(lines) * gap + (len(subs) * (subsize + 12) + 30 if subs else 0); y0 = H / 2 - total / 2
    parts = [dt(l, SERIF, size, INK, "(w-text_w)/2", int(y0 + i * gap + (gap - size) / 2)) for i, l in enumerate(lines)]
    for j, s_ in enumerate(subs): parts.append(dt(s_, SANS, subsize, MUTED, "(w-text_w)/2", int(y0 + len(lines) * gap + 30 + j * (subsize + 12))))
    fd = f",fade=t=in:st=0:d=0.4:color={PAPER},fade=t=out:st={sec-0.4}:d=0.4:color={PAPER}" if fade else ""
    run(f"ffmpeg -v error -y -f lavfi -i color=c={PAPER}:s={W}x{H}:r={FPS}:d={sec} -vf \"{','.join(parts)}{fd}\" -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
# The presentation frame for act three, after Adib's sketch: paper ground, the live product recording in a
# large box on the right labelled "Agent via WebMCP", the desk recording in a small box top-left labelled
# "Real life demo", and the caption in the left column beneath it.
BW, BH, BX, BY = 1392, 783, 480, 176          # product box (16:9)
SW, SH, SX, SY = 384, 216, 48, 176            # founder box
def cut(out, t0, t1, speed=1.0, cap=None, pip=2.0):
    dur = (t1 - t0) / speed
    fc = (f"color=c={PAPER}:s={W}x{H}:r={FPS}:d={dur:.3f}[bg];"
          f"[0:v]trim=start={t0}:end={t1},setpts=(PTS-STARTPTS)/{speed},scale={BW}:{BH},fps={FPS},pad=iw+4:ih+4:2:2:{INK}[prod];"
          f"[1:v]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},setpts=PTS-STARTPTS,pad=iw+4:ih+4:2:2:{INK}[desk];"
          f"[bg][prod]overlay={BX-2}:{BY-2}:shortest=0[a];[a][desk]overlay={SX-2}:{SY-2}:shortest=0[b];"
          f"[b]{dt('Agent via WebMCP', SANS, 22, MUTED, BX, BY - 40)},{dt('Real life demo', SANS, 22, MUTED, SX, SY + SH + 16)}"
          + ("," + dt(cap, SERIF, 30, INK, SX, SY + SH + 70) if cap else "") + "[v]")
    run(f"ffmpeg -v error -y -i {PROD} -ss {pip} -t {dur:.3f} -i {FOUNDER} -filter_complex \"{fc}\" -map \"[v]\" -t {dur:.3f} -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
    return dur
def wrapcap(t, width=24):
    words, lines, cur = t.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 > width and cur: lines.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    if cur: lines.append(cur)
    return lines
def cut_wrapped(out, t0, t1, speed=1.0, cap=None, pip=2.0):
    """cut() with the caption wrapped onto several lines in the left column."""
    dur = (t1 - t0) / speed
    caps = "".join("," + dt(l, SERIF, 30, INK, SX, SY + SH + 70 + i * 40) for i, l in enumerate(wrapcap(cap))) if cap else ""
    fc = (f"color=c={PAPER}:s={W}x{H}:r={FPS}:d={dur:.3f}[bg];"
          f"[0:v]trim=start={t0}:end={t1},setpts=(PTS-STARTPTS)/{speed},scale={BW}:{BH},fps={FPS},pad=iw+4:ih+4:2:2:{INK}[prod];"
          f"[1:v]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},setpts=PTS-STARTPTS,pad=iw+4:ih+4:2:2:{INK}[desk];"
          f"[bg][prod]overlay={BX-2}:{BY-2}:shortest=0[a];[a][desk]overlay={SX-2}:{SY-2}:shortest=0[b];"
          f"[b]{dt('Agent via WebMCP', SANS, 22, MUTED, BX, BY - 40)},{dt('Real life demo', SANS, 22, MUTED, SX, SY + SH + 16)}{caps}[v]")
    run(f"ffmpeg -v error -y -i {PROD} -ss {pip} -t {dur:.3f} -i {FOUNDER} -filter_complex \"{fc}\" -map \"[v]\" -t {dur:.3f} -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
    return dur
def pdfpages(out, pages, each):
    segs = []
    for i, pg in enumerate(pages):
        s = f"{R}/_pdf{i}.mp4"; n = int(each * FPS)
        run(f"ffmpeg -v error -y -loop 1 -t {each} -i {PDF}/page-{pg:02d}.png -vf \"scale=-2:{H-120},pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:0xfbfaf6\" -frames:v {n} -c:v libx264 -pix_fmt yuv420p -r {FPS} {s}"); segs.append(s)
    concat(out, segs)
def concat(out, segs):
    lst = out + ".txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
    run(f"ffmpeg -v error -y -f concat -safe 0 -i {lst} -c copy {out}")

# ---------- content ----------
PRACTICE = ["wall-panorama.jpg", "wall-front.jpg", "desk-rhino-grasshopper.jpg", "light-and-shadow-sheet.jpg", "sightlines-sheet.jpg", "wind-and-temperature-site.jpg",
            "room-radiation-l1-l3.jpg", "exterior-walls-study.jpg"]
PCAPS = ["How practitioners answer it."] + [None] * 7
# sales cards timed to the pauses in the narration (measured with silencedetect); durations in seconds
SALES_LONG = [(["When a home is sold,", "it gets a sentence."], 4.1), (["Bright and airy."], 1.4), (["Afternoon sun."], 1.6), (["High floor, unblocked."], 2.7), (["Every word is a guess about light."], 2.6), (["None of it is measured."], 3.0)]
SALES_SHORT = [(["When a home is sold,", "it gets a sentence."], 4.35), (["Bright and airy."], 2.05), (["Afternoon sun."], 2.3), (["None of it is measured."], 3.3)]
QUOTES = [["“This is what the sustainability consultant", "claims takes weeks to do.”"], ["“They always say four weeks,", "and the model must be simple, simple.”"], ["“Someone cracked his brain for two weeks", "to get our whole model into Rhino.”"]]
QSUB = "A practitioner, Singapore, on reading the report, 3 September 2026"
THESIS = ["Built with Ladybug and Radiance,", "the same engines architects use in practice,", "so the study a practice would run for a client", "is now open to the people who live there."]
INTRO = dict(lines=["Apartment Intelligence"], sub=["Version 0, built for the OpenAI WebMCP Challenge", "September 2026"], size=72)

def product_beats(pace):
    s = pace  # speed multipliers by beat
    return [
        ("cut", dict(t0=marks["start"] + 1.0, t1=marks["screen:place"] + 1.0, speed=s[0], cap="A real block. A real storey.", pip=2.0), "b05"),
        ("cut", dict(t0=marks["agent:show"] - 0.3, t1=marks["click:confirm"] - 0.3, speed=s[1], cap="An agent can stage a placement. It cannot confirm one.", pip=12.0), "b06"),
        ("cut", dict(t0=marks["click:confirm"] - 0.6, t1=marks["screen:analysis"] + 1.2, speed=1.0, cap="That click belongs to a person.", pip=44.0), "b07"),
        ("cut", dict(t0=marks["screen:analysis"] + 1.2, t1=marks["tool:create_apartment_study"] - 0.2, speed=s[2], cap="Radiation, per room. Every number carries its source.", pip=48.0), "b08"),
        ("cut", dict(t0=marks["tool:create_apartment_study"] - 0.2, t1=marks["agent:hide"], speed=s[3], cap="Three units. Three clicks. One table.", pip=60.0), "b09"),
        ("cut", dict(t0=marks["agent:hide"], t1=marks["end"] - 0.4, speed=s[4], cap="Keep the evidence.", pip=80.0), "b10"),
    ]
def tail(pdf_each, close_sec):
    T = [("pdf", dict(pages=[1, 2, 3, 7, 10], each=pdf_each), None)]
    for i, q in enumerate(QUOTES): T.append(("card", dict(sec=4.7, lines=q, size=56, sub=QSUB), "b12" if i == 0 else None))
    T.append(("card", dict(sec=close_sec, lines=THESIS, size=54, sub=["apartments.senibina.com.sg"], subsize=30), "b11"))
    return T
def timeline(v):
    T = []
    if v == "editorial":
        T.append(("card", dict(sec=6, lines=["Will this apartment get", "the sun you expect?"]), "b01"))
        for i, f in enumerate(PRACTICE): T.append(("still", dict(f=f"{PR}/{f}", sec=[6, 4, 3.5, 3.5, 3, 2.5, 3.5, 3.2][i], cap=PCAPS[i], push=1.0 if "wind" in f else 1.04), "b02" if i == 0 else None))
        for i, (l, sec) in enumerate(SALES_LONG): T.append(("card", dict(sec=sec, lines=l, fade=False), "b03" if i == 0 else None))
        T.append(("card", dict(sec=7, **INTRO), "b04"))
        T += product_beats([1.0, 1.0, 1.15, 1.9, 1.1]) + tail(1.5, 10)
    else:
        if v == "product-first":
            T.append(("cut", dict(t0=marks["screen:analysis"] + 8.0, t1=marks["screen:analysis"] + 13.0, speed=1.0, cap="Will this apartment get the sun you expect?", pip=46.0), "b01"))
        else:
            T.append(("card", dict(sec=4, lines=["Will this apartment get", "the sun you expect?"]), "b01"))
        for i, f in enumerate(PRACTICE): T.append(("still", dict(f=f"{PR}/{f}", sec=[3, 2, 2, 2, 1.8, 1.5, 2.2, 2.0][i], cap=PCAPS[i], push=1.0 if "wind" in f else 1.05), "b02" if i == 0 else None))
        for i, (l, sec) in enumerate(SALES_SHORT): T.append(("card", dict(sec=sec, lines=l, fade=False), "b03" if i == 0 else None))
        T.append(("card", dict(sec=5, **INTRO), "b04"))
        T += product_beats([1.25, 1.15, 1.35, 2.4, 1.3]) + tail(1.1, 8.5)
    return T

BEATNAME = {"b01":"question","b02":"practice","b03":"sales","b04":"intro","b05":"block","b06":"agent","b07":"click","b08":"runs","b09":"three","b10":"export","b11":"close","b12":"why"}
if V != "editorial": BEATNAME["b02"] = "practice-short"; BEATNAME["b03"] = "sales-short"
def alen(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]))
BEATLEN = {b: alen(f"{BEATS}/{b}-{n}.mp3") for b, n in BEATNAME.items()}
def hold(seg, dur, need):
    if dur >= need: return dur
    tmp = seg + ".hold.mp4"; run(f"ffmpeg -v error -y -i {seg} -vf tpad=stop_mode=clone:stop_duration={need-dur:.3f} -c:v libx264 -pix_fmt yuv420p -r {FPS} {tmp}"); os.replace(tmp, seg); return need
segs, cues, t = [], [], 0.0
for i, (kind, a, beat) in enumerate(timeline(V)):
    out = f"{R}/_c{i:02d}.mp4"
    if kind == "card": card(out, **a); dur = a["sec"]
    elif kind == "still": still(out, **a); dur = a["sec"]
    elif kind == "cut": dur = cut_wrapped(out, **a)
    elif kind == "pdf": pdfpages(out, **a); dur = len(a["pages"]) * a["each"]
    if beat and beat not in ("b02", "b03", "b12"): dur = hold(out, dur, BEATLEN[beat] + 0.35 + 0.7)
    if beat: cues.append((beat, t + 0.35))
    segs.append(out); t += dur
video = f"{R}/_video.mp4"; concat(video, segs); total = t
inputs = f"-i {video} -i {MUSIC} " + " ".join(f"-i {BEATS}/{b}-{BEATNAME[b]}.mp3" for b, _ in cues)
fc = f"[1:a]atrim=0:{total},afade=t=in:st=0:d=2,afade=t=out:st={total-4}:d=4,volume=0.11[m];"
fc += "".join(f"[{i+2}:a]adelay={int(at*1000)}|{int(at*1000)}[n{i}];" for i, (_, at) in enumerate(cues))
fc += "[m]" + "".join(f"[n{i}]" for i in range(len(cues))) + f"amix=inputs={len(cues)+1}:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
final = f"{D}/renders/apartment-intelligence-demo-{V}.mp4"
run(f"ffmpeg -v error -y {inputs} -filter_complex \"{fc}\" -map 0:v -map \"[a]\" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart -t {total} {final}")
json.dump({"version": V, "total_s": round(total, 2), "cues": cues}, open(f"{R}/cues.json", "w"), indent=1)
print(V, f"{total:.1f}s", final)
