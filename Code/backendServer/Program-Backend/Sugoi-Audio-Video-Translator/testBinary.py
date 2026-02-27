# from faster_whisper import WhisperModel
import math
import base64
import io

def convertFileToBase64string(fileName):
    fileInBytes = open(fileName, "rb")
    base64File = base64.b64encode(fileInBytes.read())
    result = str(base64File)
    return result


def decodeAndSaveBase64Bytes(audioBytes):
    audioFile = bytearray(audioBytes, encoding="utf-8")
    del audioFile[-1]
    del audioFile[0]
    del audioFile[0]
    audioFile_decoded = base64.b64decode(audioFile)
    return audioFile_decoded

fileInBase64 = convertFileToBase64string("original.mp3")
base64ToBinaryFile = decodeAndSaveBase64Bytes(fileInBase64)
# print(base64ToBinaryFile)

# import io

with open("original.mp3", "rb") as audio_file:
    audio_bytes = audio_file.read()
    audio_file = io.BytesIO(audio_bytes)

print(base64ToBinaryFile == audio_bytes)
# # print(audio_bytes)
# print(audio_file)