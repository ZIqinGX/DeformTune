import serial
import time
import pygame.mixer
import os

# 配置参数
midi_dir = r"D:\PhD_Year1\Prototype2\Exploring_XAI_in_GenMus_via_LSR-main\generated_midi_files"
min_switch_interval = 1.0  # 秒
last_switch_time = 0
current_xy = (None, None)

# 初始化播放系统
pygame.mixer.init()
pygame.mixer.music.set_volume(1.0)

# 连接 Arduino
try:
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)
    print("✅ 已连接到 Arduino (COM4)")
except Exception as e:
    print(f"❌ 无法连接 Arduino: {e}")
    arduino = None

# 压力值映射到编号（翻转，压力大 → 编号小）
def map_pressure_to_index(val, in_min=-1.0, in_max=0.0, out_min=1, out_max=10):
    val = max(min(val, in_max), in_min)
    scaled = (val - in_min) / (in_max - in_min)
    index = int(round(scaled * (out_max - out_min) + out_min))
    return out_max - (index - out_min)

# 播放 MIDI 文件
def play_midi_file(filepath):
    if not os.path.isfile(filepath):
        print(f"⚠️ 文件不存在: {filepath}")
        return
    try:
        pygame.mixer.music.stop()             # 停止上一首
        pygame.time.wait(100)                 # 等待 100ms，确保播放系统稳定
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        print(f"🎵 正在播放: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"⚠️ 播放失败: {e}")

# 主循环
if arduino:
    print("🎧 正在监听 Arduino 输入...")
    try:
        while True:
            line = arduino.readline().decode().strip()
            if not line or "准备" in line:
                continue
            try:
                vals = [float(v) for v in line.split(",")]
                if len(vals) != 2:
                    print(f"⚠️ 输入格式错误: {line}")
                    continue
                p0, p1 = vals
                x = map_pressure_to_index(p0)
                y = map_pressure_to_index(p1)
                print(f"📟 A0: {p0:.3f} → {x} | A1: {p1:.3f} → {y}")

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
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("🛑 用户终止程序")
    finally:
        arduino.close()
        pygame.mixer.quit()
