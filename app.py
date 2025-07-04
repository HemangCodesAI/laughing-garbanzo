from flask import Flask, render_template, request, jsonify, Response
import requests
from urllib.parse import urlparse
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from webalgo import HTMLSEOScanner
import ollama
import uuid
import threading
from queue import Queue
import json


# Import your scanner class (assuming it's in a file called html_seo_scanner.py)
# from html_seo_scanner import HTMLSEOScanner

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

class URLFetcher:
    def __init__(self):
        self.session = requests.Session()
        
        # Set up retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_url(self, url):
        """Fetch HTML content from a URL"""
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme:
                url = 'https://' + url
            
            # Set timeout
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return {
                'success': True,
                'html': response.text,
                'status_code': response.status_code,
                'final_url': response.url
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'html': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'html': None
            }

# Store for tracking background tasks
task_status = {}
task_results = {}

# SSE event queues for each client
client_queues = {}

def background_summarize_task(task_id, content):
    """Background task that simulates content summarization"""
    try:
        # Update task status
        task_status[task_id] = "processing"
        
        # Simulate long-running summarization process
        response = ollama.chat(
            model="gemma3:4b",
            messages=[
                {"role": "system", "content": '''You will be given a text content of a website by the user. summarize the text  into  a shorter form such that summary can be used later as context to firther improve the content.ruturn only the summary without any additional text or explanation. The summary should be concise and capture the main points of the content.'''},
                {"role": "user", "content": f"{content}"}
            ]
        )  # Replace with your actual summarization logic
        
        # Simulate summary result
        # summary = f"Summary of content: {content[:100]}... (This is a mock summary)"
        summary = response["message"]["content"]
        print("Summarized")
        # Store the result
        task_results[task_id] = {
            'summary': summary,
            'status': 'completed',
            'timestamp': time.time()
        }
        task_status[task_id] = "completed"
        
        # Send SSE event to client
        if task_id in client_queues:
            client_queues[task_id].put({
                'event': 'summary_complete',
                'data': {
                    'summary': summary,
                    'task_id': task_id
                }
            })
            
    except Exception as e:
        task_status[task_id] = "failed"
        task_results[task_id] = {
            'error': str(e),
            'status': 'failed',
            'timestamp': time.time()
        }
        
        if task_id in client_queues:
            client_queues[task_id].put({
                'event': 'summary_error',
                'data': {
                    'error': str(e),
                    'task_id': task_id
                }
            })

@app.route('/ai-recommendation', methods=['POST'])
def get_ai_recommendation():
    """Get AI-powered recommendations for SEO optimization"""
    try:
        data = request.get_json()
        issue_type = data.get('issue_type', '')
        description = data.get('description', '')
        current_content = data.get('current_content', '')
        context = data.get('context', '')
        print(issue_type, description, current_content, context)
        # Here you would integrate with an AI service (OpenAI, Claude, etc.)
        # For now, we'll provide rule-based recommendations
        
        recommendations = generate_ai_recommendation(issue_type, description, current_content, context)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate recommendations: {str(e)}'
        })

def generate_ai_recommendation(issue_type, description, current_content, context):
    """Generate AI-powered SEO recommendations"""
    recommendations = []
    response = ollama.chat(
    model="gemma3:4b",
    messages=[
        {"role": "system", "content": f'''This is the summaryu of a website.{context}. the user have some issues with the content of the website. The user will provide the issue type and the element that needs to be fixed. You need to provide a solution for the issue based on the content of the website.Give the user the correct statement that should replace the current text . The solution should be in a single line and should not contain any code or HTML tags. The solution should be in English.'''},
        {"role": "user", "content": f"issue_type:{issue_type},issue_decription:{description},current_contetn:{current_content}"}
    ]
)
    recommendations.append(response["message"]["content"])
    return recommendations


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/task_status/<task_id>')
def get_task_status(task_id):
    """Get current status of a background task"""
    status = task_status.get(task_id, 'not_found')
    result = task_results.get(task_id, {})
    
    return jsonify({
        'task_id': task_id,
        'status': status,
        'result': result
    })

@app.route('/events/<task_id>')
def events(task_id):
    """Server-Sent Events endpoint for real-time updates"""
    def event_stream():
        # Create queue for this client
        client_queues[task_id] = Queue()
        
        try:
            while True:
                # Wait for events
                try:
                    event = client_queues[task_id].get(timeout=30)
                    yield f"event: {event['event']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                    
                    # If task is complete, break the loop
                    if event['event'] in ['summary_complete', 'summary_error']:
                        break
                        
                except:
                    # Send heartbeat
                    yield f"event: heartbeat\n"
                    yield f"data: {json.dumps({'timestamp': time.time()})}\n\n"
                    
        except GeneratorExit:
            # Client disconnected
            pass
        finally:
            # Clean up
            if task_id in client_queues:
                del client_queues[task_id]
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/scan', methods=['POST'])
def scan_url():
    """Scan a URL for SEO vulnerabilities"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'Please enter a URL'
            })
        
        # Fetch HTML content
        fetcher = URLFetcher()
        fetch_result = fetcher.fetch_url(url)
        
        if not fetch_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to fetch URL: {fetch_result["error"]}'
            })
        
        # Scan HTML content
        # Uncomment the following lines when you import your scanner
        scanner = HTMLSEOScanner()

        page_text=scanner.extract_page_content(fetch_result['html'])

        task_id = str(uuid.uuid4())
        
        # Initialize task status
        task_status[task_id] = "started"
        
        # Start background summarization task
        thread = threading.Thread(
            target=background_summarize_task, 
            args=(task_id, page_text)
        )
        thread.daemon = True
        thread.start()
        results = scanner.scan_html(fetch_result['html'], fetch_result['final_url'])

        
        
        return jsonify({
            'success': True,
            'url': fetch_result['final_url'],
            'results': results,
            'summary': {
                'total_issues': len(results['vulnerabilities']) + len(results['warnings']),
                'critical_issues': len(results['vulnerabilities']),
                'warnings': len(results['warnings']),
                'recommendations': len(results['recommendations'])
            },
            'task_id': task_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)