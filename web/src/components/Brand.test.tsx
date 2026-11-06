// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

import { render, screen } from "@testing-library/react";

import Brand from "@components/Brand";

vi.mock("@constants/constants", () => ({
    EncodedName: Array.from("Authelia".split("").map((c) => c.charCodeAt(0))),
    EncodedURL: Array.from("https://www.authelia.com".split("").map((c) => c.charCodeAt(0))),
}));

vi.stubGlobal(
    "atob",
    vi.fn((str) => str),
);

beforeEach(() => {
    document.body.dataset.brandingcustom = "false";
    document.body.dataset.brandingtext = "";
    document.body.dataset.brandingurl = "";
    document.body.dataset.privacypolicyurl = "";
});

it.each(["https://abckx.com.br", "", "javascript:alert(1)"])("renders runtime text safely with URL %s", (url) => {
    document.body.dataset.brandingcustom = "true";
    document.body.dataset.brandingtext = "<img src=x onerror=alert(1)>";
    document.body.dataset.brandingurl = url;
    const { container } = render(<Brand />);
    expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
    if (url.startsWith("https://")) {
        expect(screen.getByRole("link")).toHaveAttribute("href", url);
    } else {
        expect(screen.queryByRole("link")).not.toBeInTheDocument();
    }
});

it.each(["", "https://example.com/privacy"])("hides empty branding and preserves privacy %s", (privacy) => {
    document.body.dataset.brandingcustom = "true";
    document.body.dataset.privacypolicyurl = privacy;
    const { container } = render(<Brand />);
    expect(screen.queryByText("Powered by Authelia")).not.toBeInTheDocument();
    expect(screen.queryByRole("separator")).not.toBeInTheDocument();
    if (privacy) {
        expect(screen.getByRole("link")).toHaveAttribute("href", privacy);
    } else {
        expect(container).toBeEmptyDOMElement();
    }
});

it("renders without crashing", () => {
    render(<Brand />);
});

it("renders link with correct text", () => {
    render(<Brand />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "https://www.authelia.com");
    expect(link).toHaveTextContent("Powered by Authelia");
});

it("renders privacy policy when enabled", () => {
    document.body.dataset.privacypolicyurl = "https://example.com";
    render(<Brand />);
    expect(screen.getByText("Privacy Policy")).toBeInTheDocument();
});

it("does not render privacy policy when disabled", () => {
    document.body.dataset.privacypolicyurl = "";
    render(<Brand />);
    expect(screen.queryByText("Privacy Policy")).not.toBeInTheDocument();
});
