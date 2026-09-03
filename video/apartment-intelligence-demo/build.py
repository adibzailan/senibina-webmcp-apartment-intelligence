"""Assemble the demo film from shared footage. Usage: build.py <version>  (editorial | fast | product-first)"""
import json, os, shlex, subprocess, sys
V = sys.argv[1] if len(sys.argv) > 1 else "editorial"
D = "video/apartment-intelligence-demo"; F = f"{D}/footage"; R = f"{D}/renders/{V}"; os.makedirs(R, exist_ok=True)
SERIF = f"{F}/fonts/snba-serif-regular.ttf"; SANS = f"{F}/fonts/snba-sans-serif-medium.ttf"
PROD = f"{F}/product/product.webm"; FOUNDER = f"{F}/founder/desk-take-1.mov"; PDF = f"{F}/product/pdf"; PR = f"{F}/practice"
MUSIC = f"{F}/music/music__20260903_191426.mp3"; BEATS = f"{F}/audio/beats"
W, H, FPS = 1920, 1080, 30
marks = {m["name"]: m["t"] for m in json.load(open(f"{F}/product/timing.json"))["marks"]}
def esc(t): return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%")
def caption(t, left=False): return (f",drawtext=fontfile={SANS}:text='{esc(t)}':fontsize=34:fontcolor=0x18211d:box=1:boxcolor=0xf5f2e9@0.94:boxborderw=16:x={'48' if left else '(w-text_w)/2'}:y=h-120") if t else ""
def run(cmd): subprocess.run(cmd, shell=True, check=True)

