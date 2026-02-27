import argparse
import json
import time
import gc
import subprocess
import sys
import wave
from pathlib import Path

from WhisperTranscriber import AudioTranscriber, normalize_compute_type


def _is_valid_wav(path):
    try:
        with wave.open(str(path), "rb") as wav_file:
            _ = wav_file.getnframes()
        return True
    except Exception:
        return False


def find_audio_files(input_dir):
    root = Path(input_dir)
    allowed = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
    raw_files = sorted(
        [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed],
        key=lambda path: str(path).lower()
    )

    files = []
    skipped_invalid_wav = 0
    for path in raw_files:
        if path.suffix.lower() == ".wav" and not _is_valid_wav(path):
            skipped_invalid_wav += 1
            continue
        files.append(path)

    if skipped_invalid_wav > 0:
        print(f"Skipped invalid WAV files: {skipped_invalid_wav}")

    return files


def benchmark_preset(audio_files, preset, recycle_every, max_runtime_seconds=0):
    transcriber = None
    effective_preset = None
    row_times = []
    benchmark_started = time.perf_counter()
    for index, audio_file in enumerate(audio_files):
        if max_runtime_seconds > 0 and (time.perf_counter() - benchmark_started) >= max_runtime_seconds:
            print(f"Reached max runtime ({max_runtime_seconds}s), stopping early.")
            break

        if transcriber is None or (recycle_every > 0 and index % recycle_every == 0):
            transcriber = AudioTranscriber(overrides=preset)
            effective_preset = {
                "model_name": transcriber.model_path,
                "compute_type": transcriber.compute_type,
                "batch_size": transcriber.batch_size,
                "beam_size": transcriber.beam_size,
                "device": transcriber.device,
                "language": transcriber.language,
                "intra_threads": transcriber.intra_threads,
            }

        start = time.perf_counter()
        _ = transcriber.getTranscription(str(audio_file))
        row_times.append(time.perf_counter() - start)

        if recycle_every > 0 and ((index + 1) % recycle_every == 0):
            transcriber = None
            gc.collect()

    total_seconds = sum(row_times)
    processed_count = len(row_times)
    avg_seconds = total_seconds / processed_count if processed_count else 0
    files_per_minute = (processed_count / total_seconds) * 60 if total_seconds > 0 else 0

    return {
        "preset": effective_preset,
        "input_count": len(audio_files),
        "processed_count": processed_count,
        "total_seconds": round(total_seconds, 3),
        "average_seconds_per_file": round(avg_seconds, 3),
        "files_per_minute": round(files_per_minute, 3),
        "rows": [
            {
                "file": str(audio_files[index]),
                "seconds": round(seconds, 3)
            }
            for index, seconds in enumerate(row_times)
        ]
    }


