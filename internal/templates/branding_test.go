// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package templates

import (
	"bytes"
	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/stretchr/testify/require"
	"testing"
)

func TestEmailBranding(t *testing.T) {
	for _, text := range []string{"Desenvolvido por abckx", "<script>alert(1)</script>", ""} {
		for _, url := range []string{"https://abckx.com.br", ""} {
			t.Run(text+url, func(t *testing.T) {
				provider, err := New(Config{Branding: schema.Branding{Text: &text, URL: url}})
				require.NoError(t, err)

				cases := []struct {
					tmpl *EmailTemplate
					data any
				}{
					{provider.GetEventEmailTemplate(), EmailEventValues{}},
					{provider.GetIdentityVerificationJWTEmailTemplate(), EmailIdentityVerificationJWTValues{}},
					{provider.GetIdentityVerificationOTCEmailTemplate(), EmailIdentityVerificationOTCValues{}},
				}
				for _, tc := range cases {

					var html, plain bytes.Buffer
					require.NoError(t, tc.tmpl.HTML.Execute(&html, tc.data))
					require.NoError(t, tc.tmpl.Text.Execute(&plain, tc.data))
					require.NotContains(t, html.String(), "Powered by")
					require.NotContains(t, plain.String(), "Powered by")
					require.Contains(t, plain.String(), text)
					require.NotContains(t, html.String(), "<script>")
					if text != "" && url != "" {
						require.Contains(t, html.String(), `href="`+url+`"`)
						require.Contains(t, plain.String(), text+" "+url)
					} else {
						require.NotContains(t, html.String(), "abckx.com.br")
					}
				}
			})
		}
	}
}
