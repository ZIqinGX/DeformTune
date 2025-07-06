import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
import pretty_midi
import time
import pygame.midi

from MeasureVAE.measure_vae import MeasureVAE
from data.dataloaders.bar_dataset import FolkNBarDataset
from utils.helpers import *

print("\U0001F50D 加载数据集和模型...")

# 初始化
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
dataset = FolkNBarDataset(dataset_type='train', is_short=True, num_bars=1)
# 定义模型
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

# 明确模型路径
model_path = "D:/PhD_Year1/Prototype1/Exploring_XAI_in_GenMus_via_LSR-main/Exploring_XAI_in_GenMus_via_LSR-main/MeasureVAE/models/MeasureVAE_4by4_FolkNBarDataset1__Encoder_512_Decoder_512.pt"

# 加载模型参数
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)



print("NUMBER OF NOTES: ", len(dataset.note2index_dicts))

# 随机用一个 latent z 向量
print("\U0001F9EA 使用 z 向量生成样本...")
for i in range(5):
    z_tilde = torch.zeros(1, model.latent_space_dim).to(device)
    z_tilde[0, 0] = i * 0.5  # 控制 z 的第 0 个维度，模拟不同节奏复杂度

    dummy_score_tensor = torch.zeros(1, 24).long().to(device)
    with torch.no_grad():
        _, samples = model.decoder(z_tilde, dummy_score_tensor, train=False)
        print("🧾 原始 samples tensor shape:", samples.shape)
        samples = samples.view(-1)  # 取预测值
        print(f"🎛️ z0 = {z_tilde[0,0].item():.2f} → 音符序列: {samples.tolist()}")


    time.sleep(1)

# 播放 MIDI
print("\U0001F3B5 正在播放生成的音乐...")
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
        midi_note = pretty_midi.Note(
            velocity=100, pitch=pitch, start=start_time, end=end_time
        )
        instrument.notes.append(midi_note)
        note_count += 1

    midi.instruments.append(instrument)
    midi_file = "generated_debug.mid"
    midi.write(midi_file)

    if debug:
        print("\U0001F3BC 已保存 MIDI 文件: generated_debug.mid")
        print(f"\U0001F3B9 共生成 {note_count} 个音符")
        for note in instrument.notes:
            print(f"Pitch: {note.pitch}, Start: {note.start:.2f}, End: {note.end:.2f}")

    if note_count == 0:
        print("⚠️ 无有效音符可播放，跳过播放。")
        return

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(midi_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        print("✅ 播放完成")
    except Exception as e:
        print(f"⚠️ 播放失败: {e}")

play_midi(samples, debug=True)
