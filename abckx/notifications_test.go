// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package abckx

import (
	"bytes"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"testing"
	"unicode/utf8"

	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/authelia/authelia/v4/internal/templates"
	"github.com/stretchr/testify/require"
)

func TestNotificationOverlay(t *testing.T) {
	field := regexp.MustCompile(`\.[A-Z][A-Za-z]+`)
	for _, name := range []string{"Event", "IdentityVerificationJWT", "IdentityVerificationOTC"} {
		for _, ext := range []string{"html", "txt"} {
			filename := name + "." + ext
			t.Run(filename, func(t *testing.T) {
				data, err := os.ReadFile(filepath.Join("templates", filename))
				require.NoError(t, err)
				require.True(t, utf8.Valid(data))
				require.True(t, bytes.HasSuffix(data, []byte("\r\n")))
				require.NotContains(t, string(bytes.ReplaceAll(data, []byte("\r\n"), nil)), "\n")
				original, err := os.ReadFile(filepath.Join("..", "internal", "templates", "embed", "notification", filename))
				require.NoError(t, err)
				want, got := field.FindAllString(string(original), -1), field.FindAllString(string(data), -1)
				// Labels are now localized; titles are also present in both text verification types (#27).
				want = slices.DeleteFunc(want, func(s string) bool { return s == ".LinkText" || s == ".RevocationLinkText" })
				want = append(want, ".Title")
				slices.Sort(want)
				slices.Sort(got)
				require.Equal(t, slices.Compact(want), slices.Compact(got), "preserve every runtime field")
				for _, english := range []string{"We would like", "This notification", "Do not share", "If you did", "Revoke this", "Contact an Administrator"} {
					require.NotContains(t, string(data), english)
				}
			})
		}
	}
	for _, populated := range []bool{false, true} {
		t.Run(map[bool]string{false: "empty", true: "populated"}[populated], func(t *testing.T) {
			logo, banner := "", ""
			if populated {
				logo = "https://login.example.com/static/media/logo.png"
				banner = "srv-DEV-04"
			}
			t.Setenv("ABCKX_EMAIL_LOGO_URL", logo)
			t.Setenv("ABCKX_EMAIL_ENV_BANNER", banner)
			text := "Desenvolvido por iAvançada"
			provider, err := templates.New(templates.Config{EmailTemplatesPath: "templates", Branding: schema.Branding{Text: &text, URL: "https://iavancada.com.br"}})
			require.NoError(t, err)
			cases := []struct {
				name     string
				template *templates.EmailTemplate
				data     any
				values   []string
			}{
				{"Event", provider.GetEventEmailTemplate(), templates.EmailEventValues{Title: "Account event", DisplayName: "Test User", RemoteIP: "192.0.2.1", BodyPrefix: "A", BodyEvent: "password", BodySuffix: "changed", Details: map[string]any{"Action": "Reset"}}, []string{"Account event", "Test User", "192.0.2.1", "password", "changed", "Ação", "Reset"}},
				{"IdentityVerificationJWT", provider.GetIdentityVerificationJWTEmailTemplate(), templates.EmailIdentityVerificationJWTValues{Title: "Verify identity", DisplayName: "Test User", Domain: "example.com", RemoteIP: "192.0.2.1", LinkURL: "https://login.example.com/verify", LinkText: "Verify", RevocationLinkURL: "https://login.example.com/revoke", RevocationLinkText: "Revoke"}, []string{"Test User", "example.com", "192.0.2.1", "https://login.example.com/verify", "https://login.example.com/revoke"}},
				{"IdentityVerificationOTC", provider.GetIdentityVerificationOTCEmailTemplate(), templates.EmailIdentityVerificationOTCValues{Title: "Verify identity", DisplayName: "Test User", Domain: "example.com", RemoteIP: "192.0.2.1", OneTimeCode: "123456", RevocationLinkURL: "https://login.example.com/revoke", RevocationLinkText: "Revoke"}, []string{"Test User", "example.com", "192.0.2.1", "123456", "https://login.example.com/revoke"}},
			}
			for _, tc := range cases {
				t.Run(tc.name, func(t *testing.T) {
					var html, plain bytes.Buffer
					require.NoError(t, tc.template.HTML.Execute(&html, tc.data))
					require.NoError(t, tc.template.Text.Execute(&plain, tc.data))
					for _, value := range append(tc.values, text) {
						require.Contains(t, html.String(), value)
						require.Contains(t, plain.String(), value)
					}
					require.Contains(t, html.String(), `lang="pt-BR"`)
					require.Contains(t, plain.String(), "Olá")
					require.NotContains(t, html.String(), "#ZgotmplZ")
					if populated {
						require.Contains(t, html.String(), `src="`+logo+`"`)
						require.Contains(t, html.String(), banner)
						require.True(t, strings.HasPrefix(plain.String(), banner+"\r\n"))
					} else {
						require.NotContains(t, html.String(), "<img")
						require.NotContains(t, html.String(), "email-environment")
						require.False(t, strings.HasPrefix(plain.String(), "\r\n"))
					}
					if dir := os.Getenv("ABCKX_EMAIL_PREVIEW_DIR"); dir != "" && populated {
						require.NoError(t, os.MkdirAll(dir, 0755))
						require.NoError(t, os.WriteFile(filepath.Join(dir, tc.name+".html"), html.Bytes(), 0644))
					}
				})
			}
		})
	}
}

