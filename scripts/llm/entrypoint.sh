#!/bin/bash

for model in $(jq -c '.models[]' ./scripts/config.json); do
  repo=$(echo $model | jq -r '._repo')
  filename=$(echo $model | jq -r '._filename')
  path=$(echo $model | jq -r '.model')

  if [ -f "$path" ]; then
    echo "File $filename existed, skipped..."
  else
    huggingface-cli download "$repo" "$filename" --local-dir "$(dirname "$path")" --local-dir-use-symlinks False
  fi
done

python3 -m llama_cpp.server --config_file ./scripts/config.json
