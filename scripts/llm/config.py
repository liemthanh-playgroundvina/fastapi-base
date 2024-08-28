import os
import json
import subprocess

with open('/app/static/files/llm/config.json', 'r') as f:
    config = json.load(f)

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