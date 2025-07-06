import pygame.midi
pygame.midi.init()
midi_out = pygame.midi.Output(0)  # 尝试不同编号
midi_out.note_on(36, 127)  # 播放 kick
import time; time.sleep(1)
midi_out.note_off(36, 127)
midi_out.close()
pygame.midi.quit()
