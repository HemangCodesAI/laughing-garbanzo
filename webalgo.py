import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os

class HTMLSEOScanner:
    def __init__(self):
        self.vulnerabilities = []
        self.warnings = []
        self.recommendations = []
    
    def scan_html(self, html_content, url=None):
        """
        Main method to scan HTML content for SEO vulnerabilities
        """
        self.vulnerabilities = []
        self.warnings = []
        self.recommendations = []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Run all checks
        self._check_title_tag(soup)
        self._check_h1_tag(soup)
        self._check_header_hierarchy(soup)
        self._check_meta_description(soup)
        self._check_image_optimization(soup)
        self._check_canonical_tags(soup)
        self._check_url_structure(url)
        
        return {
            'vulnerabilities': self.vulnerabilities,
            'warnings': self.warnings,
            'recommendations': self.recommendations
        }
    
    def _check_title_tag(self, soup):
        """Check title tag optimization"""
        title_tags = soup.find_all('title')
        
        if len(title_tags) == 0:
            self.vulnerabilities.append({
                'type': 'CRITICAL',
                'element': 'Title Tag',
                'issue': 'Missing title tag',
                'description': 'No title tag found in the HTML'
            })
        elif len(title_tags) > 1:
            self.vulnerabilities.append({
                'type': 'WARNING',
                'element': 'Title Tag',
                'issue': 'Multiple title tags',
                'description': f'Found {len(title_tags)} title tags, should have only one'
            })
        else:
            title_text = title_tags[0].get_text().strip()
            title_length = len(title_text)
            
            if title_length == 0:
                self.vulnerabilities.append({
                    'type': 'CRITICAL',
                    'element': 'Title Tag',
                    'issue': 'Empty title tag',
                    'description': 'Title tag is empty'
                })
            elif title_length < 30:
                self.warnings.append({
                    'type': 'WARNING',
                    'element': 'Title Tag',
                    'issue': 'Title too short',
                    'actual_text': title_text,
                    'description': f'Title is {title_length} characters, recommended minimum is 30'
                })
            elif title_length > 160:
                self.vulnerabilities.append({
                    'type': 'WARNING',
                    'element': 'Title Tag',
                    'issue': 'Title too long',
                    'actual_text': title_text,
                    'description': f'Title is {title_length} characters, recommended maximum is 160'
                })
            elif title_length < 150:
                self.recommendations.append({
                    'type': 'RECOMMENDATION',
                    'element': 'Title Tag',
                    'issue': 'Title could be optimized',
                    'actual_text': title_text,
                    'description': f'Title is {title_length} characters, ideal range is 150-160'
                })
    
    def _check_h1_tag(self, soup):
        """Check H1 tag optimization"""
        h1_tags = soup.find_all('h1')
        
        if len(h1_tags) == 0:
            self.vulnerabilities.append({
                'type': 'CRITICAL',
                'element': 'H1 Tag',
                'issue': 'Missing H1 tag',
                'description': 'No H1 tag found on the page'
            })
        elif len(h1_tags) > 1:
            self.vulnerabilities.append({
                'type': 'WARNING',
                'element': 'H1 Tag',
                'issue': 'Multiple H1 tags',
                'description': f'Found {len(h1_tags)} H1 tags, should have only one per page'
            })
        else:
            h1_text = h1_tags[0].get_text().strip()
            h1_length = len(h1_text)
            
            if h1_length == 0:
                self.vulnerabilities.append({
                    'type': 'CRITICAL',
                    'element': 'H1 Tag',
                    'issue': 'Empty H1 tag',
                    'description': 'H1 tag is empty'
                })
            elif h1_length < 20:
                self.warnings.append({
                    'type': 'WARNING',
                    'element': 'H1 Tag',
                    'issue': 'H1 too short',
                    'actual_text': h1_text,
                    'description': f'H1 is {h1_length} characters, recommended minimum is 20'
                })
            elif h1_length > 70:
                self.warnings.append({
                    'type': 'WARNING',
                    'element': 'H1 Tag',
                    'issue': 'H1 too long',
                    'actual_text': h1_text,
                    'description': f'H1 is {h1_length} characters, recommended maximum is 70'
                })
    
    def _check_header_hierarchy(self, soup):
        """Check header tag hierarchy (H2-H6)"""
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if len(headers) <= 1:
            self.recommendations.append({
                'type': 'RECOMMENDATION',
                'element': 'Header Hierarchy',
                'issue': 'Limited header structure',
                'description': 'Consider using H2-H6 tags to create a logical content hierarchy'
            })
            return
        
        # Check for proper hierarchy
        prev_level = 0
        hierarchy_issues = []
        
        for header in headers:
            current_level = int(header.name[1])
            
            if prev_level > 0 and current_level > prev_level + 1:
                hierarchy_issues.append(f'Header hierarchy jumps from H{prev_level} to H{current_level}')
            
            # Check for empty headers
            if not header.get_text().strip():
                self.vulnerabilities.append({
                    'type': 'WARNING',
                    'element': f'H{current_level} Tag',
                    'issue': f'Empty H{current_level} tag',
                    'description': f'Found empty H{current_level} tag'
                })
            
            prev_level = current_level
        
        for issue in hierarchy_issues:
            self.warnings.append({
                'type': 'WARNING',
                'element': 'Header Hierarchy',
                'issue': 'Header hierarchy skip',
                'description': issue
            })
    
    def _check_meta_description(self, soup):
        """Check meta description optimization"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        
        if not meta_desc:
            self.vulnerabilities.append({
                'type': 'CRITICAL',
                'element': 'Meta Description',
                'issue': 'Missing meta description',
                'description': 'No meta description tag found'
            })
        else:
            content = meta_desc.get('content', '').strip()
            desc_length = len(content)
            
            if desc_length == 0:
                self.vulnerabilities.append({
                    'type': 'CRITICAL',
                    'element': 'Meta Description',
                    'issue': 'Empty meta description',
                    'description': 'Meta description is empty'
                })
            elif desc_length < 120:
                self.warnings.append({
                    'type': 'WARNING',
                    'element': 'Meta Description',
                    'issue': 'Meta description too short',
                    'actual_text': content,
                    'description': f'Meta description is {desc_length} characters, recommended minimum is 120'
                })
            elif desc_length > 160:
                self.vulnerabilities.append({
                    'type': 'WARNING',
                    'element': 'Meta Description',
                    'issue': 'Meta description too long',
                    'actual_text': content,
                    'description': f'Meta description is {desc_length} characters, recommended maximum is 160'
                })
    
    def _check_image_optimization(self, soup):
        """Check image optimization"""
        images = soup.find_all('img')
        
        if not images:
            return
        
        images_without_alt = 0
        images_with_empty_alt = 0
        images_with_long_alt = 0
        
        for img in images:
            alt_text = img.get('alt')
            src = img.get('src', '')
            
            if alt_text is None:
                images_without_alt += 1
            elif alt_text.strip() == '':
                images_with_empty_alt += 1
            else:
                alt_length = len(alt_text)
                if alt_length > 125:
                    images_with_long_alt += 1
                elif alt_length < 80:
                    self.recommendations.append({
                        'type': 'RECOMMENDATION',
                        'element': 'Image ALT',
                        'issue': 'ALT text could be longer',
                        'actual_text': alt_text,
                        'description': f'Image ALT text is {alt_length} characters, ideal range is 80-125'
                    })
            
            # Check for descriptive file names
            if src:
                filename = os.path.basename(src).lower()
                if re.match(r'^(img|image|photo|pic)\d*\.(jpg|jpeg|png|gif|webp)$', filename):
                    self.recommendations.append({
                        'type': 'RECOMMENDATION',
                        'element': 'Image Filename',
                        'issue': 'Non-descriptive image filename',
                        'description': f'Consider using descriptive filename instead of "{filename}"'
                    })
        
        if images_without_alt > 0:
            self.vulnerabilities.append({
                'type': 'WARNING',
                'element': 'Image ALT',
                'issue': 'Missing ALT attributes',
                'description': f'{images_without_alt} images missing ALT attributes'
            })
        
        if images_with_empty_alt > 0:
            self.warnings.append({
                'type': 'WARNING',
                'element': 'Image ALT',
                'issue': 'Empty ALT attributes',
                'description': f'{images_with_empty_alt} images have empty ALT attributes'
            })
        
        if images_with_long_alt > 0:
            self.warnings.append({
                'type': 'WARNING',
                'element': 'Image ALT',
                'issue': 'ALT text too long',
                'actual_text': alt_text,
                'description': f'{images_with_long_alt} images have ALT text longer than 125 characters'
            })
    
    def _check_canonical_tags(self, soup):
        """Check canonical tag implementation"""
        canonical_tags = soup.find_all('link', rel='canonical')
        
        if len(canonical_tags) == 0:
            self.vulnerabilities.append({
                'type': 'WARNING',
                'element': 'Canonical Tag',
                'issue': 'Missing canonical tag',
                'description': 'No canonical tag found, could lead to duplicate content issues'
            })
        elif len(canonical_tags) > 1:
            self.vulnerabilities.append({
                'type': 'WARNING',
                'element': 'Canonical Tag',
                'issue': 'Multiple canonical tags',
                'description': f'Found {len(canonical_tags)} canonical tags, should have only one'
            })
        else:
            canonical_url = canonical_tags[0].get('href', '').strip()
            if not canonical_url:
                self.vulnerabilities.append({
                    'type': 'WARNING',
                    'element': 'Canonical Tag',
                    'issue': 'Empty canonical URL',
                    'description': 'Canonical tag has empty href attribute'
                })
    
    def _check_url_structure(self, url):
        """Check URL structure optimization"""
        if not url:
            return
        
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        if not path or path == '/':
            return
        
        # Check for underscores
        if '_' in path:
            self.warnings.append({
                'type': 'WARNING',
                'element': 'URL Structure',
                'issue': 'Underscores in URL',
                'description': 'URL contains underscores, hyphens are preferred for SEO'
            })
        
        # Check URL length
        if len(path) > 100:
            self.warnings.append({
                'type': 'WARNING',
                'element': 'URL Structure',
                'issue': 'URL too long',
                'description': f'URL path is {len(path)} characters, consider shortening'
            })
        
        # Check for non-descriptive URLs
        if re.search(r'/(id|page|post|article)=?\d+', path):
            self.recommendations.append({
                'type': 'RECOMMENDATION',
                'element': 'URL Structure',
                'issue': 'Non-descriptive URL',
                'description': 'URL appears to use IDs instead of descriptive keywords'
            })
    
    def generate_report(self, results):
        """Generate a formatted report"""
        report = []
        report.append("=" * 60)
        report.append("HTML SEO VULNERABILITY SCAN REPORT")
        report.append("=" * 60)
        
        if results['vulnerabilities']:
            report.append("\n🚨 CRITICAL ISSUES:")
            for vuln in results['vulnerabilities']:
                report.append(f"  • {vuln['element']}: {vuln['issue']}")
                report.append(f"    {vuln['description']}")
        
        if results['warnings']:
            report.append("\n⚠️  WARNINGS:")
            for warn in results['warnings']:
                report.append(f"  • {warn['element']}: {warn['issue']}")
                report.append(f"    {warn['description']}")
        
        if results['recommendations']:
            report.append("\n💡 RECOMMENDATIONS:")
            for rec in results['recommendations']:
                report.append(f"  • {rec['element']}: {rec['issue']}")
                report.append(f"    {rec['description']}")
        
        if not results['vulnerabilities'] and not results['warnings'] and not results['recommendations']:
            report.append("\n✅ No SEO issues found!")
        
        return "\n".join(report)

    def extract_page_content(self, html_content):
        """
        Extract clean text content from HTML by removing all tags, links, styles, and scripts
        Returns a dictionary with various content extractions
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements completely
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Remove comments
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Extract different types of content
        content_data = {
            'title': self._extract_title(soup),
            'meta_description': self._extract_meta_description(soup),
            # 'headings': self._extract_headings(soup),
            'body_text': self._extract_body_text(soup)
        }
        return content_data
    
    def _extract_title(self, soup):
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ''
    
    def _extract_meta_description(self, soup):
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '').strip() if meta_desc else ''
    
    def _extract_body_text(self, soup):
        """Extract clean body text without HTML tags"""
        # Remove navigation, footer, sidebar, and other non-content elements
        for element in soup.find_all(['nav', 'footer', 'aside', 'header']):
            element.decompose()
        
        # Remove elements with common non-content class names
        non_content_classes = [
            'navigation', 'nav', 'menu', 'sidebar', 'footer', 'header',
            'advertisement', 'ads', 'social', 'share', 'comments'
        ]
        
        for class_name in non_content_classes:
            for element in soup.find_all(class_=lambda x: x and any(nc in ' '.join(x).lower() for nc in non_content_classes)):
                element.decompose()
        
        # Get text from body or entire document if body not found
        body = soup.find('body') or soup
        
        # Extract text and clean it up
        text = body.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
        text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with single newline
        
        return text
    
