// Product capture for the demo film: 1920x1080 page recording against the live site, red cursor,
// agent console overlay bottom-right, every action stamped into timing.json.
import { chromium } from "playwright"; import fs from "fs"; import path from "path";
const URL = process.env.AI_BASE_URL || "https://apartments.senibina.com.sg";
const OUT = path.resolve(process.argv[2] || "../../video/apartment-intelligence-demo/footage/product");
fs.mkdirSync(OUT, { recursive: true });
const b = await chromium.launch({ channel: "chrome", args: ["--enable-features=WebMCP", "--use-gl=angle"] });
const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, colorScheme: "light", recordVideo: { dir: OUT, size: { width: 1920, height: 1080 } }, acceptDownloads: true });
const p = await ctx.newPage(); const t0 = Date.now(); const marks = []; let createdId = null;
p.on("response", async (r) => { if (r.request().method() === "POST" && /\/api\/studies$/.test(r.url())) { try { const j = await r.json(); createdId = j.study_id ?? createdId; } catch {} } });
const mark = (name, extra = {}) => { marks.push({ t: (Date.now() - t0) / 1000, name, ...extra }); };
const overlay = async () => p.evaluate(() => {
  if (document.getElementById("demo-cursor")) return;
  const s = document.createElement("style"); s.textContent = `
    #demo-cursor{position:fixed;left:0;top:0;width:24px;height:24px;border-radius:50%;border:3px solid #d94b3f;box-shadow:0 0 0 3px #fbfaf6;pointer-events:none;z-index:99999;transform:translate(-50%,-50%);transition:transform .08s}
    #demo-cursor.press{transform:translate(-50%,-50%) scale(.72);background:rgba(217,75,63,.42)}
    #agent{position:fixed;right:24px;bottom:24px;width:560px;max-height:300px;background:#18211d;color:#f5f2e9;font:15px/1.5 "SF Mono",Menlo,monospace;padding:16px 18px;border-radius:3px;box-shadow:0 3px 8px rgba(0,0,0,.18);z-index:99998;opacity:0;transition:opacity .4s;overflow:hidden}
    #agent.on{opacity:1}
    #agent .h{font:600 11px/1 Inter,system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#b9b7ae;margin-bottom:10px}
    #agent .l{white-space:pre-wrap;word-break:break-word}
    #agent .call{color:#f2c230}
    #agent .ok{color:#8fd0a8}
    #agent .no{color:#f08a7a}
    html{scroll-behavior:smooth}`;
  document.head.appendChild(s);
  const c = document.createElement("div"); c.id = "demo-cursor"; document.body.appendChild(c);
  const a = document.createElement("div"); a.id = "agent"; a.innerHTML = '<div class="h">Agent, via WebMCP</div><div class="l" id="agent-log"></div>'; document.body.appendChild(a);
  window.__agentLog = (line, cls) => { const l = document.getElementById("agent-log"); const d = document.createElement("div"); d.className = cls || ""; d.textContent = line; l.appendChild(d); while (l.children.length > 9) l.removeChild(l.firstChild); };
  window.__agentShow = (on) => document.getElementById("agent").classList.toggle("on", on);
  document.addEventListener("mousemove", (e) => { c.style.left = e.clientX + "px"; c.style.top = e.clientY + "px"; });
  document.addEventListener("mousedown", () => c.classList.add("press")); document.addEventListener("mouseup", () => c.classList.remove("press"));
});
const move = async (x, y, steps = 28) => { await p.mouse.move(x, y, { steps }); };
const click = async (loc, name) => { const bb = await loc.boundingBox(); await move(bb.x + bb.width / 2, bb.y + bb.height / 2); await p.waitForTimeout(250); await p.mouse.down(); await p.waitForTimeout(90); await p.mouse.up(); mark("click:" + name); };
const log = (line, cls) => p.evaluate(([l, c]) => window.__agentLog(l, c), [line, cls]);
const agent = async (name, input) => {
  await log(`${name}(${JSON.stringify(input)})`, "call"); mark("tool:" + name, { input });
  const r = await p.evaluate(([n, i]) => window.__aiTools.find(t => t.name === n).execute(i).catch(e => ({ thrown: String(e) })), [name, input]);
  const short = r.refused ? `refused: ${r.reason.split(":")[0]}` : r.thrown ? r.thrown.slice(0, 90) : r.mode === "survey" ? `survey, unconfirmed: avg ${r.radiation?.avg} kWh/m2` : r.digest ? `analysed, digest ${r.digest.slice(0, 12)}, avg ${r.radiation?.avg} kWh/m2` : r.study_id ? `study ${r.study_id}` : r.state ? `${r.state}` : JSON.stringify(r).slice(0, 90);
  await log(`  -> ${short}`, r.refused || r.thrown ? "no" : "ok"); mark("reply:" + name, { reply: short });
  return r;
};

