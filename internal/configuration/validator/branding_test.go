// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package validator

import (
	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/stretchr/testify/assert"
	"strings"
	"testing"
)

func TestBrandingURLValidation(t *testing.T) {
	for _, tc := range []struct {
		url     string
		invalid bool
	}{
		{"", false}, {"https://abckx.com.br", false},
		{"http://example.com", true}, {"javascript:alert(1)", true},
		{"//example.com", true}, {"https:", true}, {"https:///path", true},
		{"https://user:pass@example.com", true}, {"https://example.com\n", true},
	} {
		t.Run(tc.url, func(t *testing.T) {
			config := &schema.Configuration{Branding: schema.Branding{URL: tc.url}}
			val := schema.NewStructValidator()
			ValidateConfiguration(config, val)
			found := false
			for _, err := range val.Errors() {
				if strings.HasPrefix(err.Error(), "branding:") {
					found = true
				}
			}
			assert.Equal(t, tc.invalid, found)
		})
	}
}
