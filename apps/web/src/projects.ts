/** Project catalogue for the opening grid. One live; the rest are shown greyed as not yet covered.
 *  Tile art: put a PNG at public/projects/<slug>.png (1200x900, editorial ink style); a paper
 *  placeholder is drawn when the file is missing. Names are the HDB development names. */
export interface Project { slug: string; name: string; town: string; blocks: string; storeys: string; live: boolean; address?: string; postal?: string }

export const PROJECTS: Project[] = [
  { slug: "skyville-dawson", name: "SkyVille @ Dawson", town: "Queenstown", blocks: "86–88", storeys: "47", live: true, address: "87 Dawson Road", postal: "141087" },
  { slug: "skyterrace-dawson", name: "SkyTerrace @ Dawson", town: "Queenstown", blocks: "89–93", storeys: "43", live: false },
  { slug: "pinnacle-duxton", name: "Pinnacle @ Duxton", town: "Tanjong Pagar", blocks: "1–7", storeys: "50", live: false },
  { slug: "kampung-admiralty", name: "Kampung Admiralty", town: "Woodlands", blocks: "676–678", storeys: "11", live: false },
  { slug: "waterway-terraces", name: "Waterway Terraces", town: "Punggol", blocks: "308–310", storeys: "18", live: false },
  { slug: "alkaff-vista", name: "Alkaff Vista", town: "Bidadari", blocks: "104–108", storeys: "16", live: false },
  { slug: "clementi-towers", name: "Clementi Towers", town: "Clementi", blocks: "441–443", storeys: "40", live: false },
  { slug: "toa-payoh-ridge", name: "Toa Payoh Ridge", town: "Toa Payoh", blocks: "101–108", storeys: "40", live: false },
  { slug: "tampines-greenridges", name: "Tampines GreenRidges", town: "Tampines", blocks: "601–603", storeys: "15", live: false },
  { slug: "plantation-grange", name: "Plantation Grange", town: "Tengah", blocks: "115–121", storeys: "14", live: false },
];
