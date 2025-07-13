import os
import shutil
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import subprocess
import supabase

app = FastAPI()

class ProcessRequest(BaseModel):
    image_urls: List[str]
    template_url: str
    marker_url: str
    answer_key_url: str

SUPABASE_URL = "https://eshrnhrpazuqpoimtveb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVzaHJuaHJwYXp1cXBvaW10dmViIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjQyODk4NSwiZXhwIjoyMDY4MDA0OTg1fQ.BN8c-b4yMW0PgvD1vHjKr7QjK1XbhSVMqfM2waIb_-E"  # Replace with your actual key

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

def download_file(url, dest):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

@app.post("/process")
def process_images(req: ProcessRequest):
    temp_inputs = "inputs_api"
    temp_outputs = "outputs_api"
    os.makedirs(temp_inputs, exist_ok=True)
    os.makedirs(temp_outputs, exist_ok=True)

    # Download template, marker, answer_key
    download_file(req.template_url, os.path.join(temp_inputs, "template.json"))
    download_file(req.marker_url, os.path.join(temp_inputs, "omr_marker.jpg"))
    download_file(req.answer_key_url, os.path.join(temp_inputs, "answer_key.json"))

    # Download images
    for url in req.image_urls:
        fname = os.path.basename(url.split("?")[0])
        download_file(url, os.path.join(temp_inputs, fname))

    # Run your scoring script (adapted to use temp_inputs and temp_outputs)
    process = subprocess.run(
        ["python", "run_scoring.py"],  # Make sure run_scoring.py uses temp_inputs and temp_outputs
        capture_output=True, text=True, cwd=os.getcwd()
    )
    print(process.stdout)
    print(process.stderr)

    # Upload final_scores.csv to Supabase Storage
    result_path = os.path.join(temp_outputs, "final_scores.csv")
    if not os.path.exists(result_path):
        result_path = "outputs/final_scores.csv"  # fallback if script writes here

    with open(result_path, "rb") as f:
        res = supabase_client.storage.from_("omroutputs").upload("final_scores.csv", f)

    public_url = supabase_client.storage.from_("omroutputs").get_public_url("final_scores.csv")

    # Clean up
    shutil.rmtree(temp_inputs)
    shutil.rmtree(temp_outputs)

    return {"result_url": public_url}