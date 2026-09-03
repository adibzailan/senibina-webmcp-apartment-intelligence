/** Client-side slot geometry: the eight 4-room candidate slots of the plate at one storey. */
export interface Slot { id: string; facade: string; stack_position: string; corners: [number, number][]; z: number; label: string }

export function storeyFloor(plate: any, storey: number): number {
  for (const b of plate.bands) if (b.storeys[0] <= storey && storey <= b.storeys[1]) return b.base_m + (storey - b.storeys[0]) * b.storey_height_m;
  return 0;
}

/** Mirror of ai_geometry.build.unit_frame: plan frame (x along frontage, y inward) to world ENU. */
export function unitToWorld(plate: any, placement: { facade: string; stack_position: string; mirrored?: boolean }): ((x: number, y: number) => [number, number]) | null {
  const w = plate.wings.find((w: any) => w.id === placement.facade); if (!w) return null;
  const s = w.slots.find((s: any) => s.id === placement.stack_position); if (!s) return null;
  const ax = (w.axis_deg * Math.PI) / 180, inw = (w.inward_deg * Math.PI) / 180;
  const centre = s.start_m + s.width_m / 2 - w.length_m / 2;
  const ox = w.origin[0] + centre * Math.cos(ax), oy = w.origin[1] + centre * Math.sin(ax);
  return (x, y) => { if (placement.mirrored) x = -x; return [ox + x * Math.cos(ax) + y * Math.cos(inw), oy + x * Math.sin(ax) + y * Math.sin(inw)]; };
}

export interface RoomLabel { id: string; text: string; x: number; y: number; z: number }

/** One label per room at the polygon centroid, 1.2 m above the floor. */
export function roomLabels(plate: any, unit: any, placement: { facade: string; stack_position: string; mirrored?: boolean }, storey: number): RoomLabel[] {
  const to = unitToWorld(plate, placement); if (!to || !unit?.rooms) return [];
  const z = storeyFloor(plate, storey) + 1.2;
  return unit.rooms.map((r: any) => {
    const cx = r.polygon.reduce((a: number, p: number[]) => a + p[0], 0) / r.polygon.length;
    const cy = r.polygon.reduce((a: number, p: number[]) => a + p[1], 0) / r.polygon.length;
    const [x, y] = to(cx, cy); return { id: r.id, text: r.label, x, y, z };
  });
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
