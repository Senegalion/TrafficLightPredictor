import { formatAge, formatPercent, formatSeconds } from "./format";

describe("format helpers", () => {
  it("formats seconds and handles missing values", () => {
    expect(formatSeconds(12.4)).toBe("12 s");
    expect(formatSeconds(null)).toBe("–");
  });

  it("formats percentages", () => {
    expect(formatPercent(0.876)).toBe("88%");
    expect(formatPercent(undefined)).toBe("–");
  });

  it("formats ages", () => {
    expect(formatAge(42)).toBe("42 s ago");
    expect(formatAge(125)).toBe("2 min 5 s ago");
    expect(formatAge(3720)).toBe("1 h 2 min ago");
  });
});
