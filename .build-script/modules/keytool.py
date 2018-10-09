import os
import sys
from subprocess import DEVNULL, STDOUT, check_call

def generateDistingiushedName(
    commonName: str):
    return 'CN={0}'.format(commonName)

def generateKeystore(
    keystorePath: str,
    storePassword: str,
    keyAlias: str,
    keyPassword: str,
    distingiushedName: str,
    validity: int):
    check_call([
        'keytool',
        '-genkeypair',
        '-v',
        '-keystore', keystorePath,
        '-storepass', storePassword,
        '-alias', keyAlias,
        '-keypass', keyPassword,
        '-dname', distingiushedName,
        '-validity', str(validity),
        '-keyalg', 'RSA',
        '-keysize', '2048',
        '-storetype', 'jks',
    ], stdout=DEVNULL, stderr=STDOUT)
