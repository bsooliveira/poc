import sys
from .retrieval import embed
from .config import settings

if __name__ == "__main__":
    vectors = embed(
        ["O prazo de inscrição termina em novembro.", "Registration ends in November."]
    )
    print(
        f"Embeddings prontos: {len(vectors)} vetores de {len(vectors[0])} dimensões",
        flush=True,
    )
    if "--training" in sys.argv:
        from huggingface_hub import snapshot_download

        path = snapshot_download(
            settings().training_model,
            allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model"],
            max_workers=2,
        )
        print(f"Modelo de treinamento em cache: {path}", flush=True)
