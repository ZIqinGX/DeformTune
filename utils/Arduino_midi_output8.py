import serial
import pygame
import time
import os

# 设置 MIDI 文件目录
MIDI_DIR = r"D:\PhD_Year1\Prototype1\Exploring_XAI_in_GenMus_via_LSR-main\generated_midi_files"

# 初始化 pygame mixer
pygame.mixer.init()
print("✅ pygame 初始化完成")

# 连接 Arduino
ser = serial.Serial('COM4', 9600)
print(f"✅ 已连接到 Arduino ({ser.name})")
time.sleep(2)
print("🎧 正在监听 Arduino 输入...\n")

# 播放控制变量
triggerReady = True
currentMidiName = None
awaitingPlayback = False

def play_midi_file(filename):
    global currentMidiName, triggerReady, awaitingPlayback
    filepath = os.path.join(MIDI_DIR, filename)
    if os.path.exists(filepath):
        print(f"\n🎵 播放中: {filename}")
        print("─────────────────────────────")
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        currentMidiName = filename
        triggerReady = False
        awaitingPlayback = True
    else:
        print(f"⚠️ 找不到文件: {filename}")
        triggerReady = True  # 避免卡死

while True:
    try:
        # 播放中不读取 Arduino 数据
        if pygame.mixer.music.get_busy():
            time.sleep(0.1)
            continue

        # 播放结束，重启监听
        if awaitingPlayback and not pygame.mixer.music.get_busy():
            print(f"✅ 播放完成: {currentMidiName}\n")
            currentMidiName = None
            triggerReady = True
            awaitingPlayback = False

        # 正常监听状态
        if triggerReady:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("A0"):
                lines = [line]
                while len(lines) < 4:
                    l = ser.readline().decode('utf-8').strip()
                    if l.startswith("A"):
                        lines.append(l)

                # 提取 mapped 和 activated
                mapped_values = []
                activated_flags = []
                for l in lines:
                    parts = l.split('|')
                    mapped = int(parts[4].split(':')[1].strip())
                    activated = int(parts[5].split(':')[1].strip())
                    mapped_values.append(mapped)
                    activated_flags.append(activated)

                isNowActive = all(activated_flags)
                print("📊 " + " ".join([f"A{i} mapped: {mapped_values[i]} activated: {activated_flags[i]}" for i in range(4)]))
                print(f"🧠 状态 -> triggerReady: {triggerReady} | isNowActive: {isNowActive} | 正在播放: {pygame.mixer.music.get_busy()}")

                if isNowActive:
                    midi_name = f"midi_{mapped_values[0]}_{mapped_values[1]}_{mapped_values[2]}_{mapped_values[3]}.mid"
                    play_midi_file(midi_name)

    except KeyboardInterrupt:
        print("\n👋 结束监听")
        break

