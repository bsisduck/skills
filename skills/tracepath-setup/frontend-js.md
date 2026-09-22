# JS Frontend SDKs Reference

Browser-side setup for every supported framework, plus the bundler plugin and source map upload that complete each integration. The connection string everywhere is `<project-token>@https://<instance>/api/report`.

## Packages

| Package | Use for |
|---|---|
| `@tracepath/frontend` | Plain JS, vanilla apps, frameworks without official bindings |
| `@tracepath/react` | React: provider, error boundary, hooks |
| `@tracepath/vue` | Vue 3: plugin and composables |
| `@tracepath/svelte` | Svelte and SvelteKit: context-based setup |
| `@tracepath/jquery` | jQuery: automatic AJAX error capture |

All framework packages wrap the core SDK and accept the same options object (see Options below). Every SDK captures uncaught errors and unhandled promise rejections, batches uploads with retry, and ships session replay: the last ~30s of DOM events (rrweb) accompany every captured exception by default.

## Plain JS (`@tracepath/frontend`)

```javascript
import { init, captureException, captureMessage } from "@tracepath/frontend";

init("your-token@https://tracepath.example.com/api/report");

try {
  riskyOperation();
} catch (error) {
  captureException(error);
}

captureMessage("User completed checkout");
```

Via CDN (exposes `window.TracePath`, no build step):

```html
<script src="https://cdn.jsdelivr.net/npm/@tracepath/frontend@1/dist/tracepath.iife.global.js"></script>
<script>
  TracePath.init("your-token@https://tracepath.example.com/api/report");
</script>
```

## React (`@tracepath/react`)

Wrap the app in `TracePathProvider`. It doubles as an error boundary: render-time exceptions anywhere in the tree are captured and re-thrown, so app behavior is unchanged. `TracePathErrorBoundary` is still exported for the case where a crashed subtree should show a fallback UI instead of propagating; it is not required for capture.

```jsx
import { TracePathProvider } from "@tracepath/react";

function App() {
  return (
    <TracePathProvider connectionString="your-token@https://tracepath.example.com/api/report">
      <YourApp />
    </TracePathProvider>
  );
}
```

Manual capture uses the `useTracePath` hook:

```jsx
import { useTracePath } from "@tracepath/react";

function MyComponent() {
  const { captureException } = useTracePath();

  async function handleSubmit() {
    try {
      await submitForm();
    } catch (error) {
      captureException(error);
    }
  }
}
```

Options go on the provider: `<TracePathProvider connectionString="..." options={{ debug: true, version: "1.0.0" }}>`.

`TracePathProvider` initializes the SDK in its constructor, and React StrictMode double-invokes constructors in development. The Vite and CRA scaffolds both wrap the app in `<StrictMode>` by default, so in dev you get two clients and every uncaught error is reported twice. Production builds do not double-invoke, so treat inflated dev counts as expected, or mount the provider outside `<StrictMode>` while developing.

## Vue 3 (`@tracepath/vue`)

The plugin installs a global error handler for uncaught errors:

```javascript
import { createApp } from "vue";
import { createTracePathPlugin } from "@tracepath/vue";
import App from "./App.vue";

const app = createApp(App);
app.use(createTracePathPlugin({
  connectionString: "your-token@https://tracepath.example.com/api/report",
  options: { version: "1.0.0" },
}));
app.mount("#app");
```

Manual capture uses the `useTracePath` composable:

```vue
<script setup>
import { useTracePath } from "@tracepath/vue";
const { captureException } = useTracePath();
</script>
```

## Svelte / SvelteKit (`@tracepath/svelte`)

Call `setupTracePath` in the root layout. The `if (browser)` guard keeps the rrweb recorder out of the SSR bundle:

```svelte
<!-- src/routes/+layout.svelte -->
<script>
  import { setupTracePath } from "@tracepath/svelte";
  import { browser } from "$app/environment";

  if (browser) {
    setupTracePath({
      connectionString: "your-token@https://tracepath.example.com/api/report",
    });
  }
</script>

<slot />
```

For a non-SvelteKit Svelte app, drop the guard and the `$app/environment` import. Manual capture in child components uses `getTracePath()`:

```svelte
<script>
  import { getTracePath } from "@tracepath/svelte";
  const { captureException } = getTracePath();
</script>
```

## jQuery (`@tracepath/jquery`)

```javascript
import { init, captureException } from "@tracepath/jquery";

init("your-token@https://cloud.tracepath.dev/api/report");
```

Via CDN (exposes `window.TracePathJQuery`):

```html
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@tracepath/jquery@1/dist/tracepath-jquery.iife.global.js"></script>
<script>
  TracePathJQuery.init("your-token@https://cloud.tracepath.dev/api/report");
</script>
```

