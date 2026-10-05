# Design reference

`hiretrack-demo-ui.dc.html` is the clickable demo the UI must match.
It uses a design-canvas template format (`<sc-for>`, `<sc-if>`, `{{holes}}`, a `DCLogic` class),
so treat it as a **reference only**: copy the layout, screens, colors, spacing, fonts, copy text,
sample data shape and interactions — but build the real app in React + TypeScript + Tailwind
as described in CLAUDE.md. Do not copy the template syntax.

Design tokens used in the demo:
- Fonts: Plus Jakarta Sans (UI), JetBrains Mono (numbers, API/status text)
- Background #F4F5F8, surface #FFFFFF, border #E3E6EC, text #151821, muted #5A6172
- Sidebar #12151C, active nav #262C3B, primary #2F5BEA, accent #E07A1F
- Status: Wishlist #8A93A3, Applied #2F5BEA, Interview #E07A1F, Offer #2E9A5E, Rejected #7A2626
