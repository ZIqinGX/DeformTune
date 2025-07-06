import os
import serial
import time
import pygame.mixer

# === 配置参数 ===
midi_dir = r"D:\PhD_Year1\Prototype2\Exploring_XAI_in_GenMus_via_LSR-main\generated_midi_files"
serial_port = 'COM4'
baud_rate = 9600

# 播放控制
min_switch_interval = 1.0  # 防抖时间（秒）
last_switch_time = 0
current_xyzw = (None, None, None, None)

# === 初始化播放系统 ===
pygame.mixer.init()
pygame.mixer.music.set_volume(1.0)

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

def display_status(x, y, z, s, filename):
    print("\n🎧 当前播放状态：")
    print(f"📟 A0: {x}  A1: {y}  A2: {z}  A3: {s}")
    print(f"🎵 播放中: {os.path.basename(filename)}")
    print("─────────────────────────────")

# === 主循环 ===
try:
    arduino = serial.Serial(serial_port, baud_rate, timeout=1)
    time.sleep(2)
    print(f"✅ 已连接到 Arduino ({serial_port})")
    print("🎧 正在监听 Arduino 输入...")

    while True:
        line = arduino.readline().decode().strip()
        if not line:
            continue

        # 打印来自 Arduino 的调试信息（不处理）
        if line.startswith("📊") or line.startswith("isNowActive"):
            print(line)
            continue

        # 处理正式数据：DATA,x,y,z,s
        if line.startswith("DATA"):
            try:
                _, sx, sy, sz, ss = line.split(",")
                x, y, z, s = int(sx), int(sy), int(sz), int(ss)
                new_xyzw = (x, y, z, s)
                filename = os.path.join(midi_dir, f"midi_{x}_{y}_{z}_{s}.mid")
                now = time.time()

                if new_xyzw != current_xyzw and not pygame.mixer.music.get_busy():
                    current_xyzw = new_xyzw
                    last_switch_time = now
                    play_midi_file(filename)
                    display_status(x, y, z, s, filename)

                elif new_xyzw == current_xyzw and not pygame.mixer.music.get_busy():
                    play_midi_file(filename)
                    display_status(x, y, z, s, filename)

                elif not pygame.mixer.music.get_busy():
                    print("✅ 播放完成，可以继续操作")

            except Exception as e:
                print(f"⚠️ 数据解析错误: {e}")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("🛑 用户终止程序")
finally:
    if 'arduino' in locals() and arduino.is_open:
        arduino.close()
    pygame.mixer.quit()
