import { expect, it } from "vitest";
import { defaults, parsePreferences, preferredSpec } from "./preferences";

it("recovers corrupt settings and validates persisted preferences", () => {
  expect(parsePreferences("broken")).toEqual(defaults);
  expect(parsePreferences("null")).toEqual(defaults);
  expect(parsePreferences(JSON.stringify({language:"de",nickname:"  Alex  ",engine:"unknown",theme:"bad"}))).toEqual({...defaults,nickname:"Alex"});
});
it("uses preferred engine only when compatible without mutating an existing spec", () => {
  const original={kind:"bar",engine:"plotly",theme:"light"};
  const prefs={...defaults,engine:"altair",theme:"dark"};
  expect(preferredSpec(original,prefs,{altair:{kinds:["bar"]}})).toEqual({spec:{kind:"bar",engine:"altair",theme:"dark"},fallback:false});
  expect(preferredSpec(original,prefs,{altair:{kinds:["line"]}}).spec.engine).toBe("auto");
  expect(original.engine).toBe("plotly");
});

it("honors a model's explicit alternative without changing saved preferences", () => {
  const prefs={...defaults,engine:"matplotlib"};
  const spec={kind:"bar",engine:"plotly",theme:"report"};
  expect(preferredSpec(spec,prefs,{plotly:{kinds:["bar"]}},true).spec).toEqual(spec);
  expect(prefs.engine).toBe("matplotlib");
  expect(preferredSpec({...spec,engine:"auto"},prefs,{matplotlib:{kinds:["bar"]}},true).spec.engine).toBe("matplotlib");
});
