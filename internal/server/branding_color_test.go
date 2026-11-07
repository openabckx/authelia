// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package server

import (
	"os"
	"regexp"
	"testing"
	"text/template"

	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/authelia/authelia/v4/internal/mocks"
	"github.com/stretchr/testify/require"
)

func TestBrandingStyleEscapesNonce(t *testing.T) {
	data := TemplatedFileCommonData{Branding: schema.Branding{PrimaryColor: "#e91e63"}, CSPNonce: `"><script>alert(1)</script>`}
	require.Contains(t, data.BrandingStyle(), `nonce="&#34;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"`)
	require.NotContains(t, data.BrandingStyle(), `<script>`)
}

func TestServeBrandingPrimaryColor(t *testing.T) {
	source, err := os.ReadFile("../../web/index.html")
	require.NoError(t, err)
	tmpl, err := template.New("index.html").Parse(string(source))
	require.NoError(t, err)
	for _, color := range []string{"", "#e91e63", "</style><script>alert(1)</script>"} {
		t.Run(color, func(t *testing.T) {
			mock := mocks.NewMockAutheliaCtx(t)
			mock.Ctx.Configuration.Branding = schema.Branding{PrimaryColor: color}
			ServeTemplatedFile(tmpl, NewTemplatedFileOptions(&mock.Ctx.Configuration))(mock.Ctx)
			body := string(mock.Ctx.Response.Body())
			require.NotContains(t, body, "<script>alert(1)</script>")
			styles := regexp.MustCompile(`<style nonce="([a-zA-Z0-9]+)" id="branding-primary">([^<]+)</style>`).FindStringSubmatch(body)
			if color != "#e91e63" {
				require.NotContains(t, body, `id="branding-primary"`)
				return
			}
			require.Len(t, styles, 3)
			require.Contains(t, string(mock.Ctx.Response.Header.Peek("Content-Security-Policy")), "'nonce-"+styles[1]+"'")
			require.Equal(t, mock.Ctx.Configuration.Branding.PrimaryStyle(), styles[2])
		})
	}
}
