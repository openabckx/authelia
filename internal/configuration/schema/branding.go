// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package schema

import (
	"encoding/hex"
	"fmt"
	"math"
)

// Branding configures the portal accent and portal/notification footer. Nil text preserves
// the upstream branding; an explicitly empty text hides it.
type Branding struct {
	Text              *string  `koanf:"text" yaml:"text,omitempty" toml:"text,omitempty" json:"text,omitempty"`
	URL               string   `koanf:"url" yaml:"url,omitempty" toml:"url,omitempty" json:"url,omitempty"`
	PrimaryColor      string   `koanf:"primary_color" yaml:"primary_color,omitempty" toml:"primary_color,omitempty" json:"primary_color,omitempty"`
	BackgroundImage   bool     `koanf:"background_image" yaml:"background_image,omitempty" toml:"background_image,omitempty" json:"background_image,omitempty"`
	BackgroundOpacity *float64 `koanf:"background_opacity" yaml:"background_opacity,omitempty" toml:"background_opacity,omitempty" json:"background_opacity,omitempty"`
	BackgroundBlur    float64  `koanf:"background_blur" yaml:"background_blur,omitempty" toml:"background_blur,omitempty" json:"background_blur,omitempty"`
}

// ValidPrimaryColor permits only an unset value or an opaque six-digit hex color.
func (b Branding) ValidPrimaryColor() bool {
	if b.PrimaryColor == "" {
		return true
	}
	if len(b.PrimaryColor) != 7 || b.PrimaryColor[0] != '#' {
		return false
	}
	_, err := hex.DecodeString(b.PrimaryColor[1:])
	return err == nil
}

// PrimaryStyle emits only validated hex literals, never arbitrary operator CSS.
// Higher specificity than upstream theme selectors avoids depending on Vite's
// stylesheet insertion order. A white/near-black foreground maximizes contrast.
func (b Branding) PrimaryStyle() string {
	if b.PrimaryColor == "" || !b.ValidPrimaryColor() {
		return ""
	}
	rgb, _ := hex.DecodeString(b.PrimaryColor[1:])
	luminance := 0.0
	for i, weight := range []float64{0.2126, 0.7152, 0.0722} {
		channel := float64(rgb[i]) / 255
		if channel <= 0.04045 {
			channel /= 12.92
		} else {
			channel = math.Pow((channel+0.055)/1.055, 2.4)
		}
		luminance += weight * channel
	}
	foreground := "#ffffff"
	// WCAG relative-luminance contrast; #050505 has luminance 5/255/12.92.
	if (luminance+0.05)/(5.0/255/12.92+0.05) > 1.05/(luminance+0.05) {
		foreground = "#050505"
	}
	return fmt.Sprintf("html:root,html[data-theme],html [data-theme]{--primary:%s;--ring:%s;--primary-foreground:%s;}", b.PrimaryColor, b.PrimaryColor, foreground)
}

// Visible reports whether the footer should be rendered.
func (b Branding) Visible() bool {
	return b.Text == nil || *b.Text != ""
}
