# chunking_analysis.py
import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

def analyze_chunking_process(folder_path="patent_jsons", chunk_size=2500, chunk_overlap=150):
    """
    Detailed analysis of why 500 files produced only 487 chunks
    """
    
    print("🔍 CHUNKING ANALYSIS - Why 500 files = 487 chunks?")
    print("=" * 80)
    
    # Initialize text splitter (same as in your data_loader.py)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
    
    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    
    total_files = 0
    total_chunks = 0
    files_with_no_chunks = []
    files_with_multiple_chunks = []
    chunk_distribution = {}
    content_length_analysis = []
    
    for file_idx, file_name in enumerate(json_files):
        file_path = os.path.join(folder_path, file_name)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                patent = json.load(f)
            
            total_files += 1
            
            # Extract data (same logic as your data_loader.py)
            patent_number = patent.get("patent_number", f"patent_{file_idx}")
            
            # Extract English fields
            abstract = extract_english_field(patent.get("abstracts", []), "paragraph_markup")
            
            claims_data = patent.get("claims", [{}])[0].get("claims", [])
            claims_text = " ".join(
                [c.get("paragraph_markup", "") for c in claims_data if c.get("lang") == "EN"]
            )
            
            combined_text = f"{abstract} {claims_text}".strip()
            
            if not combined_text:
                files_with_no_chunks.append({
                    'file': file_name,
                    'patent': patent_number,
                    'reason': 'Empty content after combining abstract + claims'
                })
                continue
            
            # Split into chunks (same as your logic)
            chunks = splitter.split_text(combined_text)
            chunk_count = len(chunks)
            total_chunks += chunk_count
            
            # Track chunk distribution
            if chunk_count in chunk_distribution:
                chunk_distribution[chunk_count] += 1
            else:
                chunk_distribution[chunk_count] = 1
            
            # Store content analysis
            content_length_analysis.append({
                'file': file_name,
                'patent': patent_number,
                'content_length': len(combined_text),
                'chunks_created': chunk_count,
                'abstract_length': len(abstract) if abstract else 0,
                'claims_length': len(claims_text) if claims_text else 0
            })
            
            # Track files with multiple chunks
            if chunk_count > 1:
                files_with_multiple_chunks.append({
                    'file': file_name,
                    'patent': patent_number,
                    'chunks': chunk_count,
                    'content_length': len(combined_text)
                })
                
        except Exception as e:
            print(f"❌ Error processing {file_name}: {e}")
            continue
    
    # Analysis Results
    print(f"📊 CHUNKING RESULTS:")
    print("-" * 50)
    print(f"Files processed: {total_files}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Files with no chunks: {len(files_with_no_chunks)}")
    print(f"Files with multiple chunks: {len(files_with_multiple_chunks)}")
    print(f"Expected result: {total_files} files should create at least {total_files} chunks")
    print(f"Actual result: {total_chunks} chunks created")
    print(f"Difference: {total_files - total_chunks} chunks missing!")
    
    # Chunk Distribution
    print(f"\n📈 CHUNK DISTRIBUTION:")
    print("-" * 30)
    for chunk_count in sorted(chunk_distribution.keys()):
        files_count = chunk_distribution[chunk_count]
        print(f"{chunk_count} chunk(s): {files_count} files")
    
    # Show files with no chunks
    if files_with_no_chunks:
        print(f"\n⚠️  FILES WITH NO CHUNKS ({len(files_with_no_chunks)}):")
        print("-" * 50)
        for idx, file_info in enumerate(files_with_no_chunks, 1):
            print(f"{idx}. {file_info['file']}")
            print(f"   Patent: {file_info['patent']}")
            print(f"   Reason: {file_info['reason']}")
    
    # Show files with multiple chunks (top 10)
    if files_with_multiple_chunks:
        files_with_multiple_chunks.sort(key=lambda x: x['chunks'], reverse=True)
        print(f"\n🔥 FILES WITH MOST CHUNKS (Top 10):")
        print("-" * 50)
        for idx, file_info in enumerate(files_with_multiple_chunks[:10], 1):
            print(f"{idx:2d}. {file_info['file']}")
            print(f"    Patent: {file_info['patent']}")
            print(f"    Chunks: {file_info['chunks']}")
            print(f"    Content Length: {file_info['content_length']:,} chars")
    
    # Content Length Analysis
    content_length_analysis.sort(key=lambda x: x['content_length'])
    
    print(f"\n📏 CONTENT LENGTH ANALYSIS:")
    print("-" * 40)
    print(f"Shortest content: {content_length_analysis[0]['content_length']:,} chars")
    print(f"Longest content: {content_length_analysis[-1]['content_length']:,} chars")
    
    # Find very short files that might not create chunks
    very_short_files = [f for f in content_length_analysis if f['content_length'] < chunk_size]
    if very_short_files:
        print(f"\nFiles with content < {chunk_size} chars: {len(very_short_files)}")
    
    # Check for zero chunk files  
    zero_chunk_files = [f for f in content_length_analysis if f['chunks_created'] == 0]
    if zero_chunk_files:
        print(f"\n🚨 FILES THAT SHOULD HAVE CHUNKS BUT DON'T:")
        for file_info in zero_chunk_files:
            print(f"  {file_info['file']}: {file_info['content_length']} chars, 0 chunks")
    
    # The mystery solver
    print(f"\n🕵️ MYSTERY SOLVER:")
    print("=" * 40)
    if total_chunks < total_files:
        missing_chunks = total_files - total_chunks
        print(f"❗ Missing {missing_chunks} chunks!")
        print("Possible reasons:")
        print("1. Some files have empty combined_text after processing")
        print("2. Some files failed during chunk creation")  
        print("3. Text splitter returned empty chunks")
        
        # Check if any files create 0 chunks despite having content
        zero_chunk_with_content = []
        for item in content_length_analysis:
            if item['chunks_created'] == 0 and item['content_length'] > 0:
                zero_chunk_with_content.append(item)
        
        if zero_chunk_with_content:
            print(f"\n🔍 FOUND THE ISSUE! Files with content but 0 chunks:")
            for item in zero_chunk_with_content:
                print(f"  {item['file']}: {item['content_length']} chars → 0 chunks")
    
    return {
        'total_files': total_files,
        'total_chunks': total_chunks,
        'chunk_distribution': chunk_distribution,
        'files_with_no_chunks': files_with_no_chunks,
        'mystery_files': zero_chunk_with_content if 'zero_chunk_with_content' in locals() else []
    }

