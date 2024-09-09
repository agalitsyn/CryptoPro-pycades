import argparse
import base64
import http.client as http_client
import json
import logging

import pycades
import requests

"""
Повтор скрипта https://github.com/kilylabs/true-api-php-demo/blob/master/demo.php
"""

http_client.HTTPConnection.debuglevel = 1


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# constants
BASE_URL = "https://markirovka.sandbox.crptech.ru/api/v3/true-api"
DETACHED_SIGNATURE = True
ATTACHED_SINATURE = False
SIGNATURE_TYPE = ATTACHED_SINATURE


def main(oms_id: str) -> None:
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json;charset=UTF-8",
    }

    # 1. Запрос авторизации при единой аутентификации
    auth_resp = requests.get(f"{BASE_URL}/auth/key", headers=headers).json()
    logger.debug(auth_resp)

    # 2. Подпись поля data
    store = pycades.Store()
    store.Open(
        pycades.CADESCOM_CONTAINER_STORE,
        pycades.CAPICOM_MY_STORE,
        pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED,
    )
    certs = store.Certificates
    assert certs.Count != 0, "certificates with private key not found"

    cert = certs.Item(1)
    logger.debug(
        f"{cert.IssuerName} {cert.SubjectName} {cert.ValidFromDate}-{cert.ValidToDate}"
    )

    signer = pycades.Signer()
    signer.Certificate = cert
    signer.CheckCertificate = True

    logger.debug(f"raw data: {auth_resp["data"]}")
    message_bytes = auth_resp["data"].encode("ascii")
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode("ascii")
    logger.debug(f"base64 data for signing: {base64_message}")

    signedData = pycades.SignedData()
    signedData.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    signedData.Content = base64_message
    signature = signedData.SignCades(
        signer,
        pycades.CADESCOM_CADES_BES,
        SIGNATURE_TYPE,
        pycades.CAPICOM_ENCODE_BASE64,
    )
    logger.debug("signed")

    _signedData = pycades.SignedData()
    _signedData.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    _signedData.Content = signedData.Content
    _signedData.VerifyCades(
        signature,
        pycades.CADESCOM_CADES_BES,
        SIGNATURE_TYPE,
    )
    logger.debug("verified")

    token_req = {
        "uuid": auth_resp["uuid"],
        "data": "".join(signature.splitlines()),
    }

    # 3. Получение аутентификационного токена
    token_resp = requests.post(
        f"{BASE_URL}/simpleSignIn/{oms_id}",
        data=json.dumps(token_req),
        headers=headers,
    ).json()
    logger.debug(token_resp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--oms_id", type=str, required=True)
    args = parser.parse_args()
    main(args.oms_id)
