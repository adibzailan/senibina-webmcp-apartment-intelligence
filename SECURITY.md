# Security Policy

Apartment Intelligence is an in-progress hackathon implementation. It has no
supported public release until the documented release gates pass.

## Intended boundary

The public application will expose narrow, state-aware WebMCP tools through the
same application functions used by the visible interface. Tool discovery does
not grant server authority.

The MVP will not accept arbitrary server-side URL fetching, executable model
content, scripts, filesystem paths, plug-ins, Grasshopper definitions, or
Rhino.Compute endpoints. The MVP resolves addresses only from its bundled,
attributed Dawson fixture and accepts no listing or floorplan content.

Exact security objectives and release gates are maintained in
[`security-and-operations.md`](_DOCUMENTATION/20%20Areas/security-and-operations.md).

## Reporting

Do not publish credentials, private hostnames, personal apartment data, or
suspected exploit details in a public issue. A private vulnerability-reporting
route must be established before claiming a supported public security process.
