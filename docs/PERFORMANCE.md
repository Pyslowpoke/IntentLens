# Measured performance and initial budgets

Evidence: `evidence/benchmark/results.json` and `evidence/browser-timings.json`. Fixed seed 20260927. Windows 11 build 26200, Intel64 family 6/model 183, 32 logical CPUs, 34,070,192,128 bytes system RAM. Python 3.12.14. Four columns, 20 groups, three compute repetitions per size. No model requests.

| Rows | First compute ms | Repeat 2 / 3 ms | Serialized result bytes | Observed RSS after repeat 3 |
|---:|---:|---:|---:|---:|
| 10,000 | 2.94 | 2.18 / 1.78 | 1,129 | 108,335,104 |
| 100,000 | 6.94 | 5.86 / 5.36 | 1,151 | 230,068,224 |
| 1,000,000 | 33.73 | 32.04 / 30.77 | 1,171 | 292,974,592 |

The first Matplotlib render plus PNG/SVG/PDF took 2622 ms, then 345/295 ms in the already-loaded process. JSON cache reads measured 5–16 ms. RSS observations are **not sampled peak memory**, and the process accumulates imports across cases. The first case is cold for imported plotting modules; later cases are warm. Snapshot parsing/writing is not included in the compute column. These numbers do not represent millions of DOM marks or general arbitrary queries.

Browser timing records include task queue, Python startup, rendering and all exports; initial unoptimized Plotly took about 16–18 seconds per uncached chart. Reusing one Chromium session across PNG/SVG/PDF produced 4.2–10.2 second observed task times in the final run (including exact-size export). Initial UI: 445 ms; first chart: 4198 ms; title: 10141 ms; color: 9448 ms; sort: 4840 ms; filter: 9996 ms; undo: 4305 ms; already-produced PNG download: 22 ms. Caches and concurrently running verification tasks affect these measurements. No competitor comparison is implied.

Initial **regression targets on this reference host**, chosen after measurements: million-row/20-group compute under 150 ms; result serialization under 4 KiB; warm static Matplotlib export under 1.5 s; ordinary Plotly end-to-end task under 15 s once dependencies are installed; worker timeout at 120 s and sampled process-tree RSS cap at 3 GiB. These are narrow engineering budgets, not an SLA across devices. Browser first UI paint is recorded independently. Model latency is unavailable, not zero.

Reproduce with `python -m scripts.benchmark` and `node scripts/capture_demo.mjs` while the app runs. For strict peak-memory or statistical tail-latency comparisons, add continuous memory sampling and many more repetitions; this three-repeat local record is not enough to claim universal performance.
