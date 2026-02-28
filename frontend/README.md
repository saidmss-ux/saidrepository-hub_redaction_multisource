# Frontend Integration Layer (API v1)

Cette couche consomme strictement le backend `/api/v1` sans logique métier UI.

## Structure
- `src/api/apiClient.js` : client centralisé (fetch wrapper, timeout, retry, request-id, observabilité)
- `src/api/errorMessages.js` : mapping contractuel `error.code -> message UI`
- `src/services/sourcesService.js` : façade endpoints (pas de logique UI)
- `src/state/createRequestState.js` : gestion d'état contractuelle (`loading`, `success`, `error`, `over_capacity`)

## Contrat respecté
Le client attend le format figé:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

## UX contractuelle
- Timeout côté client via `AbortController`.
- Retry contrôlé sur `over_capacity`.
- `x-request-id` généré/propagé pour corrélation fullstack.
- `meta.durationMs` et `meta.requestId` exposés pour logs UI/devtools.

## Exemple d'utilisation
```js
import { ApiClient, createSourcesService, runRequest } from "./src/index.js";

const api = new ApiClient({ baseUrl: "/api/v1" });
const service = createSourcesService(api);

const { loadingState, finalState } = await runRequest(() =>
  service.downloadFromUrl({ url: "https://example.com/source.txt" }),
);
```

## Tests
- `node --test frontend/tests/apiClient.test.mjs`


## Auth Integration
- `ApiClient` injecte automatiquement le header `Authorization: Bearer <token>` via `getAccessToken`.
- En cas de `401`, callback `onUnauthorized` déclenché (stub prêt pour refresh token).
- Le parsing `BaseResponse` reste inchangé.

## Environment Base Resolution
- Résolution automatique base URL via `resolveApiBaseByEnv` (`local`, `staging`, `production`).
