// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

package schema

// Branding configures the portal and notification footer. Nil text preserves
// the upstream branding; an explicitly empty text hides it.
type Branding struct {
	Text *string `koanf:"text" yaml:"text,omitempty" toml:"text,omitempty" json:"text,omitempty"`
	URL  string  `koanf:"url" yaml:"url,omitempty" toml:"url,omitempty" json:"url,omitempty"`
}

// Visible reports whether the footer should be rendered.
func (b Branding) Visible() bool {
	return b.Text == nil || *b.Text != ""
}