Beyond the standard capture, the jQuery SDK adds exactly one thing: it hooks `$(document).ajaxError()` to capture failed `$.ajax()` calls (URL, method, status, message). Trace-header injection is not jQuery-specific. `init()` in the core SDK patches both `fetch` and `XMLHttpRequest`, so it is already active in every JS SDK.

## Options (shared by all JS SDKs)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `debug` | `boolean` | `false` | Log captured events to the browser console |
| `debounceMs` | `number` | `1500` | Batch delay in milliseconds |
| `retryDelayMs` | `number` | `10000` | Retry delay for failed uploads |
| `version` | `string` | `undefined` | App version, shown on exceptions for filtering by build (unrelated to source maps) |
| `ignoreErrors` | `Array<string \| RegExp>` | default patterns | Error patterns to ignore; pass `[]` to capture everything |
| `beforeCapture` | `(exception) => boolean` | `undefined` | Return `false` to suppress an error |
| `sessionRecording` | `boolean` | `true` | rrweb session recorder |
| `sessionRecordingSegmentDuration` | `number` | `30000` | rrweb segment length in ms |
| `recordAllSessions` | `boolean` | `false` | Always-on session recording instead of error-triggered |
| `captureLogs` | `boolean` | `true` | Mirror `console.*` calls into the rolling log buffer |
| `captureNetwork` | `boolean` | `true` | Record `fetch` / XHR calls as network actions |
| `captureNavigation` | `boolean` | `true` | Record History API transitions |
| `captureHttpServerErrors` | `boolean` | `false` | Report every `fetch` response with status >= 500 as a synthetic exception. 4xx is never included, and it is wired into the `fetch` wrapper only, so XHR and browser Axios do not trigger it |
| `eventsWindowMs` | `number` | `10000` (`30000` with `recordAllSessions`) | Rolling window the log and action buffers retain |
| `eventsMaxCount` | `number` | `200` (`600` with `recordAllSessions`) | Hard cap applied independently to the log buffer and the action buffer |

### Error filtering

By default 4xx HTTP errors, network errors, and timeouts are NOT captured. Opt in with `ignoreErrors: []`, and filter selectively with `beforeCapture`:

```javascript
init("your-token@https://<instance>/api/report", {
  ignoreErrors: [],
  beforeCapture: (exception) => {
    const status = Number(exception.attributes?.status);
    if (status >= 400 && status < 500) return false;
    return true;
  },
});
```

### Custom attributes

Attach app-level identifiers to every session and exception. Layering on each event: defaults < global scope < per-call.

```javascript
import { setAttribute, setAttributes, clearAttributes } from "@tracepath/jquery";

setAttribute("userId", "u_42");
setAttributes({ tenant: "acme", plan: "pro" });
clearAttributes();
```

(Same exports from each framework package.)

### Distributed tracing

`init()` patches both `fetch` and `XMLHttpRequest`, so every same-origin request carries a `tracepath-trace-id` header and sets the SDK's active trace id. That covers `$.ajax()` and browser Axios too, because both go through XHR. Errors the SDK captures on its own (uncaught exceptions, unhandled rejections, `captureHttpServerErrors`) pick up the active id and link to the originating backend request automatically.

**Do not register `createAxiosInterceptor()` in a browser app.** Axios already goes through the instrumented `XMLHttpRequest`. The interceptor sets a *second*, different id under the same header name, XHR concatenates duplicate headers, and the backend receives `"<uuid1>, <uuid2>"`. That value fails to parse as a UUID and is dropped without any error, so adding the interceptor breaks a link that already worked.

#### Backend side

The browser id only reaches TracePath if the backend puts it on its server span. TracePath reads the span attribute `tracepath.distributed_trace_id` and uses it as the row's distributed trace id, overriding the one derived from the OTel trace id. That override is what joins the browser exception and the backend endpoint into one trace. The value must be a bare UUID; anything else is ignored silently.

Only the Symfony bundle sets the attribute for you. Node, NestJS, Next.js, Hono, Cloudflare, Laravel and Django install vanilla OpenTelemetry, which has never heard of the header, so add one middleware:

```javascript
import { trace } from "@opentelemetry/api";

app.use((req, res, next) => {
  const id = req.headers["tracepath-trace-id"];
  if (id) {
    trace.getActiveSpan()?.setAttribute("tracepath.distributed_trace_id", id);
    res.setHeader("tracepath-trace-id", id);
  }
  next();
});
```

The `setAttribute` line is what creates the link. The `setHeader` line is optional, and only matters for the manual-capture pattern below. When the frontend and backend are on different origins, also send `Access-Control-Expose-Headers: tracepath-trace-id` or the browser cannot read the echoed value.

Verify with **View distributed trace** on the backend endpoint's detail page. The browser exception should show up as a second node.

#### Manual captures after `await fetch`

