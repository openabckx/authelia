// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";

import { Link, Text } from "react-email";

export const Brand = () => {
    return (
        <Text className="text-[#666666] text-[10px] leading-[24px] text-center text-muted">
            {"{{ $brand := branding }}{{ if ne $brand.Text nil }}{{ if $brand.Visible }}{{ if $brand.URL }}"}
            <Link href="{{ $brand.URL }}" target="_blank" className="text-[#666666]">
                {"{{ $brand.Text }}"}
            </Link>
            {"{{ else }}{{ $brand.Text }}{{ end }}{{ end }}{{ else }}"}
            Powered by{" "}
            <Link href="https://www.authelia.com" target="_blank" className="text-[#666666]">
                Authelia
            </Link>
            {"{{ end }}"}
        </Text>
    );
};
