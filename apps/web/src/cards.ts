/** Presentation-only PNG/PDF renders of the server's digest-bound SVG cards (browser rasterisation). */
import { PDFDocument, PDFPage, StandardFonts, rgb } from "pdf-lib";
import { zipSync } from "fflate";

export async function svgToPng(svgText: string, scale = 1): Promise<Blob> {
  const blob = new Blob([svgText], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  try {
    const img = new Image();
    await new Promise<void>((res, rej) => { img.onload = () => res(); img.onerror = () => rej(new Error("svg decode")); img.src = url; });
    const c = document.createElement("canvas"); c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
    const g = c.getContext("2d")!; g.fillStyle = "#fbfaf6"; g.fillRect(0, 0, c.width, c.height); g.drawImage(img, 0, 0, c.width, c.height);
    return await new Promise<Blob>((res) => c.toBlob((b) => res(b!), "image/png"));
  } finally { URL.revokeObjectURL(url); }
}

export interface PdfMeta { development: string; block: string; storey: number; placement: string; method: string; weather: string; generated: string }

const PAPER = rgb(0.961, 0.949, 0.914), WHITE = rgb(0.984, 0.98, 0.965), INK = rgb(0.094, 0.129, 0.114), MUTED = rgb(0.373, 0.4, 0.373), RULE = rgb(0.725, 0.718, 0.682);
const PW = 1190, PH = 1684, M = 96; // A4 at 2x, 96 pt margins

/** Split the server's stacked cards.svg into one SVG per card, using the translate offsets the server wrote. */
function splitCards(svgText: string): string[] {
  const doc = new DOMParser().parseFromString(svgText, "image/svg+xml");
  const root = doc.documentElement; const W = Number(root.getAttribute("width")); const H = Number(root.getAttribute("height"));
  const groups = Array.from(root.children).filter((c) => c.tagName === "g") as SVGGElement[];
  const ys = groups.map((g) => Number(/translate\(0,(\d+)\)/.exec(g.getAttribute("transform") || "")?.[1] ?? 0));
  return groups.map((g, i) => {
    const h = (i + 1 < ys.length ? ys[i + 1] - 16 : H) - ys[i];
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${h}" viewBox="0 0 ${W} ${h}">${g.innerHTML}</svg>`;
  });
}

export async function cardsPdf(svgText: string, views: { apartment: string; tower: string } | null, digest: string, meta: PdfMeta): Promise<Blob> {
  const pdf = await PDFDocument.create();
  const sans = await pdf.embedFont(StandardFonts.Helvetica), serif = await pdf.embedFont(StandardFonts.TimesRoman);
  const short = digest.slice(0, 16);
  const masthead = (p: PDFPage, paper: boolean) => {
    p.drawRectangle({ x: 0, y: 0, width: PW, height: PH, color: paper ? PAPER : WHITE });
    p.drawText("Apartment Intelligence", { x: M, y: PH - M - 6, size: 30, font: serif, color: INK });
    p.drawLine({ start: { x: M, y: PH - M - 24 }, end: { x: PW - M, y: PH - M - 24 }, thickness: 1, color: INK });
  };
  const footer = (p: PDFPage, page: number, total: number) => {
    p.drawLine({ start: { x: M, y: M + 34 }, end: { x: PW - M, y: M + 34 }, thickness: 0.6, color: RULE });
    p.drawText(`${meta.development}, Block ${meta.block}, Storey ${meta.storey}. Result digest ${short}.`, { x: M, y: M + 12, size: 11, font: sans, color: MUTED });
    const n = `${page} / ${total}`; p.drawText(n, { x: PW - M - sans.widthOfTextAtSize(n, 11), y: M + 12, size: 11, font: sans, color: MUTED });
  };
  const wrap = (text: string, size: number, font: any, width: number) => {
    const words = text.split(" "); const lines: string[] = []; let cur = "";
    for (const w of words) { const t = cur ? cur + " " + w : w; if (font.widthOfTextAtSize(t, size) > width && cur) { lines.push(cur); cur = w; } else cur = t; }
    if (cur) lines.push(cur); return lines;
  };

  // cover
  const cover = pdf.addPage([PW, PH]); masthead(cover, true);
  let y = PH - 420;
  for (const line of wrap("Will this apartment get the sun you expect?", 78, serif, PW - 2 * M)) { cover.drawText(line, { x: M, y, size: 78, font: serif, color: INK }); y -= 88; }
  y -= 40;
  cover.drawText(meta.development, { x: M, y, size: 34, font: serif, color: INK }); y -= 46;
  cover.drawText(`Block ${meta.block}, Storey ${meta.storey}`, { x: M, y, size: 20, font: sans, color: MUTED }); y -= 30;
  cover.drawText(meta.placement, { x: M, y, size: 20, font: sans, color: MUTED }); y -= 60;
  const rows: [string, string][] = [["Generated", meta.generated], ["Method", meta.method], ["Weather file", meta.weather.slice(0, 16)], ["Result digest", digest]];
  for (const [k, v] of rows) { cover.drawLine({ start: { x: M, y: y + 22 }, end: { x: PW - M, y: y + 22 }, thickness: 0.6, color: RULE }); cover.drawText(k, { x: M, y, size: 13, font: sans, color: MUTED }); cover.drawText(v, { x: M + 220, y, size: 13, font: sans, color: INK }); y -= 34; }
  cover.drawText("A public-interest study by Senibina for apartment living. Singapore now, the region next.", { x: M, y: M + 32, size: 13, font: serif, color: MUTED });
  cover.drawText("Version 0, built for the OpenAI WebMCP Challenge, September 2026.", { x: M, y: M + 12, size: 13, font: sans, color: MUTED });

  const pages: PDFPage[] = [];
  // site and unit
  if (views) {
    const p = pdf.addPage([PW, PH]); masthead(p, false); pages.push(p);
    p.drawText("Site and unit", { x: M, y: PH - M - 80, size: 34, font: serif, color: INK });
    const place = async (dataUrl: string, top: number, caption: string) => {
      const png = await pdf.embedPng(dataUrl);
      const s = Math.min((PW - 2 * M) / png.width, 560 / png.height);
      p.drawImage(png, { x: M, y: top - png.height * s, width: png.width * s, height: png.height * s });
      p.drawText(caption, { x: M, y: top - png.height * s - 20, size: 13, font: sans, color: MUTED });
      return top - png.height * s - 56;
    };
    let top = PH - M - 110;
    top = await place(views.apartment, top, "The confirmed apartment on its storey, room by room, with the massing switched off.");
    await place(views.tower, top, "The tower and its neighbours, with the apartment in place.");
  }
  // one card at a time; a card that does not fit the remaining page starts a new page
  let page: PDFPage | null = null; let cursor = 0;
  for (const cardSvg of splitCards(svgText)) {
    const png = await pdf.embedPng(await (await svgToPng(cardSvg, 2)).arrayBuffer());
    const s = (PW - 2 * M) / png.width; const h = png.height * s;
    if (!page || cursor - h < M + 60) { page = pdf.addPage([PW, PH]); masthead(page, false); pages.push(page); cursor = PH - M - 60; }
    page.drawImage(png, { x: M, y: cursor - h, width: PW - 2 * M, height: h });
    cursor -= h + 32;
  }
  // back cover
  const back = pdf.addPage([PW, PH]); back.drawRectangle({ x: 0, y: 0, width: PW, height: PH, color: PAPER });
  back.drawLine({ start: { x: M, y: PH / 2 + 90 }, end: { x: PW - M, y: PH / 2 + 90 }, thickness: 1, color: INK });
  back.drawText("Apartment Intelligence", { x: M, y: PH / 2 + 40, size: 34, font: serif, color: INK });
  back.drawText("A public-interest study by Senibina for apartment living. Singapore now, the region next.", { x: M, y: PH / 2, size: 18, font: serif, color: MUTED });
  y = PH / 2 - 60;
  const thesis = "Built with Ladybug and Radiance, the same daylight engines architects use in practice, so the study a practice would run for a client is now open to the people who live there.";
  for (const line of wrap(thesis, 13, sans, PW - 2 * M)) { back.drawText(line, { x: M, y, size: 13, font: sans, color: INK }); y -= 19; }
  y -= 14;
  const legal = "Footprints and storey counts: HDB via data.gov.sg, Singapore Open Data Licence v1.0. No endorsement by HDB, OneMap or the Singapore Government. Not a valuation, compliance or daylight certification. Upper-storey plate inferred from the ground outline; openings assumed unless published. PDF and PNG are presentation renders of the digest-bound cards.";
  for (const line of wrap(legal, 13, sans, PW - 2 * M)) { back.drawText(line, { x: M, y, size: 13, font: sans, color: MUTED }); y -= 19; }
  back.drawText("Version 0, built for the OpenAI WebMCP Challenge, September 2026.", { x: M, y: M + 32, size: 13, font: sans, color: MUTED });
  back.drawText("senibina.com.sg", { x: M, y: M + 12, size: 13, font: sans, color: INK });
  const total = pages.length + 2;
  pages.forEach((p, i) => footer(p, i + 2, total));
  return new Blob([(await pdf.save()) as unknown as BlobPart], { type: "application/pdf" });
}

export function zipBlob(files: Record<string, Uint8Array>): Blob {
  return new Blob([zipSync(files, { level: 6 }) as unknown as BlobPart], { type: "application/zip" });
}

export function download(name: string, blob: Blob) {
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
