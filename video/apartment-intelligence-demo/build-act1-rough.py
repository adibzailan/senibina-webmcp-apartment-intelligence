"""Act one rough cut: twelve stills with a slow push, phrase captions, narration. No music yet."""
import subprocess, os, shlex
D = "video/apartment-intelligence-demo"
F = f"{D}/footage/practice"; FONT_S = f"{D}/footage/fonts/snba-serif-regular.ttf"; FONT_I = f"{D}/footage/fonts/snba-sans-serif-medium.ttf"
NARR = f"{D}/footage/audio/tts_In_pr_20260903_190959.mp3"
OUT = f"{D}/renders/act1-rough.mp4"
W, H, FPS = 1920, 1080, 30
# (file, seconds, caption); the opening card is drawn, not a file
shots = [
    (None, 5.0, None),
    ("wall-panorama.jpg", 5.0, "How architects answer it."),
    ("wall-front.jpg", 3.0, "A wall of trace."),
    ("desk-rhino-grasshopper.jpg", 3.0, "Modelled."),
    ("light-and-shadow-sheet.jpg", 3.0, "Light, room by room."),
    ("sightlines-sheet.jpg", 2.5, "Sightlines."),
    ("wind-and-temperature-site.jpg", 2.0, "Wind and heat."),
    ("room-radiation-l1-l3-print.jpg", 3.0, "Radiation, floor by floor."),
    ("exterior-walls-study.jpg", 2.5, "Radiation, floor by floor."),
    ("radiation-benefit-trace.jpg", 3.0, "Drawn over, argued over."),
    ("sunlight-hours-june.jpg", 3.0, "Hours of sun, June."),
    ("sunlight-hours-june-annotated.jpg", 3.5, "Drawn over, argued over."),
]
def esc(t): return t.replace("'", "\\'").replace(":", "\\:")
cap = lambda t: (f",drawtext=fontfile={FONT_I}:text='{esc(t)}':fontsize=34:fontcolor=0x18211d:box=1:boxcolor=0xf5f2e9@0.94:boxborderw=16"
                 f":x=(w-text_w)/2:y=h-120") if t else ""
segs = []
for i, (f, sec, t) in enumerate(shots):
    frames = int(sec * FPS); seg = f"{D}/renders/_seg{i:02d}.mp4"
    if f is None:
        vf = (f"drawtext=fontfile={FONT_S}:text='Will this apartment get':fontsize=96:fontcolor=0x18211d:x=(w-text_w)/2:y=h/2-110,"
              f"drawtext=fontfile={FONT_S}:text='the sun you expect?':fontsize=96:fontcolor=0x18211d:x=(w-text_w)/2:y=h/2+10,fade=t=in:st=0:d=0.8,fade=t=out:st={sec-0.6}:d=0.6")
        cmd = f"ffmpeg -v error -y -f lavfi -i color=c=0xf5f2e9:s={W}x{H}:r={FPS}:d={sec} -vf \"{vf}\" -c:v libx264 -pix_fmt yuv420p -r {FPS} {seg}"
    else:
        push = 1.04 if "wind" not in f else 1.0
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='1+({push}-1)*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
              f"eq=saturation=0.92:contrast=1.02{cap(t)}")
        cmd = f"ffmpeg -v error -y -loop 1 -t {sec} -i {shlex.quote(F+'/'+f)} -vf \"{vf}\" -frames:v {frames} -c:v libx264 -pix_fmt yuv420p -r {FPS} {seg}"
    subprocess.run(cmd, shell=True, check=True); segs.append(seg)
with open(f"{D}/renders/_list.txt", "w") as fh:
    for s in segs: fh.write(f"file '{os.path.abspath(s)}'\n")
total = sum(s[1] for s in shots)
subprocess.run(f"ffmpeg -v error -y -f concat -safe 0 -i {D}/renders/_list.txt -i {NARR} -filter_complex \"[1:a]adelay=4600|4600,volume=1.0[a]\" -map 0:v -map \"[a]\" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 160k -t {total} -movflags +faststart {OUT}", shell=True, check=True)
for s in segs: os.remove(s)
print("built", OUT, f"{total:.1f}s")
