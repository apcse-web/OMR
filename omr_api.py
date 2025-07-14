import os
import shutil
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import subprocess
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

class ProcessRequest(BaseModel):
    image_url: str
    template_url: str
    marker_url: str
    answer_key_url: str

SUPABASE_URL = "https://eshrnhrpazuqpoimtveb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVzaHJuaHJwYXp1cXBvaW10dmViIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjQyODk4NSwiZXhwIjoyMDY4MDA0OTg1fQ.BN8c-b4yMW0PgvD1vHjKr7QjK1XbhSVMqfM2waIb_-E"  # Replace with your actual key
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your Lovable app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def download_file(url, dest):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

@app.post("/process")
def process_image(req: ProcessRequest):
    temp_inputs = "inputs_api"
    temp_outputs = "outputs_api"
    os.makedirs(temp_inputs, exist_ok=True)
    os.makedirs(temp_outputs, exist_ok=True)

    # Download template, marker, answer_key
    download_file(req.template_url, os.path.join(temp_inputs, "template.json"))
    download_file(req.marker_url, os.path.join(temp_inputs, "omr_marker.jpg"))
    download_file(req.answer_key_url, os.path.join(temp_inputs, "answer_key.json"))

    # Download the single image
    fname = os.path.basename(req.image_url.split("?")[0])
    download_file(req.image_url, os.path.join(temp_inputs, fname))

    # Run your scoring script
    process = subprocess.run(
        ["python", "run_scoring.py", "--input_dir", temp_inputs, "--output_dir", temp_outputs],
        capture_output=True, text=True
    )
    print(process.stdout)
    print(process.stderr)

    # Upload final_scores.csv to Supabase Storage
    result_path = os.path.join(temp_outputs, "final_scores.csv")
    with open(result_path, "rb") as f:
        supabase_client.storage.from_("omroutputs").upload(fname.replace('.jpeg', '_score.csv'), f)

    public_url = supabase_client.storage.from_("omroutputs").get_public_url(fname.replace('.jpeg', '_score.csv'))

    # Clean up
    shutil.rmtree(temp_inputs)
    shutil.rmtree(temp_outputs)

    return {"result_url": public_url}