import csv
import os
import json
import subprocess
import glob
import shutil
import argparse

def load_answer_key(file_path):
    """Load the answer key from a JSON file."""
    if not os.path.exists(file_path):
        print(f"Error: Answer key file not found at {file_path}.")
        return {}
    with open(file_path, "r") as file:
        answer_key = json.load(file)
    return {item["question_number"]: item for item in answer_key}

def process_image(image_path, input_dir):
    """Process an image and extract the response."""
    temp_dir = os.path.join(input_dir, "temp_inputs")
    os.makedirs(temp_dir, exist_ok=True)

    temp_image_path = os.path.join(temp_dir, os.path.basename(image_path))
    shutil.copy(image_path, temp_image_path)

    template_path = os.path.join(input_dir, "template.json")
    if os.path.exists(template_path):
        shutil.copy(template_path, temp_dir)
    else:
        print(f"Error: template.json not found in {input_dir} directory.")
        return None

    marker_path = os.path.join(input_dir, "omr_marker.jpg")
    if os.path.exists(marker_path):
        shutil.copy(marker_path, temp_dir)
    else:
        print(f"Error: omr_marker.jpg not found in {input_dir} directory.")
        return None

    try:
        process = subprocess.run(["python", "main.py", "-i", temp_dir], capture_output=True, text=True)
        output = process.stdout

        print(f"Full output for {image_path}:\n{output}")

        response_start = output.find("Read Response:")
        if response_start == -1:
            print(f"Error: 'Read Response:' not found for {image_path}.")
            return None

        response_raw = output[response_start + len("Read Response:"):].strip()
        start_index = response_raw.find("{")
        end_index = response_raw.rfind("}") + 1
        if start_index == -1 or end_index == -1:
            print(f"Error: Could not find JSON object in the output for {image_path}.")
            return None

        cleaned_response = response_raw[start_index:end_index].replace("'", '"')
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON for {image_path}. Exception: {e}")
            return None
    finally:
        shutil.rmtree(temp_dir)

def main():
    parser = argparse.ArgumentParser(description="OMR Scoring Script")
    parser.add_argument('--input_dir', type=str, default='inputs', help='Input directory containing images and config files')
    parser.add_argument('--output_dir', type=str, default='outputs', help='Output directory for final_scores.csv')
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    answer_key_path = os.path.join(input_dir, "answer_key.json")
    answer_key = load_answer_key(answer_key_path)

    image_paths = glob.glob(os.path.join(input_dir, "*.jpeg"))
    output_file = os.path.join(output_dir, "final_scores.csv")

    os.makedirs(output_dir, exist_ok=True)

    # Write header to the CSV file
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        header = ["Apaar_ID", "Exam_Code"]
        for i in range(1, 11):  # Only 10 MCQs
            header.extend([f"Q{i}_recognized_answer", f"Q{i}_correct_answer", f"marks_for_Q{i}"])
        header.extend(["PART_D_recognition", "PART_D_marks", "Total_marks"])
        writer.writerow(header)

    # Process each image and append results to the CSV file
    for image_path in image_paths:
        response = process_image(image_path, input_dir)
        if not response:
            continue

        apaar_id = response.get("Apaar_ID", "N/A")
        exam_code = response.get("Exam_code", "N/A")
        try:
            recognized_answers = {int(k[1:]): v for k, v in response.items() if k.startswith('q')}
        except ValueError as e:
            print(f"Error parsing recognized answers for {image_path}: {e}")
            recognized_answers = {}

        # Handle PART_D recognition
        part_d_recognition = response.get("part_d", "")
        if not part_d_recognition:
            print(f"Warning: PART_D_recognition is empty for {image_path}.")
            part_d_marks = 0
        else:
            # Example logic: Sum digits in PART_D_recognition
            part_d_marks = sum(int(d) for d in part_d_recognition if d.isdigit())

        # Calculate MCQ score
        mcq_score = 0
        row = [apaar_id, exam_code]

        for question_number in range(1, 11):  # Only 10 MCQs
            recognized_answer = recognized_answers.get(question_number, "N/A")
            correct_answer = answer_key.get(question_number, {}).get("correct_answer", "N/A")
            points = answer_key.get(question_number, {}).get("points", 0)
            marks = points if recognized_answer == correct_answer else 0
            mcq_score += marks
            row.extend([recognized_answer, correct_answer, marks])

        # Calculate total marks
        total_marks = mcq_score + part_d_marks
        row.extend([part_d_recognition, part_d_marks, total_marks])

        # Write the row to the CSV file
        with open(output_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(row)

        print(f"Processed and saved results for {image_path}.")

if __name__ == "__main__":
    main()