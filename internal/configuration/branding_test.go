// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package configuration

import (
	"encoding/json"
	"testing"

	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/stretchr/testify/require"
)

func TestBrandingEnvironment(t *testing.T) {
	for _, text := range []string{"Desenvolvido por abckx", ""} {
		t.Run(text, func(t *testing.T) {
			t.Setenv("AUTHELIA_BRANDING_TEXT", text)
			t.Setenv("AUTHELIA_BRANDING_URL", "https://abckx.com.br")
			_, config, err := Load(schema.NewStructValidator(), NewEnvironmentSource(DefaultEnvPrefix, DefaultEnvDelimiter))
			require.NoError(t, err)
			data, err := json.Marshal(config)
			require.NoError(t, err)
			var decoded map[string]json.RawMessage
			require.NoError(t, json.Unmarshal(data, &decoded))
			require.Contains(t, decoded, "branding")
			var branding map[string]string
			require.NoError(t, json.Unmarshal(decoded["branding"], &branding))
			require.Equal(t, text, branding["text"])
			require.Equal(t, "https://abckx.com.br", branding["url"])
		})
	}
}
