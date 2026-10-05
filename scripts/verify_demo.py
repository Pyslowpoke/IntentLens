"""Verify the standalone public demo with a real browser and known answers.

Run: python scripts/verify_demo.py [--capture docs/evidence]
Requires the repository's dev dependencies and an installed Playwright Chromium.
"""
import argparse
import functools
import http.server
import json
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path)
    args = parser.parse_args()
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Handler, directory=str(ROOT / 'demo'))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p, tempfile.TemporaryDirectory() as temp:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1240, 'height': 1040}, device_scale_factor=1, reduced_motion='reduce')
            errors, external = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: external.append(request.url) if not request.url.startswith(url) else None)
            page.goto(url)
            frames = []
            def capture(name):
                if args.capture:
                    args.capture.mkdir(parents=True, exist_ok=True)
                    path = args.capture / name
                    page.screenshot(path=str(path), full_page=True)
                    frames.append(path)
            assert page.locator('#output').is_hidden()
            capture('demo-01-plan.png')
            page.locator('#generate').click()
            assert page.locator('#chart rect').count() == 5
            assert page.locator('#computed').text_content().find('57,000') >= 0
            capture('demo-02-chart.png')
            page.locator('#title').fill('区域销售表现')
            page.locator('#color').select_option('#257b91')
            page.locator('#apply').click()
            assert page.locator('#chart').get_attribute('aria-label') == '区域销售表现'
            capture('demo-03-edit.png')
            with page.expect_download() as event:
                page.locator('#svg').click()
            download = event.value
            download.save_as(str(Path(temp) / 'chart.svg'))
            assert '<svg' in (Path(temp) / 'chart.svg').read_text(encoding='utf-8')
            capture('demo-04-download.png')
            page.locator('#undo').click()
            assert page.locator('#title').input_value() == '各地区季度销售额'
            page.locator('#question').select_option('conversion')
            page.locator('#generate').click()
            assert '7.50%' in page.locator('#computed').text_content()
            page.locator('#ratio').select_option('mean')
            page.locator('#generate').click()
            assert '8.33%' in page.locator('#computed').text_content()
            with page.expect_download() as event:
                page.locator('#reproduce').click()
            event.value.save_as(str(Path(temp) / 'bundle.json'))
            bundle = json.loads((Path(temp) / 'bundle.json').read_text())
            assert len(bundle['source']) == 12 and bundle['plan']['aggregation'] == 'ratio_mean'
            for result in bundle['result']:
                rows = [row for row in bundle['source'] if row['region'] == result['region']]
                expected = sum(row['orders'] / row['visits'] for row in rows) / len(rows)
                assert abs(expected - result['value']) < 1e-12
            with page.expect_download() as event:
                page.locator('#csv').click()
            assert event.value.suggested_filename.endswith('.csv')
            page.locator('#title').fill('<img src=x onerror=alert(1)>')
            page.locator('#apply').click()
            assert page.locator('#chart img').count() == 0
            page.locator('#language').click()
            assert page.locator('html').get_attribute('lang') == 'en'
            assert 'Define the metric' in page.locator('h1').inner_text()
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.goto(url + '?lang=en')
            assert page.locator('html').get_attribute('lang') == 'en'
            assert not errors, errors
            assert not external, external
            browser.close()
            if frames:
                from PIL import Image
                originals = [Image.open(path).convert('RGB') for path in frames]
                width = max(image.width for image in originals)
                height = max(image.height for image in originals)
                images = []
                for original in originals:
                    canvas = Image.new('RGB', (width, height), '#f8f7fb')
                    canvas.paste(original, (0, 0))
                    images.append(canvas)
                images[0].save(args.capture / 'intentlens-demo.gif', save_all=True,
                               append_images=images[1:], duration=[7000, 8000, 8000, 7000], loop=0)
            print('Demo passed: known sales/ratios, actual SVG/CSV/JSON downloads, style undo, safe title, English, mobile layout, zero external requests.')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
