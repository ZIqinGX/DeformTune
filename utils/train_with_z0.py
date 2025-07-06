import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import pretty_midi
import time
import pygame.mixer
import serial

from MeasureVAE.measure_vae import MeasureVAE
from data.dataloaders.bar_dataset import FolkNBarDataset
from utils.helpers import *

# 初始化设备
print("[INFO] 加载数据集和模型...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 加载数据集
dataset = FolkNBarDataset(dataset_type='train', is_short=True, num_bars=1)

# 创建模型
model = MeasureVAE(
    dataset=dataset,
    note_embedding_dim=10,
    metadata_embedding_dim=2,
    num_encoder_layers=2,
    encoder_hidden_size=512,
    encoder_dropout_prob=0.5,
    latent_space_dim=256,
    num_decoder_layers=2,
    decoder_hidden_size=512,
    decoder_dropout_prob=0.5,
    has_metadata=False
)

model_path = "D:/PhD_Year1/Prototype1/Exploring_XAI_in_GenMus_via_LSR-main/Exploring_XAI_in_GenMus_via_LSR-main/MeasureVAE/models/MeasureVAE_4by4_FolkNBarDataset1__Encoder_512_Decoder_512.pt"
model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)
model.eval()

def analyze_rhythm_complexity(note_tensor):
    total_notes = len(note_tensor)
    nonzero_notes = sum(1 for n in note_tensor if n > 0)
    rhythm_density = nonzero_notes / total_notes
    return rhythm_density

def play_midi(samples, debug=True):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    note_count = 0
    for i, note in enumerate(samples):
        pitch = int(note.item())
        if pitch <= 0 or pitch > 127:
            continue
        start_time = i * 0.5
        end_time = start_time + 0.5
        midi_note = pretty_midi.Note(velocity=100, pitch=pitch, start=start_time, end=end_time)
        instrument.notes.append(midi_note)
        note_count += 1

    midi.instruments.append(instrument)
    midi_file = "generated_debug.mid"
    midi.write(midi_file)

    if debug:
        print("[INFO] 已保存 MIDI 文件: generated_debug.mid")
        print(f"[INFO] 共生成 {note_count} 个音符")
        for note in instrument.notes:
            print(f"Pitch: {note.pitch}, Start: {note.start:.2f}, End: {note.end:.2f}")

    if note_count == 0:
        print("[WARN] 无有效音符可播放，跳过播放。")
        return

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(midi_file)
        pygame.mixer.music.play()
        print("[PLAYING] 正在播放...")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        print("[DONE] 播放完成")
    except Exception as e:
        print(f"[ERROR] 播放失败: {e}")

# 初始化 Arduino
try:
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)
    print("[INFO] 已连接到 Arduino")
except Exception as e:
    print(f"[ERROR] 无法连接 Arduino: {e}")
    arduino = None

if arduino:
    print("[INFO] 开始实时监听 Arduino 输入...")
    while True:
        try:
            line_bytes = arduino.readline()
            print("[RAW] 原始字节数据:", line_bytes)
            raw = line_bytes.decode('utf-8', errors='ignore').strip()

            try:
                z0 = float(raw)
                z0_scaled = z0 * 10
                print(f"[INFO] 转换后 z0: {z0:.4f}")
            except Exception as e:
                print(f"[WARN] z0 转换失败: {e}, raw = {repr(raw)}")
                continue

            z_tilde = torch.zeros(1, model.latent_space_dim).to(device)
            z_tilde[0, 0] = z0_scaled

            dummy_score_tensor = torch.zeros(1, 1).long().to(device)
            with torch.no_grad():
                _, samples = model.decoder(z_tilde, dummy_score_tensor, train=False)

            print("[DEBUG] samples tensor shape:", samples.shape)
            note_tensor = samples.view(-1).cpu()
            print(f"[INFO] z0 = {z0:.2f} → 音符序列: {note_tensor.tolist()}")

            rhythm_density = analyze_rhythm_complexity(note_tensor)
            print(f"[INFO] 节奏密度: {rhythm_density:.3f} (1.0 = 所有时值均有音符)")

            play_midi(note_tensor, debug=True)

        except KeyboardInterrupt:
            print("[STOP] 用户终止监听")
            break
        except Exception as e:
            print(f"[ERROR] 运行中发生错误: {e}")
