from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import openai
import re
from urllib.parse import urlparse

app = Flask(__name__)

# Configure your OpenAI API key
openai.api_key = 'your-openai-api-key'

def analyze_website(url):
    """Analyze the website and return structured data"""
    try:
        # Fetch the website content
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic information
        data = {
            'title': soup.title.string if soup.title else 'No title',
            'meta_description': soup.find('meta', attrs={'name': 'description'})['content'] 
                              if soup.find('meta', attrs={'name': 'description'}) else 'No meta description',
            'headings': {
                'h1': [h1.text.strip() for h1 in soup.find_all('h1')],
                'h2': [h2.text.strip() for h2 in soup.find_all('h2')],
                'h3': [h3.text.strip() for h3 in soup.find_all('h3')],
            },
            'links': [a['href'] for a in soup.find_all('a', href=True)],
            'images': len(soup.find_all('img')),
            'word_count': len(re.findall(r'\w+', soup.get_text())),
            'status_code': response.status_code,
            'load_time': response.elapsed.total_seconds()
        }
        
        return data
    except Exception as e:
        return {'error': str(e)}

def generate_ai_response(website_data, user_question):
    """Generate an AI response based on website data and user question"""
    prompt = f"""
    You are a website analysis assistant. Here's data about the website:
    {website_data}
    
    The user asks: {user_question}
    
    Provide a detailed, helpful response analyzing the website based on the available data.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful website analysis assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error generating AI response: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    url = data.get('url')
    question = data.get('question', 'Tell me about this website')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Validate URL
    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):
        return jsonify({'error': 'Invalid URL'}), 400
    
    # Analyze website
    website_data = analyze_website(url)
    if 'error' in website_data:
        return jsonify({'error': website_data['error']}), 500
    
    # Generate AI response
    ai_response = generate_ai_response(website_data, question)
    
    return jsonify({
        'website_data': website_data,
        'ai_response': ai_response
    })

if __name__ == '__main__':
    app.run(debug=True)
