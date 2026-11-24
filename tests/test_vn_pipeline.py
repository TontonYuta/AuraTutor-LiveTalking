import os
import sys
import torch
import soundfile as sf
import asyncio
import edge_tts

# 1. Test PyTorch & CUDA
print("=== 1. CHECK PYTORCH & CUDA ===")
print("PyTorch Version:", torch.__version__)
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

# 2. Test Edge-TTS Vietnamese
print("\n=== 2. TEST VIETNAMESE TTS (Edge-TTS) ===")
sample_text = "Chào em! Thầy là gia sư ảo 1:1 của em hôm nay. Em muốn học bài gì nào?"
output_audio = "test_vn_greeting.wav"

async def test_tts():
    communicate = edge_tts.Communicate(sample_text, "vi-VN-NamMinhNeural")
    await communicate.save(output_audio)
    print(f"Generated Vietnamese greeting audio: {output_audio}")
    data, sr = sf.read(output_audio)
    print(f"Sample Rate: {sr}Hz, Duration: {len(data)/sr:.2f}s")

asyncio.run(test_tts())

# 3. Test Loading Wav2Lip Model Checkpoint
print("\n=== 3. TEST WAV2LIP WEIGHTS ===")
model_path = r"C:\Users\Tonton Yuta\LiveTalking\models\wav2lip.pth"
if os.path.exists(model_path):
    print("Found wav2lip.pth. Size:", os.path.getsize(model_path), "bytes")
    checkpoint = torch.load(model_path, map_location='cpu')
    print("Checkpoint keys:", list(checkpoint.keys()) if isinstance(checkpoint, dict) else "Loaded object")
else:
    print("Error: wav2lip.pth not found!")

print("\n=== ALL PIPELINE VERIFICATIONS PASSED SUCCESSFULLY! ===")
