import { test, expect } from "@playwright/test";
test("real import → recommendation → render → five edits → export → reload", async ({
  page,
}) => {
  await page.route("**/api/model/status", route => route.fulfill({json:{provider:"rule",model:"",ready:false}}));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "先理解问题，再看见答案。" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../../docs/evidence/01-workbench.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "新建分析项目" }).click();
  await page.getByRole("button", { name: "销售订单", exact: true }).click();
  await expect(page.getByText("720 行")).toBeVisible();
  await page.getByRole("button", { name: "生成分析方案" }).click();
  await expect(page.locator(".proposal")).toHaveCount(3);
  await page.locator(".proposal").filter({ hasText: "地区 ·" }).click();
  await expect(page.locator(".chart-preview iframe")).toBeVisible({
    timeout: 120000,
  });
  await expect(page.getByRole("heading", {name: "AI 决策建议"})).toBeVisible();
  await page.route("**/api/projects/*/decision", route => route.request().method()==="POST" ? route.fulfill({status:422,json:{detail:"Configure scripts/configure-deepseek.ps1"}}) : route.continue());
  await page.getByRole("button", {name: "生成决策建议", exact: true}).click();
  await expect(page.locator('p[role="alert"]')).toContainText("configure-deepseek.ps1");
  await expect(page.frameLocator(".chart-preview iframe").locator(".barlayer .point").first()).toBeVisible();
  async function revision() {
    return (await page.locator(".engine-tag").innerText()).split(" · ")[1];
  }
  async function edit(text: string) {
    const before = await revision();
    await page.getByLabel("Chart edit").fill(text);
    await page.getByRole("button", { name: "Apply edit" }).click();
    await expect.poll(revision, { timeout: 120000 }).not.toBe(before);
  }
  await edit("标题：区域销售表现");
  await edit("改成蓝色");
  await edit("按数值降序");
  await edit("筛选 地区=华东");
  await edit("撤销");
  await expect(
    page.getByRole("link", { name: "PNG", exact: true }),
  ).toBeVisible();
  const png = await page
    .getByRole("link", { name: "PNG", exact: true })
    .getAttribute("href");
  expect((await page.request.get(png!)).status()).toBe(200);
  const downloadEvent=page.waitForEvent("download");
  await page.getByRole("link",{name:"一键下载图片",exact:true}).click();
  const downloaded=await downloadEvent;
  expect(downloaded.suggestedFilename()).toMatch(/^intentlens-.*\.png$/);
  expect(await downloaded.failure()).toBeNull();
  await page.screenshot({
    path: "../../docs/evidence/02-analysis.png",
    fullPage: true,
  });
  const head = await revision();
  await page.reload();
  await expect.poll(revision).toBe(head);
  await page.getByRole("button", { name: "版本记录", exact: true }).click();
  await expect(page.locator(".history-item")).toHaveCount(6);
  await page.screenshot({
    path: "../../docs/evidence/03-history.png",
    fullPage: true,
  });
});
