import { expect, test, Page } from "@playwright/test";

async function noHorizontalOverflow(page: Page) {
  const over = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(over).toBe(false);
}

test("human journey: locate, place, confirm by click, analyse, export", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Will this apartment/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /SkyVille @ Dawson/ })).toBeEnabled();
  await expect(page.getByRole("button", { name: /Pinnacle @ Duxton/ })).toBeDisabled();
  await noHorizontalOverflow(page);
  await page.getByRole("button", { name: "Start the study" }).click();
  await expect(page.getByRole("heading", { name: /Choose the wing|Confirm the placement/ })).toBeVisible();
  // click a slot on the tower picker list (the 3D outlines are also clickable)
  await page.getByRole("button", { name: /SE Wing, Near the Core/ }).click();
  await page.getByRole("button", { name: "Type B, Larger Living" }).click();
  await expect(page.getByText(/SE Wing, Near the Core, Type B/)).toBeVisible();
  await expect(page.getByTestId("confirm-button")).toBeEnabled({ timeout: 15_000 });
  await page.getByTestId("confirm-button").click();
  await expect(page.getByRole("heading", { name: /Sun, shade and radiation/ })).toBeVisible();
  await page.getByRole("button", { name: "Coarse, 0.5 m" }).click();
  await page.getByRole("button", { name: "Run the analysis" }).click();
  await expect(page.getByRole("heading", { name: "Room by room" })).toBeVisible({ timeout: 60_000 });
  // every displayed number sits with its provenance: the numbers block, the room table, and the closed method disclosure
  await expect(page.locator(".numbers strong")).toHaveCount(3);
  await expect(page.getByText("Method, sources and limitations")).toBeVisible();
  await page.locator("summary", { hasText: "Method, sources" }).click();
  await expect(page.getByText(/result digest [0-9a-f]{16}/)).toBeVisible();
  for (const preset of ["Sunpath", "Shadow", "Solar access", "Radiation"]) await page.getByRole("button", { name: preset, exact: true }).click();
  for (const cam of ["Precinct", "Tower", "Apartment", "Isometric", "From above", "Face north", "Reset", "Map", "Section", "Section"]) await page.getByRole("button", { name: cam, exact: true }).click();
  // orbit, pan, zoom on the live canvas must not throw
  const canvas = page.locator(".canvas canvas");
  const box = (await canvas.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down(); await page.mouse.move(box.x + box.width / 2 + 60, box.y + box.height / 2 + 30, { steps: 5 }); await page.mouse.up();
  await page.mouse.wheel(0, -200);
  await page.getByRole("button", { name: "Keep the evidence", exact: true }).click();
  const dl = page.waitForEvent("download");
  await page.getByRole("button", { name: "PDF report", exact: true }).click(); // unpick the default
  await page.getByRole("button", { name: "GLB", exact: true }).click();
  await page.getByRole("button", { name: /^Export 1 file$/ }).click();
  expect((await dl).suggestedFilename()).toContain(".glb");
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `test-results/journey-${test.info().project.name}.png`, fullPage: true });
});

