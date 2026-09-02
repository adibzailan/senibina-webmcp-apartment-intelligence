import { zipSync } from 'fflate'
import { PDFDocument } from 'pdf-lib'
import { renderSiteEvidence } from './sceneRender'


export const CARD_WIDTH = 1600
export const CARD_HEIGHT = 2400
export const CARD_NAMES = ['site-unit', 'sunpath', 'shadow', 'solar-access', 'radiation'] as const
type CardName = typeof CARD_NAMES[number]

export function exportManifest(digest: string, study?: any) {
  return { product: 'Apartment Intelligence', digest, address: study?.address, storey: study?.storey, cards: CARD_NAMES, width: CARD_WIDTH, height: CARD_HEIGHT }
}

export function cardNarrative(name: CardName, result: any) {
  const content = {
    'site-unit': { method: 'Official HDB footprint, inferred massing, and resident-confirmed approximate apartment floor plate.', limitations: 'The ground-level footprint is reused at the selected storey; the apartment rectangle and opening are approximations.' },
    sunpath: { method: 'Ladybug solar positions for equinoxes and solstices in Singapore time.', limitations: 'Paths describe the sun; context obstruction is shown in the other studies.' },
    shadow: { method: 'Aperture-gated Ladybug Geometry rays across the apartment floor plate at 09:00, 12:00 and 15:00.', limitations: 'Three representative instants on 21 March; open plan with no internal partitions.' },
    'solar-access': { method: 'Direct-sun hours on the apartment floor plate, sampled every 30 minutes on four seasonal dates.', limitations: 'The apartment footprint and one exterior opening are resident-confirmed approximations.' },
    radiation: { method: '12 monthly representative days: EPW direct and diffuse exposure reaching the floor through the confirmed window aperture.', limitations: result.radiation?.limitations?.join('; ') || 'no glazing transmittance; no inter-reflection' },
  }
  return content[name]
}

function title(ctx: CanvasRenderingContext2D, name: CardName, result: any, studyPackage?: any) {
  ctx.fillStyle = '#f5f2e9'; ctx.fillRect(0, 0, CARD_WIDTH, CARD_HEIGHT)
  ctx.fillStyle = '#18211d'; ctx.font = '650 28px Inter'; ctx.fillText('AI', 110, 110)
  ctx.font = '550 30px Inter'; ctx.fillText('Apartment Intelligence', 165, 110)
  const identity = studyPackage?.study ? `${studyPackage.study.address} · Storey ${studyPackage.study.storey}` : 'Dawson precinct study'
  ctx.textAlign = 'right'; ctx.font = '500 24px Inter'; ctx.fillStyle = '#5f665f'; ctx.fillText(identity, 1490, 110); ctx.textAlign = 'left'
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

function drawPlateGrid(ctx: CanvasRenderingContext2D, result: any, values: number[], x: number, y: number, width: number, height: number, colour: (value: number, values: number[]) => string) {
  const [cols, rows] = result.plate.grid
  const cellWidth = width / cols, cellHeight = height / rows
  values.forEach((value, index) => {
    if (!result.plate.mask[index]) return
    const row = Math.floor(index / cols), col = index % cols
    ctx.fillStyle = colour(value, values); ctx.fillRect(x + col * cellWidth, y + (rows - row - 1) * cellHeight, cellWidth - 2, cellHeight - 2)
  })
  ctx.strokeStyle = '#18211d'; ctx.lineWidth = 3; ctx.strokeRect(x, y, width, height)
}

function drawShadow(ctx: CanvasRenderingContext2D, result: any) {
  result.shadow.samples.forEach((sample: any, index: number) => {
    const x = 110 + index * 470
    ctx.fillStyle = '#18211d'; ctx.font = '550 64px Newsreader'; ctx.fillText(sample.time, x + 38, 650)
    drawPlateGrid(ctx, result, sample.sensor_values, x + 38, 750, 344, 650, value => value ? '#f2c230' : '#45534d')
    ctx.fillStyle = '#18211d'; ctx.font = '30px Inter'; ctx.fillText(`${sample.sun_patch_area_m2.toFixed(1)} m² sun patch`, x + 38, 1470)
  })
}

function drawAccess(ctx: CanvasRenderingContext2D, result: any) {
  Object.entries(result.solar_access).forEach(([date, study]: any, index) => {
    const x = 110 + (index % 2) * 710, y = 570 + Math.floor(index / 2) * 540
    const maximum = Math.max(1, ...study.sensor_hours)
    ctx.fillStyle = '#18211d'; ctx.font = '600 30px Inter'; ctx.fillText(date, x, y)
    drawPlateGrid(ctx, result, study.sensor_hours, x, y + 45, 620, 390, value => radiationCanvasColour(value / maximum))
    ctx.font = '550 36px Newsreader'; ctx.fillText(`${study.total_hours.toFixed(1)} h average`, x, y + 490)
  })
}

function drawRadiation(ctx: CanvasRenderingContext2D, result: any) {
  const values = result.radiation.sensor_values_kwh_m2
  const min = result.radiation.minimum_kwh_m2, max = result.radiation.maximum_kwh_m2
  drawPlateGrid(ctx, result, values, 110, 570, 1380, 960, value => radiationCanvasColour(max === min ? .5 : (value - min) / (max - min)))
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
  const ctx = canvas.getContext('2d')!; title(ctx, name, result, studyPackage)
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
    'manifest.json': new TextEncoder().encode(JSON.stringify({ ...exportManifest(result.digest, studyPackage?.study), method_version: result.method_version, weather: result.weather }, null, 2)),
    'apartment-intelligence.pdf': await pdf.save(),
    'apartment-intelligence.3dm': new Uint8Array(await model.arrayBuffer()),
  }
  for (const [name, png] of cards) files[`${name}.png`] = new Uint8Array(await png.arrayBuffer())
  return new Blob([zipSync(files)], { type: 'application/zip' })
}
