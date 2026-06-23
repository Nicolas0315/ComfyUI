import os, shutil
from huggingface_hub import hf_hub_download

MODELS = r'D:\AI\Models\ComfyUI'
JOBS = [
    ('SG161222/RealVisXL_V5.0', 'RealVisXL_V5.0_fp16.safetensors', 'checkpoints'),
    ('cagliostrolab/animagine-xl-4.0', 'animagine-xl-4.0-opt.safetensors', 'checkpoints'),
]

for repo, fname, sub in JOBS:
    dest_dir = os.path.join(MODELS, sub)
    os.makedirs(dest_dir, exist_ok=True)
    final = os.path.join(dest_dir, os.path.basename(fname))
    if os.path.exists(final):
        print(f'SKIP  {final}', flush=True)
        continue
    print(f'DL    {repo}/{fname}', flush=True)
    path = hf_hub_download(repo_id=repo, filename=fname, local_dir=dest_dir)
    if os.path.abspath(path) != os.path.abspath(final):
        shutil.move(path, final)
        top = os.path.join(dest_dir, fname.split('/')[0])
        if os.path.isdir(top):
            shutil.rmtree(top, ignore_errors=True)
    print(f'DONE  {final}', flush=True)
print('ALL DONE', flush=True)