# ---------- clip builders (each writes a silent 1920x1080 mp4 of exactly `sec` seconds) ----------
def still(out, f, sec, cap=None, push=1.04):
    n = int(sec * FPS)
    vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
          f"zoompan=z='1+({push}-1)*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},eq=saturation=0.92:contrast=1.02{caption(cap)}")
    run(f"ffmpeg -v error -y -loop 1 -t {sec} -i {shlex.quote(f)} -vf \"{vf}\" -frames:v {n} -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
def card(out, sec, lines, size=84, sub=None, fade=True, cap=None, gap=None):
    gap = gap or int(size * 1.12); total = len(lines) * gap; y0 = H / 2 - total / 2 + (gap - size) / 2
    dt = ",".join(f"drawtext=fontfile={SERIF}:text='{esc(l)}':fontsize={size}:fontcolor=0x18211d:x=(w-text_w)/2:y={int(y0 + i*gap)}" for i, l in enumerate(lines))
    if sub: dt += f",drawtext=fontfile={SANS}:text='{esc(sub)}':fontsize=26:fontcolor=0x5f665f:x=(w-text_w)/2:y={int(y0 + total + 36)}"
    fd = f",fade=t=in:st=0:d=0.5:color=0xf5f2e9,fade=t=out:st={sec-0.5}:d=0.5:color=0xf5f2e9" if fade else ""
    run(f"ffmpeg -v error -y -f lavfi -i color=c=0xf5f2e9:s={W}x{H}:r={FPS}:d={sec} -vf \"{dt}{caption(cap)}{fd}\" -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
def cut(out, src, t0, t1, speed=1.0, cap=None, pip=None, sec=None):
    """Product footage from t0 to t1, played at `speed`; optional founder pip (src_t0) top-left."""
    dur = (t1 - t0) / speed if sec is None else sec
    vf = f"[0:v]trim=start={t0}:end={t1},setpts=(PTS-STARTPTS)/{speed},scale={W}:{H},fps={FPS}[base]"
    inputs = f"-i {PROD}"
    if pip is not None:
        inputs += f" -ss {pip} -t {dur} -i {FOUNDER}"
        vf += f";[1:v]scale=520:-2,pad=iw+8:ih+8:4:4:0xf5f2e9,setpts=PTS-STARTPTS[p];[base][p]overlay=48:48:shortest=0[v0]"
    else:
        vf += ";[base]null[v0]"
    vf += f";[v0]null{caption(cap, left=True)}[v]" if cap else ";[v0]null[v]"
    run(f"ffmpeg -v error -y {inputs} -filter_complex \"{vf}\" -map \"[v]\" -t {dur} -c:v libx264 -pix_fmt yuv420p -r {FPS} {out}")
    return dur
def pdfpages(out, pages, each, cap=None):
    segs = []
    for i, pg in enumerate(pages):
        s = f"{R}/_pdf{i}.mp4"; n = int(each * FPS)
        vf = f"scale=-2:{H-120},pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:0xfbfaf6{caption(cap) if i == 0 else ''}"
        run(f"ffmpeg -v error -y -loop 1 -t {each} -i {PDF}/page-{pg:02d}.png -vf \"{vf}\" -frames:v {n} -c:v libx264 -pix_fmt yuv420p -r {FPS} {s}"); segs.append(s)
    concat(out, segs)
def concat(out, segs):
    lst = out + ".txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
    run(f"ffmpeg -v error -y -f concat -safe 0 -i {lst} -c copy {out}")

# ---------- version timelines ----------
PRACTICE = ["wall-panorama.jpg", "wall-front.jpg", "desk-rhino-grasshopper.jpg", "light-and-shadow-sheet.jpg", "sightlines-sheet.jpg", "wind-and-temperature-site.jpg",
            "room-radiation-l1-l3-print.jpg", "exterior-walls-study.jpg", "radiation-benefit-trace.jpg", "sunlight-hours-june.jpg", "sunlight-hours-june-annotated.jpg"]
PCAPS = ["How architects answer it.", "A wall of trace.", "Modelled.", "Light, room by room.", "Sightlines.", "Wind and heat.", "Radiation, floor by floor.", None, "Drawn over, argued over.", "Hours of sun, June.", None]
SALES = [["Bright and airy."], ["Gets the afternoon sun."], ["High floor, unblocked."], ["None of it is measured."]]
THESIS = ["Built with Ladybug and Radiance,", "the same engines architects use in practice,", "so the study a practice would run for a client", "is now open to the people who live there."]

def timeline(v):
    T = []  # (kind, args, narration_beat or None)
    if v == "editorial":
        T.append(("card", dict(sec=6, lines=["Will this apartment get", "the sun you expect?"]), "b01"))
        for i, f in enumerate(PRACTICE): T.append(("still", dict(f=f"{PR}/{f}", sec=[5, 3, 3, 3, 2.5, 2, 3, 2.5, 3, 3, 3.5][i], cap=PCAPS[i], push=1.0 if "wind" in f else 1.04), "b02" if i == 0 else None))
        for i, s in enumerate(SALES): T.append(("card", dict(sec=[3.2, 3.2, 3.2, 4.4][i], lines=s), "b03" if i == 0 else None))
        T.append(("card", dict(sec=7, lines=["Apartment Intelligence"], sub="Version 0, built for the OpenAI WebMCP Challenge, September 2026", size=72), "b04"))
        T.append(("cut", dict(t0=marks["start"], t1=marks["screen:place"] + 1.2, speed=1.0, cap="A real block. A real storey.", pip=2.0), "b05"))
        T.append(("cut", dict(t0=marks["agent:show"] - 0.4, t1=marks["click:confirm"] - 0.3, speed=1.0, cap="An agent can stage a placement. It cannot confirm one."), "b06"))
        T.append(("cut", dict(t0=marks["click:confirm"] - 0.6, t1=marks["tool:run_solar_analysis"] + 0.2 if False else marks["screen:analysis"] + 1.4, speed=1.0, cap="That click belongs to a person.", pip=46.0), "b07"))
        T.append(("cut", dict(t0=marks["screen:analysis"] + 1.4, t1=marks["tool:create_apartment_study"] - 0.2, speed=1.15, cap="Radiation, per room. Every number carries its source."), "b08"))
        T.append(("cut", dict(t0=marks["tool:create_apartment_study"] - 0.2, t1=marks["agent:hide"], speed=1.9, cap="Three units. Three clicks. One table."), "b09"))
        T.append(("cut", dict(t0=marks["agent:hide"], t1=marks["end"] - 0.3, speed=1.1, cap="Keep the evidence."), "b10"))
        T.append(("pdf", dict(pages=[1, 2, 3, 7, 10], each=1.5), None))
        T.append(("card", dict(sec=6.5, lines=["“This is the report a sustainability consultant", "takes four weeks to run, and the model", "has to be kept simple. Not any more.”"], size=54, sub="An architectural assistant at a Singapore practice, on reading the PDF, 3 September 2026"), None))
        T.append(("card", dict(sec=10, lines=THESIS, size=54, sub="apartments.senibina.com.sg   A public-interest study by Senibina for apartment living. Singapore now, the region next."), "b11"))
    elif v == "fast":
        T.append(("card", dict(sec=4, lines=["Will this apartment get", "the sun you expect?"]), "b01"))
        for i, f in enumerate(PRACTICE): T.append(("still", dict(f=f"{PR}/{f}", sec=[3, 2, 2, 2, 1.8, 1.5, 2.2, 1.8, 2.2, 2.2, 2.6][i], cap=PCAPS[i], push=1.0 if "wind" in f else 1.05), "b02" if i == 0 else None))
        for i, s in enumerate(SALES): T.append(("card", dict(sec=[2.2, 2.2, 2.2, 3.4][i], lines=s), "b03" if i == 0 else None))
        T.append(("card", dict(sec=5, lines=["Apartment Intelligence"], sub="Version 0, built for the OpenAI WebMCP Challenge, September 2026", size=72), "b04"))
        T.append(("cut", dict(t0=marks["start"] + 1.5, t1=marks["screen:place"] + 0.8, speed=1.25, cap="A real block. A real storey.", pip=2.0), "b05"))
        T.append(("cut", dict(t0=marks["agent:show"] - 0.3, t1=marks["click:confirm"] - 0.3, speed=1.15, cap="An agent can stage a placement. It cannot confirm one."), "b06"))
        T.append(("cut", dict(t0=marks["click:confirm"] - 0.5, t1=marks["screen:analysis"] + 1.0, speed=1.0, cap="That click belongs to a person.", pip=46.0), "b07"))
        T.append(("cut", dict(t0=marks["screen:analysis"] + 1.0, t1=marks["tool:create_apartment_study"] - 0.2, speed=1.35, cap="Radiation, per room. Every number carries its source."), "b08"))
        T.append(("cut", dict(t0=marks["tool:create_apartment_study"] - 0.2, t1=marks["agent:hide"], speed=2.4, cap="Three units. Three clicks. One table."), "b09"))
        T.append(("cut", dict(t0=marks["agent:hide"], t1=marks["end"] - 0.5, speed=1.3, cap="Keep the evidence."), "b10"))
        T.append(("pdf", dict(pages=[1, 2, 3, 10], each=1.1), None))
        T.append(("card", dict(sec=6.5, lines=["“This is the report a sustainability consultant", "takes four weeks to run, and the model", "has to be kept simple. Not any more.”"], size=54, sub="An architectural assistant at a Singapore practice, on reading the PDF, 3 September 2026"), None))
        T.append(("card", dict(sec=8.5, lines=THESIS, size=54, sub="apartments.senibina.com.sg   A public-interest study by Senibina for apartment living. Singapore now, the region next."), "b11"))
    elif v == "product-first":
        T.append(("cut", dict(t0=marks["screen:analysis"] + 8.0, t1=marks["screen:analysis"] + 13.5, speed=1.0, cap="Will this apartment get the sun you expect?"), "b01"))
        for i, f in enumerate(PRACTICE): T.append(("still", dict(f=f"{PR}/{f}", sec=[3, 2, 2, 2, 1.8, 1.5, 2.2, 1.8, 2.2, 2.2, 2.6][i], cap=PCAPS[i], push=1.0 if "wind" in f else 1.05), "b02" if i == 0 else None))
        for i, s in enumerate(SALES): T.append(("card", dict(sec=[2.2, 2.2, 2.2, 3.4][i], lines=s), "b03" if i == 0 else None))
        T.append(("card", dict(sec=5.5, lines=["Apartment Intelligence"], sub="Version 0, built for the OpenAI WebMCP Challenge, September 2026", size=72), "b04"))
        T.append(("cut", dict(t0=marks["start"] + 1.0, t1=marks["screen:place"] + 1.0, speed=1.1, cap="A real block. A real storey.", pip=2.0), "b05"))
        T.append(("cut", dict(t0=marks["agent:show"] - 0.3, t1=marks["click:confirm"] - 0.3, speed=1.0, cap="An agent can stage a placement. It cannot confirm one."), "b06"))
        T.append(("cut", dict(t0=marks["click:confirm"] - 0.6, t1=marks["screen:analysis"] + 1.2, speed=1.0, cap="That click belongs to a person.", pip=46.0), "b07"))
        T.append(("cut", dict(t0=marks["screen:analysis"] + 1.2, t1=marks["tool:create_apartment_study"] - 0.2, speed=1.2, cap="Radiation, per room. Every number carries its source."), "b08"))
        T.append(("cut", dict(t0=marks["tool:create_apartment_study"] - 0.2, t1=marks["agent:hide"], speed=2.0, cap="Three units. Three clicks. One table."), "b09"))
        T.append(("cut", dict(t0=marks["agent:hide"], t1=marks["end"] - 0.4, speed=1.2, cap="Keep the evidence."), "b10"))
        T.append(("pdf", dict(pages=[1, 2, 3, 7, 10], each=1.3), None))
        T.append(("card", dict(sec=6.5, lines=["“This is the report a sustainability consultant", "takes four weeks to run, and the model", "has to be kept simple. Not any more.”"], size=54, sub="An architectural assistant at a Singapore practice, on reading the PDF, 3 September 2026"), None))
        T.append(("card", dict(sec=9, lines=THESIS, size=54, sub="apartments.senibina.com.sg   A public-interest study by Senibina for apartment living. Singapore now, the region next."), "b11"))
    return T

BEATNAME = {"b01":"question","b02":"practice","b03":"sales","b04":"intro","b05":"block","b06":"agent","b07":"click","b08":"runs","b09":"three","b10":"export","b11":"close"}
def alen(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]))
if V != "editorial":  # the faster cuts use the short practice and sales lines
    BEATNAME["b02"] = "practice-short"; BEATNAME["b03"] = "sales-short"
