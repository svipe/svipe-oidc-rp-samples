#! /usr/bin/env bash

client_id=""
client_secret=""

token=$(uuidgen)
scope="profile"

oidc_issuer="https://api.svipe.com/oidc/v1"

build_qs () { echo -n $* | tr -s ' \n' '&'; }

ciba_request=$(
    curl -s -X POST \
    -d $(build_qs "
            client_notification_token=${token}
            login_hint=authref
            client_id=${client_id}
            scope=${scope}
    ")  \
    ${oidc_issuer}/authorize_ciba
)

qrcode=$(      echo $ciba_request | jq -r .authref.qrcode)
auth_req_id=$( echo $ciba_request | jq -r .auth_req_id)

if [[ "$qrcode" == "null" ]]; then
    echo "*** Invalid client_id ***"
    echo 'Please enter a valid value for "client_id" and "client_secret" in the script'
    echo "Read this first: https://developer.svipe.com/documentation#/oidc?id=ciba-client-initiated-backchannel-authentication"
    echo 'and be sure to set the "Token delivery mode" to "Pull"'
    exit 1
fi

open $qrcode

while sleep 1; do
    ciba_response=$(curl -s -X POST \
        -d $(build_qs "
                grant_type=urn:openid:params:grant-type:ciba
                auth_req_id=${auth_req_id}
                client_id=${client_id}
                client_secret=${client_secret}
        ")  \
    ${oidc_issuer}/token)
    id_token=$(echo $ciba_response | jq -r .id_token)
    if [[ $id_token != null ]]; then break; fi
done

echo "got id_token: $id_token"

echo $id_token | jq -R 'split(".") | .[1] | @base64d | fromjson'
