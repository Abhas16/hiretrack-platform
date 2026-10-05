import { getConfig, loadConfig, setConfigForTests } from "./config";

function fakeFetch(status: number, body: unknown): typeof fetch {
  return vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));
}

afterEach(() =>
  setConfigForTests({ apiBaseUrl: "http://api.test", environment: "test", version: "test" }),
);

describe("loadConfig", () => {
  it("loads /config.json and strips a trailing slash from the API URL", async () => {
    const config = await loadConfig(
      fakeFetch(200, {
        apiBaseUrl: "https://api.example.com/",
        environment: "dev",
        version: "abc123",
      }),
    );
    expect(config).toEqual({
      apiBaseUrl: "https://api.example.com",
      environment: "dev",
      version: "abc123",
    });
    expect(getConfig().apiBaseUrl).toBe("https://api.example.com");
  });

  it("fills in defaults for optional fields", async () => {
    const config = await loadConfig(fakeFetch(200, { apiBaseUrl: "http://localhost:8000" }));
    expect(config.environment).toBe("unknown");
  });

  it("fails clearly when the file is missing or invalid", async () => {
    await expect(loadConfig(fakeFetch(404, {}))).rejects.toThrow("HTTP 404");
    await expect(loadConfig(fakeFetch(200, { apiBaseUrl: "not-a-url" }))).rejects.toThrow(
      "Invalid /config.json",
    );
  });
});