await p.goto(URL); await p.waitForFunction(() => window.__aiTools?.length === 9); await overlay(); await move(960, 540, 5);
mark("start"); await p.waitForTimeout(2500);
// beat 5: human
await move(700, 700, 20); await p.waitForTimeout(300);
await click(p.getByRole("button", { name: /SkyVille @ Dawson/ }), "tile"); await p.waitForTimeout(1600);
await click(p.locator("#storey"), "storey"); await p.keyboard.press("Meta+a"); await p.keyboard.type("30", { delay: 120 }); mark("typed:storey"); await p.waitForTimeout(500);
await click(p.getByRole("button", { name: "Start the study" }), "start"); await p.getByRole("heading", { name: /Choose the wing/ }).waitFor(); mark("screen:place"); await p.waitForTimeout(2200);
// beat 6: agent
await p.evaluate(() => window.__agentShow(true)); mark("agent:show"); await p.waitForTimeout(700);
const studyId = createdId;
await agent("get_study_state", { study_id: studyId });
await p.waitForTimeout(800);
await agent("propose_unit_placement", { study_id: studyId, facade: "SE", stack_position: "inner", variant: "A" }); await p.waitForTimeout(1800);
await agent("run_solar_analysis", { study_id: studyId, grid_spacing_m: 0.25 }); await p.waitForTimeout(2200);
// beat 7: human click
await click(p.getByTestId("confirm-button"), "confirm"); await p.getByRole("heading", { name: /Sun, shade/ }).waitFor(); mark("screen:analysis"); await p.waitForTimeout(1500);
// beat 8: agent runs
await agent("run_solar_analysis", { study_id: studyId, grid_spacing_m: 0.25 }); mark("heat:on"); await p.waitForTimeout(1200);
await click(p.getByRole("button", { name: "Apartment", exact: true }), "apartment"); await p.waitForTimeout(2200);
await click(p.getByRole("button", { name: "Massing" }), "massing-off"); await p.waitForTimeout(2200);
await click(p.getByRole("button", { name: "Massing" }), "massing-on"); await p.waitForTimeout(600);
const ev = await agent("explain_evidence", { study_id: studyId, item: "radiation" }); await p.waitForTimeout(2600);
// beat 9: survey mode, three units in a row, no click
const rows = [];
for (const u of [{ storey: 12, facade: "NE", stack_position: "end", variant: "A" }, { storey: 30, facade: "SE", stack_position: "inner", variant: "B" }, { storey: 44, facade: "SW", stack_position: "end", variant: "C" }]) {
  const r = await agent("survey_unit", { address: "87 Dawson Road", ...u, grid_spacing_m: 0.5 }); rows.push({ ...u, avg: r.radiation?.avg }); await p.waitForTimeout(700);
}
await log(`survey table: NE tip s12 ${rows[0].avg} | SE core s30 ${rows[1].avg} | SW tip s44 ${rows[2].avg} kWh/m2, all unconfirmed`, "ok"); mark("table"); await p.waitForTimeout(3200);
// beat 10: export PDF
await p.evaluate(() => window.__agentShow(false)); mark("agent:hide");
await click(p.getByRole("button", { name: "Keep the evidence", exact: true }), "keep"); await p.waitForTimeout(1200);
const dl = p.waitForEvent("download", { timeout: 60000 });
await click(p.getByRole("button", { name: /^Export/ }), "export"); const d = await dl; await d.saveAs(path.join(OUT, "report.pdf")); mark("pdf:saved"); await p.waitForTimeout(1500);
mark("end");
const video = p.video(); await ctx.close(); const vp = await video.path(); fs.renameSync(vp, path.join(OUT, "product.webm"));
fs.writeFileSync(path.join(OUT, "timing.json"), JSON.stringify({ url: URL, marks, rows }, null, 1));
await b.close(); console.log("captured", marks.length, "marks; end at", marks.at(-1).t, "s");
