import sys
import os
import json
from datetime import datetime
import utils

def analyze_results(date_str, keyword, score, name_only=False):
    results_dir = "./results"
    filename = f"{date_str}_{keyword.replace(' ', '_')}.json"
    file_path = os.path.join(results_dir, filename)

    if not os.path.exists(file_path):
        print(f"No results file found for date {date_str} and keyword '{keyword}'.")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)

    matching_results = [entry for entry in data if entry['score'] == score]

    if not matching_results:
        print(f"No entries found with score {score} for date {date_str} and keyword '{keyword}'.")
        return

    if name_only:
        print("Matching image files:")
        for entry in matching_results:
            print(os.path.basename(entry['image_path']))
    else:
        print(f"Matching entries with score {score} for date {date_str} and keyword '{keyword}':")
        for entry in matching_results:
            print(f"Image path: {entry['image_path']}")
            print(f"Reasoning: {entry['reasoning']}")
            print("-" * 50)

def main():
    if len(sys.argv) < 4:
        print("Usage: python analysis.py <date:YYYYMMDD> <topic_id> <score> [-nameOnly]")
        sys.exit(1)

    date_str = sys.argv[1]
    try:
        topic_id = int(sys.argv[2])
    except ValueError:
        print("Error: topic_id must be an integer.")
        sys.exit(1)

    topics = utils.load_topics()
    topic = utils.get_topic_by_id(topics, topic_id)
    keyword = topic['keyword']
    
    try:
        score = int(sys.argv[3])
    except ValueError:
        print("Error: score must be an integer.")
        sys.exit(1)

    # Check for -nameOnly option
    name_only = "-nameOnly" in sys.argv

    # Validate date format
    try:
        datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        print("Error: Invalid date format. Use YYYYMMDD.")
        sys.exit(1)

    analyze_results(date_str, keyword, score, name_only)

if __name__ == "__main__":
    main()