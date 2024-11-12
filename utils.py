import sys
import os
import json

def load_topics():
    """
    Load topics from the 'topics.json' file.
    """
    with open('topics.json', 'r') as f:
        return json.load(f)

def get_topic_by_id(topics, topic_id):
    """
    Get a topic by its ID.
    """
    for topic in topics:
        if topic['id'] == topic_id:
            return topic
    return None

def get_topic_by_name(topics, topic_name):
    """
    Get a topic by its name.
    """
    for topic in topics:  
        if 'keyword' in topic and topic['keyword'].lower() == topic_name.lower():  # Case-insensitive comparison
            return topic
    return None
