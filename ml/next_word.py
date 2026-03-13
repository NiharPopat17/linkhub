from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch

_model = None
_tokenizer = None


def _load():
    global _model, _tokenizer
    if _model is None:
        _tokenizer = GPT2Tokenizer.from_pretrained('distilgpt2')
        _tokenizer.pad_token = _tokenizer.eos_token
        _model = GPT2LMHeadModel.from_pretrained('distilgpt2')
        _model.eval()
    return _model, _tokenizer


def predict_next_words(text, num_words=5):
    if not text or not text.strip():
        return ''
    try:
        model, tokenizer = _load()
        inputs = tokenizer(text, return_tensors='pt')
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=num_words,
                pad_token_id=tokenizer.eos_token_id,
                do_sample=False,
            )
        generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        suggestion = generated[len(text):]
        return suggestion.split('\n')[0].strip()
    except Exception:
        return ''
