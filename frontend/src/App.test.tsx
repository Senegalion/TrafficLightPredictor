import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import { intersections, mockFetch, observations, prediction } from "./test/fixtures";

// Leaflet needs a real browser layout engine; the map is covered by manual testing.
vi.mock("./components/IntersectionMap", () => ({ IntersectionMap: () => <div data-testid="map" /> }));

const modelInfo = {
  model_version: "tlp-gbm-test",
  trained_at: "2026-11-16T10:00:00Z",
  training_data_origin: "SYNTHETIC",
  signals: ["LDZ-KOS-STR-S1"],
  dataset_time_range: ["2026-10-04T00:00:00Z", "2026-10-31T23:59:59Z"],
  reliability_policy: { min_confidence: 0.8, max_interval_width_s: 20, max_anchor_age_s: 900 },
};

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        "GET /api/v1/intersections/1/observations": () => ({
          body: { content: observations, page: 0, size: 15, totalElements: 1, totalPages: 1 },
        }),
        "GET /api/v1/intersections": () => ({ body: intersections }),
        "GET /api/v1/model": () => ({ body: modelInfo }),
        "POST /api/v1/predictions": () => ({ status: 201, body: prediction() }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", "/");
  });

  it("preselects the intersection from the URL and updates the URL on selection", async () => {
    window.history.replaceState(null, "", "/?intersection=LDZ-SIE-NAR");
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Sienkiewicza / Narutowicza" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Kościuszki/ }));
    expect(window.location.search).toBe("?intersection=LDZ-KOS-STR");
  });

  it("shows the safety notice and the intersection list", async () => {
    render(<App />);
    expect(screen.getByRole("note", { name: "Safety notice" })).toHaveTextContent("not connected to any traffic signal");
    expect(await screen.findByRole("button", { name: /Kościuszki/ })).toBeInTheDocument();
    expect(await screen.findByText("SYNTHETIC")).toBeInTheDocument();
  });

  it("selects an intersection, requests a prediction and shows history", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: /Kościuszki/ }));

    expect(screen.getByRole("heading", { name: "Al. Kościuszki / Struga" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /Al. Tadeusza Kościuszki/ })).toBeChecked();
    expect(screen.getAllByText("Sample configuration")).toHaveLength(2);

    const history = await screen.findByRole("region", { name: "Recent observations" });
    expect(await within(history).findByText("Simulated")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Predict now" }));

    const result = await screen.findByRole("article", { name: "Prediction result" });
    expect(within(result).getByText("~12 s")).toBeInTheDocument();
    expect(within(result).getByText("Simulated data")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/predictions",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ intersectionId: 1, signalId: 10 }) }),
    );
  });

  it("shows API errors", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        "GET /api/v1/intersections": () => ({ status: 500, body: { title: "Internal error", detail: "Database down" } }),
        "GET /api/v1/model": () => ({ status: 503, body: { title: "Model unavailable" } }),
      }),
    );
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Database down");
    expect(await screen.findByText("The ML service is not reachable right now.")).toBeInTheDocument();
  });
});
