// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package abckx

import (
	"bytes"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"github.com/authelia/authelia/v4/internal/templates"
	"github.com/stretchr/testify/require"
)

func TestNotificationPortuguese(t *testing.T) {
	p, err := templates.New(templates.Config{EmailTemplatesPath: "templates"})
	require.NoError(t, err)
	docs, err := os.ReadFile("../docs/content/configuration/notifications/events.md")
	require.NoError(t, err)
	titles := map[string]string{
		"Reset your password":           "Defina sua senha",
		"Confirm your identity":         "Confirme sua identidade",
		"Password changed successfully": "Sua senha foi alterada",
		"Second Factor Method Added":    "Método de segundo fator adicionado",
		"Second Factor Method Removed":  "Método de segundo fator removido",
	}
	documented := regexp.MustCompile("`([^`]+)`").FindAllStringSubmatch(strings.Split(string(docs), "The subject line")[0], -1)
	for _, match := range documented {
		if strings.Contains(match[1], " ") {
			require.Contains(t, titles, match[1], "new documented subject needs a translation")
		}
	}
	for title, translated := range titles {
		for _, name := range []string{"Event", "IdentityVerificationJWT", "IdentityVerificationOTC"} {
			t.Run(name+"/"+title, func(t *testing.T) {
				et, data := portugueseFixture(p, name, title)
				for _, render := range []func(*bytes.Buffer) error{
					func(b *bytes.Buffer) error { return et.HTML.Execute(b, data) },
					func(b *bytes.Buffer) error { return et.Text.Execute(b, data) },
				} {
					var b bytes.Buffer
					require.NoError(t, render(&b))
					require.Contains(t, b.String(), translated)
					for _, english := range []string{title, "your", "Password Reset", "was successful.", "Action", "Category", "Description", "One-Time Password", "Reset</a>", "Revoke</a>"} {
						require.NotContains(t, b.String(), english)
					}
					require.Contains(t, b.String(), "192.0.2.1")
					if name == "Event" {
						for _, want := range []string{"sua", "redefinição de senha", "foi concluída com sucesso.", "Ação", "Categoria", "Descrição", "Senha de uso único", "My device"} {
							require.Contains(t, b.String(), want)
						}
					} else {
						require.Contains(t, b.String(), "https://login.example.com/revoke")
						require.Contains(t, b.String(), "Revogar")
					}
				}
			})
		}
	}
	for _, tc := range []struct{ prefix, event, suffix, category, want string }{
		{"your", "Password Change", "was successful.", "WebAuthn Credential", "alteração de senha foi concluída com sucesso."},
		{"a", "Second Factor Method", "was added to your account.", "One-Time Password", "um método de segundo fator foi adicionado à sua conta."},
		{"a", "Second Factor Method", "was removed from your account.", "WebAuthn Credential", "um método de segundo fator foi removido da sua conta."},
		{"new prefix", "new event", "new suffix", "new category", "new prefix new event new suffix"},
	} {
		data := templates.EmailEventValues{Title: "Unknown title", BodyPrefix: tc.prefix, BodyEvent: tc.event, BodySuffix: tc.suffix, Details: map[string]any{"Action": tc.event, "Category": tc.category, "Unknown key": "Unknown value"}}
		for _, html := range []bool{false, true} {
			var b bytes.Buffer
			if html {
				err = p.GetEventEmailTemplate().HTML.Execute(&b, data)
			} else {
				err = p.GetEventEmailTemplate().Text.Execute(&b, data)
			}
			require.NoError(t, err)
			require.Contains(t, b.String(), "Unknown title")
			require.Contains(t, b.String(), tc.want)
			require.Contains(t, b.String(), "Unknown key")
			require.Contains(t, b.String(), "Unknown value")
			require.NotContains(t, b.String(), "WebAuthn Credential")
			if tc.category == "WebAuthn Credential" {
				require.Contains(t, b.String(), "Credencial WebAuthn")
			}
		}
	}
}

