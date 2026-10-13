"""Bounded CPU LoRA experiment. Never enables the resulting adapter automatically."""

import argparse
import json
import random
import time
from pathlib import Path


def main():
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--steps", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.steps <= 100:
        raise ValueError("Use de 1 a 100 passos para a POC")
    torch.set_num_threads(2)
    torch.manual_seed(42)
    random.seed(42)
    records = [
        json.loads(line)
        for line in Path(args.dataset).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(records) < 4:
        raise ValueError("Ao menos quatro exemplos são necessários")
    random.shuffle(records)
    # Group by shared evidence to prevent PT/EN counterparts leaking into holdout.
    groups = {}
    for record in records:
        evidence = record["messages"][1]["content"].split("\nQuestion:")[0]
        groups.setdefault(evidence, []).append(record)
    grouped = list(groups.values())
    random.shuffle(grouped)
    validation = grouped[-1] if len(grouped) > 1 else []
    training = [r for group in (grouped[:-1] if validation else grouped) for r in group]
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.float32,
        trust_remote_code=False,
        attn_implementation="eager",
    )
    model = get_peft_model(
        model,
        LoraConfig(
            r=4,
            lora_alpha=8,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            task_type="CAUSAL_LM",
        ),
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False}
    )
    model.enable_input_require_grads()

    def encode(record):
        messages = record["messages"]
        prompt = tokenizer.apply_chat_template(
            messages[:-1], tokenize=False, add_generation_prompt=True
        )
        full = tokenizer.apply_chat_template(messages, tokenize=False)
        ids = tokenizer(full, return_tensors="pt", add_special_tokens=False)[
            "input_ids"
        ][0]
        prompt_length = len(tokenizer(prompt, add_special_tokens=False)["input_ids"])
        # Retain the answer when context is long. Loss is applied only to assistant tokens.
        prompt_ids = ids[:prompt_length][-128:]
        answer_ids = ids[prompt_length:][:128]
        if len(answer_ids) < 2:
            raise ValueError("Exemplo sem resposta treinável")
        joined = torch.cat([prompt_ids, answer_ids]).unsqueeze(0)
        labels = joined.clone()
        labels[:, : len(prompt_ids)] = -100
        return {
            "input_ids": joined,
            "attention_mask": torch.ones_like(joined),
            "labels": labels,
        }

    train_data = [encode(r) for r in training]
    valid_data = [encode(r) for r in validation]

    def evaluate():
        model.eval()
        with torch.no_grad():
            return (
                sum(model(**r).loss.item() for r in valid_data) / len(valid_data)
                if valid_data
                else None
            )

    start = time.monotonic()
    before = evaluate()
    model.train()
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=0.0002
    )
    losses = []
    for step in range(args.steps):
        batch = train_data[step % len(train_data)]
        optimizer.zero_grad(set_to_none=True)
        loss = model(**batch).loss
        if not torch.isfinite(loss):
            raise RuntimeError("Loss não finita")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(round(loss.item(), 6))
        print(json.dumps({"step": step + 1, "loss": losses[-1]}), flush=True)
    after = evaluate()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output)
    tokenizer.save_pretrained(output)
    metrics = {
        "base_model": args.model,
        "steps": args.steps,
        "train_samples": len(train_data),
        "validation_samples": len(valid_data),
        "losses": losses,
        "validation_loss_before": before,
        "validation_loss_after": after,
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "seed": 42,
        "rank": 4,
        "limitation": "Experimento pequeno de estilo. Loss não demonstra precisão factual nem melhora de tradução. Adapter não ativado automaticamente.",
    }
    (output / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    print(json.dumps(metrics), flush=True)


if __name__ == "__main__":
    main()
