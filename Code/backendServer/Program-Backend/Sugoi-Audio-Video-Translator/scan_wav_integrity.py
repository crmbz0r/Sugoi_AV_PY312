import argparse
import json
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def check_wav_file(file_path: Path):
    try:
        size = file_path.stat().st_size
        if size < 44:
            return (str(file_path), False, "too_small")

        with file_path.open("rb") as handle:
            header = handle.read(12)
        if len(header) < 12:
            return (str(file_path), False, "short_header")
        if header[0:4] != b"RIFF" or header[8:12] != b"WAVE":
            return (str(file_path), False, "invalid_riff_wave_header")

        with wave.open(str(file_path), "rb") as wav_reader:
            channels = wav_reader.getnchannels()
            sample_width = wav_reader.getsampwidth()
            frame_rate = wav_reader.getframerate()
            frame_count = wav_reader.getnframes()

            if channels <= 0:
                return (str(file_path), False, "invalid_channels")
            if sample_width <= 0:
                return (str(file_path), False, "invalid_sample_width")
            if frame_rate <= 0:
                return (str(file_path), False, "invalid_sample_rate")
            if frame_count < 0:
                return (str(file_path), False, "invalid_frame_count")

            wav_reader.readframes(1)

        return (str(file_path), True, "ok")
    except wave.Error as exc:
        return (str(file_path), False, f"wave_error: {exc}")
    except Exception as exc:
        return (str(file_path), False, f"exception: {exc}")


def scan(input_dir: Path, workers: int):
    wav_files = sorted(input_dir.rglob("*.wav"), key=lambda path: str(path).lower())
    results = []

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        for result in executor.map(check_wav_file, wav_files):
            results.append(result)

    total = len(results)
    ok = sum(1 for _, valid, _ in results if valid)
    invalid_rows = [{"file": file_path, "reason": reason} for file_path, valid, reason in results if not valid]

    reason_counts = {}
    for row in invalid_rows:
        reason = row["reason"]
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    report = {
        "input": str(input_dir.resolve()),
        "total_wav_files": total,
        "valid_wav_files": ok,
        "invalid_wav_files": total - ok,
        "invalid_reason_counts": reason_counts,
        "invalid_files": invalid_rows,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="Scan WAV files for integrity issues")
    parser.add_argument("--input", required=True, help="Root folder to scan recursively")
    parser.add_argument("--output", default="OUTPUT/wav_integrity_report.json", help="Output report JSON path")
    parser.add_argument("--workers", type=int, default=8, help="Number of worker threads")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")

    report = scan(input_dir, args.workers)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Scanned WAV files: {report['total_wav_files']}")
    print(f"Valid WAV files: {report['valid_wav_files']}")
    print(f"Invalid WAV files: {report['invalid_wav_files']}")
    print(f"Report: {output_path.resolve()}")


if __name__ == "__main__":
    main()
