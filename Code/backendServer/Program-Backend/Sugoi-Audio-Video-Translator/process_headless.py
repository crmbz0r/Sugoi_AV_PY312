import json
import time

import requests

from SubtitleProcessor import SubtitleProcessor


def _load_transcription_port():
    with open("../../../User-Settings.json", encoding="utf-8") as user_settings_file:
        user_settings_data = json.load(user_settings_file)
    return int(user_settings_data["Sugoi_Audio_Video_Translator"]["transcription_server_port_number"])


def _wait_for_transcription_server(port, timeout_seconds=180):
    url = f"http://localhost:{port}/"
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = requests.post(
                url,
                json={"message": "test server", "content": ""},
                timeout=(2, 2)
            )
            if response.ok:
                print(f"Transcription server is ready on port {port}.")
                return True
        except Exception:
            pass

        time.sleep(2)

    print(f"[ERROR] Transcription server did not become ready on port {port} within {timeout_seconds}s.")
    return False


def main():
    port = _load_transcription_port()
    if not _wait_for_transcription_server(port):
        raise SystemExit(1)

    subtitle_processor = SubtitleProcessor()
    subtitle_processor.batch_process()


if __name__ == "__main__":
    main()
