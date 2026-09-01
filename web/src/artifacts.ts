import { zipSync } from 'fflate'
import { PDFDocument } from 'pdf-lib'


export const CARD_WIDTH = 1600
export const CARD_HEIGHT = 2400
export const CARD_NAMES = ['site-unit', 'sunpath', 'shadow', 'solar-access', 'radiation'] as const
type CardName = typeof CARD_NAMES[number]

export function exportManifest(digest: string) {
  return { product: 'Apartment Intelligence', digest, cards: CARD_NAMES, width: CARD_WIDTH, height: CARD_HEIGHT }
}

export function cardNarrative(name: CardName, result: any) {
  const content = {
    'site-unit': { method: 'Official HDB footprint extruded using inferred 3.0 m floor-to-floor height.', limitations: 'Facade, unit zone and openings are resident-confirmed approximations.' },
    sunpath: { method: 'Ladybug solar positions for equinoxes and solstices in Singapore time.', limitations: 'Paths describe the sun; context obstruction is shown in the other studies.' },
    shadow: { method: 'Ladybug Geometry rays from the confirmed window grid at 09:00, 12:00 and 15:00.', limitations: 'Three representative instants on 21 March, not a full-year animation.' },
    'solar-access': { method: 'Direct-sun hours sampled every 30 minutes on four seasonal dates.', limitations: 'Hours are averaged across the 16 × 8 confirmed window sensor grid.' },
    radiation: { method: '12 monthly representative days: occluded EPW DNI × incidence plus isotropic DHI × 0.5.', limitations: result.radiation?.limitations?.join('; ') || 'no inter-reflection; diffuse sky is unobstructed' },
  }
  return content[name]
}

function title(ctx: CanvasRenderingContext2D, name: CardName, result: any) {
  ctx.fillStyle = '#f2efe7'; ctx.fillRect(0, 0, CARD_WIDTH, CARD_HEIGHT)
  ctx.fillStyle = '#17231e'; ctx.font = '700 104px Georgia'; ctx.fillText('Apartment Intelligence', 110, 170)
  ctx.fillStyle = '#d95c37'; ctx.font = '700 54px system-ui'; ctx.fillText(name.replaceAll('-', ' ').toUpperCase(), 110, 275)
  ctx.strokeStyle = '#17231e'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(110, 325); ctx.lineTo(1490, 325); ctx.stroke()
  ctx.font = '500 34px system-ui'; ctx.fillStyle = '#17231e'; ctx.fillText('87 Dawson Road · Storey 30 · Dawson, Singapore', 110, 390)
  const narrative = cardNarrative(name, result)
  ctx.font = '30px system-ui'; wrap(ctx, narrative.method, 110, 1930, 1380, 44)
  ctx.fillStyle = '#d95c37'; ctx.font = '700 26px ui-monospace, monospace'; ctx.fillText('METHOD & LIMITATIONS', 110, 1855)
  ctx.fillStyle = '#17231e'; ctx.font = '28px system-ui'; wrap(ctx, narrative.limitations, 110, 2070, 1380, 42)
  ctx.strokeStyle = '#17231e'; ctx.beginPath(); ctx.moveTo(110, 2190); ctx.lineTo(1490, 2190); ctx.stroke()
  ctx.font = '24px ui-monospace, monospace'; ctx.fillText(`RESULT ${result.digest}`, 110, 2260)
  ctx.fillText('SOURCED CONTEXT · INFERRED HEIGHT · HUMAN-CONFIRMED UNIT', 110, 2320)
  ctx.fillText('CONSUMER DECISION SUPPORT · NOT PROFESSIONAL CERTIFICATION', 110, 2370)
}

function wrap(ctx: CanvasRenderingContext2D, value: string, x: number, y: number, width: number, lineHeight: number) {
  let line = ''
  for (const word of value.split(' ')) {
    const next = `${line}${word} `
    if (ctx.measureText(next).width > width && line) { ctx.fillText(line, x, y); line = `${word} `; y += lineHeight } else line = next
  }
  ctx.fillText(line, x, y)
}

function drawSite(ctx: CanvasRenderingContext2D) {
  ctx.fillStyle = '#dbe4db'; ctx.fillRect(110, 490, 1380, 1180)
  for (let row = 0; row < 4; row++) for (let col = 0; col < 5; col++) {
    ctx.save(); ctx.translate(250 + col * 260, 650 + row * 240); ctx.rotate((row - col) * .07)
    ctx.fillStyle = row === 2 && col === 2 ? '#d95c37' : '#eee8dc'; ctx.strokeStyle = '#17231e'; ctx.lineWidth = 3
    ctx.fillRect(-80, -55, 160, 110); ctx.strokeRect(-80, -55, 160, 110); ctx.restore()
  }
  ctx.strokeStyle = '#17231e'; ctx.lineWidth = 10; ctx.strokeRect(830, 1090, 180, 100)
  ctx.fillStyle = '#17231e'; ctx.font = '700 32px ui-monospace, monospace'; ctx.fillText('CONFIRMED WINDOW ZONE', 790, 1260)
}

