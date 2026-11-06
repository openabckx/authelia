// SPDX-FileCopyrightText: 2026 Authelia
//
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from "react-i18next";

import PrivacyPolicyLink from "@components/PrivacyPolicyLink";
import { Separator } from "@components/UI/Separator";
import { EncodedName, EncodedURL } from "@constants/constants";
import { getPrivacyPolicyEnabled } from "@utils/Configuration";

export interface Props {}

const Brand = function () {
    const { t: translate } = useTranslation();
    const privacyEnabled = getPrivacyPolicyEnabled();
    const custom = document.body.dataset.brandingcustom === "true";
    const text = custom
        ? (document.body.dataset.brandingtext ?? "")
        : translate("Powered by {{authelia}}", { authelia: atob(String.fromCodePoint(...EncodedName)) });
    const url = custom ? (document.body.dataset.brandingurl ?? "") : atob(String.fromCodePoint(...EncodedURL));
    const className = "text-[#9e9e9e] text-[0.7rem] whitespace-nowrap hover:underline";

    if (!text && !privacyEnabled) return null;

    return (
        <div className="flex items-center justify-center gap-2 w-full">
            {text ? (
                url.startsWith("https://") ? (
                    <a href={url} target="_blank" rel="noopener noreferrer" className={className}>
                        {text}
                    </a>
                ) : (
                    <span className={className}>{text}</span>
                )
            ) : null}
            {text && privacyEnabled ? <Separator orientation="vertical" className="h-4" /> : null}
            {privacyEnabled ? <PrivacyPolicyLink className={className} /> : null}
        </div>
    );
};

export default Brand;
