package server

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/stretchr/testify/require"
)

func TestBrandingBackgroundAvailability(t *testing.T) {
	for _, present := range []bool{false, true} {
		t.Run(map[bool]string{false: "missing", true: "present"}[present], func(t *testing.T) {
			dir := t.TempDir()
			if present {
				require.NoError(t, os.WriteFile(filepath.Join(dir, "background.png"), []byte("fixture"), 0600))
			}
			config := &schema.Configuration{Branding: schema.Branding{BackgroundImage: true}}
			config.Server.AssetPath = dir
			data := NewTemplatedFileOptions(config).CommonData("/auth", "https://example.com/auth/", "example.com", "nonce", "en", "false", "false")
			css := data.BrandingStyle()
			if present {
				require.Contains(t, css, `url("./static/media/background.png")`)
				require.Contains(t, css, "--branding-background-opacity:0.25")
				require.Contains(t, css, "background:var(--background)")
				require.Contains(t, css, `nonce="nonce"`)
			} else {
				require.Empty(t, css)
			}
			config.Branding.BackgroundImage = false
			require.Empty(t, NewTemplatedFileOptions(config).CommonData("", "", "", "nonce", "en", "false", "false").BrandingStyle())
		})
	}
}
