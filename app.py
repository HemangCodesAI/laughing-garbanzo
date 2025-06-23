from flask import Flask, render_template, request, jsonify, flash
import requests
from urllib.parse import urlparse
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from webalgo import HTMLSEOScanner

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

@app.route('/')
def index():
    return render_template('index.html')

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
        results = scanner.scan_html(fetch_result['html'], fetch_result['final_url'])
        report = scanner.generate_report(results)

        # Mock results for demonstration (remove when using actual scanner)
        # results = {
        #     'vulnerabilities': [
        #         {
        #             'type': 'CRITICAL',
        #             'element': 'Title Tag',
        #             'issue': 'Title too long',
        #             'description': 'Title is 165 characters, recommended maximum is 160'
        #         }
        #     ],
        #     'warnings': [
        #         {
        #             'type': 'WARNING',
        #             'element': 'Image ALT',
        #             'issue': 'Missing ALT attributes',
        #             'description': '3 images missing ALT attributes'
        #         }
        #     ],
        #     'recommendations': [
        #         {
        #             'type': 'RECOMMENDATION',
        #             'element': 'URL Structure',
        #             'issue': 'Non-descriptive URL',
        #             'description': 'URL appears to use IDs instead of descriptive keywords'
        #         }
        #     ]
        # }
        
        return jsonify({
            'success': True,
            'url': fetch_result['final_url'],
            'results': results,
            'summary': {
                'total_issues': len(results['vulnerabilities']) + len(results['warnings']),
                'critical_issues': len(results['vulnerabilities']),
                'warnings': len(results['warnings']),
                'recommendations': len(results['recommendations'])
            }
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