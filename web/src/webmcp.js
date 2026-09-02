import { api } from './api'


const object = (properties, required = Object.keys(properties)) => ({ type: 'object', additionalProperties: false, properties, required })
const text = { type: 'string', maxLength: 80 }
const analyses = ['sunpath', 'shadow', 'solar_access', 'radiation']
const shadowTimes = ['09:00', '12:00', '15:00']
const solarDates = ['2026-03-21', '2026-06-21', '2026-09-21', '2026-12-21']
const views = ['precinct', 'tower', 'home']
export const DEFAULT_PROPOSAL = { mirrored: false, window_width: 4, window_height: 1.2, sill_height: .9 }

export function validateShowAnalysis(input) {
  const allowed = ['analysis', 'shadow_time', 'solar_date', 'view']
  if (!input || Object.keys(input).some(key => !allowed.includes(key)) || !analyses.includes(input.analysis) ||
    ('shadow_time' in input && !shadowTimes.includes(input.shadow_time)) || ('solar_date' in input && !solarDates.includes(input.solar_date)) ||
    ('view' in input && !views.includes(input.view)) || ('shadow_time' in input && input.analysis !== 'shadow') || ('solar_date' in input && input.analysis !== 'solar_access')) {
    throw new Error('INVALID_PRESENTATION')
  }
  return { analysis: input.analysis, ...(input.shadow_time ? { shadowTime: input.shadow_time } : {}),
    ...(input.solar_date ? { solarDate: input.solar_date } : {}), ...(input.view ? { view: input.view } : {}) }
}

export function conciseStudyState(state) {
  return {
    study_id: state.study_id,
    state: state.state,
    address: state.address,
    storey: state.storey,
    source_state: state.source_state,
    height_state: state.height_state,
    plate_summary: state.plate_summary,
    next_action: state.next_action,
  }
}

export async function registerWebMCP(dispatch, getState, onExport) {
  const modelContext = document.modelContext
  if (!modelContext) return () => {}
  const controller = new AbortController()
  const execute = (operation) => async (input, options = {}) => {
    const signal = options.signal || controller.signal
    try {
      const result = await operation(input, signal)
      if (result?.state) dispatch({ type: 'study-state', payload: result, source: 'webmcp' })
      return result
    } catch (error) {
      return { study_id: input.study_id, state: getState().status, error: error.body?.error || 'REQUEST_FAILED', next_action: error.body?.next_action || 'Review the visible application state.' }
    }
  }
  const tools = [
    { name: 'create_apartment_study', description: 'Start the Dawson HDB solar study and open the sourced context for resident review.',
      inputSchema: object({ address: text, storey: { type: 'integer', minimum: 1, maximum: 47 } }),
      execute: execute(async (input, signal) => { const result = await api.create(input, signal); dispatch({ type: 'study-created', payload: result, source: 'webmcp' }); return result }) },
    { name: 'propose_unit_location', description: 'Stage an approximate facade and horizontal unit position for visible resident review. This never confirms geometry.',
      inputSchema: object({ study_id: text, facade: { type: 'string', enum: ['north', 'east', 'south', 'west'] }, position: { type: 'string', enum: ['left', 'centre', 'right'] }, mirrored: { type: 'boolean' } }, ['study_id', 'facade', 'position']),
      execute: execute((input, signal) => api.proposal(input.study_id, { facade: input.facade, position: input.position, ...DEFAULT_PROPOSAL, mirrored: input.mirrored ?? false }, signal)) },
    { name: 'get_study_state', description: 'Read concise provenance, state, missing information, and the next human action.', annotations: { readOnlyHint: true },
      inputSchema: object({ study_id: text }), execute: execute(async (input, signal) => {
        const state = await api.state(input.study_id, signal); dispatch({ type: 'study-state', payload: state, source: 'webmcp' }); return conciseStudyState(state)
      }) },
    { name: 'run_solar_analysis', description: 'Run all four deterministic solar studies. Unconfirmed or stale geometry is refused.',
      inputSchema: object({ study_id: text }), execute: execute((input, signal) => api.analyse(input.study_id, signal)) },
    { name: 'show_analysis', description: 'Show a completed analysis in the shared visible interface without changing evidence.', annotations: { readOnlyHint: true },
      inputSchema: object({ analysis: { type: 'string', enum: analyses }, shadow_time: { type: 'string', enum: shadowTimes }, solar_date: { type: 'string', enum: solarDates }, view: { type: 'string', enum: views } }, ['analysis']),
      execute: async input => { try { const presentation = validateShowAnalysis(input); dispatch({ type: 'show-analysis', ...presentation, source: 'webmcp' }); return { study_id: getState().studyId, state: getState().status, outcome: `Showing ${presentation.analysis}.`, next_action: 'Review the visible computed graphic.' } } catch { return { study_id: getState().studyId, state: getState().status, error: 'INVALID_PRESENTATION', next_action: 'Choose a supported analysis, time, date, and view.' } } } },
    { name: 'export_study', description: 'Produce the completed architectural evidence bundle.',
      inputSchema: object({ study_id: text }), execute: execute(async input => onExport(input.study_id)) },
  ]
  for (const tool of tools) await modelContext.registerTool(tool, { signal: controller.signal })
  document.documentElement.dataset.webmcpTools = String((await modelContext.getTools()).length)
  return () => controller.abort()
}