**Manual captures in a `fetch`/API wrapper MUST pass the trace id explicitly. This is the #1 reason frontend issues show up unlinked to the backend.** The SDK holds the active distributed-trace id only *for the duration of the request* and clears it the instant the fetch settles. A `captureException` call in your `catch` or `if (!res.ok)` branch runs *after* `await fetch`, by which point the active id is already `null`, so the exception is stored with `distributedTraceId: null` and never connects to the backend trace, even though the request header was sent correctly.

Read the id off the SDK synchronously, after starting the request and before awaiting it, then pass it as the third argument. This needs nothing from the backend:

```javascript
import {
  captureExceptionWithAttributes,
  getActiveDistributedTraceId,
} from "@tracepath/frontend";

async function request(path, options) {
  const pending = fetch(path, options);
  const distributedTraceId = getActiveDistributedTraceId() || undefined;
  const res = await pending;
  if (!res.ok) {
    const err = new Error(`Request to ${path} failed (${res.status})`);
    captureExceptionWithAttributes(
      err,
      { path, method: options?.method || "GET", status: String(res.status) },
      distributedTraceId ? { distributedTraceId } : undefined
    );
    throw err;
  }
  return res.json();
}
```

No other code can run between the `fetch` call and the `getActiveDistributedTraceId` call, so the id always belongs to this request. If the backend echoes the header (the `res.setHeader` line above), `res.headers.get("tracepath-trace-id")` gives you the same value after the await.

The same applies to the React `useTracePath().captureExceptionWithAttributes`, the Vue/Svelte equivalents, and any other place you capture by hand after awaiting a request. Every framework package re-exports `getActiveDistributedTraceId` and `captureExceptionWithAttributes`, so import them from the package you installed.

## Bundler Plugin (debug IDs)

`@tracepath/bundler-plugin` embeds a deterministic 128-bit debug ID into each emitted chunk and its `.map` (ECMA-426 debug ID format, interoperable with Sentry tooling). The backend then matches stack frames to the exact map from the same build, immune to filename collisions and concurrent deploys. Without it, matching falls back to filename (fine with content-hashed bundle names, broken with stable names like `app.js`).

```bash
npm install -D @tracepath/bundler-plugin
```

Vite:

```ts
import { tracepathDebugIds } from "@tracepath/bundler-plugin/vite";

export default defineConfig({
  build: { sourcemap: true },
  plugins: [tracepathDebugIds()],
});
```

Rollup: same import from `@tracepath/bundler-plugin/rollup`, with `output: { sourcemap: true }`.

webpack (requires webpack 5):

```js
const { TracePathDebugIdsWebpackPlugin } = require("@tracepath/bundler-plugin/webpack");

module.exports = {
  devtool: "source-map",
  plugins: [new TracePathDebugIdsWebpackPlugin()],
};
```

esbuild is not covered; bundles processed by Sentry's esbuild plugin still work (the SDK reads `_sentryDebugIds` too), otherwise esbuild falls back to filename matching.

## Source Map Upload

Uploads authenticate with a dedicated upload token (Connection page > Source Maps > Generate Upload Token), NOT the project token. It is a CI secret; never commit it. `readonly` members cannot generate one.

First make the build actually emit maps, or there is nothing to upload. Vite needs `build: { sourcemap: true }`, Rollup needs `output: { sourcemap: true }`, webpack needs `devtool: "source-map"`. Vite's default is `false`, so a stock `vite build` produces no `.map` files at all, and `tracepath-sourcemaps` then prints `No .map files found` and exits 0. A `postbuild` hook reports success while uploading nothing.

```bash
npm install -D @tracepath/sourcemap-upload

tracepath-sourcemaps --url https://<instance> --token <upload-token> --directory ./dist
```

Env vars `TRACEPATH_URL` and `TRACEPATH_SOURCEMAP_TOKEN` replace the flags. The CLI uploads all `*.map` files plus the sibling `.js`/`.cjs`/`.mjs` bundles (the bundle is what enables function-name resolution). Limit: 50 MB per file. Uploads take effect immediately.

Wire it as a postbuild script:

```json
{
  "scripts": {
    "build": "vite build",
    "postbuild": "tracepath-sourcemaps --directory ./dist"
  }
}
```

Or as a CI step after build:

```yaml
- name: Upload source maps
  run: npx tracepath-sourcemaps --directory ./dist
  env:
    TRACEPATH_URL: ${{ secrets.TRACEPATH_URL }}
    TRACEPATH_SOURCEMAP_TOKEN: ${{ secrets.TRACEPATH_SOURCEMAP_TOKEN }}
```

Self-hosted instances must have blob storage (S3 or a persistent volume) configured, or uploaded maps disappear when the container is recreated.

## Verify

Trigger a test error (`captureException(new Error("Test error"))` behind a button) and check the Issues page: the error appears, and with the bundler plugin plus upload in place the stack trace resolves to original files and lines.
