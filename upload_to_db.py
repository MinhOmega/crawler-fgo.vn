import os
import sys
from pymongo import MongoClient
from datetime import datetime

def connect_to_mongodb(connection_string):
    try:
        # Add retry logic and timeout settings
        client = MongoClient(connection_string, 
                           serverSelectionTimeoutMS=5000,
                           connectTimeoutMS=5000)
        # Force a connection to verify it works
        client.server_info()
        db = client['fgo_database']
        print("Successfully connected to MongoDB")
        return db.images
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return None

def process_images(folder_path, collection, repo_owner, repo_name, branch='main'):
    base_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}"
    
    try:
        # Get all jpg files in the folder
        image_files = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]
        
        # Prepare bulk operations
        operations = []
        for image_file in image_files:
            image_code = image_file.replace('.jpg', '')  # s88248
            image_number = int(image_code[1:])  # 88248
            
            image_url = f"{base_url}/{folder_path}/{image_file}"
            
            # Prepare document
            doc = {
                'code': image_code,
                'number': image_number,
                'url': image_url,
                'folder': folder_path,
                'created_at': datetime.utcnow()
            }
            
            # Prepare upsert operation
            operations.append(
                {
                    'replaceOne': {
                        'filter': {'code': image_code},
                        'replacement': doc,
                        'upsert': True
                    }
                }
            )
        
        if operations:
            # Execute bulk write
            result = collection.bulk_write(operations)
            print(f"Processed {len(operations)} images: {result.upserted_count} inserted, {result.modified_count} modified")
        else:
            print("No images found to process")
            
    except Exception as e:
        print(f"Error processing images: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_to_db.py <folder_path>")
        sys.exit(1)
        
    folder_path = sys.argv[1]
    
    # Try different environment variable names
    mongodb_url = os.environ.get('MONGODB_URL') or os.environ.get('MONGO_URL')
    
    if not mongodb_url:
        print("Error: MongoDB URL not found in environment variables")
        print("Available environment variables:", list(os.environ.keys()))
        sys.exit(1)
    
    print("Attempting to connect to MongoDB...")
    collection = connect_to_mongodb(mongodb_url)
    if not collection:
        sys.exit(1)
    
    print(f"Processing images from folder: {folder_path}")
    success = process_images(
        folder_path, 
        collection,
        repo_owner="MinhOmega",
        repo_name="crawler-fgo.vn"
    )
    
    if not success:
        sys.exit(1) 