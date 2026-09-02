import { zipSync } from 'fflate'
import { PDFDocument } from 'pdf-lib'
import { renderSiteEvidence } from './sceneRender'


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
  ctx.fillStyle = '#f5f2e9'; ctx.fillRect(0, 0, CARD_WIDTH, CARD_HEIGHT)
  ctx.fillStyle = '#18211d'; ctx.font = '650 28px Inter'; ctx.fillText('AI', 110, 110)
  ctx.font = '550 30px Inter'; ctx.fillText('Apartment Intelligence', 165, 110)
  ctx.textAlign = 'right'; ctx.font = '500 24px Inter'; ctx.fillStyle = '#5f665f'; ctx.fillText('87 Dawson Road · Storey 30', 1490, 110); ctx.textAlign = 'left'
  ctx.strokeStyle = '#18211d'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(110, 145); ctx.lineTo(1490, 145); ctx.stroke()
  ctx.fillStyle = '#c8472d'; ctx.font = '650 24px Inter'; ctx.fillText(`STUDY ${String(CARD_NAMES.indexOf(name) + 1).padStart(2, '0')} / 05`, 110, 235)
  ctx.fillStyle = '#18211d'; ctx.font = '500 118px Newsreader'; ctx.fillText(name.replaceAll('-', ' '), 110, 350)
  ctx.font = '500 34px Newsreader'; ctx.fillStyle = '#5f665f'; ctx.fillText('Dawson precinct · Singapore · deterministic consumer study', 110, 418)
  const narrative = cardNarrative(name, result)
  ctx.strokeStyle = '#b9b7ae'; ctx.beginPath(); ctx.moveTo(110, 1835); ctx.lineTo(1490, 1835); ctx.stroke()
  ctx.fillStyle = '#c8472d'; ctx.font = '650 22px Inter'; ctx.fillText('Method', 110, 1895)
  ctx.fillStyle = '#18211d'; ctx.font = '30px Newsreader'; wrap(ctx, narrative.method, 330, 1895, 1160, 42)
  ctx.fillStyle = '#c8472d'; ctx.font = '650 22px Inter'; ctx.fillText('Limit', 110, 2045)
  ctx.fillStyle = '#18211d'; ctx.font = '29px Newsreader'; wrap(ctx, narrative.limitations, 330, 2045, 1160, 41)
  ctx.strokeStyle = '#18211d'; ctx.beginPath(); ctx.moveTo(110, 2190); ctx.lineTo(1490, 2190); ctx.stroke()
  ctx.font = '21px Inter'; ctx.fillStyle = '#5f665f'; ctx.fillText(`Result ${result.digest}`, 110, 2250)
  ctx.fillText('Sourced context · inferred height · human-confirmed unit', 110, 2310)
  ctx.fillText('Consumer decision support · not professional certification', 110, 2360)
}

function wrap(ctx: CanvasRenderingContext2D, value: string, x: number, y: number, width: number, lineHeight: number) {
  let line = ''
  for (const word of value.split(' ')) {
    const next = `${line}${word} `
    if (ctx.measureText(next).width > width && line) { ctx.fillText(line, x, y); line = `${word} `; y += lineHeight } else line = next
  }
  ctx.fillText(line, x, y)
}

function drawSite(ctx: CanvasRenderingContext2D, studyPackage: any) {
  if (!studyPackage?.context || !studyPackage?.study) throw new Error('SITE_CONTEXT_REQUIRED')
  ctx.drawImage(renderSiteEvidence(studyPackage.context, studyPackage.study, 1380, 1180), 110, 490, 1380, 1180)
}

function drawSunpath(ctx: CanvasRenderingContext2D, result: any) {
  const cx = 800, cy = 1480, radius = 560
  ctx.strokeStyle = '#bbb8ae'; ctx.lineWidth = 3
  for (const scale of [.25, .5, .75, 1]) { ctx.beginPath(); ctx.arc(cx, cy, radius * scale, Math.PI, Math.PI * 2); ctx.stroke() }
  result.sunpath.forEach((path: any, index: number) => {
    ctx.strokeStyle = ['#d7a900', '#f2c230', '#b18b08', '#e5b72a'][index]; ctx.lineWidth = 10; ctx.beginPath()
    path.samples.forEach((sample: any, point: number) => {
      const x = cx + Math.cos((sample.azimuth - 90) * Math.PI / 180) * radius * (1 - sample.altitude / 100)
      const y = cy - Math.sin((sample.azimuth - 90) * Math.PI / 180) * radius * (1 - sample.altitude / 100)
      point ? ctx.lineTo(x, y) : ctx.moveTo(x, y)
    }); ctx.stroke(); ctx.fillStyle = ctx.strokeStyle; ctx.font = '24px Inter'; ctx.fillText(path.date.slice(5), 190 + index * 320, 540)
  })
}

