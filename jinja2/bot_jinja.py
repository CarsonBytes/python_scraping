import json
from flask import Flask, render_template
import os

class JinjaBot: 
    def __init__(self):
        self.app = Flask(__name__)
        self.file_list = []

    def render_comments(self,comments, level=0):
        """Recursively render comments into HTML."""
        html = '<div class="nested-comments">'
        for comment in comments:
            html += f'''
                <div class="comment">
                    <div class="comment-content">
                        <div class="comment-header">
                            <i class="fa-solid fa-user avatar"></i>
                            <div class="text">{comment['user']}</div>
                        </div>
                        <div class="text">{comment['text']}</div>
                    </div>
                    <div style="display: flex; align-items: center; width: 100%;">
                        <div class="timestamp" data-timestamp="{comment['timestamp']}">
                            <!-- Placeholder for the formatted date -->
                        </div>
                        <div class="tags-upvotes">
                            <span class="upvotes"><i class="fa-solid fa-caret-up"></i> {comment['upvotes']}</span>
                            {''.join(f'<span class="tag">{tag}</span>' for tag in comment['tags'])}
                        </div>
                    </div>
            '''

            # Render nested comments if they exist, but limit to 5 levels
            if comment['nested_comments'] and level < 5:
                html += self.render_comments(comment['nested_comments'], level + 1)

            html += '</div>'  # Close comment div
        html += '</div>'  # Close nested-comments div
        return html  # Return safe HTML to render in template

    def create_qna(self):
        # Read data from data.json
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract exam and comments data
        exam_data = data["exam"]
        comments_data = data["comments"]
        vote_distribution_data = data["vote_distribution"]

        # Calculate total votes for width calculation
        total_votes = sum(vote_distribution_data.values())

        # Prepare width percentages for the bar segments
        width_percentages = {
            key: (value / total_votes * 100) if total_votes > 0 else 0
            for key, value in vote_distribution_data.items()
        }

        # Create application context
        with self.app.app_context():
            # Render comments to HTML
            rendered_comments = self.render_comments(comments_data)

            # Prepare the context for the template
            context = {
                "exam": exam_data,
                "comments": rendered_comments,
                "vote_distribution": width_percentages  # Pass calculated widths
            }

            # Render the template with the context
            output_html = render_template('template_qna.html', **context)

            # Write the output HTML to a file
            with open('output.html', 'w', encoding='utf-8') as f:
                f.write(output_html)

        print("HTML output saved to output.html")
    
    def create_table_of_contents(self, exam_code):
        current_dir = os.path.dirname(__file__) 
        json_path = os.path.join(current_dir, "file_list", f"{exam_code}.json")

        if not self.file_list:
            with open(json_path, "r") as json_file:
                self.file_list = json.load(json_file)

        sorted_data = sorted(self.file_list, key=lambda x: x["id"])
        with open(json_path, "w") as json_file:
            json.dump(sorted_data, json_file, indent=4)

        # Read the HTML template
        with open("template_table_of_contents.html", "r") as template_file:
            template_content = template_file.read()

        # Generate the file list HTML
        file_list_html = ""
        for file in sorted_data:
            file_list_html += f"""
                <li>
                    <a href="qna/{file['id']}.mhtml">{file['id']} - {file['description']}</a>
                    <button class="save-button" data-file="{file['id']}">Mark for Review</button>
                </li>
            """

        # Replace placeholder in the template
        final_html = template_content.replace("{exam_code}", exam_code).replace("{file_list}", file_list_html)

        final_html_path = os.path.join(current_dir, exam_code, "table_of_contents.html")
        # Write the final HTML to a new file
        with open(final_html_path, "w") as html_file:
            html_file.write(final_html)

        print("HTML file has been generated: table_of_contents.html")