from faster_whisper import WhisperModel
try:
    from faster_whisper import BatchedInferencePipeline
except ImportError:
    BatchedInferencePipeline = None
import math
import base64
import io
import json
import os
# https://github.com/guillaumekln/faster-whisper/issues/80

def normalize_compute_type(value):
    compute_type = str(value).strip().lower()
    aliases = {
        "fp16": "float16",
        "half": "float16",
        "float16": "float16",
        "int8": "int8",
        "int8_float16": "int8_float16",
        "int8-float16": "int8_float16",
        "int8_fp16": "int8_float16"
    }
    return aliases.get(compute_type, compute_type)


def load_transcriber_settings():
    with open("../../../User-Settings.json", encoding="utf-8") as user_settings_file:
        user_settings_data = json.load(user_settings_file)
    settings = user_settings_data["Sugoi_Audio_Video_Translator"]
    return {
        "model_name": settings.get("model_name", "whisper_small/"),
        "device": settings.get("device", "cuda"),
        "compute_type": normalize_compute_type(settings.get("compute_type", "float16")),
        "vad_filter": bool(settings.get("vad_filter", True)),
        "beam_size": int(settings.get("beam_size", 4)),
        "language": settings.get("language", "ja"),
        "batch_size": max(1, int(settings.get("batch_size", 1))),
        "intra_threads": max(0, int(settings.get("intra_threads", 0)))
    }

class AudioTranscriber:
    def __init__(self, overrides=None):
        settings = load_transcriber_settings()
        if overrides:
            if "compute_type" in overrides:
                overrides = {**overrides, "compute_type": normalize_compute_type(overrides["compute_type"])}
            settings.update(overrides)

        self.model_path = settings["model_name"]
        self.device = settings["device"]
        self.compute_type = normalize_compute_type(settings["compute_type"])
        self.vad_filter = settings["vad_filter"]
        self.beam_size = int(settings["beam_size"])
        self.language = settings["language"]
        self.batch_size = max(1, int(settings["batch_size"]))
        self.intra_threads = max(0, int(settings["intra_threads"]))
        self.log_segments = str(os.getenv("SUGOI_LOG_SEGMENTS", "0")).strip().lower() in {"1", "true", "yes", "on"}

        self.model = WhisperModel(
            self.model_path,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=self.intra_threads
        )
        self.batched_model = None
        if BatchedInferencePipeline is not None and self.batch_size > 1:
            self.batched_model = BatchedInferencePipeline(model=self.model)
        # or run on GPU with INT8
        # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
        # or run on CPU with INT8
        #model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    def test(self):
        print("hello world")

    def convert_seconds_to_hms(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = math.floor((seconds % 1) * 1000)
        output = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"
        return output

    def printListToTextFile(self, listToPrint, name):
        print(*listToPrint, sep='\n', file=open(name, "w", encoding="utf8"))
        return "print list to txt file"

    def _decode_base64_audio(self, base64audioFile):
        audioFile = bytearray(base64audioFile, encoding="utf-8")
        del audioFile[-1]
        del audioFile[0]
        del audioFile[0]
        audioFile_decoded = base64.b64decode(audioFile)
        return io.BytesIO(audioFile_decoded)

    def _transcribe(self, audio_source):
        if self.batched_model is not None:
            return self.batched_model.transcribe(
                audio_source,
                vad_filter=self.vad_filter,
                beam_size=self.beam_size,
                language=self.language,
                batch_size=self.batch_size
            )
        return self.model.transcribe(
            audio_source,
            vad_filter=self.vad_filter,
            beam_size=self.beam_size,
            language=self.language
        )
    
    def getTranscription(self, audioInput):
        if isinstance(audioInput, str) and os.path.exists(audioInput):
            audio_source = audioInput
        else:
            audio_source = self._decode_base64_audio(audioInput)

        audioSegments, audioInfo = self._transcribe(audio_source)
        print("Detected language '%s' with probability %f" % (audioInfo.language, audioInfo.language_probability))

        listOfAudioSegments = []

        count = 0
        totalDurationInSeconds = round(audioInfo.duration)

        for segment in audioSegments:
            count +=1
            duration = f"{self.convert_seconds_to_hms(segment.start)} --> {self.convert_seconds_to_hms(segment.end)}\n"
            print(round(round(segment.end)/totalDurationInSeconds*100))
            text = f"{segment.text.lstrip()}\n"
            
            listOfAudioSegments.append(f"{count}\n{duration}{text}")  # Write formatted string to the file
            if self.log_segments:
                print(f"{duration}{text}", end='')

        return listOfAudioSegments
    
    def convertOutputToSRT(self, audioInput):
        listOfAudioSegments = self.getTranscription(audioInput)
        self.printListToTextFile(listOfAudioSegments, "BinaryOutput.srt")


# audioTranscriber = AudioTranscriber()

# def convertFileToBase64string(fileName):
#     fileInBytes = open(fileName, "rb")
#     base64File = base64.b64encode(fileInBytes.read())
#     result = str(base64File)
#     return result

# base64Input = convertFileToBase64string("original.mp3")

# audioTranscriber.getTranscription()
