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

BASE_URL = "https://markirovka.sandbox.crptech.ru/api/v3/true-api"


def main(oms_id: str) -> None:
    headers = {"Content-Type": "application/json"}

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

    cert = certs.Item(2)
    logger.debug(
        f"{cert.IssuerName} {cert.SubjectName} {cert.ValidFromDate}-{cert.ValidToDate}"
    )

    signer = pycades.Signer()
    signer.Certificate = cert
    signer.CheckCertificate = True

    signedData = pycades.SignedData()
    signedData.Content = base64.b64encode(auth_resp["data"].encode("utf-8")).decode(
        "utf-8"
    )
    signature = signedData.SignCades(signer, pycades.CADESCOM_CADES_BES)
    logger.debug("signed")

    _signedData = pycades.SignedData()
    _signedData.VerifyCades(signature, pycades.CADESCOM_CADES_BES)
    logger.debug("verified")

    token_req = {
        "uuid": auth_resp["uuid"],
        "data": signature.replace("\r\n", ""),
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
    parser.add_argument("--oms_id", type=str)
    args = parser.parse_args()
    main(args.oms_id)
