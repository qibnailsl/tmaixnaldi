import sys, json
import binascii
from zipfile import ZipFile
import shutil
import os
import os.path
import requests
import modules.keytool as keytool

def extract_all_with_permission(zf, target_dir):
    ZIP_UNIX_SYSTEM = 3
    for info in zf.infolist():
        extracted_path = zf.extract(info, target_dir)

        if info.create_system == ZIP_UNIX_SYSTEM:
            unix_attributes = info.external_attr >> 16
            if unix_attributes:
                os.chmod(extracted_path, unix_attributes)

def getBuildConfig():
    def getNewBuildId():
        response = requests.get(serviceHost + "/api/builds/new")
        response.raise_for_status()
        return response.json()["id"]

    buildId = getNewBuildId()
    response = requests.get(serviceHost + "/api/builds/" + buildId + "/build-config")
    response.raise_for_status()
    return response.json()

def generateCertificate(buildConfig):
    buildConfig['signingKeyStorePassword'] = '9ce711aae2259376733117020c803d8ccc14d828'
    buildConfig['signingKey'] = 'cert'
    buildConfig['signingKeyPassword'] = '9ce711aae2259376733117020c803d8ccc14d828'
    keytool.generateKeystore(
        keystorePath='./app/signingKeyStore.jks',
        storePassword=buildConfig['signingKeyStorePassword'],
        keyAlias=buildConfig['signingKey'],
        keyPassword=buildConfig['signingKeyPassword'],
        distingiushedName=keytool.generateDistingiushedName(
            commonName=buildConfig['applicationId']),
        validity=365*25)

def saveKeyStore(keyStore):
    fp = open("./app/signingKeyStore.jks", "wb")
    fp.write(binascii.a2b_base64(keyStore))
    fp.close()

def unzipWebAppTemplateSource(password: str):
    if os.path.isfile('./source.zip') == False:
        return

    with ZipFile('./source.zip', 'r') as zf:
        zf.setpassword(str.encode(password))
        extract_all_with_permission(zf, './')

    os.remove('source.zip')

def saveAppIconArchieve(applicationIcon):
    fp = open("./appIcon.zip", "wb")
    fp.write(binascii.a2b_base64(applicationIcon))
    fp.close()

def unzipAppIcon():
    appArchieve = ZipFile("./appIcon.zip")
    appArchieve.extractall("./appIcon")
    appArchieve.close()
    os.remove('appIcon.zip')

def overrideAppIcon():
    # os.system('mv -f ./appIcon ./app/src/main/res')
    # moverecursively('appIcon', 'app/src/main/res')
    shutil.move('./appIcon/mipmap-hdpi', './app/src/main/res/mipmap-hdpi')
    shutil.move('./appIcon/mipmap-mdpi', './app/src/main/res/mipmap-mdpi')
    shutil.move('./appIcon/mipmap-xhdpi', './app/src/main/res/mipmap-xhdpi')
    shutil.move('./appIcon/mipmap-xxhdpi', './app/src/main/res/mipmap-xxhdpi')
    shutil.move('./appIcon/mipmap-xxxhdpi', './app/src/main/res/mipmap-xxxhdpi')
    shutil.rmtree('./appIcon')

def build(
    applicationId,
    applicationName,
    targetSdkVersion,
    versionCode,
    versionName,
    url,
    signingKeyStorePassword,
    signingKey,
    signingKeyPassword):
    command = './gradlew assembleRelease' \
        + ' -Purl=\\"' + url + '\\"' \
        + ' -PapplicationId="' + applicationId + '"' \
        + ' -PappName="' + applicationName + '"' \
        + ' -PversionName="' + versionName + '"' \
        + ' -PsigningKeyStorePassword="' + signingKeyStorePassword + '"' \
        + ' -PsigningKey="' + signingKey + '"' \
        + ' -PsigningKeyPassword="' + signingKeyPassword + '"'
    #  -PtargetSdkVersion={targetSdkVersion} -PversionCode={versionCode}
    # print(command)
    return os.system(command)

def uploadArtifacts(buildId):
    filePath = "app/build/outputs/apk/release/app-release.apk"
    url = serviceHost + "/api/builds/" + buildId
    files = {'apkFile': open(filePath, 'rb')}
    response = requests.post(
        url,
        files=files)
    response.raise_for_status()
    print("UploadArtifacts success: {0}".format(buildId))
    

def reportBuildError(buildId, message):
    url = serviceHost + "/api/builds/" + buildId + "/report"
    params = {'message': message }
    response = requests.post(
        url,
        data=params)
    response.raise_for_status()

serviceHost = os.environ['BUILD_FACADE_HOST']
buildConfig = getBuildConfig()

unzipWebAppTemplateSource(os.environ['SOURCE_PASSWORD'])
saveAppIconArchieve(buildConfig['applicationIcon'])
unzipAppIcon()
overrideAppIcon()

if (buildConfig['signingKeyStore']):
    saveKeyStore(buildConfig['signingKeyStore'])
else:
    generateCertificate(buildConfig)

buildId = buildConfig['buildId']
print("Build Start: {0}".format(buildId))

result = build(
    buildConfig['applicationId'],
    buildConfig['applicationName'],
    buildConfig['targetSdkVersion'],
    buildConfig['versionCode'],
    buildConfig['versionName'],
    buildConfig['url'],
    buildConfig['signingKeyStorePassword'],
    buildConfig['signingKey'],
    buildConfig['signingKeyPassword'])

if result == 0:
    uploadArtifacts(buildId)
else:
    reportBuildError(buildId, 'exitCode: {0}'.format(result))
    exit(result)
