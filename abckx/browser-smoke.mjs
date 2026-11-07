import assert from "node:assert/strict";
import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
try {
    const origin = "https://login.example.com";
    const backend = process.argv[2];
    const headers = { "X-Forwarded-Host": "login.example.com", "X-Forwarded-Proto": "https" };
    const page = await browser.newPage();
    // In-process reverse proxy: preserve the configured browser origin and CSP.
    // Every response still comes from the real binary/image, not a mock API.
    await page.route(`${origin}/**`, async route => {
        const url = new URL(route.request().url());
        const response = await page.request.fetch(new URL(url.pathname + url.search, backend).href, {
            method: route.request().method(),
            headers: { ...route.request().headers(), ...headers },
            data: route.request().postDataBuffer() ?? undefined,
        });
        await route.fulfill({ response });
    });
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("console", message => {
        // React Router reports an unmatched basename as a warning, not an error.
        if (message.type() === "error" || /Router.*basename|not able to match the URL/.test(message.text())) {
            errors.push(message.text());
        }
    });
    const response = await page.goto(origin, { waitUntil: "networkidle" });
    assert.equal(response.status(), 200);
    const username = page.locator('input#username-textfield');
    try {
        await username.waitFor({ state: "visible", timeout: 15000 });
    } catch (error) {
        console.error("Browser diagnostics:", errors, await page.locator("body").innerText());
        throw error;
    }
    assert.equal(await page.locator('input[type="password"]').isVisible(), true);
    const logo = page.locator('img[src="./static/media/logo.png"]');
    assert.equal(await logo.isVisible(), true, "official logo is visible on login");
    assert.deepEqual(await logo.evaluate(image => [image.naturalWidth, image.naturalHeight]), [180, 180]);
    for (const script of await page.locator("script[src]").evaluateAll(nodes => nodes.map(node => node.src))) {
        const bundle = await page.request.get(new URL(new URL(script).pathname, backend).href, { headers });
        assert.equal(bundle.ok(), true);
        assert.equal((await bundle.text()).includes("%VITE_BASEPATH%"), false, script);
    }
    assert.deepEqual(errors, [], "browser errors or Router basename mismatch");
    console.log("PASS: Chromium renders username/password; no Router errors or literal VITE_BASEPATH in served bundles");
} finally {
    await browser.close();
}
