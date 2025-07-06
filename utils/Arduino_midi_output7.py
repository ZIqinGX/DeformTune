import serial
import time
import pygame
import os

# 配置区域
SERIAL_PORT = 'COM4'  # 根据你的实际串口修改
BAUD_RATE = 9600
MIDI_FOLDER = 'D:/PhD_Year1/Prototype1/Exploring_XAI_in_GenMus_via_LSR-main/generated_midi_files'

# 初始化 pygame 音乐模块
pygame.init()
pygame.mixer.init()
print("✅ pygame 初始化完成")

# 尝试连接 Arduino
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    time.sleep(2)
    print(f"✅ 已连接到 Arduino ({SERIAL_PORT})")
except Exception as e:
    print(f"❌ 连接 Arduino 失败: {e}")
    exit()

# 播放 MIDI 的函数
def play_midi_file(filename):
    global currentMidiName
    filepath = os.path.join(MIDI_FOLDER, filename)
    if os.path.exists(filepath):
        print("\n🎧 当前播放状态：")
        print(f"📟 A0: {mapped_list[0]}  A1: {mapped_list[1]}  A2: {mapped_list[2]}  A3: {mapped_list[3]}")
        print(f"🎵 播放中: {filename}")
        print("─────────────────────────────")
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        currentMidiName = filename
    else:
        print(f"⚠️ 文件不存在: {filename}")

# 初始化变量
triggerReady = True
currentMidiName = None
mapped_list = [0, 0, 0, 0]

print("🎧 正在监听 Arduino 输入...\n")

# 主循环
mapped_values = {}
activated_flags = {}

try:
    while True:
        # 如果正在播放，等待
        if pygame.mixer.music.get_busy():
            time.sleep(0.05)
            continue

        # 播放结束后允许下一次触发
        if not pygame.mixer.music.get_busy() and not triggerReady:
            print(f"✅ 播放完成: {currentMidiName}\n")
            triggerReady = True
            currentMidiName = None

        # 读取串口数据
        line = ser.readline().decode('utf-8').strip()

        if line.startswith("A"):
            sensor_id = line[1]
            parts = line.split('|')
            mapped = int(parts[4].split(':')[1].strip())
            activated = int(parts[5].split(':')[1].strip())
            mapped_values[sensor_id] = mapped
            activated_flags[sensor_id] = activated

        # 当所有 A0–A3 都有了，处理一次
        if all(k in mapped_values for k in ['0','1','2','3']):
            mapped_list = [mapped_values[k] for k in ['0','1','2','3']]
            activated_list = [activated_flags[k] for k in ['0','1','2','3']]
            isNowActive = all(activated_list)

            print("📊 " + " ".join([f"A{i} mapped: {mapped_list[i]} activated: {activated_list[i]}" for i in range(4)]))
            print(f"🧠 状态 -> triggerReady: {triggerReady} | isNowActive: {isNowActive} | 正在播放: {pygame.mixer.music.get_busy()}")

            if triggerReady and isNowActive:
                midi_name = f"midi_{mapped_list[0]}_{mapped_list[1]}_{mapped_list[2]}_{mapped_list[3]}.mid"
                play_midi_file(midi_name)
                triggerReady = False

            # 清空，准备下一轮
            mapped_values.clear()
            activated_flags.clear()

except KeyboardInterrupt:
    print("\n👋 手动中断监听，程序退出")
    ser.close()
    pygame.quit()
