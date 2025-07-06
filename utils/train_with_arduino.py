import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import pretty_midi
import time
import pygame.midi
import serial

from MeasureVAE.measure_vae import MeasureVAE
from data.dataloaders.bar_dataset import FolkNBarDataset
from utils.helpers import *

# ✨ 初始化设备
print("\U0001F50D 加载数据集和模型...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 加载数据集
dataset = FolkNBarDataset(dataset_type='train', is_short=True, num_bars=1)

# 创建 MeasureVAE 模型
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

model_path = "D:/PhD_Year1/Prototype1/Exploring_XAI_in_GenMus_via_LSR-main/Exploring_XAI_in_GenMus_via_LSR-main/MeasureVAE/models/MeasureVAE_model.pth"
model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)
model.eval()

# 操作功能: 播放 MIDI

def play_midi(samples, debug=True):
    import re

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    note_count = 0
    for i, note in enumerate(samples):
        pitch = int(note.item())
        if pitch <= 0 or pitch > 127:
            continue
        start_time = i * 0.5
        end_time = start_time + 0.5
        midi_note = pretty_midi.Note(
            velocity=100, pitch=pitch, start=start_time, end=end_time
        )
        instrument.notes.append(midi_note)
        note_count += 1

    midi.instruments.append(instrument)

    # 播放用文件
    debug_filename = "generated_debug.mid"
    midi.write(debug_filename)

    # ✅ 保存编号文件到指定路径
    save_dir = "D:/PhD_Year1/Prototype1/Exploring_XAI_in_GenMus_via_LSR-main/Exploring_XAI_in_GenMus_via_LSR-main"
    os.makedirs(save_dir, exist_ok=True)

    existing = [f for f in os.listdir(save_dir) if re.match(r"^(\d+)\.mid$", f)]
    numbers = [int(re.match(r"^(\d+)\.mid$", f).group(1)) for f in existing]
    next_num = max(numbers) + 1 if numbers else 1
    save_filename = os.path.join(save_dir, f"{next_num:03d}.mid")
    midi.write(save_filename)

    if debug:
        print(f"💾 MIDI 文件已保存为: {save_filename}")
        print(f"🎧 播放用文件: {debug_filename}")
        print(f"🎶 共生成 {note_count} 个音符")
        for note in instrument.notes:
            print(f"Pitch: {note.pitch}, Start: {note.start:.2f}, End: {note.end:.2f}")

    if note_count == 0:
        print("⚠️ 无有效音符可播放, 跳过播放.")
        return

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(debug_filename)
        pygame.mixer.music.play()
        print("🎵 正在播放...")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        print("✅ 播放完成")
    except Exception as e:
        print(f"⚠️ 播放失败: {e}")



# 初始化 Arduino
try:
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)
    print("✅ connect Arduino")
except Exception as e:
    print(f"⚠️ can't connect Arduino: {e}")
    arduino = None

if arduino:
    print("🎧 start receiving Arduino input...")
    while True:
        try:
            raw = arduino.readline().decode().strip()
            print(f"📅 Arduino input value: {raw}")
            if not raw or 'prepare' in raw:
                print(f"⚠️ ignore invalid value: {raw}")
                continue

            z0 = float(raw)
            z_tilde = torch.zeros(1, model.latent_space_dim).to(device)
            z_tilde[0, 0] = z0

            dummy_score_tensor = torch.zeros(1, 24).long().to(device)
            with torch.no_grad():
                _, samples = model.decoder(z_tilde, dummy_score_tensor, train=False)

            print("📟 original samples tensor shape:", samples.shape)
            note_tensor = samples.view(-1).cpu()
            print(f"🎛 z0 = {z0:.2f} → notes generated: {note_tensor.tolist()}")
            play_midi(note_tensor, debug=True)

        except KeyboardInterrupt:
            print("🔚 stop.")
            break
        except Exception as e:
            print(f"⚠️ error: {e}")