function drawShadow(ctx: CanvasRenderingContext2D, result: any) {
  result.shadow.samples.forEach((sample: any, index: number) => {
    const x = 110 + index * 470
    ctx.fillStyle = '#d9ddd5'; ctx.fillRect(x, 540, 420, 1030)
    ctx.fillStyle = '#18211d'; ctx.font = '550 64px Newsreader'; ctx.fillText(sample.time, x + 38, 650)
    ctx.fillStyle = '#f2c230'; ctx.fillRect(x + 38, 1400 - 650 * sample.sunlit_fraction, 344, 650 * sample.sunlit_fraction)
    ctx.strokeStyle = '#18211d'; ctx.strokeRect(x + 38, 750, 344, 650)
    ctx.fillStyle = '#18211d'; ctx.font = '30px Inter'; ctx.fillText(`${Math.round(sample.sunlit_fraction * 100)}% sunlit`, x + 38, 1470)
  })
}

function drawAccess(ctx: CanvasRenderingContext2D, result: any) {
  Object.entries(result.solar_access).forEach(([date, study]: any, index) => {
    const y = 570 + index * 270
    ctx.fillStyle = '#18211d'; ctx.font = '600 30px Inter'; ctx.fillText(date, 110, y)
    ctx.fillStyle = '#45534d'; ctx.fillRect(500, y - 50, 900, 76)
    ctx.fillStyle = '#f2c230'; ctx.fillRect(500, y - 50, study.total_hours / 12 * 900, 76)
    ctx.font = '550 46px Newsreader'; ctx.fillStyle = '#18211d'; ctx.fillText(`${study.total_hours.toFixed(1)} h`, 500, y + 100)
  })
}

function drawRadiation(ctx: CanvasRenderingContext2D, result: any) {
  const values = result.radiation.sensor_values_kwh_m2
  const min = result.radiation.minimum_kwh_m2, max = result.radiation.maximum_kwh_m2
  for (let row = 0; row < 8; row++) for (let col = 0; col < 16; col++) {
    const ratio = max === min ? .5 : (values[row * 16 + col] - min) / (max - min)
    ctx.fillStyle = radiationCanvasColour(ratio)
    ctx.fillRect(110 + col * 86, 570 + (7 - row) * 120, 82, 116)
  }
  ctx.fillStyle = '#18211d'; ctx.font = '550 50px Newsreader'; ctx.fillText(`Average ${result.radiation.average_kwh_m2} kWh/m²`, 110, 1650)
  ctx.font = '24px Inter'; ctx.fillText(`${min} minimum`, 110, 1730); ctx.fillText(`${max} maximum`, 1280, 1730)
}

function radiationCanvasColour(ratio: number) {
  const stops = [[24, 63, 90], [43, 140, 134], [227, 201, 70], [200, 71, 45]]
  const scaled = Math.min(.999, Math.max(0, ratio)) * 3
  const index = Math.floor(scaled), amount = scaled - index
  const colour = stops[index].map((value, channel) => Math.round(value + (stops[index + 1][channel] - value) * amount))
  return `rgb(${colour.join(' ')})`
}

function card(name: CardName, result: any, studyPackage?: any): HTMLCanvasElement {
  const canvas = document.createElement('canvas'); canvas.width = CARD_WIDTH; canvas.height = CARD_HEIGHT
  const ctx = canvas.getContext('2d')!; title(ctx, name, result)
  if (name === 'site-unit') drawSite(ctx, studyPackage)
  else if (name === 'sunpath') drawSunpath(ctx, result)
  else if (name === 'shadow') drawShadow(ctx, result)
  else if (name === 'solar-access') drawAccess(ctx, result)
  else drawRadiation(ctx, result)
  return canvas
}

const blob = (canvas: HTMLCanvasElement) => new Promise<Blob>((resolve, reject) =>
  canvas.toBlob(value => value ? resolve(value) : reject(new Error('PNG_FAILED')), 'image/png'))

export async function exportBundle(result: any, model: Blob, studyPackage?: any) {
  await Promise.all([document.fonts.load('500 118px Newsreader'), document.fonts.load('500 30px Inter')])
  const cards = await Promise.all(CARD_NAMES.map(async name => [name, await blob(card(name, result, studyPackage))] as const))
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
