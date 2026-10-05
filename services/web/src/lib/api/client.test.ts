import { tokenStorage } from "@/lib/auth/tokenStorage";

import { ApiError, describeError } from "./ApiError";
import { apiRequest, buildUrl, setUnauthorizedHandler } from "./client";

function mockFetch(status: number, body: unknown, headers: Record<string, string> = {}) {
  const fetchMock = vi
    .fn()
    .mockResolvedValue(
      new Response(body === null ? null : JSON.stringify(body), { status, headers }),
    );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
  setUnauthorizedHandler(null);
});

describe("buildUrl", () => {
  it("prefixes /api/v1, repeats array params and skips empty values", () => {
    expect(buildUrl("/applications", { status: ["APPLIED", "OFFER"], q: "", page: 2 })).toBe(
      "http://api.test/api/v1/applications?status=APPLIED&status=OFFER&page=2",
    );
  });
});

describe("apiRequest", () => {
  it("sends the bearer token and JSON body", async () => {
    tokenStorage.set("token-123");
    const fetchMock = mockFetch(200, { ok: true });

    await apiRequest("/applications", { method: "POST", body: { role: "SRE" } });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.headers).toMatchObject({
      Authorization: "Bearer token-123",
      "Content-Type": "application/json",
    });
    expect(init.body).toBe('{"role":"SRE"}');
  });

  it("returns undefined for 204 No Content", async () => {
    mockFetch(204, null);
    await expect(apiRequest("/notes/1", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("turns the API error body into an ApiError with the toast summary", async () => {
    mockFetch(409, {
      error: { code: "invalid_status_transition", message: "Cannot move", request_id: "r1" },
    });

    const error = await apiRequest("/applications/1/status").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("invalid_status_transition");
    expect((error as ApiError).requestId).toBe("r1");
    expect(describeError(error)).toBe("409 Conflict · Cannot move");
  });

  it("reads FastAPI 422 validation errors", async () => {
    mockFetch(422, { detail: [{ loc: ["body", "role"], msg: "Field required" }] });
    const error = (await apiRequest("/applications").catch((e: unknown) => e)) as ApiError;
    expect(error.summary).toBe("422 Unprocessable Entity · role: Field required");
  });

  it("calls the unauthorized handler on 401 when a token was sent", async () => {
    tokenStorage.set("expired");
    const onUnauthorized = vi.fn();
    setUnauthorizedHandler(onUnauthorized);
    mockFetch(401, { error: { code: "unauthorized", message: "Invalid token", request_id: null } });

    await expect(apiRequest("/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });
});
