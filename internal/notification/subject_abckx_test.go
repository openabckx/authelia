// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package notification

import (
	"bytes"
	"io"
	"mime"
	"mime/multipart"
	"mime/quotedprintable"
	"net/mail"
	"strings"
	"testing"

	"github.com/sirupsen/logrus/hooks/test"
	"github.com/stretchr/testify/require"

	"github.com/authelia/authelia/v4/internal/templates"
)

func TestABCKXSubjectMIME(t *testing.T) {
	p, err := templates.New(templates.Config{EmailTemplatesPath: "../../abckx/templates"})
	require.NoError(t, err)
	titles := map[string]string{"Reset your password": "Defina sua senha", "Confirm your identity": "Confirme sua identidade", "Password changed successfully": "Sua senha foi alterada", "Second Factor Method Added": "Método de segundo fator adicionado", "Second Factor Method Removed": "Método de segundo fator removido", "Future title": "Future title"}
	for _, enabled := range []string{"", "false", "true"} {
		t.Setenv("ABCKX_EMAIL_SUBJECT_PT_BR", enabled)
		for title, translated := range titles {
			t.Run(enabled+"/"+title, func(t *testing.T) {
				logger, _ := test.NewNullLogger()
				n := SetupNotifier(nil, logger)
				n.config.Sender = mail.Address{Address: "admin@example.com"}
				n.config.Subject = "[iAvançada] {title}"
				msg, err := n.buildMessage(mail.Address{Address: "test@example.com"}, title, p.GetEventEmailTemplate(), templates.EmailEventValues{Title: title})
				require.NoError(t, err)
				var wire bytes.Buffer
				_, err = msg.WriteTo(&wire)
				require.NoError(t, err)
				require.NotContains(t, strings.ReplaceAll(wire.String(), "\r\n", ""), "\n")
				parsed, err := mail.ReadMessage(&wire)
				require.NoError(t, err)
				subject, err := new(mime.WordDecoder).DecodeHeader(parsed.Header.Get("Subject"))
				require.NoError(t, err)
				want := title
				if enabled == "true" {
					want = translated
				}
				require.Equal(t, "[iAvançada] "+want, subject)
				kind, params, err := mime.ParseMediaType(parsed.Header.Get("Content-Type"))
				require.NoError(t, err)
				require.Equal(t, "multipart/alternative", kind)
				parts := multipart.NewReader(parsed.Body, params["boundary"])
				var types []string
				for {
					part, err := parts.NextPart()
					if err == io.EOF {
						break
					}
					require.NoError(t, err)
					kind, params, err = mime.ParseMediaType(part.Header.Get("Content-Type"))
					require.NoError(t, err)
					require.Equal(t, "UTF-8", strings.ToUpper(params["charset"]))
					types = append(types, kind)
					var body []byte
					if strings.EqualFold(part.Header.Get("Content-Transfer-Encoding"), "quoted-printable") {
						body, err = io.ReadAll(quotedprintable.NewReader(part))
					} else {
						body, err = io.ReadAll(part)
					}
					require.NoError(t, err)
					require.Contains(t, string(body), translated)
				}
				require.ElementsMatch(t, []string{"text/plain", "text/html"}, types)
			})
		}
	}
}
