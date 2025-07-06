import serial
import time
import pygame.mixer
import os
import time

# 初始化路径
midi_dir = r"D:\PhD_Year1\Prototype2\Exploring_XAI_in_GenMus_via_LSR-main\generated_midi_files"

last_switch_time = 0
min_switch_interval = 3.0

# 初始化播放器
pygame.mixer.init()
pygame.mixer.music.set_volume(1.0)

# 初始化 Arduino 串口
try:
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)
    print("✅ 已连接到 Arduino (COM4)")
except Exception as e:
    print(f"❌ 无法连接 Arduino: {e}")
    arduino = None

current_index = None  # 当前正在播放的编号
current_file = None

def play_midi_file(filename):
    if not os.path.isfile(filename):
        print(f"⚠️ 文件不存在: {filename}")
        return
    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        print(f"🎵 正在播放: {os.path.basename(filename)}")
    except Exception as e:
        print(f"⚠️ 播放失败: {e}")

def map_pressure_to_index(val, in_min=-1.0, in_max=0.0, out_min=1, out_max=10):
    val = max(min(val, in_max), in_min)  # 限制 val 在输入范围内
    scaled = (val - in_min) / (in_max - in_min)  # 映射到 0~1
    index = int(round(scaled * (out_max - out_min) + out_min))
    return out_max - (index - out_min)  # ✅ 翻转编号：用力越大，编号越小

if arduino:
    print("🎧 开始监听 Arduino 输入...")
    try:
        while True:
            raw = arduino.readline().decode().strip()
            if not raw or "准备" in raw:
                continue
            try:
                pressure_val = float(raw)
                new_index = map_pressure_to_index(pressure_val)

                print(f"📟 原始压力值: {pressure_val:.4f} → 映射编号: {new_index}")

                current_time = time.time()
                if new_index != current_index and (current_time - last_switch_time > min_switch_interval):
                    current_index = new_index
                    last_switch_time = current_time
                    current_file = os.path.join(midi_dir, f"midi_{new_index}_1_1_1.mid")
                    play_midi_file(current_file)
                elif new_index == current_index and not pygame.mixer.music.get_busy():
                    play_midi_file(current_file)

            except ValueError:
                print(f"⚠️ 无效输入: {raw}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("🛑 用户中断，退出程序")
    finally:
        arduino.close()
        pygame.mixer.quit()