def extract_english_field(entries, field_name):
    """Extract English version of a specific field."""
    for entry in entries:
        if entry.get("lang") == "EN":
            return entry.get(field_name, "")
    return ""

def debug_specific_file(file_name, folder_path="patent_jsons"):
    """Debug a specific file's chunking process"""
    
    print(f"\n🔬 DEBUGGING FILE: {file_name}")
    print("=" * 60)
    
    file_path = os.path.join(folder_path, file_name)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            patent = json.load(f)
        
        patent_number = patent.get("patent_number", "UNKNOWN")
        
        # Check abstracts
        abstracts = patent.get("abstracts", [])
        print(f"Abstracts found: {len(abstracts)}")
        for i, abs_item in enumerate(abstracts):
            print(f"  {i+1}. Lang: {abs_item.get('lang')}, Length: {len(abs_item.get('paragraph_markup', ''))}")
        
        # Check claims 
        claims_data = patent.get("claims", [])
        print(f"Claims data structure: {type(claims_data)}")
        if claims_data and isinstance(claims_data, list):
            claims_list = claims_data[0].get("claims", [])
            print(f"Claims found: {len(claims_list)}")
            en_claims = [c for c in claims_list if c.get("lang") == "EN"]
            print(f"English claims: {len(en_claims)}")
        
        # Process text
        abstract = extract_english_field(patent.get("abstracts", []), "paragraph_markup")
        claims_data = patent.get("claims", [{}])[0].get("claims", [])
        claims_text = " ".join(
            [c.get("paragraph_markup", "") for c in claims_data if c.get("lang") == "EN"]
        )
        
        combined_text = f"{abstract} {claims_text}".strip()
        
        print(f"\nProcessed Text:")
        print(f"  Abstract length: {len(abstract)}")
        print(f"  Claims length: {len(claims_text)}")
        print(f"  Combined length: {len(combined_text)}")
        print(f"  Combined preview: {combined_text[:200]}...")
        
        # Test chunking
        splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=150)
        chunks = splitter.split_text(combined_text) if combined_text else []
        
        print(f"  Chunks created: {len(chunks)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    results = analyze_chunking_process()
    
    # If you want to debug a specific problematic file:
    # debug_specific_file("US-6654854-B1.json")  # Replace with actual filename
    
    print("\n✨ Chunking Analysis Complete!")