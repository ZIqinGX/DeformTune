import serial
import time
import pygame
import os
from mido import MidiFile, MidiTrack, Message, merge_tracks

# === 初始化参数 ===
MIDI_DIR = "D:/PhD_Year1/Prototype1/Exploring_XAI_in_GenMus_via_LSR-main/Exploring_XAI_in_GenMus_via_LSR-main/generated_midi_files"
BAUD_RATE = 9600
SERIAL_PORT = 'COM4'

# === 自动编号合并 MIDI 文件名 ===
def get_new_merged_midi_path():
    base_filename = "merged_output"
    existing = [
        f for f in os.listdir(MIDI_DIR)
        if f.startswith(base_filename) and f.endswith(".mid")
    ]
    existing_numbers = []
    for name in existing:
        number_part = name.replace(base_filename, "").replace(".mid", "").strip("_")
        if number_part.isdigit():
            existing_numbers.append(int(number_part))
    next_index = max(existing_numbers, default=0) + 1
    return os.path.join(MIDI_DIR, f"{base_filename}_{next_index}.mid")

MERGED_MIDI_PATH = get_new_merged_midi_path()

# === 初始化 Pygame MIDI 播放器 ===
pygame.init()
pygame.mixer.init()

# === 连接 Arduino ===
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    print(f"✅ 已连接到 Arduino ({SERIAL_PORT})")
except Exception as e:
    print("❌ 无法连接 Arduino:", e)
    exit()

print("🎧 正在监听 Arduino 输入...\n")

# 合并用 MIDI 对象
merged_mid = MidiFile()
merged_track = MidiTrack()
merged_mid.tracks.append(merged_track)

def print_play_status(midi_name, values):
    a0, a1, a2, a3 = values
    print("🎧 当前播放状态：")
    print(f"📟 A0: {a0}  A1: {a1}  A2: {a2}  A3: {a3}")
    print(f"🎵 播放中: {midi_name}")
    print("─────────────────────────────")

def add_to_merged_midi(file_path):
    try:
        segment = MidiFile(file_path)
        for msg in merge_tracks(segment.tracks):
            merged_track.append(msg.copy(time=msg.time))
        merged_mid.save(MERGED_MIDI_PATH)
        print(f"💾 已合并并保存至 {MERGED_MIDI_PATH}")
    except Exception as e:
        print(f"⚠️ 合并 MIDI 出错: {e}")

while True:
    try:
        if pygame.mixer.music.get_busy():
            time.sleep(0.1)
            continue

        line = ser.readline().decode().strip()

        if line.startswith("DATA"):
            parts = line.split(",")
            if len(parts) != 5:
                continue

            values = parts[1:]
            if not all(v.isdigit() for v in values):
                continue

            a0, a1, a2, a3 = map(int, values)
            midi_name = f"midi_{a0}_{a1}_{a2}_{a3}.mid"
            full_path = os.path.join(MIDI_DIR, midi_name)

            print_play_status(midi_name, (a0, a1, a2, a3))

            if os.path.exists(full_path):
                try:
                    pygame.mixer.music.load(full_path)
                    pygame.mixer.music.play()
                    add_to_merged_midi(full_path)
                except Exception as e:
                    print(f"⚠️ 播放错误: {e}")
            else:
                print(f"⚠️ 找不到 MIDI 文件: {midi_name}")

        else:
            print(line)

    except KeyboardInterrupt:
        print("🛑 用户终止程序")
        break
    except Exception as e:
        print(f"❌ 错误: {e}")
