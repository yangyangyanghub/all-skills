"""实时会议转录小控制台。"""
import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol

from transcribe import get_model


CHUNK = 1600
CHANNELS = 1
RATE = 16000
MODEL_NAME = "paraformer-zh-streaming"
DEFAULT_OUTPUT = "temp/live-meeting-console.json"
DEPENDENCY_HELP = '''缺少实时转录依赖，请先安装：
uv pip install pyaudio numpy --python ".opencode/skills/meeting-minutes/funasr-env/Scripts/python.exe"'''


class StreamingModel(Protocol):
  """FunASR 流式模型协议。"""

  def generate(
    self,
    input: object,
    cache: dict[str, object],
    chunk_size: list[int],
    is_final: bool,
  ) -> object:
    """生成转录结果。"""


@dataclass
class TranscriptSegment:
  """单段转录文本。"""

  text: str
  start: float
  end: float


@dataclass
class ConsoleState:
  """控制台运行状态。"""

  output_path: Path
  device: str
  language: str
  audio_input: str = "系统默认输入设备"
  start_time: float = field(default_factory=time.time)
  current_start: float = 0.0
  latest_text: str = ""
  paused: bool = False
  stopping: bool = False
  segments: list[TranscriptSegment] = field(default_factory=list)
  last_render: float = 0.0
  last_saved_text: str = ""


class DependencyError(RuntimeError):
  """实时音频依赖缺失。"""


def format_clock(seconds: float) -> str:
  """格式化运行时长。"""
  total_seconds = max(0, int(seconds))
  minutes, secs = divmod(total_seconds, 60)
  hours, mins = divmod(minutes, 60)
  return f"{hours:02d}:{mins:02d}:{secs:02d}"


def parse_args() -> argparse.Namespace:
  """解析命令行参数。"""
  parser = argparse.ArgumentParser(description="实时会议转录小控制台")
  parser.add_argument(
    "--output",
    "-o",
    default=DEFAULT_OUTPUT,
    help="输出 JSON 文件路径，默认 temp/live-meeting-console.json",
  )
  parser.add_argument("--device", default="cpu", help="模型运行设备，默认 cpu")
  parser.add_argument("--language", "-l", default="zh", help="语言代码，默认 zh")
  parser.add_argument(
    "--dry-run",
    action="store_true",
    help="不加载模型和麦克风，只生成一份兼容 JSON 用于验证",
  )
  return parser.parse_args()


def get_elapsed(state: ConsoleState) -> float:
  """获取已运行秒数。"""
  return time.time() - state.start_time


def build_output(state: ConsoleState) -> dict[str, object]:
  """构建兼容 format_minutes.py 的 JSON 输出。"""
  segments = [
    {
      "text": segment.text,
      "start": round(segment.start, 3),
      "end": round(segment.end, 3),
    }
    for segment in state.segments
  ]
  return {
    "metadata": {
      "mode": "realtime-console",
      "duration": round(get_elapsed(state), 3),
      "model": MODEL_NAME,
      "language": state.language,
      "device": state.device,
      "audio_input": state.audio_input,
      "timestamp": datetime.now().isoformat(),
    },
    "segments": segments,
    "full_text": " ".join(segment.text for segment in state.segments),
  }


def save_output(state: ConsoleState) -> None:
  """保存 UTF-8 JSON 输出。"""
  state.output_path.parent.mkdir(parents=True, exist_ok=True)
  with state.output_path.open("w", encoding="utf-8") as output_file:
    json.dump(build_output(state), output_file, ensure_ascii=False, indent=2)


def render_screen(state: ConsoleState, force: bool = False) -> None:
  """渲染实时控制台面板。"""
  now = time.time()
  if not force and now - state.last_render < 1.0:
    return
  state.last_render = now
  status = "暂停中" if state.paused else "录音中"
  os.system("cls")
  print("实时会议转录小控制台")
  print("=" * 60)
  print(f"状态：{status}")
  print(f"已运行：{format_clock(get_elapsed(state))}")
  print(f"输出：{state.output_path}")
  print(f"麦克风：{state.audio_input}")
  print("命令：p 暂停/继续 | v 最近10段 | s 停止保存 | q 停止保存")
  print("-" * 60)
  print("最近识别：")
  print(state.latest_text or "（等待语音输入...）")
  print("-" * 60)
  print("提示：识别文本变化时会自动保存 JSON。")


def print_recent_segments(state: ConsoleState) -> None:
  """显示最近 10 段转录。"""
  os.system("cls")
  print("最近 10 段转录")
  print("=" * 60)
  recent_segments = state.segments[-10:]
  if not recent_segments:
    print("暂无转录片段。")
  for segment in recent_segments:
    start = format_clock(segment.start)
    end = format_clock(segment.end)
    print(f"[{start} - {end}] {segment.text}")
  print("\n按任意键返回控制台...")


