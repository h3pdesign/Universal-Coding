import os
import ebooklib
from ebooklib import epub
import fitz  # PyMuPDF
import re
from bs4 import BeautifulSoup
import pandas as pd
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering, Trainer, TrainingArguments
import torch
from pathlib import Path

# Set device to MPS for M1 Pro
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

# Function to extract text from EPUB
def extract_epub_text(epub_path):
    try:
        book = epub.read_epub(epub_path)
        text = ""
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content = item.get_content().decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            text += soup.get_text(separator=' ', strip=True) + "\n"
        return text
    except Exception as e:
        print(f"Error processing EPUB {epub_path}: {e}")
        return ""

# Function to extract text from PDF
def extract_pdf_text(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return ""

# Clean text
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = re.sub(r'[^\w\s.,!?]', '', text)  # Remove special characters
    return text.strip()

# Process eBooks in a directory
def process_ebooks(directory, max_books=1000):
    texts = []
    for file in Path(directory).glob("*"):
        if file.suffix.lower() == ".epub":
            text = extract_epub_text(file)
        elif file.suffix.lower() == ".pdf":
            text = extract_pdf_text(file)
        else:
            continue
        if text:
            texts.append(clean_text(text))
        if len(texts) >= max_books:
            break
    return texts

# Generate synthetic Q&A pairs (simplified example)
def generate_qa_pairs(texts, num_questions=100):
    # Placeholder: Generate Q&A pairs manually or use a model like T5
    # For simplicity, create dummy Q&A based on text snippets
    qa_pairs = []
    for i, text in enumerate(texts[:num_questions]):
        context = text[:512]  # First 512 characters
        question = f"What is the main topic of text {i+1}?"
        answer = context[:100]  # Dummy answer
        qa_pairs.append({"context": context, "question": question, "answer": answer})
    return qa_pairs

# Prepare dataset for fine-tuning
class QADataset(torch.utils.data.Dataset):
    def __init__(self, qa_pairs, tokenizer, max_length=512):
        self.qa_pairs = qa_pairs
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.qa_pairs)

    def __getitem__(self, idx):
        qa = self.qa_pairs[idx]
        encoding = self.tokenizer(
            qa["question"],
            qa["context"],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        # Dummy start/end positions (replace with actual answer spans for real Q&A)
        start_positions = torch.tensor([0])
        end_positions = torch.tensor([len(qa["answer"].split())])
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "start_positions": start_positions,
            "end_positions": end_positions,
        }

# Main function
def main():
    # Directory containing eBooks
    ebook_dir = "/path/to/your/ebooks"  # Replace with your eBook directory
    output_dir = "./chatbot_model"

    # Process eBooks
    print("Processing eBooks...")
    texts = process_ebooks(ebook_dir, max_books=1000)
    print(f"Processed {len(texts)} eBooks")

    # Generate Q&A pairs
    qa_pairs = generate_qa_pairs(texts)
    print(f"Generated {len(qa_pairs)} Q&A pairs")

    # Initialize tokenizer and model
    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
    model = DistilBertForQuestionAnswering.from_pretrained("distilbert-base-uncased").to(device)

    # Create dataset
    dataset = QADataset(qa_pairs, tokenizer)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=1,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        save_steps=1000,
        save_total_limit=2,
        logging_dir="./logs",
        logging_steps=100,
        learning_rate=2e-5,
        fp16=False,  # MPS does not support fp16
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )

    # Train model
    print("Starting training...")
    trainer.train()

    # Save model
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")

    # Example inference
    question = "What is the main topic of the first eBook?"
    context = texts[0][:512]
    inputs = tokenizer(question, context, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    start_idx = outputs.start_logits.argmax()
    end_idx = outputs.end_logits.argmax()
    answer = tokenizer.decode(inputs["input_ids"][0][start_idx:end_idx+1])
    print(f"Question: {question}")
    print(f"Answer: {answer}")

if __name__ == "__main__":
    main()