#!/usr/bin/env bash
# vim: ts=4 sts=4 sw=4 noet:

set -eo pipefail; [[ $TRACE ]] && set -x

BASE_URL="${BASE_URL:?echo 'BASE_URL is required'}"
OMS_ID="${OMS_ID:? echo 'OMS_ID is required'}"
OMS_CONNECTION_ID="${OMS_CONNECTION_ID:? echo 'OMS_CONNECTION_ID is required'}"
CERTIFICATE_THUMBPRINT="${CERTIFICATE_THUMBPRINT:? echo 'CERTIFICATE_THUMBPRINT is required'}"

# Set current directory
cd "$(dirname "$0")"

sign_content() {
    echo -n "$1" > tosign.txt
    # OR full path: /opt/cprocsp/bin/cryptcp
    cryptcp -sign -addchain -thumbprint $CERTIFICATE_THUMBPRINT tosign.txt signed.txt
    # Remove comments and whitespace
    sed -e 's|//.*||g' -e 's/[[:space:]]//g' signed.txt > signed_cleaned.txt
}

get_crpt_auth_token() {
    crpt_key=$(curl -sSL -H 'Content-Type: application/json; charset=utf-8' "${BASE_URL}/auth/key"; )

    to_sign=$(echo $crpt_key | jq -r '.data')
    uuid=$(echo $crpt_key | jq -r '.uuid')

    sign_content "$to_sign"
    signed_data=$(cat signed_cleaned.txt)

    json_body=$(jq -n \
                --arg uuid "$uuid" \
                --arg data "$signed_data" \
                '{uuid: $uuid, data: $data}')

    res=$(curl -sSL -X POST \
            -H "Content-Type: application/json; charset=utf-8" \
            -d "$json_body" \
            "${BASE_URL}/auth/simpleSignIn/${OMS_CONNECTION_ID}")
    echo $res | jq -r '.token' > token.txt

    curl -sSL \
        -H "Content-Type: application/json; charset=utf-8" \
        -H "clientToken: $(cat token.txt)" \
        "https://suz.sandbox.crptech.ru/api/v3/ping?omsId=${OMS_ID}";
}

get_crpt_auth_token
echo
cat token.txt