// The upstream payloads are distinct; any here is limited to the Execute boundary.
func portugueseFixture(p *templates.Provider, name, title string) (*templates.EmailTemplate, any) {
	switch name {
	case "Event":
		return p.GetEventEmailTemplate(), templates.EmailEventValues{Title: title, DisplayName: "", RemoteIP: "192.0.2.1", BodyPrefix: "your", BodyEvent: "Password Reset", BodySuffix: "was successful.", Details: map[string]any{"Action": "Password Reset", "Category": "One-Time Password", "Description": "My device"}}
	case "IdentityVerificationJWT":
		return p.GetIdentityVerificationJWTEmailTemplate(), templates.EmailIdentityVerificationJWTValues{Title: title, Domain: "example.com", RemoteIP: "192.0.2.1", LinkURL: "https://login.example.com/verify", LinkText: "Reset", RevocationLinkURL: "https://login.example.com/revoke", RevocationLinkText: "Revoke"}
	default:
		return p.GetIdentityVerificationOTCEmailTemplate(), templates.EmailIdentityVerificationOTCValues{Title: title, Domain: "example.com", RemoteIP: "192.0.2.1", OneTimeCode: "123456", RevocationLinkURL: "https://login.example.com/revoke", RevocationLinkText: "Revoke"}
	}
}

func TestPortugueseUnknownAndEscaped(t *testing.T) {
	p, err := templates.New(templates.Config{EmailTemplatesPath: "templates"})
	require.NoError(t, err)
	for _, name := range []string{"Event", "IdentityVerificationJWT", "IdentityVerificationOTC"} {
		et, data := portugueseFixture(p, name, `<script>future title</script>`)
		var html, plain bytes.Buffer
		require.NoError(t, et.HTML.Execute(&html, data))
		require.NoError(t, et.Text.Execute(&plain, data))
		require.Contains(t, html.String(), "&lt;script&gt;future title&lt;/script&gt;")
		require.NotContains(t, html.String(), "<script>")
		require.Contains(t, plain.String(), `<script>future title</script>`)
	}
}

func TestNotificationEventDetails(t *testing.T) {
	p, err := templates.New(templates.Config{EmailTemplatesPath: "templates"})
	require.NoError(t, err)
	for _, action := range []string{"Second Factor Method Added", "Second Factor Method Removed"} {
		for _, category := range []string{"One-Time Password", "WebAuthn Credential"} {
			data := templates.EmailEventValues{Title: action, Details: map[string]any{"Action": action, "Category": category, "Description": "Password Reset"}}
			for _, html := range []bool{false, true} {
				var b bytes.Buffer
				if html {
					err = p.GetEventEmailTemplate().HTML.Execute(&b, data)
				} else {
					err = p.GetEventEmailTemplate().Text.Execute(&b, data)
				}
				require.NoError(t, err)
				require.NotContains(t, b.String(), action)
				require.NotContains(t, b.String(), category)
				require.Contains(t, b.String(), "Password Reset", "user descriptions must not be translated")
			}
		}
	}
}

func TestPortuguesePreviews(t *testing.T) {
	// Relative official asset keeps committed previews usable offline; runtime uses the operator HTTPS URL.
	t.Setenv("ABCKX_EMAIL_LOGO_URL", "../assets/logo.png")
	t.Setenv("ABCKX_EMAIL_ENV_BANNER", "srv-DEV-04")
	p, err := templates.New(templates.Config{EmailTemplatesPath: "templates"})
	require.NoError(t, err)
	for _, tc := range []struct{ name, title string }{
		{"IdentityVerificationJWT", "Reset your password"}, {"IdentityVerificationOTC", "Confirm your identity"}, {"Event", "Second Factor Method Added"}, {"PasswordChanged", "Password changed successfully"},
	} {
		name := tc.name
		if name == "PasswordChanged" {
			name = "Event"
		}
		et, data := portugueseFixture(p, name, tc.title)
		if name == "Event" {
			event := data.(templates.EmailEventValues)
			if tc.name == "Event" {
				event.BodyPrefix, event.BodyEvent, event.BodySuffix = "a", "Second Factor Method", "was added to your account."
				event.Details = map[string]any{"Action": "Second Factor Method Added", "Category": "WebAuthn Credential", "Description": "Notebook"}
			} else {
				event.Details = map[string]any{"Action": "Password Reset"}
			}
			data = event
		}
		var b bytes.Buffer
		require.NoError(t, et.HTML.Execute(&b, data))
		require.Contains(t, b.String(), `width="44" height="44" alt="iAvançada"`)
		require.Contains(t, b.String(), `max-width:600px`)
		require.Contains(t, b.String(), "Olá,")
		if dir := os.Getenv("ABCKX_PTBR_PREVIEW_DIR"); dir != "" {
			require.NoError(t, os.MkdirAll(dir, 0755))
			require.NoError(t, os.WriteFile(filepath.Join(dir, tc.name+".html"), b.Bytes(), 0644))
		}
	}
}
