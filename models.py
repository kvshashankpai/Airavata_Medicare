"""Shared lazy model interface: generate(model_key, prompt) -> str.

The application uses this only as a language/wording layer. Backend extraction,
workflow, safety, triage, and persistence remain deterministic and authoritative.
"""
import os
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
except ImportError:  # The web app can still run with its safe fallback.
    torch = None
    AutoTokenizer = AutoModelForCausalLM = None

MODEL_REGISTRY = {
    'airavata': 'ai4bharat/Airavata',
    'qwen': 'Qwen/Qwen2.5-1.5B-Instruct',
    'openhathi': 'sarvamai/OpenHathi-7B-Hi-v0.1-Base',
    'sarvam': 'sarvam-105b',
}
_loaded_hf_models = {}


def _load_hf_model(repo_id):
    if torch is None or AutoTokenizer is None:
        raise RuntimeError('Install torch and transformers to use local Hugging Face models.')
    if repo_id in _loaded_hf_models: return _loaded_hf_models[repo_id]
    print(f'Loading {repo_id} ...')
    tokenizer = AutoTokenizer.from_pretrained(repo_id, padding_side='left')
    if tokenizer.pad_token is None: tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(repo_id, torch_dtype='auto', device_map='auto')
    model.eval()
    _loaded_hf_models[repo_id] = (tokenizer, model)
    print(f'{repo_id} loaded.')
    return tokenizer, model


def _generate_hf(repo_id, prompt, max_new_tokens=350):
    tokenizer, model = _load_hf_model(repo_id)
    if repo_id.startswith('Qwen/') and hasattr(tokenizer, 'apply_chat_template'):
        inputs = tokenizer.apply_chat_template([{'role':'user','content':prompt}], add_generation_prompt=True, tokenize=True, return_tensors='pt').to(model.device)
        input_ids = inputs
        with torch.inference_mode():
            outputs = model.generate(input_ids, max_new_tokens=max_new_tokens, do_sample=False, repetition_penalty=1.08, pad_token_id=tokenizer.eos_token_id)
        generated = outputs[0][input_ids.shape[1]:]
    else:
        # Airavata model card specifies this exact open-instruct format.
        formatted = '<|user|>\n' + prompt + '\n<|assistant|>\n'
        inputs = tokenizer(formatted, return_tensors='pt').to(model.device)
        with torch.inference_mode():
            outputs = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, repetition_penalty=1.08, pad_token_id=tokenizer.eos_token_id)
        generated = outputs[0][inputs['input_ids'].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def _generate_sarvam(prompt, model_name='sarvam-105b', max_tokens=500):
    from openai import OpenAI
    api_key = os.environ.get('SARVAM_API_KEY')
    if not api_key: raise RuntimeError('Set SARVAM_API_KEY environment variable first.')
    client = OpenAI(api_key=api_key, base_url='https://api.sarvam.ai/v1')
    response = client.chat.completions.create(model=model_name, messages=[{'role':'user','content':prompt}], temperature=0.1, max_tokens=max_tokens)
    return response.choices[0].message.content.strip()


def generate(model_key, prompt):
    if model_key in ('airavata', 'qwen', 'openhathi'):
        return _generate_hf(MODEL_REGISTRY[model_key], prompt)
    if model_key == 'sarvam': return _generate_sarvam(prompt, model_name=MODEL_REGISTRY['sarvam'])
    raise ValueError(f"Unknown model_key '{model_key}'. Valid options: {list(MODEL_REGISTRY.keys())}")
