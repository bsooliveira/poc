"""Evaluate a saved adapter locally without promoting it into the FAQ workflow."""

import argparse
import json
from pathlib import Path


def main():
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    adapter = Path(args.adapter)
    config = json.loads((adapter / "adapter_config.json").read_text())
    base = config["base_model_name_or_path"]
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(base, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        base, torch_dtype=torch.float32, trust_remote_code=False
    )
    model = PeftModel.from_pretrained(model, str(adapter))
    model.eval()
    text = tokenizer.apply_chat_template(
        [
            {"role": "system", "content": "Answer only using the supplied evidence."},
            {"role": "user", "content": args.prompt},
        ],
        tokenize=False,
        add_generation_prompt=True,
    )
    encoded = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        answer = model.generate(
            **encoded,
            max_new_tokens=100,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    print(
        tokenizer.decode(
            answer[0][encoded.input_ids.shape[1] :], skip_special_tokens=True
        )
    )


if __name__ == "__main__":
    main()
