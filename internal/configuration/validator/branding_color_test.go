// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package validator

import (
	"strings"
	"testing"

	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/stretchr/testify/require"
)

func TestBrandingPrimaryColorValidation(t *testing.T) {
	for _, color := range []string{"", "#e91e63", "#AABBCC", "#fff", "red", "#12345678", "#12345g", "#123456\n", "</style>"} {
		t.Run(color, func(t *testing.T) {
			config := &schema.Configuration{Branding: schema.Branding{PrimaryColor: color}}
			val := schema.NewStructValidator()
			ValidateConfiguration(config, val)
			var errors []string
			for _, err := range val.Errors() {
				if strings.HasPrefix(err.Error(), "branding:") {
					errors = append(errors, err.Error())
				}
			}
			if color == "" || color == "#e91e63" || color == "#AABBCC" {
				require.Empty(t, errors)
			} else {
				require.Equal(t, []string{"branding: option 'primary_color' must be a six-digit hex color (#RRGGBB)"}, errors)
			}
		})
	}
}
