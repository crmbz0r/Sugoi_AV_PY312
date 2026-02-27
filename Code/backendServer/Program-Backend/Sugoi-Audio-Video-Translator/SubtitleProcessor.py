import json
import os
import time
from pathlib import Path

import requests


class SubtitleProcessor:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.input_dir = self.base_dir / "INPUT"
        self.output_dir = self.base_dir / "OUTPUT"
        self.settings_path = (self.base_dir / "../../../User-Settings.json").resolve()

        with open(self.settings_path, encoding="utf-8") as user_settings_file:
            user_settings_data = json.load(user_settings_file)

        av_settings = user_settings_data["Sugoi_Audio_Video_Translator"]
        translation_api_settings = user_settings_data["Translation_API_Server"]

        current_translator = translation_api_settings["current_translator"]
        self.translation_port = int(translation_api_settings[current_translator]["HTTP_port_number"])
        self.transcription_port = int(av_settings["transcription_server_port_number"])

        self.only_transcribe = bool(av_settings.get("only_transcribe", False))
        self.only_transcribe_and_translate = bool(av_settings.get("only_transcribe_and_translate", True))
        self.pipeline_mode = av_settings.get("pipeline_mode", "transcribe_then_translate")

        self.write_strategy = av_settings.get("write_strategy", "immediate")
        self.cache_flush_every = max(1, int(av_settings.get("cache_flush_every", 100)))
        self.single_manifest_filename = av_settings.get("single_manifest_filename", "batch_cached_results.jsonl")

        self.transcription_timeout_seconds = int(av_settings.get("transcription_timeout_seconds", 300))

        self.transcription_server_url = f"http://localhost:{self.transcription_port}"
        self.translation_server_url = f"http://localhost:{self.translation_port}"

        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def setProgressStatus(self, status):
        print(status)

    def request_server(self, server_url, message, content, timeout_seconds=60):
        payload = {"message": message, "content": content}
        response = requests.post(server_url, json=payload, timeout=(10, timeout_seconds))
        response.raise_for_status()
        return response.json()

    def get_audio_files(self):
        supported_extensions = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".opus", ".wma"}
        files = []
        for root, _, file_names in os.walk(self.input_dir):
            for file_name in file_names:
                path = Path(root) / file_name
                if path.suffix.lower() in supported_extensions:
                    files.append(path)
        files.sort()
        return files

    def get_output_dir_for_audio(self, audio_path):
        relative = audio_path.relative_to(self.input_dir)
        stem_without_extension = relative.with_suffix("")
        output_folder = self.output_dir / stem_without_extension
        output_folder.mkdir(parents=True, exist_ok=True)
        return output_folder

    def convertTranscriptionListToString(self, transcription_list):
        if isinstance(transcription_list, list):
            return "\n".join(str(item).rstrip("\n") for item in transcription_list).strip() + "\n"
        if isinstance(transcription_list, str):
            return transcription_list
        return ""

    def readAndSaveSRTcontentFromTranscriptionList(self, output_folder, transcription_list):
        transcription_srt = self.convertTranscriptionListToString(transcription_list)
        transcription_file = output_folder / "transcription.srt"
        with open(transcription_file, "w", encoding="utf-8") as f:
            f.write(transcription_srt)
        return transcription_srt

    def write_jsonl_rows(self, rows):
        if not rows:
            return
        manifest_path = self.output_dir / self.single_manifest_filename
        with open(manifest_path, "a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def flush_cached_outputs(self, transcription_cache, translation_cache, manifest_rows):
        if self.write_strategy == "single_manifest":
            self.write_jsonl_rows(manifest_rows)
            manifest_rows.clear()
            transcription_cache.clear()
            translation_cache.clear()
            return

        if self.write_strategy != "batch_flush_per_file":
            return

        for item in transcription_cache:
            output_folder = self.get_output_dir_for_audio(item["audio_path"])
            with open(output_folder / "transcription.srt", "w", encoding="utf-8") as f:
                f.write(item["transcription_srt"])

        for item in translation_cache:
            output_folder = self.get_output_dir_for_audio(item["audio_path"])
            with open(output_folder / "translated.srt", "w", encoding="utf-8") as f:
                f.write(item["translated_srt"])
            with open(output_folder / "translated.txt", "w", encoding="utf-8") as f:
                f.write(item["translated_srt"])

        transcription_cache.clear()
        translation_cache.clear()

    def run_translation_step(self, audio_path, transcription_payload=None):
        start = time.time()

        if transcription_payload is None:
            output_folder = self.get_output_dir_for_audio(audio_path)
            transcription_file = output_folder / "transcription.srt"
            if not transcription_file.exists():
                raise FileNotFoundError(f"Missing transcription file: {transcription_file}")
            with open(transcription_file, encoding="utf-8") as f:
                transcription_srt = f.read()
        else:
            transcription_srt = self.convertTranscriptionListToString(transcription_payload)

        translated_srt = ""
        if not self.only_transcribe:
            translation_response = self.request_server(
                self.translation_server_url,
                "translate sentences",
                transcription_srt,
                timeout_seconds=max(60, self.transcription_timeout_seconds)
            )

            if isinstance(translation_response, list):
                translated_srt = "\n".join(str(item) for item in translation_response)
            else:
                translated_srt = str(translation_response)

            if self.write_strategy == "immediate":
                output_folder = self.get_output_dir_for_audio(audio_path)
                with open(output_folder / "translated.srt", "w", encoding="utf-8") as f:
                    f.write(translated_srt)
                with open(output_folder / "translated.txt", "w", encoding="utf-8") as f:
                    f.write(translated_srt)

        end = time.time()
        return end - start, translated_srt

    def batch_process(self):
        audio_files = self.get_audio_files()
        total = len(audio_files)

        if total == 0:
            self.setProgressStatus("No audio files found in INPUT.")
            return

        self.setProgressStatus(f"Found {total} file(s).")

        transcription_cache = []
        translation_cache = []
        manifest_rows = []

        transcribed_entries = []

        throughput_mode = (
            self.pipeline_mode == "transcribe_all_then_translate_all"
            and self.only_transcribe_and_translate
        )

        for index, audio_path in enumerate(audio_files, start=1):
            self.setProgressStatus(f"Step 1/{total}: Transcribing {audio_path.name}")
            start = time.time()
            try:
                transcription_response = self.request_server(
                    self.transcription_server_url,
                    "get srt transcription",
                    str(audio_path),
                    timeout_seconds=self.transcription_timeout_seconds
                )
            except Exception as error:
                self.setProgressStatus(f"[ERROR] Transcription failed for {audio_path.name}: {error}")
                continue

            if isinstance(transcription_response, dict) and transcription_response.get("error"):
                self.setProgressStatus(f"[ERROR] Transcription server error for {audio_path.name}: {transcription_response['error']}")
                continue

            output_folder = self.get_output_dir_for_audio(audio_path)
            transcription_srt = self.convertTranscriptionListToString(transcription_response)

            if self.write_strategy == "immediate":
                self.readAndSaveSRTcontentFromTranscriptionList(output_folder, transcription_response)
            elif self.write_strategy == "batch_flush_per_file":
                transcription_cache.append({
                    "audio_path": audio_path,
                    "transcription_srt": transcription_srt
                })
            elif self.write_strategy == "single_manifest":
                manifest_rows.append({
                    "input_file": str(audio_path),
                    "type": "transcription",
                    "content": transcription_srt
                })

            transcribed_entries.append((audio_path, transcription_response, transcription_srt))

            elapsed = time.time() - start
            self.setProgressStatus(f"Transcription done in {elapsed:.2f}s for {audio_path.name}")

            if self.write_strategy in {"batch_flush_per_file", "single_manifest"} and len(transcription_cache) >= self.cache_flush_every:
                self.flush_cached_outputs(transcription_cache, translation_cache, manifest_rows)

            if self.only_transcribe and not throughput_mode:
                continue

            if not throughput_mode and self.only_transcribe_and_translate:
                self.setProgressStatus(f"Step 2/{total}: Translating {audio_path.name}")
                try:
                    elapsed_translate, translated_srt = self.run_translation_step(audio_path, transcription_response)
                except Exception as error:
                    self.setProgressStatus(f"[ERROR] Translation failed for {audio_path.name}: {error}")
                    continue

                if self.write_strategy == "batch_flush_per_file":
                    translation_cache.append({
                        "audio_path": audio_path,
                        "translated_srt": translated_srt
                    })
                elif self.write_strategy == "single_manifest":
                    manifest_rows.append({
                        "input_file": str(audio_path),
                        "type": "translation",
                        "content": translated_srt
                    })

                self.setProgressStatus(f"Translation done in {elapsed_translate:.2f}s for {audio_path.name}")

                if self.write_strategy in {"batch_flush_per_file", "single_manifest"} and (
                    len(translation_cache) >= self.cache_flush_every or len(manifest_rows) >= self.cache_flush_every
                ):
                    self.flush_cached_outputs(transcription_cache, translation_cache, manifest_rows)

        if throughput_mode and self.only_transcribe_and_translate and not self.only_transcribe:
            for index, (audio_path, transcription_response, _) in enumerate(transcribed_entries, start=1):
                self.setProgressStatus(f"Step 2/{len(transcribed_entries)}: Translating {audio_path.name}")
                try:
                    elapsed_translate, translated_srt = self.run_translation_step(audio_path, transcription_response)
                except Exception as error:
                    self.setProgressStatus(f"[ERROR] Translation failed for {audio_path.name}: {error}")
                    continue

                if self.write_strategy == "batch_flush_per_file":
                    translation_cache.append({
                        "audio_path": audio_path,
                        "translated_srt": translated_srt
                    })
                elif self.write_strategy == "single_manifest":
                    manifest_rows.append({
                        "input_file": str(audio_path),
                        "type": "translation",
                        "content": translated_srt
                    })

                self.setProgressStatus(f"Translation done in {elapsed_translate:.2f}s for {audio_path.name}")

                if self.write_strategy in {"batch_flush_per_file", "single_manifest"} and (
                    len(translation_cache) >= self.cache_flush_every or len(manifest_rows) >= self.cache_flush_every
                ):
                    self.flush_cached_outputs(transcription_cache, translation_cache, manifest_rows)

        self.flush_cached_outputs(transcription_cache, translation_cache, manifest_rows)
        self.setProgressStatus("All files are done")
