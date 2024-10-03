import requests
import os
from bs4 import BeautifulSoup
import json  # Import json module to parse JSON data
from datetime import datetime

class SoupBot:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        # Define the directory to save the images
        self.base_image_dir = 'images'
        os.makedirs(self.base_image_dir, exist_ok=True)  # Create the base directory if it doesn't exist
    def parse_comments(self, soup):
        comments = []
        for comment in soup.select('.discussion-container > .comment-container'):
            comments.append(self.parse_comment(comment))
        return comments
    def parse_comment(self, comment):
        user = comment.find('h5', class_='comment-username').text.strip()
        text = comment.find('div', class_='comment-content').text.strip()
        text = text.replace('\n', '<br>')  # Replace newlines with <br> tags
        upvotes = int(comment.find('span', class_='upvote-count').text.strip())
        
        # Handling the timestamp
        timestamp_str = comment.find('span', class_='comment-date')['title']
        timestamp = datetime.strptime(timestamp_str, '%a %d %b %Y %H:%M').isoformat() + 'Z'

        # Check for tags in the badges
        tags = [badge.text.strip() for badge in comment.find_all('span', class_='badge')]
        
        # Check for nested comments
        nested_comments = []
        replies = comment.find('div', class_='comment-replies')
        if replies:
            for nested_comment in replies.find_all('div', class_='comment-container'):
                nested_comments.append(self.parse_comment(nested_comment))

        return {
            "user": user,
            "text": text,
            "timestamp": timestamp,
            "upvotes": upvotes,
            "tags": tags,  # Now includes all badges
            "nested_comments": nested_comments
        }


    def downloadImage(self, img):
        if 'src' in img.attrs:
            img_url = img['src']  # Get the image URL
            # Split the URL to get the path after the domain
            path_parts = img_url.split('/', 3)[-1:]  # Get the part after the domain
            img_path = os.path.join(self.base_image_dir, *path_parts)  # Create the local path

            # Create directory structure if it doesn't exist
            os.makedirs(os.path.dirname(img_path), exist_ok=True)

            # Download the image
            try:
                img_response = requests.get(img_url)
                img_response.raise_for_status()  # Raise an error for bad responses
                with open(img_path, 'wb') as f:
                    f.write(img_response.content)  # Save the image
                print(f"Image saved locally as {img_path}")
                img['src'] = img_path.replace('\\', '/')
            except requests.HTTPError as e:
                print(f"Failed to download {img_url}. Status code: {e.response.status_code}")
            except requests.RequestException as e:
                print(f"An error occurred while downloading {img_url}: {e}")

    def processPage(self, url):
        # Send a GET request to the URL
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise an error for bad responses
        except requests.RequestException as e:
            print(f"Failed to retrieve the webpage. Error: {e}")
        else:
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract the suggested answer using the correct class
            suggested_answer = soup.select_one('.correct-answer')
            suggested_answer_text = suggested_answer.decode_contents().strip() if suggested_answer else "No correct answer found."

            # Check if the suggested answer is an image or text
            if suggested_answer and suggested_answer.find('img'):
                # If it's an image, download it
                img_tags = suggested_answer.find_all('img')
                for img in img_tags:
                    self.downloadImage(img)
                suggested_answer_text = suggested_answer.decode_contents()
            else:
                # If it's text, just keep the text
                print("Suggested Answer (Text):", suggested_answer_text)

            # Remove unwanted elements
            for unwanted_class in ['hide-solution', 'question-answer', 'reveal-solution']:
                for element in soup.find_all(class_=unwanted_class):
                    element.decompose()  # Removes the element from the tree

            # Find images within the card text
            card_text = soup.select_one('p.card-text')  # Select the specific parent
            img_tags = card_text.find_all('img') if card_text else []  # Ensure card_text is not None

            # Download images
            for img in img_tags:
                self.downloadImage(img)

            # Extract the question
            question = soup.select_one('.question-body')  # Get the question element
            question_cleaned = question.decode_contents() if question else "Question not found."
            question_cleaned = ' '.join(question_cleaned.split()).strip()  # Clean up whitespace

            # Extract vote distribution from the JSON in the script tag
            vote_distribution = {}
            voted_answers_tally = soup.select_one('.voted-answers-tally script')

            if voted_answers_tally:
                try:
                    # Load the JSON data from the script tag
                    vote_data = json.loads(voted_answers_tally.string)
                    for item in vote_data:
                        answer = item["voted_answers"]
                        count = item["vote_count"]
                        vote_distribution[answer] = count
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON data: {e}")

            # Print the results
            print("Question:", question_cleaned)
            print("Suggested Answer:", suggested_answer_text)
            print("Vote Distribution:", vote_distribution)
            
            # Convert comments to JSON format
            comments_json = {
                "comments": self.parse_comments(soup.select_one('.discussion-container'))
            }

            # Print the JSON structure
            print(json.dumps(comments_json, indent=4))

            # Create the structured JSON
            structured_json = {
                "exam": {
                    "question": question_cleaned,
                    "answer": suggested_answer_text
                },
                "comments": comments_json["comments"],
                "vote_distribution": vote_distribution
            }

            # Export the JSON to a file named data.json
            with open('data.json', 'w') as json_file:
                json.dump(structured_json, json_file, indent=4)

            print("Data exported to data.json")