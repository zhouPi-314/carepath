import { describe, expect, it } from "vitest";

import { ApiError, explainApiError } from "./api";

describe("API errors", () => {
  it("turns known status codes into actionable Chinese messages", () => {
    expect(explainApiError(new ApiError(401, "expired"))).toContain("重新登录");
    expect(explainApiError(new ApiError(403, "denied"))).toContain("权限");
    expect(explainApiError(new ApiError(500, "boom"))).toContain("系统");
  });
});
