import pygame.midi
import time

# 初始化
pygame.midi.init()

# 显示可用输出设备
for i in range(pygame.midi.get_count()):
    interf, name, is_input, is_output, opened = pygame.midi.get_device_info(i)
    if is_output:
        print(f"{i}: {name.decode()} (output)")

# 使用 Microsoft GS Wavetable Synth（通常是设备1）
player = pygame.midi.Output(1)
instrument = 0  # Acoustic Grand Piano
player.set_instrument(instrument)

print("🎹 播放测试音符：C大调")
notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale

for note in notes:
    player.note_on(note, velocity=100)
    time.sleep(0.4)
    player.note_off(note, velocity=100)

player.close()
pygame.midi.quit()
