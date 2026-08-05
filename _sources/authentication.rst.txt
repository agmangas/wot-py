Authentication Mechanisms
=========================


============================================================================ ==== ==== ==== ========= =====
Mechanism                                                                    HTTP CoAP MQTT WebSocket Zenoh
============================================================================ ==== ==== ==== ========= =====
Basic Authentication                                                         ✔    ✔    ✔
Bearer Token                                                                 ✔
`OpenID for Verifiable Credentials <https://www.w3.org/TR/vc-data-model/>`__ ✔
Oauth2                                                                       ⚠️
============================================================================ ==== ==== ==== ========= =====

⚠️ Oauth2 has not been tested and requires an external endpoint to authenticate tokens.
