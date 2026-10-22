import { describe, expect, it } from "vitest";

import { defaultSectionForRole, roleLabel } from "./navigation";

describe("role navigation", () => {
  it("maps every MVP role to a Chinese label and first section", () => {
    expect(roleLabel("PATIENT")).toBe("患者");
    expect(roleLabel("CAREGIVER")).toBe("家属");
    expect(roleLabel("DOCTOR")).toBe("医生");
    expect(roleLabel("HOSPITAL_ADMIN")).toBe("医院");
    expect(roleLabel("REGULATOR")).toBe("政府");
    expect(roleLabel("PHARMA")).toBe("药企");
    expect(defaultSectionForRole("PHARMA")).toBe("pharma");
  });
});
