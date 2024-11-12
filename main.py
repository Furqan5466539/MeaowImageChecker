import sys
import os
from image_checker import check_image_relevance
from dotenv import load_dotenv
import utils

def process_image(keyword, trend_reason, image_path):
    score, reasoning = check_image_relevance(keyword, trend_reason, image_path)
    print(f"Image: {image_path}")
    print(f"Relevance score: {score}")
    print(f"Reasoning: {reasoning}")
    print("-" * 50)

def main():
    load_dotenv()

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python main.py <topic_id> [image_filename]")
        sys.exit(1)

    try:
        topic_id = int(sys.argv[1])
    except ValueError:
        print("Error: topic_id must be an integer.")
        sys.exit(1)

    topics = utils.load_topics()
    topic = utils.get_topic_by_id(topics, topic_id)

    if topic is None:
        print(f"Error: No topic found with id {topic_id}")
        sys.exit(1)

    keyword = topic['keyword']
    trend_reason = topic['trending_reason']

    if len(sys.argv) == 3:
        # Process single image
        image_filename = sys.argv[2]
        image_path = os.path.join("images\\" + keyword, *image_filename.split('\\'))
        if not os.path.exists(image_path):
            print(f"Error: Image file '{image_path}' not found.")
            sys.exit(1)
        process_image(keyword, trend_reason, image_path)
    else:
        # Process all images in the keyword folder
        keyword_folder = os.path.join("images", keyword.lower())
        if not os.path.exists(keyword_folder):
            print(f"Error: Folder '{keyword_folder}' not found.")
            sys.exit(1)

        image_files = [f for f in os.listdir(keyword_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.jfif'))]
        
        if not image_files:
            print(f"No image files found in '{keyword_folder}'.")
            sys.exit(1)

        for image_file in image_files:
            image_path = os.path.join(keyword_folder, image_file)
            process_image(keyword, trend_reason, image_path)

    print("All results saved to file.")

if __name__ == "__main__":
    main()