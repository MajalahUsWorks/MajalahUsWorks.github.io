#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path
from datetime import datetime

def parse_post(content, filename):
    """Parse a blog post file with the custom markup format."""
    post = {
        'path': f'posts/{filename}',
        'title': '',
        'thumbnail': '',
        'content': '',
        'date': '',
        'category': ''
    }
    
    lines = content.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        # Check for section headers (not escaped with \)
        # Match [SectionName] but not \[SectionName]
        section_match = re.match(r'^(?<!\\)\[(\w+)\]$', line)
        
        if section_match:
            # Save previous section
            if current_section and section_content:
                post[current_section.lower()] = '\n'.join(section_content).strip()
            
            current_section = section_match.group(1)
            section_content = []
        elif current_section:
            # Unescape \[ to [
            unescaped_line = line.replace(r'\[', '[')
            section_content.append(unescaped_line)
    
    # Save last section
    if current_section and section_content:
        post[current_section.lower()] = '\n'.join(section_content).strip()
    
    # Generate excerpt (first 150 chars, strip image tags)
    content_without_images = re.sub(r'<img\s+"[^"]*">', '', post['content'])
    post['excerpt'] = content_without_images[:150].strip()
    post['excerpt'] = re.sub(r'<[^>]*>', '', post['excerpt'])
    if len(content_without_images) > 150:
        post['excerpt'] += '...'
    
    # Validate required fields
    if not post['title'] or not post['date'] or not post['category']:
        raise ValueError(f"Missing required fields in {filename}")
    
    return post

def generate_indexes(posts):
    """Generate chrono.json and catalog.json from parsed posts."""
    # Sort by date (newest first)
    sorted_posts = sorted(posts, key=lambda p: datetime.strptime(p['date'], '%m/%d/%Y'), reverse=True)
    
    # Generate chrono.json
    chrono_map = {}
    for post in sorted_posts:
        date = post['date']
        if date not in chrono_map:
            chrono_map[date] = []
        chrono_map[date].append({
            'path': post['path'],
            'title': post['title'],
            'excerpt': post['excerpt'],
            'thumbnail': post['thumbnail'],
            'category': post['category']
        })
    
    chrono = [{'date': date, 'posts': posts} for date, posts in chrono_map.items()]
    
    # Generate catalog.json
    catalog = {}
    for post in sorted_posts:
        category = post['category']
        if category not in catalog:
            catalog[category] = []
        catalog[category].append({
            'path': post['path'],
            'title': post['title'],
            'excerpt': post['excerpt'],
            'thumbnail': post['thumbnail'],
            'date': post['date']
        })
    
    return chrono, catalog

def main():
    """Main indexer function."""
    # Configuration
    posts_dir = Path('posts')
    output_dir = Path('.')
    
    if not posts_dir.exists():
        print(f"Error: '{posts_dir}' directory not found!")
        print("Please create a 'posts' directory and add your .txt files there.")
        return
    
    # Find all .txt files
    post_files = list(posts_dir.glob('*.txt'))
    
    if not post_files:
        print(f"No .txt files found in '{posts_dir}' directory!")
        return
    
    print(f"Found {len(post_files)} post file(s)")
    print("-" * 50)
    
    posts = []
    
    # Parse each post
    for post_file in post_files:
        try:
            print(f"Parsing {post_file.name}...")
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            post = parse_post(content, post_file.name)
            posts.append(post)
            print(f"  ✓ '{post['title']}'")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    if not posts:
        print("\nNo posts were successfully parsed!")
        return
    
    print("-" * 50)
    print("Generating indexes...")
    
    # Generate indexes
    chrono, catalog = generate_indexes(posts)
    
    # Write chrono.json
    chrono_file = output_dir / 'chrono.json'
    with open(chrono_file, 'w', encoding='utf-8') as f:
        json.dump(chrono, f, indent=2, ensure_ascii=False)
    print(f"✓ Created {chrono_file} ({len(chrono)} date(s))")
    
    # Write catalog.json
    catalog_file = output_dir / 'catalog.json'
    with open(catalog_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"✓ Created {catalog_file} ({len(catalog)} categor(ies))")
    
    print("-" * 50)
    print("Done!")


if __name__ == '__main__':
    main()
