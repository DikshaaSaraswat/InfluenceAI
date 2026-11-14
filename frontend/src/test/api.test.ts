import { describe, expect, it } from "vitest";
import { API_BASE_URL } from "@/lib/api";

describe("FastAPI configuration", () => {
  it("uses the documented local backend by default", () => {
    expect(API_BASE_URL).toBe("http://127.0.0.1:8000");
  });
});