function drawSunpath(ctx: CanvasRenderingContext2D, result: any) {
  const cx = 800, cy = 1480, radius = 560
  ctx.strokeStyle = '#bbb8ae'; ctx.lineWidth = 3
  for (const scale of [.25, .5, .75, 1]) { ctx.beginPath(); ctx.arc(cx, cy, radius * scale, Math.PI, Math.PI * 2); ctx.stroke() }
  result.sunpath.forEach((path: any, index: number) => {
    ctx.strokeStyle = ['#d95c37', '#17231e', '#6c8b78', '#d0a533'][index]; ctx.lineWidth = 12; ctx.beginPath()
    path.samples.forEach((sample: any, point: number) => {
      const x = cx + Math.cos((sample.azimuth - 90) * Math.PI / 180) * radius * (1 - sample.altitude / 100)
      const y = cy - Math.sin((sample.azimuth - 90) * Math.PI / 180) * radius * (1 - sample.altitude / 100)
      point ? ctx.lineTo(x, y) : ctx.moveTo(x, y)
    }); ctx.stroke(); ctx.fillStyle = ctx.strokeStyle; ctx.font = '28px ui-monospace, monospace'; ctx.fillText(path.date.slice(5), 190 + index * 320, 540)
  })
}

function drawShadow(ctx: CanvasRenderingContext2D, result: any) {
  result.shadow.samples.forEach((sample: any, index: number) => {
    const x = 110 + index * 470
    ctx.fillStyle = '#dbe4db'; ctx.fillRect(x, 540, 420, 1030)
    ctx.fillStyle = '#17231e'; ctx.font = '700 64px Georgia'; ctx.fillText(sample.time, x + 38, 650)
    ctx.fillStyle = '#d95c37'; ctx.fillRect(x + 38, 1400 - 650 * sample.sunlit_fraction, 344, 650 * sample.sunlit_fraction)
    ctx.strokeStyle = '#17231e'; ctx.strokeRect(x + 38, 750, 344, 650)
    ctx.fillStyle = '#17231e'; ctx.font = '30px ui-monospace, monospace'; ctx.fillText(`${Math.round(sample.sunlit_fraction * 100)}% sunlit`, x + 38, 1470)
  })
}

function drawAccess(ctx: CanvasRenderingContext2D, result: any) {
  Object.entries(result.solar_access).forEach(([date, study]: any, index) => {
    const y = 570 + index * 270
    ctx.fillStyle = '#17231e'; ctx.font = '700 36px ui-monospace, monospace'; ctx.fillText(date, 110, y)
    ctx.fillStyle = '#dbe4db'; ctx.fillRect(500, y - 50, 900, 76)
    ctx.fillStyle = '#d95c37'; ctx.fillRect(500, y - 50, study.total_hours / 12 * 900, 76)
    ctx.font = '700 42px Georgia'; ctx.fillStyle = '#17231e'; ctx.fillText(`${study.total_hours.toFixed(1)} h`, 500, y + 100)
  })
}

function drawRadiation(ctx: CanvasRenderingContext2D, result: any) {
  const values = result.radiation.sensor_values_kwh_m2
  const min = result.radiation.minimum_kwh_m2, max = result.radiation.maximum_kwh_m2
  for (let row = 0; row < 8; row++) for (let col = 0; col < 16; col++) {
    const ratio = max === min ? .5 : (values[row * 16 + col] - min) / (max - min)
    ctx.fillStyle = `hsl(${45 - ratio * 33} 78% ${70 - ratio * 25}%)`
    ctx.fillRect(110 + col * 86, 570 + (7 - row) * 120, 82, 116)
  }
  ctx.fillStyle = '#17231e'; ctx.font = '700 48px Georgia'; ctx.fillText(`Average ${result.radiation.average_kwh_m2} kWh/m²`, 110, 1650)
  ctx.font = '28px ui-monospace, monospace'; ctx.fillText(`${min} MIN`, 110, 1730); ctx.fillText(`${max} MAX`, 1310, 1730)
}

function card(name: CardName, result: any): HTMLCanvasElement {
  const canvas = document.createElement('canvas'); canvas.width = CARD_WIDTH; canvas.height = CARD_HEIGHT
  const ctx = canvas.getContext('2d')!; title(ctx, name, result)
  if (name === 'site-unit') drawSite(ctx)
  else if (name === 'sunpath') drawSunpath(ctx, result)
  else if (name === 'shadow') drawShadow(ctx, result)
  else if (name === 'solar-access') drawAccess(ctx, result)
  else drawRadiation(ctx, result)
  return canvas
}

const blob = (canvas: HTMLCanvasElement) => new Promise<Blob>((resolve, reject) =>
  canvas.toBlob(value => value ? resolve(value) : reject(new Error('PNG_FAILED')), 'image/png'))

export async function exportBundle(result: any, model: Blob) {
  const cards = await Promise.all(CARD_NAMES.map(async name => [name, await blob(card(name, result))] as const))
  const pdf = await PDFDocument.create()
  for (const [, png] of cards) {
    const image = await pdf.embedPng(await png.arrayBuffer())
    const page = pdf.addPage([CARD_WIDTH, CARD_HEIGHT]); page.drawImage(image, { x: 0, y: 0, width: CARD_WIDTH, height: CARD_HEIGHT })
  }
  const files: Record<string, Uint8Array> = {
    'manifest.json': new TextEncoder().encode(JSON.stringify({ ...exportManifest(result.digest), method_version: result.method_version, weather: result.weather }, null, 2)),
    'apartment-intelligence.pdf': await pdf.save(),
    'apartment-intelligence.3dm': new Uint8Array(await model.arrayBuffer()),
  }
  for (const [name, png] of cards) files[`${name}.png`] = new Uint8Array(await png.arrayBuffer())
  return new Blob([zipSync(files)], { type: 'application/zip' })
}
