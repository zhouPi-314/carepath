import { describe, expect, it } from "vitest";

import { defaultSectionForRole, roleLabel } from "./navigation";

describe("role navigation", () => {
  it("maps every role to a Chinese label and first section", () => {
    expect(roleLabel("PATIENT")).toBe("用户 · 病患");
    expect(roleLabel("CAREGIVER")).toBe("用户 · 家属");
    expect(roleLabel("DOCTOR")).toBe("医院 · 医生");
    expect(roleLabel("HOSPITAL_ADMIN")).toBe("医院 · 管理");
    expect(roleLabel("REGULATOR")).toBe("政府 · 入驻认证");
    expect(roleLabel("PHARMA")).toBe("药企");
    expect(roleLabel("COMMUNITY_ORG")).toBe("社区与志愿组织");
    expect(defaultSectionForRole("PHARMA")).toBe("pharma");
    expect(defaultSectionForRole("COMMUNITY_ORG")).toBe("community");
  });
});
