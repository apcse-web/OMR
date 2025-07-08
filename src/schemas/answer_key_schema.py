# Schema for SCERT Answer Key

class AnswerKeySchema:
    def __init__(self, question_number: int, correct_answer: str, points: int):
        """
        Initialize the schema for an answer key entry.

        :param question_number: The question number (1-15).
        :param correct_answer: The correct answer for the question.
        :param points: The points allocated to the question.
        """
        self.question_number = question_number
        self.correct_answer = correct_answer
        self.points = points

    def to_dict(self):
        """Convert the answer key entry to a dictionary."""
        return {
            "question_number": self.question_number,
            "correct_answer": self.correct_answer,
            "points": self.points
        }
