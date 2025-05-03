from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline

# Load model and tokenizer
model_path = "sportsbert-finetuned"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForMaskedLM.from_pretrained(model_path)

# Create fill-mask pipeline
pipe = pipeline("fill-mask", model=model, tokenizer=tokenizer)

# Example input text with [MASK]
text = "Michael Jordan is a [MASK] player."

# Perform inference
results = pipe(text)

print("All predicted tokens and scores:")
for result in results:
    print(f"Token: {result['token_str']}, Score: {result['score']}")

# Define a list of acceptable options
acceptable_tokens = ['good', 'bad', 'strong', 'weak']

# Filter results to show only acceptable tokens
filtered_results = [result for result in results if result['token_str'] in acceptable_tokens]

if filtered_results:
    print("\nFiltered results:")
    for result in filtered_results:
        print(f"Token: {result['token_str']}, Score: {result['score']}")
else:
    print("\nNo acceptable tokens found.")