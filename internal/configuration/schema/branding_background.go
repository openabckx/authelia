// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package schema

import (
	"fmt"
	"math"
)

// ValidBackground constrains every CSS number, including non-finite YAML values.
func (b Branding) ValidBackground() bool {
	opacity := b.BackgroundOpacity
	return (opacity == nil || (!math.IsNaN(*opacity) && *opacity >= 0 && *opacity <= 1)) &&
		!math.IsNaN(b.BackgroundBlur) && b.BackgroundBlur >= 0 && b.BackgroundBlur <= 20
}

// BackgroundStyle uses a fixed same-origin asset; operator input cannot become CSS.
// The image is translucent over the upstream theme, never over the opaque card.
func (b Branding) BackgroundStyle() string {
	if !b.BackgroundImage || !b.ValidBackground() {
		return ""
	}
	opacity := 0.25
	if b.BackgroundOpacity != nil {
		opacity = *b.BackgroundOpacity
	}
	return fmt.Sprintf(`html:root{--branding-background-opacity:%g;--branding-background-blur:%gpx;}body{isolation:isolate;}body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background-image:url("./static/media/background.png");background-size:cover;background-position:center;opacity:var(--branding-background-opacity);filter:blur(var(--branding-background-blur));}#root div[id$="-stage"]>.mx-auto{background:var(--background);color:var(--foreground);border-radius:1rem;padding-top:1rem;padding-bottom:1rem;}`, opacity, b.BackgroundBlur)
}
