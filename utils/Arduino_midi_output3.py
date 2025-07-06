import serial
import time
import pygame.mixer
import os

# 📁 MIDI 文件路径
midi_dir = r"D:\PhD_Year1\Prototype2\Exploring_XAI_in_GenMus_via_LSR-main\generated_midi_files"
min_switch_interval = 1.0  # 防抖时间（秒）
last_switch_time = 0
current_xy = (None, None)

# 🎧 初始化播放系统
pygame.mixer.init()
pygame.mixer.music.set_volume(1.0)

# 🔌 连接 Arduino
try:
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)
    print("✅ 已连接 Arduino (COM4)")
except Exception as e:
    print(f"❌ 无法连接 Arduino: {e}")
    arduino = None

# 🎵 播放 MIDI 文件
def play_midi_file(filepath):
    if not os.path.isfile(filepath):
        print(f"⚠️ 文件不存在: {filepath}")
        return
    try:
        pygame.mixer.music.stop()
        pygame.time.wait(100)
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        print(f"🎵 正在播放: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"⚠️ 播放失败: {e}")

# 🧠 主循环监听 DATA,x,y
if arduino:
    print("🎧 正在监听 Arduino 输入...")
    try:
        while True:
            line = arduino.readline().decode().strip()
            if not line.startswith("DATA"):
                continue

            try:
                _, val0, val1 = line.split(",")
                x = int(val0)
                y = int(val1)
                print(f"📟 A0: {x} | A1: {y}")

                now = time.time()
                if (x, y) != current_xy and (now - last_switch_time) > min_switch_interval:
                    current_xy = (x, y)
                    last_switch_time = now
                    filename = os.path.join(midi_dir, f"midi_{x}_{y}_4_4.mid")
                    play_midi_file(filename)

                elif (x, y) == current_xy and not pygame.mixer.music.get_busy():
                    filename = os.path.join(midi_dir, f"midi_{x}_{y}_4_4.mid")
                    play_midi_file(filename)

            except Exception as e:
                print(f"⚠️ 数据解析错误: {e}")
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("🛑 用户终止程序")
    finally:
        arduino.close()
        pygame.mixer.quit()
