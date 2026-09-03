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
  await page.getByRole("button", { name: "Type B, larger living" }).click();
  await expect(page.getByText(/SE wing, inner stack, Type B/)).toBeVisible();
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
  for (const cam of ["Precinct", "Tower", "Apartment", "From above", "Face north", "Reset", "Map"]) await page.getByRole("button", { name: cam, exact: true }).click();
  // orbit, pan, zoom on the live canvas must not throw
  const canvas = page.locator(".canvas canvas");
  const box = (await canvas.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down(); await page.mouse.move(box.x + box.width / 2 + 60, box.y + box.height / 2 + 30, { steps: 5 }); await page.mouse.up();
  await page.mouse.wheel(0, -200);
  await page.getByRole("button", { name: "Keep the evidence", exact: true }).click();
  const dl = page.waitForEvent("download");
  await page.getByRole("button", { name: "cards.svg", exact: true }).click();
  expect((await dl).suggestedFilename()).toContain("cards.svg");
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `test-results/journey-${test.info().project.name}.png`, fullPage: true });
});

test("WebMCP journey: eight tools, read-only hints, no confirm tool, refusal before click", async ({ page }) => {
  await page.goto("/");
  await page.waitForFunction(() => (window as any).__aiTools?.length === 8);
  const native = await page.evaluate(() => {
    const mc: any = (document as any).modelContext ?? (navigator as any).modelContext;
    if (!mc) return { exposed: false, tools: [] as any[] };
    const tools = typeof mc.getTools === "function" ? mc.getTools() : [];
    return { exposed: true, tools: Array.from(tools as any[]).map((t: any) => ({ name: t.name, readOnly: !!t.annotations?.readOnlyHint })) };
  });
  const names = await page.evaluate(() => (window as any).__aiTools.map((t: any) => t.name));
  expect(names.sort()).toEqual(["create_apartment_study", "explain_evidence", "export_study", "get_study_state", "list_supported_homes", "propose_unit_placement", "run_solar_analysis", "show_analysis"]);
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
  const ev: any = await call("explain_evidence", { study_id: created.study_id, item: "radiation" });
  expect(ev.value).toBe(st.radiation.avg);
  await call("show_analysis", { analysis: "shadow", date: "12-21", hour: 9, camera: "home" });
  await expect(page.getByText(/12-21 9:00/)).toBeVisible();
  await page.screenshot({ path: `test-results/webmcp-${test.info().project.name}.png`, fullPage: true });
});
