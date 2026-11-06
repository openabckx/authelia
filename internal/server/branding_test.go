// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package server

import (
	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/authelia/authelia/v4/internal/mocks"
	"github.com/stretchr/testify/require"
	"os"
	"testing"
	"text/template"
)

func TestServeBranding(t *testing.T) {
	for _, text := range []string{"Desenvolvido por abckx", `"><script>alert(1)</script>`, ""} {
		t.Run(text, func(t *testing.T) {
			source, err := os.ReadFile("../../web/index.html")
			require.NoError(t, err)
			tmpl, err := template.New("index.html").Parse(string(source))
			require.NoError(t, err)
			mock := mocks.NewMockAutheliaCtx(t)
			mock.Ctx.Configuration.Branding = schema.Branding{Text: &text, URL: "https://abckx.com.br/?a=1&b=2"}
			mock.Ctx.Request.Header.Set("X-Forwarded-Proto", "https")
			mock.Ctx.Request.Header.Set("X-Forwarded-Host", "auth.example.com")
			ServeTemplatedFile(tmpl, NewTemplatedFileOptions(&mock.Ctx.Configuration))(mock.Ctx)
			require.Equal(t, 200, mock.Ctx.Response.StatusCode())
			body := string(mock.Ctx.Response.Body())
			require.Contains(t, body, `data-brandingcustom="true"`)
			require.Contains(t, body, `data-brandingtext="`+template.HTMLEscapeString(text)+`"`)
			require.Contains(t, body, `data-brandingurl="https://abckx.com.br/?a=1&amp;b=2"`)
			require.NotContains(t, body, `<script>alert(1)</script>`)
		})
	}
}
