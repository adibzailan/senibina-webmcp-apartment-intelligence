/** Presentation-only PNG/PDF renders of the server's digest-bound SVG cards (browser rasterisation). */
import { PDFDocument, StandardFonts } from "pdf-lib";
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

export async function cardsPdf(svgText: string, sceneDataUrl: string | null, digest: string): Promise<Blob> {
  const pdf = await PDFDocument.create();
  const font = await pdf.embedFont(StandardFonts.Helvetica);
  if (sceneDataUrl) {
    const png = await pdf.embedPng(await (await fetch(sceneDataUrl)).arrayBuffer());
    const p = pdf.addPage([1600, 2400]);
    p.drawText("Site & Unit", { x: 80, y: 2280, size: 48, font });
    const s = Math.min(1440 / png.width, 1800 / png.height);
    p.drawImage(png, { x: 80, y: 300, width: png.width * s, height: png.height * s });
    p.drawText(`digest ${digest}`, { x: 80, y: 120, size: 18, font });
  }
  const png = await pdf.embedPng(await (await svgToPng(svgText, 2)).arrayBuffer());
  const pagesNeeded = Math.ceil(png.height / (png.width * 1.5));
  for (let i = 0; i < pagesNeeded; i++) {
    const p = pdf.addPage([1600, 2400]);
    const s = 1440 / png.width;
    p.drawImage(png, { x: 80, y: 2280 - png.height * s + i * png.width * 1.5 * s, width: png.width * s, height: png.height * s });
    p.drawRectangle({ x: 0, y: 0, width: 1600, height: 160, color: undefined as any, opacity: 0 });
    p.drawText(`Apartment Intelligence evidence cards · presentation render of cards.svg · digest ${digest}`, { x: 80, y: 100, size: 16, font });
  }
  return new Blob([(await pdf.save()) as unknown as BlobPart], { type: "application/pdf" });
}

export function zipBlob(files: Record<string, Uint8Array>): Blob {
  return new Blob([zipSync(files, { level: 6 }) as unknown as BlobPart], { type: "application/zip" });
}

export function download(name: string, blob: Blob) {
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
