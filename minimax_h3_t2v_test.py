"""MiniMax H3 T2V の RTX 4090 単発検証。テンプレート video_minimax_h3_t2v の構成を API 形式で再現する。"""
import json, time, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
PROMPT = (
    "Realistic live-action cinematic look: a quiet Tokyo backstreet at dusk after rain, "
    "neon signs reflected in puddles, a black cat walks slowly toward the camera, "
    "anamorphic lens, shallow depth of field, ambient city noise and distant train"
)
import sys
WIDTH, HEIGHT, STEPS = 864, 480, 20
LENGTH = int(sys.argv[1]) if len(sys.argv) > 1 else 56

wf = {
    "6":  {"class_type": "UNETLoader", "inputs": {
        "unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
    "13": {"class_type": "CLIPLoader", "inputs": {
        "clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
    "11": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
    "24": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
    "104": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {
        "clip": ["13", 0], "vae": ["11", 0], "prompt": PROMPT,
        "width": WIDTH, "height": HEIGHT, "length": LENGTH}},
    "15": {"class_type": "RandomNoise", "inputs": {"noise_seed": 260805}},
    "17": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
    "9":  {"class_type": "BasicScheduler", "inputs": {
        "model": ["6", 0], "scheduler": "simple", "steps": STEPS, "denoise": 1.0}},
    "16": {"class_type": "BasicGuider", "inputs": {"model": ["6", 0], "conditioning": ["104", 0]}},
    "14": {"class_type": "SamplerCustomAdvanced", "inputs": {
        "noise": ["15", 0], "guider": ["16", 0], "sampler": ["17", 0],
        "sigmas": ["9", 0], "latent_image": ["104", 1]}},
    "10": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["11", 0]}},
    "23": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["14", 0], "vae": ["24", 0]}},
    "91": {"class_type": "CreateVideo", "inputs": {
        "images": ["10", 0], "fps": 24.0, "audio": ["23", 0], "bit_depth": 8}},
    "92": {"class_type": "SaveVideo", "inputs": {
        "video": ["91", 0], "filename_prefix": "video/MiniMax_H3_test",
        "format": "auto", "codec": "auto"}},
}

cid = str(uuid.uuid4())
req = urllib.request.Request(f"{SERVER}/prompt", method="POST",
                             data=json.dumps({"prompt": wf, "client_id": cid}).encode(),
                             headers={"Content-Type": "application/json"})
try:
    res = json.load(urllib.request.urlopen(req))
except urllib.error.HTTPError as e:
    print("SUBMIT FAILED:", e.code)
    print(e.read().decode()[:3000])
    raise SystemExit(1)

pid = res["prompt_id"]
print(f"submitted prompt_id={pid} node_errors={res.get('node_errors')}", flush=True)
t0 = time.time()
while True:
    time.sleep(15)
    hist = json.load(urllib.request.urlopen(f"{SERVER}/history/{pid}"))
    if pid in hist:
        h = hist[pid]
        st = h.get("status", {})
        print(f"DONE status={st.get('status_str')} elapsed={time.time()-t0:.0f}s", flush=True)
        print(json.dumps(h.get("outputs", {}), ensure_ascii=False)[:1500], flush=True)
        if st.get("status_str") != "success":
            for m in st.get("messages", [])[-6:]:
                print("  ", json.dumps(m, ensure_ascii=False)[:600], flush=True)
        break
    q = json.load(urllib.request.urlopen(f"{SERVER}/prompt"))
    print(f"  ...{time.time()-t0:.0f}s queue_remaining={q.get('exec_info',{}).get('queue_remaining')}", flush=True)
