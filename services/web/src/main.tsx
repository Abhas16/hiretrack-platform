import "@fontsource/plus-jakarta-sans/400.css";
import "@fontsource/plus-jakarta-sans/500.css";
import "@fontsource/plus-jakarta-sans/600.css";
import "@fontsource/plus-jakarta-sans/700.css";
import "@fontsource/jetbrains-mono/500.css";
import "./index.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/App";
import { ConfigErrorScreen } from "./app/ConfigErrorScreen";
import { loadConfig } from "./lib/config";

const root = createRoot(document.getElementById("root")!);

// Load /config.json first: every API call needs apiBaseUrl from it.
loadConfig()
  .then(() =>
    root.render(
      <StrictMode>
        <App />
      </StrictMode>,
    ),
  )
  .catch((error: unknown) =>
    root.render(
      <ConfigErrorScreen message={error instanceof Error ? error.message : String(error)} />,
    ),
  );
