#!/bin/bash

set -e

# SANDBOX
baseURI="https://markirovka.sandbox.crptech.ru/api/v3/true-api"
omsId="477284ae-d313-403e-b177-df7b5d0ebb70"
omsConnId="d1a81f6b-aca1-4bb8-b085-9df98e7ab3bc"
certSHA="a32da0a2a01083cfb35ba46e0d8acff2702dd5ce"

# PROD
# baseURI="https://markirovka.crpt.ru/api/v3/true-api"

sign_content() {
    echo -n "$1" > tosign.txt

    # /opt/cprocsp/bin/cryptcp
    cryptcp -sign -addchain -thumbprint $certSHA tosign.txt signed.txt

    # Remove comments and whitespace
    sed -e 's|//.*||g' -e 's/[[:space:]]//g' signed.txt > signed_cleaned.txt
}

get_crpt_auth_token() {
    crpt_key=$(curl -sSL -H 'Content-Type: application/json; charset=utf-8' "${baseURI}/auth/key"; )

    toSign=$(echo $crpt_key | jq -r '.data')
    uuid=$(echo $crpt_key | jq -r '.uuid')

    sign_content "$toSign"
    signeddata=$(cat signed_cleaned.txt)

    jsonBody=$(jq -n \
                  --arg uuid "$uuid" \
                  --arg data "$signeddata" \
                  '{uuid: $uuid, data: $data}')


    res=$(set -x;
        curl -sSL -X POST \
            -H "Content-Type: application/json; charset=utf-8" \
            -d "$jsonBody" \
            "${baseURI}/auth/simpleSignIn/${omsConnId}";
        set +x;)
    echo $res | jq -r '.token' > token.txt

    set -x;
    curl -sSL \
        -H "Content-Type: application/json; charset=utf-8" \
        -H "clientToken: $(cat token.txt)" \
        "https://suz.sandbox.crptech.ru/api/v3/ping?omsId=${omsId}";
    set +x;
}

# Set current directory
cd "$(dirname "$0")"

get_crpt_auth_token
