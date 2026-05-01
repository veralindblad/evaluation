import csv
import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("openai_api_key"))
# -----------------------
# EMBEDDINGS
# -----------------------

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return np.array(response.data[0].embedding)


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# -----------------------
# LOAD DATA
# -----------------------
# id | referens | robust | parafras | fel

def load_data(file_path):
    data = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split("|")]

            if len(parts) != 8:
                print(f"Skipping line: {line}")
                continue

            data.append({
                "id": parts[0],
                "ref": parts[1],
                "robust": parts[2],
                "parafras": parts[3],
                "fel": parts[4],
        
            })

    return data


# -----------------------
# SCORE ROW
# -----------------------

def score_row(row):
    ref_emb = get_embedding(row["ref"])

    def sim(text):
        return cosine_similarity(ref_emb, get_embedding(text))

    return {
        "id": row["id"],
        "robust_sim": sim(row["robust"]),
        "parafras_sim": sim(row["parafras"]),
        "fel_sim": sim(row["fel"])
    }


# -----------------------
# MAIN
# -----------------------

def run_evaluation(input_file, output_csv):
    data = load_data(input_file)

    results = []

    for i, row in enumerate(data):
        print(f"Processing {row['id']} ({i+1}/{len(data)})")
        results.append(score_row(row))

    keys = [
        "id",
        "robust_sim",
        "parafras_sim",
        "fel_sim"
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved to {output_csv}")


if __name__ == "__main__":
    run_evaluation("answer_versions.txt", "cosine_results.csv")