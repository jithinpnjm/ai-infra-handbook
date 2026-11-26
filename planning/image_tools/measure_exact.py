from playwright.sync_api import sync_playwright

html = '''
<!DOCTYPE html>
<html>
<head>
<style>
  span { display: inline-block; font-size: 24px; }
  .sans { font-family: sans-serif; }
  .mono { font-family: monospace; }
</style>
</head>
<body>
  <div><span id="w1" class="sans">creationTimestamp</span></div>
  <div><span id="w2" class="sans">lastTransitionTime,</span></div>
  <div><span id="w3" class="sans">PodScheduled</span></div>
  <div><span id="w4" class="sans">kubelet_run_podsandbox_duration_seconds</span></div>
  <div><span id="w5" class="mono">kubelet_run_podsandbox_duration_seconds</span></div>
  <div><span id="w6" class="sans">kubelet_image_pull_duration_seconds,</span></div>
  <div><span id="w7" class="mono">kubelet_image_pull_duration_seconds,</span></div>
  <div><span id="w8" class="sans">ContainersReady time</span></div>
  <div><span id="w9" class="sans">readiness probe success,</span></div>
  <div><span id="w10" class="sans">Ready condition</span></div>
</body>
</html>
'''

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html)
    for i in range(1, 11):
        box = page.locator(f"#w{i}").bounding_box()
        text = page.locator(f"#w{i}").inner_text()
        print(f"{text}: width = {box['width']:.1f}px")
    browser.close()
