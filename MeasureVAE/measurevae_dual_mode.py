import sys
import os
import time
import torch
import serial
import pygame.midi
import pretty_midi
sys.path.append(os.path.abspath("D:\PhD_Year1\Prototype1\Exploring_XAI_in_GenMus_via_LSR-main\Exploring_XAI_in_GenMus_via_LSR-main"))
from datetime import datetime
from pathlib import Path
from measure_vae import MeasureVAE


from data.dataloaders.bar_dataset import FolkBarDataset
from measure_vae import MeasureVAE

# 初始化 pygame mixer
pygame.mixer.init()

# 设置基本参数
latent_dim = 256
model_path = "D:/PhD_Year1/Prototype1/Exploring_XAI_in_GenMus_via_LSR-main/Exploring_XAI_in_GenMus_via_LSR-main/MeasureVAE/models/MeasureVAE_model.pth"

# 加载数据集
print("📦 加载 FolkBarDataset ...")
dataset = FolkBarDataset('train', is_short=True)

# 加载模型
print("🎛 加载 MeasureVAE 模型 ...")
model = MeasureVAE(
    dataset=dataset,
    note_embedding_dim=10,
    metadata_embedding_dim=2,
    num_encoder_layers=2,
    encoder_hidden_size=512,
    encoder_dropout_prob=0.5,
    latent_space_dim=latent_dim,
    num_decoder_layers=2,
    decoder_hidden_size=512,
    decoder_dropout_prob=0.5,
    has_metadata=False
)
model.load_state_dict(torch.load(model_path, map_location="cpu"))
model.eval()

# 初始化 Arduino（使用 COM4）
try:
    arduino = serial.Serial('COM4', 9600)
    time.sleep(2)
    print("✅ 成功连接 Arduino (COM4)")
except Exception as e:
    print(f"❌ Arduino 初始化失败: {e}")
    arduino = None

# 构造 latent 向量
def build_latent_vector(z0, fixed_noise):
    z = torch.zeros(1, latent_dim)
    z[0, 0] = z0
    z[0, 1:] = fixed_noise
    return z

# 保存并播放 MIDI
def save_and_play_midi(pianoroll):
    pm = pretty_midi.PrettyMIDI()
    drum = pretty_midi.Instrument(program=0, is_drum=True)
    drum_pitch_map = [36, 38, 42]

    for step in range(pianoroll.shape[1]):
        start = step * 0.1
        end = start + 0.1
        for drum_index, val in enumerate(pianoroll[0, step]):
            if val > 0.5:
                pitch = drum_pitch_map[drum_index]
                note = pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=end)
                drum.notes.append(note)
    pm.instruments.append(drum)

    filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mid"
    pm.write(filename)
    print(f"🎼 已保存: {filename}")

    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    print("🎵 正在播放 ...")
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    print("✅ 播放完成")

# 主循环
if arduino:
    print("🟢 开始监听 Arduino 输入并生成节奏...")
    fixed_noise = torch.randn(latent_dim - 1) * 0.2

    try:
        while True:
            raw = arduino.readline().decode().strip()
            if not raw:
                continue
            try:
                z0 = float(raw) / 1023
                print(f"📡 Arduino → z[0]: {z0:.3f}")
                z = build_latent_vector(z0, fixed_noise)

                with torch.no_grad():
                    segment, *_ = model.decoder(z)

                print(f"🥁 Segment sum: {segment.sum().item():.2f}")
                save_and_play_midi(segment)

            except ValueError:
                print(f"⚠️ 无效输入: {raw}")
            except Exception as e:
                print(f"⚠️ 处理出错: {e}")

    except KeyboardInterrupt:
        print("⛔ 已终止监听")
    finally:
        arduino.close()
        pygame.mixer.quit()