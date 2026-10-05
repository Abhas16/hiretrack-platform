# HireTrack Web

React 18 + TypeScript + Vite single-page app: login, dashboard, board (drag & drop), applications
table with CSV export, analytics, add-application modal, toasts.

## Structure: UI and logic in separate files

Every screen is a feature folder with the same three kinds of file:

```
features/board/
├── BoardPage.tsx           UI only: JSX, no state, no API calls
├── useBoardController.ts   logic: queries, mutations, event handlers, toasts
├── boardModel.ts           pure functions (no React) — easiest to unit-test
└── components/             small presentational pieces (BoardColumn, ApplicationCard)
```

```
src/
├── app/            App.tsx (providers), router.tsx (lazy-loaded pages), queryClient.ts
├── features/       auth, dashboard, board, applications, analytics, add-application, review-queue
├── components/     shared UI: layout/ (Sidebar, TopBar), ui/ (Button, Card, Modal…), toast/
├── lib/
│   ├── api/        client.ts (the only file that calls fetch) + one file per API resource
│   ├── config.ts   loads /config.json at start-up
│   └── …           status.ts, format.ts, hooks/
├── types/          TypeScript shapes of the API responses
└── test/           test providers + fixtures
```

Data flow: `Page` → calls `useXController()` → uses `lib/api/*` through TanStack Query → `client.ts` → API.

## Runtime config (`/config.json`)

The API URL is **not** compiled into the bundle. At start-up the app fetches `/config.json`:

```json
{ "apiBaseUrl": "http://localhost:8000", "environment": "local", "version": "dev" }
```

`public/config.json` is the local-dev version. In a container, the start-up script must
**overwrite** it from environment variables, so one image works in every environment.
`environment` and `version` are shown in the sidebar and on the login screen.

## Run locally

Requires Node 22+ and the API running on :8000 with `CORS_ALLOWED_ORIGINS=http://localhost:5173`.

```bash
cd services/web
npm ci              # exact versions from package-lock.json
npm run dev         # http://localhost:5173
```

## Checks

```bash
npm run typecheck   # tsc
npm run lint        # eslint
npm run format:check
npm test            # vitest (jsdom), no API needed — the API layer is mocked
npm run build       # production build -> dist/ (static files)
```

## Notes

- Pages are lazy-loaded, so charts (Recharts) and drag-and-drop (dnd-kit) download only on
  the pages that use them.
- The JWT is kept in `sessionStorage` (cleared when the tab closes); any 401 signs you out.
- Job links are rendered only if they are `http(s)` URLs (blocks `javascript:` links).
- Source maps are built as `hidden`: generated for error tracking, not referenced by the served JS.