test("WebMCP journey: nine tools, read-only hints, no confirm tool, refusal before click", async ({ page }) => {
  await page.goto("/");
  await page.waitForFunction(() => (window as any).__aiTools?.length === 9);
  const native = await page.evaluate(() => {
    const mc: any = (document as any).modelContext ?? (navigator as any).modelContext;
    if (!mc) return { exposed: false, tools: [] as any[] };
    const tools = typeof mc.getTools === "function" ? mc.getTools() : [];
    return { exposed: true, tools: Array.from(tools as any[]).map((t: any) => ({ name: t.name, readOnly: !!t.annotations?.readOnlyHint })) };
  });
  const names = await page.evaluate(() => (window as any).__aiTools.map((t: any) => t.name));
  expect(names.sort()).toEqual(["create_apartment_study", "explain_evidence", "export_study", "get_study_state", "list_supported_homes", "propose_unit_placement", "run_solar_analysis", "show_analysis", "survey_unit"]);
  if (native.exposed && native.tools.length) {
    expect(native.tools.map((t) => t.name).sort()).toEqual(names.sort());
    expect(native.tools.filter((t) => t.readOnly).map((t) => t.name).sort()).toEqual(["explain_evidence", "get_study_state", "list_supported_homes", "show_analysis"]);
  }
  const call = (name: string, input: any) => page.evaluate(([n, i]) => (window as any).__aiTools.find((t: any) => t.name === n).execute(i), [name, input] as any);
  const homes: any = await call("list_supported_homes", {});
  expect(homes.homes[0].postal_code).toBe("141087");
  const created: any = await call("create_apartment_study", { address: "87 Dawson Road", storey: 30 });
  expect(created.state).toBe("created");
  await call("propose_unit_placement", { study_id: created.study_id, facade: "SE", variant: "B" });
  await expect(page.getByRole("heading", { name: /Confirm the placement/ })).toBeVisible();
  const refused: any = await call("run_solar_analysis", { study_id: created.study_id });
  expect(refused.refused).toBe(true);
  await expect(call("propose_unit_placement", { study_id: created.study_id, facade: "SE", confirmed: true })).rejects.toThrow(/422/);
  await page.getByTestId("confirm-button").click();
  await expect(page.getByRole("heading", { name: /Sun, shade and radiation/ })).toBeVisible();
  const ran: any = await call("run_solar_analysis", { study_id: created.study_id, grid_spacing_m: 0.5 });
  expect(ran.digest).toMatch(/^[0-9a-f]{64}$/);
  const st: any = await call("get_study_state", { study_id: created.study_id });
  expect(st.confirmed).toBe(true);
  expect(st.placement.facade).toBe("SE");
  // survey: an agent may analyse a staged placement without a click, but every number is labelled unconfirmed
  const sv: any = await call("survey_unit", { address: "87 Dawson Road", storey: 12, facade: "NE", stack_position: "end", variant: "A", grid_spacing_m: 0.5 });
  expect(sv.provenance).toBe("survey_unconfirmed");
  await expect(page.getByText(/Surveys by an agent, unconfirmed/)).toBeVisible();
  const ev: any = await call("explain_evidence", { study_id: created.study_id, item: "radiation" });
  expect(ev.value).toBe(st.radiation.avg);
  await call("show_analysis", { analysis: "shadow", date: "12-21", hour: 9, camera: "home" });
  await expect(page.getByText(/12-21 9:00/)).toBeVisible();
  await page.screenshot({ path: `test-results/webmcp-${test.info().project.name}.png`, fullPage: true });
});

test("delegated confirmation: one click lets the agent confirm the next placements, labelled and revocable", async ({ page }) => {
  await page.goto("/");
  await page.waitForFunction(() => (window as any).__aiTools?.length === 9);
  const call = (name: string, input: any) => page.evaluate(([n, i]) => (window as any).__aiTools.find((t: any) => t.name === n).execute(i), [name, input] as any);
  const created: any = await call("create_apartment_study", { address: "87 Dawson Road", storey: 30 });
  await call("propose_unit_placement", { study_id: created.study_id, facade: "NE" });
  await expect(call("propose_unit_placement", { study_id: created.study_id, facade: "NE", delegate: true })).rejects.toThrow(/422/);
  const refused: any = await call("run_solar_analysis", { study_id: created.study_id });
  expect(refused.reason).toMatch(/Let my agent confirm/);
  await page.getByTestId("delegate-button").click(); // the resident's one click
  await expect(page.getByTestId("delegation-status")).toContainText(/2 more placements/);
  await expect(page.getByRole("heading", { name: /Sun, shade and radiation/ })).toBeVisible();
  // the agent re-stages: no click, yet confirmed, and the page says by whom
  const staged: any = await call("propose_unit_placement", { study_id: created.study_id, facade: "SW", variant: "C" });
  expect(staged.confirmation.kind).toBe("delegated");
  await expect(page.getByTestId("delegation-status")).toContainText(/1 more placement\b/);
  await expect(page.getByText(/by your agent, under your delegation/)).toBeVisible();
  const ran: any = await call("run_solar_analysis", { study_id: created.study_id, grid_spacing_m: 0.5 });
  expect(ran.digest).toMatch(/^[0-9a-f]{64}$/);
  await call("show_analysis", { camera: "isometric", section: true, massing: false });
  await expect(page.getByRole("button", { name: "Section", exact: true })).toHaveAttribute("aria-pressed", "true");
  await page.locator("summary", { hasText: "Method, sources" }).click();
  await expect(page.getByText("confirmed by your agent under your delegation")).toBeVisible();
  await page.screenshot({ path: `test-results/delegated-${test.info().project.name}.png`, fullPage: true });
  await page.getByRole("button", { name: "Revoke", exact: true }).click();
  await expect(page.getByTestId("delegation-status")).toHaveCount(0);
  const st: any = await call("get_study_state", { study_id: created.study_id });
  expect(st.confirmation.kind).toBe("delegated"); expect(st.delegation).toBeNull();
});
