// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package notification

import "os"

// abckxNotificationTitle localizes only the SMTP {title} substitution, never event data.
// Unset/false preserves upstream behavior, including unknown future subjects.
func abckxNotificationTitle(title string) string {
	if os.Getenv("ABCKX_EMAIL_SUBJECT_PT_BR") != "true" {
		return title
	}
	titles := map[string]string{
		"Reset your password":           "Defina sua senha",
		"Confirm your identity":         "Confirme sua identidade",
		"Password changed successfully": "Sua senha foi alterada",
		"Second Factor Method Added":    "Método de segundo fator adicionado",
		"Second Factor Method Removed":  "Método de segundo fator removido",
	}
	if translated, ok := titles[title]; ok {
		return translated
	}
	return title
}
