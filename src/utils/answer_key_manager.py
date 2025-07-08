import json
from src.schemas.answer_key_schema import AnswerKeySchema

class AnswerKeyManager:
    def __init__(self, storage_path="inputs/answer_key.json"):
        """
        Initialize the AnswerKeyManager.

        :param storage_path: Path to store the answer key JSON file.
        """
        self.storage_path = storage_path

    def upload_answer_key(self, answer_key_data):
        """
        Upload and save the SCERT answer key.

        :param answer_key_data: List of dictionaries containing question_number, correct_answer, and points.
        """
        try:
            # Validate and convert to schema objects
            answer_key = [
                AnswerKeySchema(**entry).to_dict() for entry in answer_key_data
            ]

            # Save to JSON file
            with open(self.storage_path, "w") as file:
                json.dump(answer_key, file, indent=4)

            print("Answer key uploaded successfully.")
        except Exception as e:
            print(f"Error uploading answer key: {e}")

    def load_answer_key(self):
        """
        Load the SCERT answer key from storage.

        :return: List of answer key entries as dictionaries.
        """
        try:
            with open(self.storage_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("Answer key file not found.")
            return []
        except Exception as e:
            print(f"Error loading answer key: {e}")
            return []
