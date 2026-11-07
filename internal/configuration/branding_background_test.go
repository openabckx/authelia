package configuration

import (
	"github.com/authelia/authelia/v4/internal/configuration/schema"
	"github.com/authelia/authelia/v4/internal/configuration/validator"
	"github.com/stretchr/testify/require"
	"testing"
)

func TestBrandingBackgroundEnvironment(t *testing.T) {
	t.Setenv("AUTHELIA_BRANDING_BACKGROUND_IMAGE", "true")
	t.Setenv("AUTHELIA_BRANDING_BACKGROUND_OPACITY", "0")
	t.Setenv("AUTHELIA_BRANDING_BACKGROUND_BLUR", "20")
	_, config, err := Load(schema.NewStructValidator(), NewEnvironmentSource(DefaultEnvPrefix, DefaultEnvDelimiter))
	require.NoError(t, err)
	require.True(t, config.Branding.BackgroundImage)
	require.NotNil(t, config.Branding.BackgroundOpacity)
	require.Equal(t, 0.0, *config.Branding.BackgroundOpacity)
	require.Equal(t, 20.0, config.Branding.BackgroundBlur)
}

func TestBrandingBackgroundValidation(t *testing.T) {
	for _, tc := range []struct {
		name          string
		opacity, blur float64
		valid         bool
	}{
		{"minimum", 0, 0, true}, {"maximum", 1, 20, true}, {"negative opacity", -0.1, 0, false},
		{"high opacity", 1.01, 0, false}, {"negative blur", 0.25, -1, false}, {"high blur", 0.25, 21, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			config := &schema.Configuration{Branding: schema.Branding{BackgroundImage: true, BackgroundOpacity: &tc.opacity, BackgroundBlur: tc.blur}}
			val := schema.NewStructValidator()
			validator.ValidateConfiguration(config, val)
			var brandingErrors []error
			for _, err := range val.Errors() {
				if len(err.Error()) >= 9 && err.Error()[:9] == "branding:" {
					brandingErrors = append(brandingErrors, err)
				}
			}
			require.Equal(t, tc.valid, len(brandingErrors) == 0)
		})
	}
}
