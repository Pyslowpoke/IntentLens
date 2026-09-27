import { it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { Button } from "./button";
it("retains accessibility and disabled state for unavailable actions", () => {
  const html = renderToStaticMarkup(
    <Button disabled aria-label="Export PNG" variant="outline">
      PNG
    </Button>,
  );
  expect(html).toContain("disabled");
  expect(html).toContain('aria-label="Export PNG"');
  expect(html).toContain("border-slate-200");
});
