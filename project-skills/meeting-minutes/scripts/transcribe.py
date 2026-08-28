"""音频转录核心脚本 - 支持离线和实时两种模式"""
import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime


def get_model(model_name: str, device: str = "cuda"):
    """加载指定模型"""
    from funasr import AutoModel

    models = {
        "nano": {
            "model": "FunAudioLLM/Fun-ASR-Nano-2512",
            "kwargs": {"hub": "ms", "vad_model": "fsmn-vad"}
        },
        "sensevoice": {
            "model": "iic/SenseVoiceSmall",
            "kwargs": {"vad_model": "fsmn-vad"}
        },
        "streaming": {
            "model": "paraformer-zh-streaming",
            "kwargs": {}
        },
        "paraformer": {
            "model": "paraformer-zh",
            "kwargs": {"vad_model": "fsmn-vad", "punc_model": "ct-punc"}
        }
    }

    if model_name not in models:
        print(f"未知模型: {model_name}，可选: {', '.join(models.keys())}")
        sys.exit(1)

    config = models[model_name]
    print(f"正在加载模型: {config['model']}...")
    model = AutoModel(
        model=config["model"],
        device=device,
        disable_update=True,
        **config["kwargs"]
    )
    print("模型加载完成")
    return model


def transcribe_offline(model, input_path: str, language: str = "auto", batch_size: int = 1) -> dict:
    """离线转录音频文件"""
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)

    print(f"正在转录: {input_path.name}")
    start_time = time.time()

    result = model.generate(
        input=str(input_path),
        batch_size=batch_size,
        language=language
    )

    elapsed = time.time() - start_time

    # 构建输出
    segments = []
    if result:
        for item in result:
            segment = {
                "text": item.get("text", ""),
                "start": item.get("timestamp", [[0]])[0][0] / 1000 if item.get("timestamp") else 0,
                "end": item.get("timestamp", [[0]])[-1][1] / 1000 if item.get("timestamp") else 0,
            }
            segments.append(segment)

    full_text = " ".join([s["text"] for s in segments])

    output = {
        "metadata": {
            "input_file": str(input_path),
            "duration": segments[-1]["end"] if segments else 0,
            "model": model.__class__.__name__,
            "language": language,
            "timestamp": datetime.now().isoformat(),
            "process_time": round(elapsed, 2)
        },
        "segments": segments,
        "full_text": full_text
    }

    print(f"转录完成: {len(segments)} 段，耗时 {elapsed:.1f}s")
    return output


def transcribe_streaming(model, duration: int = 0, output_path: str = None) -> dict:
    """流式实时转录"""
    try:
        import pyaudio
        import numpy as np
    except ImportError:
        print("需要安装 pyaudio: pip install pyaudio")
        sys.exit(1)

    # 音频配置
    CHUNK = 1600  # 100ms @ 16kHz
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    cache = {}
    chunk_size = [0, 10, 5]
    segments = []
    current_text = ""
    start_time = time.time()
    segment_start = 0

    print("开始实时转录... (Ctrl+C 停止)")
    print("-" * 50)

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

            result = model.generate(
                input=audio,
                cache=cache,
                chunk_size=chunk_size,
                is_final=False
            )

            if result and result[0].get("text"):
                new_text = result[0]["text"]
                if new_text != current_text:
                    current_text = new_text
                    elapsed = time.time() - start_time
                    print(f"\r[{elapsed:.1f}s] {current_text}", end="", flush=True)

            # 检查时长限制
            if duration > 0 and (time.time() - start_time) >= duration:
                break

    except KeyboardInterrupt:
        print("\n\n停止转录...")

    # 最终结果
    result = model.generate(
        input=np.array([]),
        cache=cache,
        chunk_size=chunk_size,
        is_final=True
    )

    if result and result[0].get("text"):
        segments.append({
            "text": result[0]["text"],
            "start": segment_start,
            "end": time.time() - start_time
        })

    stream.stop_stream()
    stream.close()
    p.terminate()

    full_text = " ".join([s["text"] for s in segments])

    output = {
        "metadata": {
            "mode": "realtime",
            "duration": time.time() - start_time,
            "model": "paraformer-zh-streaming",
            "timestamp": datetime.now().isoformat()
        },
        "segments": segments,
        "full_text": full_text
    }

    print(f"\n转录完成: {len(segments)} 段")
    return output


def main():
    parser = argparse.ArgumentParser(description="FunASR 音频转录工具")
    parser.add_argument("--input", "-i", help="输入音频文件路径")
    parser.add_argument("--realtime", "-r", action="store_true", help="实时麦克风转录")
    parser.add_argument("--duration", "-d", type=int, default=0, help="实时转录时长（秒），0=无限")
    parser.add_argument("--model", "-m", default="nano", choices=["nano", "sensevoice", "streaming", "paraformer"], help="模型选择")
    parser.add_argument("--language", "-l", default="auto", help="语言代码（auto/zh/en/ja/ko）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径")
    parser.add_argument("--device", default="cuda", help="设备（cuda/cpu）")

    args = parser.parse_args()

    if not args.input and not args.realtime:
        parser.print_help()
        sys.exit(1)

    # 加载模型
    model_name = "streaming" if args.realtime else args.model
    model = get_model(model_name, args.device)

    # 执行转录
    if args.realtime:
        result = transcribe_streaming(model, args.duration, args.output)
    else:
        result = transcribe_offline(model, args.input, args.language)

    # 输出结果
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"结果已保存: {output_path}")
    else:
        print("\n" + "=" * 50)
        print("转录结果:")
        print("=" * 50)
        print(result["full_text"])


if __name__ == "__main__":
    main()