BEATLEN = {b: alen(f"{BEATS}/{b}-{n}.mp3") for b, n in BEATNAME.items()}
def hold(seg, dur, need):
    """Freeze the last frame so the picture lasts at least as long as its narration plus a breath."""
    if dur >= need: return dur
    tmp = seg + ".hold.mp4"; run(f"ffmpeg -v error -y -i {seg} -vf tpad=stop_mode=clone:stop_duration={need-dur:.3f} -c:v libx264 -pix_fmt yuv420p -r {FPS} {tmp}"); os.replace(tmp, seg); return need
segs, cues, t = [], [], 0.0
for i, (kind, a, beat) in enumerate(timeline(V)):
    out = f"{R}/_c{i:02d}.mp4"
    if kind == "card": card(out, **a); dur = a["sec"]
    elif kind == "still": still(out, **a); dur = a["sec"]
    elif kind == "cut": dur = cut(out, PROD, **a)
    elif kind == "pdf": pdfpages(out, **a); dur = len(a["pages"]) * a["each"]
    if beat and beat not in ("b02", "b03"):  # practice and sales narration runs across several clips, handled by their own lengths
        dur = hold(out, dur, BEATLEN[beat] + 0.35 + 0.7)
    if beat: cues.append((beat, t + 0.35))
    segs.append(out); t += dur
video = f"{R}/_video.mp4"; concat(video, segs); total = t
# audio: beats at cues, music bed at -20 dB with a fade, then loudness-normalised master
inputs = f"-i {video} -i {MUSIC} " + " ".join(f"-i {BEATS}/{b}-{BEATNAME[b]}.mp3" for b, _ in cues)
fc = f"[1:a]atrim=0:{total},afade=t=in:st=0:d=2,afade=t=out:st={total-4}:d=4,volume=0.11[m];"
fc += "".join(f"[{i+2}:a]adelay={int(at*1000)}|{int(at*1000)}[n{i}];" for i, (_, at) in enumerate(cues))
fc += "[m]" + "".join(f"[n{i}]" for i in range(len(cues))) + f"amix=inputs={len(cues)+1}:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
final = f"{D}/renders/apartment-intelligence-demo-{V}.mp4"
run(f"ffmpeg -v error -y {inputs} -filter_complex \"{fc}\" -map 0:v -map \"[a]\" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart -t {total} {final}")
json.dump({"version": V, "total_s": round(total, 2), "cues": cues}, open(f"{R}/cues.json", "w"), indent=1)
print(V, f"{total:.1f}s", final)
