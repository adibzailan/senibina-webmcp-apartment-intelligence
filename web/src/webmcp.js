import { api } from './api'


const object = (properties, required = Object.keys(properties)) => ({ type: 'object', additionalProperties: false, properties, required })
const text = { type: 'string', maxLength: 80 }

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
      inputSchema: object({ study_id: text, facade: { type: 'string', enum: ['north', 'east', 'south', 'west'] }, position: { type: 'string', enum: ['left', 'centre', 'right'] } }),
      execute: execute((input, signal) => api.proposal(input.study_id, { facade: input.facade, position: input.position, width: 8, window_width: 4, window_height: 1.2, sill_height: .9 }, signal)) },
    { name: 'get_study_state', description: 'Read concise provenance, state, missing information, and the next human action.', annotations: { readOnlyHint: true },
      inputSchema: object({ study_id: text }), execute: execute((input, signal) => api.state(input.study_id, signal)) },
    { name: 'run_solar_analysis', description: 'Run all four deterministic solar studies. Unconfirmed or stale geometry is refused.',
      inputSchema: object({ study_id: text }), execute: execute((input, signal) => api.analyse(input.study_id, signal)) },
    { name: 'show_analysis', description: 'Show a completed analysis in the shared visible interface without changing evidence.', annotations: { readOnlyHint: true },
      inputSchema: object({ analysis: { type: 'string', enum: ['sunpath', 'shadow', 'solar_access', 'radiation'] }, shadow_time: { type: 'string', enum: ['09:00', '12:00', '15:00'] } }, ['analysis']),
      execute: async input => { dispatch({ type: 'show-analysis', analysis: input.analysis, source: 'webmcp' }); return { study_id: getState().studyId, state: getState().status, outcome: `Showing ${input.analysis}.`, next_action: 'Review the visible computed graphic.' } } },
    { name: 'export_study', description: 'Produce the completed architectural evidence bundle.',
      inputSchema: object({ study_id: text }), execute: execute(async input => onExport(input.study_id)) },
  ]
  for (const tool of tools) await modelContext.registerTool(tool, { signal: controller.signal })
  document.documentElement.dataset.webmcpTools = String((await modelContext.getTools()).length)
  return () => controller.abort()
}
