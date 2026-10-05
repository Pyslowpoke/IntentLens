import {test,expect} from "@playwright/test";
test("empty first sheet cannot silently import; selected second sheet with null category renders",async({page})=>{
  await page.route("**/api/model/status",r=>r.fulfill({json:{provider:"rule",model:"",ready:false}}));
  await page.addInitScript(()=>localStorage.setItem("intentlens.preferences.v1",JSON.stringify({language:"en",nickname:"",engine:"matplotlib",theme:"light"})));
  // Exercise slow initial discovery: the user's new project must stay selected.
  let initialProjects = true;
  await page.route("**/api/projects", async route => {
    if (route.request().method() === "GET" && initialProjects) {
      initialProjects = false;
      const response = await route.fetch();
      await new Promise(resolve => setTimeout(resolve, 1500));
      await route.fulfill({response});
    } else await route.continue();
  });
  await page.goto("/");
  await page.getByRole("button",{name:"New analysis",exact:true}).click();
  await page.getByRole("button",{name:"Import data",exact:true}).click();
  await page.locator('input[type="file"]').setInputFiles('../../samples/regression-multisheet.xlsx');
  await expect(page.getByRole("button",{name:"Parse & preview",exact:true})).toBeDisabled();
  await expect(page.getByLabel("Worksheet",{exact:true}).locator('option')).toHaveCount(3);
  await page.getByLabel("Worksheet",{exact:true}).selectOption('业务数据');
  await page.getByText("Header row",{exact:true}).locator('input').fill('2');
  await page.getByRole("button",{name:"Parse & preview",exact:true}).click();
  await expect(page.getByRole("button",{name:"Import snapshot",exact:true})).toBeEnabled();
  await page.getByRole("button",{name:"Import snapshot",exact:true}).click();
  await expect(page.getByText('3 rows')).toBeVisible();
  await page.getByRole("button",{name:"Generate plans",exact:true}).click();
  await page.locator('.proposal').first().click();
  const chart=page.locator('.chart-preview img');
  await expect(chart).toBeVisible({timeout:60000});
  await expect.poll(()=>chart.evaluate((image:HTMLImageElement)=>image.complete && image.naturalWidth>300)).toBe(true);
  await page.reload();
  await expect(page.getByLabel('Analysis conversation')).toContainText('Rule mode');
});
