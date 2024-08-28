import os
import json
import subprocess

config = {
  "host": "0.0.0.0",
  "port": 8000,
  "models": [
    {
      "_repo": "Qwen/Qwen2-1.5B-Instruct-GGUF",
      "_filename": "qwen2-1_5b-instruct-q4_k_m.gguf",

      "model": "/models/qwen2-1_5b-instruct-q4_k_m.gguf",
      "model_alias": "qwen2-1.5b",
      "chat_format": "qwen",
      "n_ctx": 32768,
      "n_threads": 4,
      "n_gpu_layers": 35,
      "offload_kqv": True,
      "flash_attn": True
    },
    {
      "_repo": "Qwen/Qwen2-1.5B-Instruct-GGUF",
      "_filename": "qwen2-1_5b-instruct-q8_0.gguf",

      "model": "/models/qwen2-1_5b-instruct-q8_0.gguf",
      "model_alias": "qwen2-1.5b-q8",
      "chat_format": "qwen",
      "n_ctx": 32768,
      "n_threads": 4,
      "n_gpu_layers": 35,
      "offload_kqv": True,
      "flash_attn": True
    }
  ]
}

# Download Models
for model in config['models']:
    repo = model['_repo']
    filename = model['_filename']
    path = model['model']

    if os.path.exists(path):
        print(f"File {filename} existed, skipped...")
    else:
        subprocess.run([
            "huggingface-cli", "download", repo, filename,
            "--local-dir", os.path.dirname(path),
            "--local-dir-use-symlinks", "False"
        ])


def remove_keys_with_leading_underscore(d):
    if isinstance(d, dict):
        return {k: remove_keys_with_leading_underscore(v) for k, v in d.items() if not k.startswith('_')}
    elif isinstance(d, list):
        return [remove_keys_with_leading_underscore(item) for item in d]
    else:
        return d

cleaned_config = remove_keys_with_leading_underscore(config)

with open('/app/scripts/config.json', 'w') as f:
    json.dump(cleaned_config, f, indent=2)