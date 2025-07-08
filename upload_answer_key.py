from src.utils.answer_key_manager import AnswerKeyManager

# Generate a random answer key with 1 mark for each question
import random
import os

# Ensure the inputs directory exists
os.makedirs("inputs", exist_ok=True)

answer_key_data = [
    {"question_number": i, "correct_answer": random.choice(["A", "B", "C", "D"]), "points": 1}
    for i in range(1, 16)
]

manager = AnswerKeyManager()
manager.upload_answer_key(answer_key_data)
