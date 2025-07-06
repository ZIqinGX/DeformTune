import serial
import time
import pygame
import os

# === 初始化参数 ===
MIDI_DIR = "D:/PhD_Year1/Prototype1/Exploring_XAI_in_GenMus_via_LSR-main/Exploring_XAI_in_GenMus_via_LSR-main/generated_midi_files"
BAUD_RATE = 9600
SERIAL_PORT = 'COM4'

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

current_filename = None
is_playing = False

def wait_for_playback():
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    print("✅ 播放完成，可以继续操作\n")

def print_play_status(midi_name, values):
    a0, a1, a2, a3 = values
    print("🎧 当前播放状态：")
    print(f"📟 A0: {a0}  A1: {a1}  A2: {a2}  A3: {a3}")
    print(f"🎵 播放中: {midi_name}")
    print("─────────────────────────────")

while True:
    try:
        # === 等待播放结束 ===
        if pygame.mixer.music.get_busy():
            time.sleep(0.1)
            continue

        # === 播放已完成，等待新输入 ===
        line = ser.readline().decode().strip()

        if line.startswith("DATA"):
            # 解析 MIDI 文件索引
            parts = line.split(",")
            if len(parts) != 5:
                continue

            values = parts[1:]  # A0, A1, A2, A3
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
                except Exception as e:
                    print(f"⚠️ 播放错误: {e}")
            else:
                print(f"⚠️ 找不到 MIDI 文件: {midi_name}")
        else:
            # 显示 Arduino 端来的调试信息（例如 smoothed, mapped）
            print(line)

    except KeyboardInterrupt:
        print("🛑 用户终止程序")
        break
    except Exception as e:
        print(f"❌ 错误: {e}")
        continue
