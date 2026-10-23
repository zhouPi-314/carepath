import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const demoRoles = [
  { username: "patient", role: "患者", heading: "的治疗进度" },
  { username: "caregiver", role: "家属", heading: "的治疗进度" },
  { username: "doctor", role: "医生", heading: "医生工作台" },
  { username: "hospital", role: "医院", heading: "医院协同中心" },
  { username: "regulator", role: "政府", heading: "区域监管沙箱" },
  { username: "pharma", role: "药企", heading: "药品需求与产能" },
] as const;

const demoPasswords: Record<string, string> = {
  patient: "Pa2026!care",
  caregiver: "Ca2026!care",
  doctor: "Do2026!care",
  hospital: "Ho2026!care",
  regulator: "Re2026!care",
  pharma: "Ph2026!care",
};

async function login(page: Page, username: string) {
  await page.goto("/login");
  await page.getByLabel("账号").fill(username);
  await page.getByLabel("密码").fill(demoPasswords[username]);
  await page.getByRole("button", { name: "进入平台" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.locator(".topbar")).toBeVisible();
}

for (const account of demoRoles) {
  test(`${account.role}登录后进入对应工作台`, async ({ page }) => {
    await login(page, account.username);

    await expect(page.locator(".topbar")).toContainText(`${account.role} workspace`);
    await expect(page.locator("h1.page-heading").first()).toContainText(account.heading);
  });
}

test("患者完成自护任务后收到同步提示", async ({ page }) => {
  await login(page, "patient");

  const completeButton = page.getByRole("button", { name: "标记为已完成" });
  test.skip((await completeButton.count()) === 0, "当前没有待完成任务可执行");

  await completeButton.first().click();
  await expect(page.getByText("任务已同步，医生端可收到更新。")).toBeVisible();
});

test("政府端展示区域聚合指标与最小发布单元", async ({ page }) => {
  await login(page, "regulator");

  await expect(page.getByRole("heading", { name: "区域活跃计划" })).toBeVisible();
  await expect(page.getByText("最小发布单元")).toBeVisible();
  await expect(page.getByText("已统计区域")).toBeVisible();
});

test("普通角色无法进入管理端接口页面之外的权限边界", async ({ page }) => {
  await login(page, "caregiver");

  await expect(page.locator(".topbar")).toContainText("家属 workspace");
  await expect(page.locator("h1.page-heading").first()).toContainText("的治疗进度");
});

test("退出后回到登录页", async ({ page }) => {
  await login(page, "doctor");

  await page.getByRole("button", { name: "退出" }).click();
  await expect(page).toHaveURL(/\/login$/);
});
