import click
import torch
import os
import shutil
import numpy as np
import serial
import time
import pygame.midi

from torch.utils.data.dataset import TensorDataset
from MeasureVAE.measure_vae import MeasureVAE
from MeasureVAE.vae_trainer import VAETrainer
from MeasureVAE.vae_tester import VAETester
from data.dataloaders.bar_dataset import *
from utils.helpers import *

# ✅ 确保 PyTorch 多进程初始化
if __name__ == '__main__':
    import torch.multiprocessing as mp
    mp.set_start_method('spawn', force=True)
    torch.serialization.add_safe_globals([TensorDataset])

print("✅ 正在使用的 VAETrainer 文件路径: MeasureVAE.vae_trainer")
print("PyTorch版本:", torch.__version__)
print("CUDA是否可用:", torch.cuda.is_available())
print("当前设备:", torch.cuda.current_device())
print("设备名称:", torch.cuda.get_device_name(0))

# ✅ 初始化 Arduino 连接
try:
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)
    print("✅ 已连接到 Arduino")
except Exception as e:
    print(f"⚠️ 无法连接到 Arduino: {e}")
    arduino = None

# ✅ MIDI 播放函数

def play_midi(samples, debug=True):
    import pretty_midi

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
        print("🎼 已保存 MIDI 文件: generated_debug.mid")
        print(f"🎹 共生成 {note_count} 个音符")
        for note in instrument.notes:
            print(f"Pitch: {note.pitch}, Start: {note.start:.2f}, End: {note.end:.2f}")

    if note_count == 0:
        print("⚠️ 无有效音符可播放，跳过播放。")
        return

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(midi_file)
        pygame.mixer.music.play()
        print("🎵 正在播放...")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        print("✅ 播放完成")
    except Exception as e:
        print(f"⚠️ 播放失败: {e}")

@click.command()
@click.option('--batch_size', default=256)
@click.option('--num_epochs', default=30)
@click.option('--train/--test', default=False)
def main(batch_size, num_epochs, train):
    print("✅ 进入 main() 函数")
    print(f"[DEBUG] CLI 参数解析成功: train = {train}, epochs = {num_epochs}")
    print(f"⚙️ 当前运行模式: {'训练' if train else '测试'}")

    dataset_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'datasets')
    if os.path.exists(dataset_dir):
        print("⚠️  发现旧数据集，删除 `datasets/` 目录...")
        shutil.rmtree(dataset_dir)
    os.makedirs(dataset_dir, exist_ok=True)

    print("📅 重新加载 `FolkNBarDataset` 数据集...")
    folk_dataset_train = FolkNBarDataset('train', is_short=True, num_bars=1)
    print(f"✅ FolkNBarDataset Train loaded with {folk_dataset_train.num_dataset_files} files")
    folk_dataset_test = FolkNBarDataset('test', is_short=True, num_bars=1)
    print(f"✅ FolkNBarDataset Test loaded with {folk_dataset_test.num_dataset_files} files")

    model = MeasureVAE(
        dataset=folk_dataset_train,
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
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if os.path.exists(model_path) and not train:
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"✅ 加载模型: {model_path}")

    model.to(device)

    if train:
        print("🚀 训练模式启动...")
        trainer = VAETrainer(
            dataset=folk_dataset_train,
            model=model,
            lr=1e-4,
            has_reg_loss=True,
            reg_type='rhy_complexity',
            reg_dim=0
        )
        print("📦 准备启动训练流程...")
        trainer.train_model(batch_size=batch_size, num_epochs=num_epochs, plot=True, log=True)
        print("✅ 模型训练完成。")
    else:
        print("🧪 测试模式启动...")
        model.eval()
        tester = VAETester(
            dataset=folk_dataset_test,
            model=model,
            has_reg_loss=True,
            reg_type='rhy_complexity',
            reg_dim=0
        )
        print("🎯 评估模型...")
        tester.test_model(batch_size=batch_size)

        if arduino:
            print("🎇 开始实时监听 Arduino 输入...")
            while True:
                try:
                    raw = arduino.readline().decode().strip()
                    print(f"🗓️ Arduino 输入原始值: {raw}")
                    if not raw or '准备' in raw:
                        print(f"⚠️ 跳过无效输入: {raw}")
                        continue
                    z0 = float(raw)
                    print(f"🎛️ 转换后 z0: {z0:.2f}")
                    z_tilde = torch.zeros(1, model.latent_space_dim).to(device)
                    z_tilde[0, 0] = z0
                    dummy_score_tensor = torch.zeros(1, 24).long().to(device)

                    with torch.no_grad():
                        _, samples = model.decoder(z_tilde, dummy_score_tensor, train=False)

                    print("📋 samples tensor shape:", samples.shape)
                    if samples.ndim == 3:
                        note_tensor = samples[0, 0].cpu()
                    elif samples.ndim == 2:
                        note_tensor = samples[0].cpu()
                    else:
                        note_tensor = samples.cpu()

                    print(f"🎛️ z0 = {z0:.2f} → 音符序列: {note_tensor.tolist()}")
                    play_midi(note_tensor, debug=True)

                except KeyboardInterrupt:
                    print("🛑 终止监听。")
                    break
                except Exception as e:
                    print(f"⚠️ 错误: {e}")

if __name__ == '__main__':
    main()
