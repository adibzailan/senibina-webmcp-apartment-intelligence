/** Client-side slot geometry: the eight 4-room candidate slots of the plate at one storey. */
export interface Slot { id: string; facade: string; stack_position: string; corners: [number, number][]; z: number; label: string }

export function storeyFloor(plate: any, storey: number): number {
  for (const b of plate.bands) if (b.storeys[0] <= storey && storey <= b.storeys[1]) return b.base_m + (storey - b.storeys[0]) * b.storey_height_m;
  return 0;
}

export function plateSlots(plate: any, storey: number): Slot[] {
  const z = storeyFloor(plate, storey);
  const out: Slot[] = [];
  for (const w of plate.wings) {
    const ax = (w.axis_deg * Math.PI) / 180, inw = (w.inward_deg * Math.PI) / 180;
    const P = (c: number, d: number): [number, number] => [w.origin[0] + c * Math.cos(ax) + d * Math.cos(inw), w.origin[1] + c * Math.sin(ax) + d * Math.sin(inw)];
    for (const s of w.slots) {
      const c0 = s.start_m - w.length_m / 2, c1 = c0 + s.width_m;
      out.push({ id: `${w.id}:${s.id}`, facade: w.id, stack_position: s.id, z, corners: [P(c0, 0), P(c1, 0), P(c1, w.depth_m), P(c0, w.depth_m)], label: `${w.id} Wing, ${s.id === "end" ? "Wing Tip" : "Near the Core"}` });
    }
  }
  return out;
}