def benchmark_preset_isolated(audio_files, preset, max_runtime_seconds=0):
    row_times = []
    failed_files = []
    nonzero_exit_files = []
    start_wallclock = time.perf_counter()

    for audio_file in audio_files:
        if max_runtime_seconds > 0 and (time.perf_counter() - start_wallclock) >= max_runtime_seconds:
            print(f"Reached max runtime ({max_runtime_seconds}s), stopping early.")
            break

        cmd = [
            sys.executable,
            __file__,
            "--single-file",
            str(audio_file),
            "--compute-type",
            str(preset["compute_type"]),
            "--batch-size",
            str(preset["batch_size"]),
            "--beam-size",
            str(preset["beam_size"]),
        ]
        if preset.get("model_name"):
            cmd.extend(["--model-name", str(preset["model_name"])])

        completed = subprocess.run(cmd, capture_output=True, text=True)
        try:
            output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
            payload = json.loads(output_lines[-1])
            row_times.append((str(audio_file), float(payload["seconds"])))
            if completed.returncode != 0:
                nonzero_exit_files.append(str(audio_file))
        except Exception:
            failed_files.append(str(audio_file))

    total_seconds = sum(seconds for _, seconds in row_times)
    success_count = len(row_times)
    files_per_minute = (success_count / total_seconds) * 60 if total_seconds > 0 else 0
    avg_seconds = total_seconds / success_count if success_count > 0 else 0
    wallclock_seconds = time.perf_counter() - start_wallclock

    return {
        "preset": {
            "model_name": str(preset.get("model_name", "")),
            "compute_type": normalize_compute_type(preset["compute_type"]),
            "batch_size": int(preset["batch_size"]),
            "beam_size": int(preset["beam_size"]),
            "device": "cuda",
            "language": "ja",
            "intra_threads": None,
        },
        "input_count": len(audio_files),
        "success_count": success_count,
        "failed_count": len(failed_files),
        "failed_files": failed_files,
        "nonzero_exit_count": len(nonzero_exit_files),
        "nonzero_exit_files": nonzero_exit_files,
        "total_seconds": round(total_seconds, 3),
        "wallclock_seconds": round(wallclock_seconds, 3),
        "average_seconds_per_file": round(avg_seconds, 3),
        "files_per_minute": round(files_per_minute, 3),
        "rows": [{"file": file_path, "seconds": round(seconds, 3)} for file_path, seconds in row_times]
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark RTX 4080 transcription presets")
    parser.add_argument("--input", default="INPUT", help="Input directory with audio files")
    parser.add_argument("--max-files", type=int, default=20, help="Limit files for quick benchmark")
    parser.add_argument("--start-index", type=int, default=0, help="Start offset in sorted input file list")
    parser.add_argument("--output", default="OUTPUT/benchmark_presets.json", help="Benchmark report path")
    parser.add_argument("--compute-type", default="", help="Optional single preset compute type (fp16/float16)")
    parser.add_argument("--batch-size", type=int, default=0, help="Optional single preset batch size")
    parser.add_argument("--beam-size", type=int, default=0, help="Optional single preset beam size")
    parser.add_argument("--model-name", default="", help="Optional model name/path override")
    parser.add_argument("--recycle-every", type=int, default=50, help="Recreate transcriber every N files for long-run stability")
    parser.add_argument("--single-file", default="", help="Internal mode: benchmark one audio file and print JSON")
    parser.add_argument("--isolate-files", action="store_true", help="Run each file in a separate subprocess for crash resilience")
    parser.add_argument("--max-runtime-seconds", type=int, default=0, help="Stop benchmark after N seconds (0 = no limit)")
    args = parser.parse_args()

    if args.single_file:
        single_start = time.perf_counter()
        single_preset = {
            "model_name": args.model_name,
            "compute_type": normalize_compute_type(args.compute_type or "float16"),
            "batch_size": max(1, int(args.batch_size or 1)),
            "beam_size": max(1, int(args.beam_size or 4)),
        }
        transcriber = AudioTranscriber(overrides=single_preset)
        _ = transcriber.getTranscription(args.single_file)
        elapsed = time.perf_counter() - single_start
        print(json.dumps({"file": args.single_file, "seconds": round(elapsed, 6)}, ensure_ascii=False))
        return

    audio_files = find_audio_files(args.input)
    if args.start_index > 0:
        audio_files = audio_files[args.start_index:]
    if args.max_files > 0:
        audio_files = audio_files[:args.max_files]

    if not audio_files:
        raise SystemExit(f"No audio files found in {args.input} for start-index {args.start_index}")

    if args.compute_type and args.batch_size > 0 and args.beam_size > 0:
        preset_matrix = [{
            "compute_type": args.compute_type,
            "batch_size": args.batch_size,
            "beam_size": args.beam_size
        }]
    else:
        preset_matrix = [
            {"compute_type": "fp16", "batch_size": 8, "beam_size": 4},
            {"compute_type": "fp16", "batch_size": 8, "beam_size": 8},
            {"compute_type": "fp16", "batch_size": 16, "beam_size": 4},
            {"compute_type": "fp16", "batch_size": 16, "beam_size": 8},
            {"compute_type": "float16", "batch_size": 8, "beam_size": 4},
            {"compute_type": "float16", "batch_size": 8, "beam_size": 8},
            {"compute_type": "float16", "batch_size": 16, "beam_size": 4},
            {"compute_type": "float16", "batch_size": 16, "beam_size": 8},
        ]

    started_at = time.perf_counter()
    results = []

    for preset in preset_matrix:
        normalized_preset = {
            **preset,
            "compute_type": normalize_compute_type(preset["compute_type"])
        }
        if args.model_name:
            normalized_preset["model_name"] = args.model_name
        print(f"Running preset {normalized_preset} on {len(audio_files)} files...")
        if args.isolate_files:
            result = benchmark_preset_isolated(audio_files, normalized_preset, args.max_runtime_seconds)
        else:
            result = benchmark_preset(audio_files, normalized_preset, args.recycle_every, args.max_runtime_seconds)
        results.append(result)

    total_duration = time.perf_counter() - started_at
    ranked = sorted(results, key=lambda row: row["average_seconds_per_file"])

    report = {
        "input": str(Path(args.input).resolve()),
        "start_index": args.start_index,
        "tested_files": len(audio_files),
        "benchmark_wallclock_seconds": round(total_duration, 3),
        "fastest_preset": ranked[0]["preset"] if ranked else None,
        "results_ranked": ranked
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Benchmark complete. Fastest preset: {report['fastest_preset']}")
    print(f"Report: {output_path.resolve()}")


if __name__ == "__main__":
    main()
