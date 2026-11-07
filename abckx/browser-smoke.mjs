import assert from "node:assert/strict";
import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
try {
    const origin = "https://login.example.com";
    const backend = process.argv[2];
    const headers = { "X-Forwarded-Host": "login.example.com", "X-Forwarded-Proto": "https" };
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
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
    const accent = "rgb(233, 30, 99)";
    const computed = async (selector, property) => page.locator(selector).evaluate(
        (element, property) => getComputedStyle(element)[property], property);
    const themes = ["light", "dark", "grey", "oled"];
    const style = page.locator("style#branding-primary");
    assert.equal(await style.count(), 1);
    const nonce = await style.evaluate(element => element.nonce);
    assert.ok(nonce);
    const csp = response.headers()["content-security-policy"];
    assert.ok(csp.includes(`'nonce-${nonce}'`));
    assert.ok(!csp.includes("'unsafe-inline'"), "CSP must not be relaxed");
    assert.ok(csp.includes("default-src 'self'"), "images inherit same-origin default-src");
    const backgroundEnabled = ["default", "override"].includes(process.env.BACKGROUND_MODE);
    const background = await page.evaluate(() => {
        const style = getComputedStyle(document.body, "::before");
        return { image: style.backgroundImage, opacity: style.opacity, filter: style.filter };
    });
    assert.equal(background.image.includes("/static/media/background.png"), backgroundEnabled);
    if (backgroundEnabled) {
        assert.equal(background.opacity, "0.35");
        assert.equal(background.filter, "blur(4px)");
        const image = await page.evaluate(async () => {
            const image = new Image();
            image.src = "./static/media/background.png";
            await image.decode();
            return [image.naturalWidth, image.naturalHeight];
        });
        assert.deepEqual(image, process.env.BACKGROUND_MODE === "override" ? [180, 180] : [1280, 720]);
    }
    for (const theme of themes) {
        await page.evaluate(theme => {
            document.documentElement.dataset.theme = theme;
            document.body.dataset.theme = theme;
        }, theme);
        assert.equal(await computed("#sign-in-button", "backgroundColor"), accent, theme);
        assert.equal(await computed("#sign-in-button", "color"), "rgb(5, 5, 5)", theme);
        assert.equal(await computed("#reset-password-button", "color"), accent, theme);
        await username.focus();
        assert.equal(await computed("#username-textfield", "borderTopColor"), accent, theme);
        if (backgroundEnabled) {
            const contrast = await page.locator("#first-factor-stage > .mx-auto").evaluate(card => {
                const style = getComputedStyle(card);
                const canvas = document.createElement("canvas");
                const context = canvas.getContext("2d", { willReadFrequently: true });
                const luminance = color => {
                    context.clearRect(0, 0, 1, 1);
                    context.fillStyle = color;
                    context.fillRect(0, 0, 1, 1);
                    const [r, g, b, a] = context.getImageData(0, 0, 1, 1).data;
                    assertOpaque(a);
                    return [r, g, b].map(v => v / 255).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)
                        .reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
                };
                function assertOpaque(alpha) { if (alpha !== 255) throw new Error("card/text must be opaque"); }
                const a = luminance(style.color), b = luminance(style.backgroundColor);
                return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
            });
            // Upstream grey's foreground/background pair is below AA; preserve it.
            // Acceptance requires AA in light/dark; grey is measured, not repaired here.
            if (theme !== "grey") assert.ok(contrast >= 4.5, `${theme}: card contrast ${contrast}`);
            console.log(`PASS: ${process.env.BACKGROUND_MODE} ${theme} opaque card contrast ${contrast.toFixed(2)}:1`);
            if (process.env.SMOKE_SCREENSHOT_DIR && ["light", "dark"].includes(theme)) {
                await page.screenshot({ path: `${process.env.SMOKE_SCREENSHOT_DIR}/${process.env.BACKGROUND_MODE}-${theme}.png` });
            }
        }
    }
    assert.ok(process.env.SMOKE_PASSWORD, "disposable runtime password required");
    await username.fill("smoke");
    await page.locator('input[type="password"]').fill(process.env.SMOKE_PASSWORD);
    const login = page.waitForResponse(response => response.url().endsWith("/api/firstfactor") && response.request().method() === "POST");
    await page.locator("#sign-in-button").click();
    assert.equal((await login).status(), 200, "real first-factor authentication");
    await page.goto(`${origin}/settings`, { waitUntil: "networkidle" });
    await page.locator("#settings-menu").waitFor({ state: "visible" });
    assert.ok(new URL(page.url()).pathname.startsWith("/settings"));
    for (const theme of themes) {
        await page.evaluate(theme => {
            document.documentElement.dataset.theme = theme;
            document.body.dataset.theme = theme;
        }, theme);
        assert.equal(await computed("nav", "backgroundColor"), accent, theme);
        assert.equal(await computed("nav", "color"), "rgb(5, 5, 5)", theme);
    }
    assert.deepEqual(errors, [], "browser errors or Router basename mismatch");
    console.log("PASS: 390x844 Chromium login, link, focus and authenticated Settings accent in light/dark/grey/oled; nonce CSP intact; console clean");
} finally {
    await browser.close();
}
