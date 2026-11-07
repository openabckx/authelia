// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package schema

import (
	"fmt"
	"math"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"
)

// Sweep the full grayscale range, including the foreground-switch boundary.
func TestBrandingPrimaryContrast(t *testing.T) {
	for gray := 0; gray <= 255; gray++ {
		color := fmt.Sprintf("#%02x%02x%02x", gray, gray, gray)
		style := (Branding{PrimaryColor: color}).PrimaryStyle()
		linear := func(value float64) float64 {
			if value <= 0.04045 {
				return value / 12.92
			}
			return math.Pow((value+0.055)/1.055, 2.4)
		}
		background := linear(float64(gray) / 255)
		foreground := 1.0
		if strings.Contains(style, "--primary-foreground:#050505") {
			foreground = linear(5.0 / 255)
		}
		contrast := (math.Max(background, foreground) + 0.05) / (math.Min(background, foreground) + 0.05)
		require.GreaterOrEqual(t, contrast, 4.5, color)
	}
}

func TestBrandingPrimaryStyle(t *testing.T) {
	for _, tc := range []struct{ color, foreground string }{
		{"#000000", "#ffffff"}, {"#ffffff", "#050505"},
		{"#e91e63", "#050505"}, {"#123ABC", "#ffffff"},
	} {
		t.Run(tc.color, func(t *testing.T) {
			b := Branding{PrimaryColor: tc.color}
			require.True(t, b.ValidPrimaryColor())
			require.Equal(t, "html:root,html[data-theme],html [data-theme]{--primary:"+tc.color+";--ring:"+tc.color+";--primary-foreground:"+tc.foreground+";}", b.PrimaryStyle())
		})
	}
	for _, color := range []string{"", "#fff", "red", "#12345678", "#12345g", " #123456", "#123456\n", "#123456;}", "</style><script>alert(1)</script>"} {
		b := Branding{PrimaryColor: color}
		require.Equal(t, color == "", b.ValidPrimaryColor(), color)
		require.Empty(t, b.PrimaryStyle(), color)
	}
}
