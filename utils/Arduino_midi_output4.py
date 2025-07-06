import serial
import time
import pygame.mixer
import os

# === 配置参数 ===
midi_dir = r"D:\PhD_Year1\Prototype2\Exploring_XAI_in_GenMus_via_LSR-main\generated_midi_files"
serial_port = 'COM4'
baud_rate = 9600
min_switch_interval = 0.5

# === 初始化播放系统 ===
pygame.mixer.init()
pygame.mixer.music.set_volume(1.0)

# === 连接 Arduino ===
try:
    arduino = serial.Serial(serial_port, baud_rate, timeout=1)
    time.sleep(2)
    print(f"✅ 已连接到 Arduino ({serial_port})")
except Exception as e:
    print(f"❌ 无法连接 Arduino: {e}")
    arduino = None

# === 播放 MIDI 文件 ===
def play_midi_file(filepath):
    if not os.path.isfile(filepath):
        print(f"⚠️ 文件不存在: {filepath}")
        return False
    try:
        pygame.mixer.music.stop()
        pygame.time.wait(100)
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        print(f"🎵 正在播放: {os.path.basename(filepath)}")
        return True
    except Exception as e:
        print(f"⚠️ 播放失败: {e}")
        return False

# === 状态显示 ===
def show_visualization(x, y, z, s):
    print("\n🎧 当前播放状态：")
    print(f"📟 A0: {x}  A1: {y}  A2: {z}  A3: {s}")
    print(f"🎵 播放中: midi_{x}_{y}_{z}_{s}.mid")
    print("─────────────────────────────")

# === 主循环 ===
if arduino:
    print("🎧 正在监听 Arduino 输入...")
    last_switch_time = 0
    current_vals = (None, None, None, None)
    waiting_for_completion = False

    try:
        while True:
            # 播放完成提示
            if waiting_for_completion and not pygame.mixer.music.get_busy():
                print("✅ 播放完成，可以继续操作")
                waiting_for_completion = False

            line = arduino.readline().decode(errors='ignore').strip()
            if not line:
                continue

            # ✅ 如果是调试信息，直接打印
            if not line.startswith("DATA"):
                print(line)
                continue

            try:
                parts = line.split(",")[1:]  # 去掉 "DATA"
                if len(parts) != 4:
                    print(f"⚠️ 数据格式错误: {line}")
                    continue

                x, y, z, s = map(int, parts)
                now = time.time()

                if pygame.mixer.music.get_busy():
                    print("⏳ 播放尚未完成，请稍等...")
                    continue

                # 播放新值
                if (x, y, z, s) != current_vals and (now - last_switch_time) > min_switch_interval:
                    current_vals = (x, y, z, s)
                    last_switch_time = now
                    filepath = os.path.join(midi_dir, f"midi_{x}_{y}_{z}_{s}.mid")
                    if play_midi_file(filepath):
                        show_visualization(x, y, z, s)
                        waiting_for_completion = True

                # 播放完成后，值没变，也重新播放
                elif not pygame.mixer.music.get_busy() and not waiting_for_completion:
                    filepath = os.path.join(midi_dir, f"midi_{x}_{y}_{z}_{s}.mid")
                    if play_midi_file(filepath):
                        show_visualization(x, y, z, s)
                        waiting_for_completion = True

            except Exception as e:
                print(f"⚠️ 数据解析错误: {e}")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("🛑 用户终止程序")
    finally:
        arduino.close()
        pygame.mixer.quit()
