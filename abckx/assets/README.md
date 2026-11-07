# Fork brand assets

The image copies this directory to `/abckx/assets/` and sets
`AUTHELIA_SERVER_ASSET_PATH=/abckx/assets/`. The existing upstream overlay serves
`logo.png` and `favicon.ico`; no core or theme change is required.

## Official sources

Downloaded from the iAvançada website for issue #6:

| Shipped file | Official source | SHA-256 |
| --- | --- | --- |
| `logo.png` | https://iavancada.com.br/apple-touch-icon.png | `5d82f6ef5d2406fe3465e6e4f28386a95e403da185174c39c21f9374b113e90b` |
| `favicon.ico` | https://iavancada.com.br/favicon.ico | `e692fb7a30e029a06bafeaa193eb42f921d40cd200e9cd1cf5040e18c0ad7045` |

The logo is the original 180×180 PNG, not a reconstruction of the brand. The
favicon contains four resolutions. Both use the official cyan mark on a dark
rounded square, keeping its own background in light and dark portal themes.
Run `python3 -m unittest discover -s abckx` to verify these pinned originals.
Review the official source and update the asset tests together when replacing them.

Operators may mount a different directory and set `AUTHELIA_SERVER_ASSET_PATH`
to that directory. Such a mount takes precedence over these defaults. To roll
back, restore the previous image digest or the previous asset directory and
restart. No database or authentication state is changed.

Custom portal colors are excluded from #6 by the scope decision. Track upstream
https://github.com/authelia/authelia/pull/11862 (custom CSS asset override) and
https://github.com/authelia/authelia/issues/8839 (custom theming); do not add CSS
here until upstream provides a supported runtime consumer.

Upstream reference: https://www.authelia.com/reference/guides/server-asset-overrides/
