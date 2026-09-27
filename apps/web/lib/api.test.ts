import { afterEach, expect, it, vi } from "vitest";
import { api } from "./api";

afterEach(()=>{vi.unstubAllGlobals();vi.useRealTimers();});
it("releases a hanging request after the deadline with an actionable error",async()=>{
  vi.useFakeTimers();
  vi.stubGlobal("fetch",vi.fn((_url,options)=>new Promise((_resolve,reject)=>options.signal.addEventListener("abort",()=>reject(new DOMException("Aborted","AbortError"))))));
  const pending=expect(api("/projects/test/recommend",{})).rejects.toThrow("请求超时");
  await vi.advanceTimersByTimeAsync(90000);
  await pending;
});
it("explains disconnected services",async()=>{
  vi.stubGlobal("fetch",vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
  await expect(api("/projects")).rejects.toThrow("无法连接服务");
});
it("preserves server validation messages",async()=>{
  vi.stubGlobal("fetch",vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:"Dataset changed"}),{status:422})));
  await expect(api("/projects/test/runs",{})).rejects.toThrow("Dataset changed");
});