def handle_keypress(state: ConsoleState) -> None:
  """处理 Windows 终端快捷键。"""
  import msvcrt

  if not msvcrt.kbhit():
    return
  key = msvcrt.getwch().lower()
  if key == "p":
    state.paused = not state.paused
    save_output(state)
    render_screen(state, force=True)
  elif key == "v":
    print_recent_segments(state)
    msvcrt.getwch()
    render_screen(state, force=True)
  elif key in {"s", "q"}:
    state.stopping = True


def extract_text(result: object) -> str:
  """从 FunASR 结果中提取文本。"""
  if not isinstance(result, list) or not result:
    return ""
  first_item = result[0]
  if not isinstance(first_item, dict):
    return ""
  text = first_item.get("text", "")
  if not isinstance(text, str):
    return ""
  return text.strip()


def append_segment_if_changed(state: ConsoleState, text: str, end_time: float) -> bool:
  """文本变化时追加片段。"""
  clean_text = text.strip()
  if not clean_text or clean_text == state.latest_text:
    return False
  state.latest_text = clean_text
  state.segments.append(
    TranscriptSegment(text=clean_text, start=state.current_start, end=end_time)
  )
  state.current_start = end_time
  return True


def import_audio_dependencies() -> tuple[object, object]:
  """导入实时音频依赖。"""
  try:
    import numpy
    import pyaudio
  except ImportError as error:
    raise DependencyError(DEPENDENCY_HELP) from error
  return numpy, pyaudio


def get_audio_input_label(audio: object) -> str:
  """获取系统默认输入设备名称。"""
  try:
    info = audio.get_default_input_device_info()
  except OSError:
    return "系统默认输入设备"
  if not isinstance(info, dict):
    return "系统默认输入设备"
  name = info.get("name")
  if isinstance(name, str) and name:
    return name
  return "系统默认输入设备"


def open_audio_stream() -> tuple[object, object]:
  """打开麦克风音频流。"""
  _, pyaudio = import_audio_dependencies()
  audio = pyaudio.PyAudio()
  stream = audio.open(
    format=pyaudio.paInt16,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
  )
  return audio, stream


def close_audio_stream(audio: object | None, stream: object | None) -> None:
  """关闭并释放麦克风音频流。"""
  if stream is not None:
    if stream.is_active():
      stream.stop_stream()
    stream.close()
  if audio is not None:
    audio.terminate()


def generate_text(
  model: StreamingModel,
  audio_chunk: object,
  cache: dict[str, object],
  chunk_size: list[int],
  is_final: bool,
) -> str:
  """调用流式模型并返回识别文本。"""
  result = model.generate(
    input=audio_chunk,
    cache=cache,
    chunk_size=chunk_size,
    is_final=is_final,
  )
  return extract_text(result)


def run_console(model: StreamingModel, state: ConsoleState) -> None:
  """运行实时转录控制台。"""
  numpy, _ = import_audio_dependencies()
  audio: object | None = None
  stream: object | None = None
  cache: dict[str, object] = {}
  chunk_size = [0, 10, 5]
  try:
    audio, stream = open_audio_stream()
    state.audio_input = get_audio_input_label(audio)
    render_screen(state, force=True)
    while not state.stopping:
      handle_keypress(state)
      if state.paused:
        render_screen(state)
        time.sleep(0.1)
        continue
      data = stream.read(CHUNK, exception_on_overflow=False)
      audio_chunk = numpy.frombuffer(data, dtype=numpy.int16).astype(numpy.float32) / 32768.0
      text = generate_text(model, audio_chunk, cache, chunk_size, is_final=False)
      elapsed = get_elapsed(state)
      if append_segment_if_changed(state, text, elapsed):
        save_output(state)
        render_screen(state, force=True)
      else:
        render_screen(state)
    final_audio = numpy.array([], dtype=numpy.float32)
    final_text = generate_text(model, final_audio, cache, chunk_size, is_final=True)
    if append_segment_if_changed(state, final_text, get_elapsed(state)):
      save_output(state)
  finally:
    close_audio_stream(audio, stream)
    save_output(state)


def run_dry_run(state: ConsoleState) -> None:
  """生成一份非交互验证 JSON。"""
  state.latest_text = "这是实时转录控制台 dry-run 验证。"
  state.segments.append(
    TranscriptSegment(text=state.latest_text, start=0.0, end=0.1)
  )
  save_output(state)
  print(f"dry-run JSON 已保存: {state.output_path}")


def configure_stdio() -> None:
  """配置 Windows 终端 UTF-8 输出。"""
  if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
  if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def main() -> int:
  """入口函数。"""
  configure_stdio()
  args = parse_args()
  state = ConsoleState(
    output_path=Path(args.output),
    device=args.device,
    language=args.language,
  )
  if args.dry_run:
    run_dry_run(state)
    return 0
  try:
    model = get_model("streaming", args.device)
    run_console(model, state)
  except DependencyError as error:
    print(error)
    return 1
  except KeyboardInterrupt:
    state.stopping = True
    save_output(state)
    print(f"\n已停止并保存: {state.output_path}")
    return 0
  except Exception:
    save_output(state)
    raise
  print(f"\n已保存: {state.output_path}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
