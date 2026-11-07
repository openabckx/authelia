// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package schema

import (
	"github.com/stretchr/testify/require"
	"math"
	"testing"
)

func TestBackgroundStyleRejectsNonFiniteValues(t *testing.T) {
	for _, value := range []float64{math.NaN(), math.Inf(1), math.Inf(-1), -1, 21} {
		require.Empty(t, (Branding{BackgroundImage: true, BackgroundBlur: value}).BackgroundStyle())
		require.Empty(t, (Branding{BackgroundImage: true, BackgroundOpacity: &value}).BackgroundStyle())
	}
}

func TestBackgroundStyleZeroAndDefaults(t *testing.T) {
	zero := 0.0
	require.Contains(t, (Branding{BackgroundImage: true, BackgroundOpacity: &zero}).BackgroundStyle(), "--branding-background-opacity:0;")
	require.Contains(t, (Branding{BackgroundImage: true}).BackgroundStyle(), "--branding-background-opacity:0.25;")
	require.Empty(t, (Branding{}).BackgroundStyle())
}