# Example usage
def scan_html_file(file_path, url=None):
    """Scan an HTML file for SEO vulnerabilities"""
    scanner = HTMLSEOScanner()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        results = scanner.scan_html(html_content, url)
        report = scanner.generate_report(results)
        
        return results, report
    
    except FileNotFoundError:
        return None, f"Error: File '{file_path}' not found"
    except Exception as e:
        return None, f"Error: {str(e)}"

def scan_html_string(html_string, url=None):
    """Scan HTML string for SEO vulnerabilities"""
    scanner = HTMLSEOScanner()
    results = scanner.scan_html(html_string, url)
    report = scanner.generate_report(results)
    
    return results, report

# Example usage:
if __name__ == "__main__":
    # Example HTML content
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Page</title>
        <meta name="description" content="This is a sample page for testing.">
        <link rel="canonical" href="https://example.com/sample-page">
    </head>
    <body>
        <h1>Welcome to Our Sample Page</h1>
        <h2>About Us</h2>
        <img src="image1.jpg" alt="Beautiful landscape">
        <img src="photo2.png">
        <h3>Our Services</h3>
        <p>Content goes here...</p>
    </body>
    </html>
    """
    
    # Scan the HTML
    results, report = scan_html_string(sample_html, "https://example.com/sample_page")
    print(report)