func TestNotificationOverlayEscaping(t *testing.T) {
	t.Setenv("ABCKX_EMAIL_LOGO_URL", "javascript:alert(1)")
	t.Setenv("ABCKX_EMAIL_ENV_BANNER", `<script>alert(1)</script>`)
	provider, err := templates.New(templates.Config{EmailTemplatesPath: "templates"})
	require.NoError(t, err)
	for _, tc := range []struct {
		template *templates.EmailTemplate
		data     any
	}{
		{provider.GetEventEmailTemplate(), templates.EmailEventValues{}},
		{provider.GetIdentityVerificationJWTEmailTemplate(), templates.EmailIdentityVerificationJWTValues{}},
		{provider.GetIdentityVerificationOTCEmailTemplate(), templates.EmailIdentityVerificationOTCValues{}},
	} {
		var output bytes.Buffer
		require.NoError(t, tc.template.HTML.Execute(&output, tc.data))
		require.NotContains(t, output.String(), "<script>")
		require.NotContains(t, output.String(), `src="javascript:`)
		require.Contains(t, output.String(), "iAvançada")
	}
}

func TestNotificationOverlayFooter(t *testing.T) {
	for _, text := range []string{"", "Custom footer"} {
		provider, err := templates.New(templates.Config{EmailTemplatesPath: "templates", Branding: schema.Branding{Text: &text}})
		require.NoError(t, err)
		for _, tc := range []struct {
			template *templates.EmailTemplate
			data     any // Three upstream notification payload types share the template Execute interface.
		}{
			{provider.GetEventEmailTemplate(), templates.EmailEventValues{}},
			{provider.GetIdentityVerificationJWTEmailTemplate(), templates.EmailIdentityVerificationJWTValues{}},
			{provider.GetIdentityVerificationOTCEmailTemplate(), templates.EmailIdentityVerificationOTCValues{}},
		} {
			var html, plain bytes.Buffer
			require.NoError(t, tc.template.HTML.Execute(&html, tc.data))
			require.NoError(t, tc.template.Text.Execute(&plain, tc.data))
			require.NotContains(t, html.String(), "Desenvolvido por")
			require.NotContains(t, plain.String(), "Desenvolvido por")
			if text != "" {
				require.Contains(t, html.String(), text)
				require.Contains(t, plain.String(), text)
			}
		}
	}
}

func TestNotificationImageWiring(t *testing.T) {
	data, err := os.ReadFile("Dockerfile")
	require.NoError(t, err)
	require.Contains(t, string(data), `AUTHELIA_NOTIFIER_TEMPLATE_PATH="/abckx/templates/"`)
	require.Contains(t, string(data), "COPY abckx/templates/ /abckx/templates/")
	ignore, err := os.ReadFile("Dockerfile.dockerignore")
	require.NoError(t, err)
	require.Contains(t, string(ignore), "!abckx/templates/**")
	attributes, err := os.ReadFile(".gitattributes")
	require.NoError(t, err)
	require.Contains(t, string(attributes), "templates/*.html text eol=crlf")
	require.Contains(t, string(attributes), "templates/*.txt text eol=crlf")
}
