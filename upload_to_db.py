import os
import sys
from pymongo import MongoClient, UpdateOne
from datetime import datetime, UTC

def connect_to_mongodb(connection_string, repo_name):
    try:
        print(f"Connecting to MongoDB with string length: {len(connection_string)}")
        # Add retry logic and timeout settings
        client = MongoClient(connection_string, 
                           serverSelectionTimeoutMS=5000,
                           connectTimeoutMS=5000)
        # Force a connection to verify it works
        client.server_info()
        db = client[repo_name]
        
        # Check if collection exists, create if it doesn't
        if 'images' not in db.list_collection_names():
            db.create_collection('images')
            print(f"Created new 'images' collection in database {repo_name}")
        else:
            print(f"Using existing 'images' collection in database {repo_name}")
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
        print(f"Found {len(image_files)} images in {folder_path}")
        
        # Prepare bulk operations
        operations = []
        for image_file in image_files:
            image_code = image_file.replace('.jpg', '')  # s88248
            image_number = int(image_code[1:])  # 88248
            
            image_url = f"{base_url}/{folder_path}/{image_file}"
            
            # Check if document exists with same code but different URL
            existing_doc = collection.find_one({'code': image_code})
            
            # Skip if document exists with same code and URL
            if existing_doc and existing_doc.get('url') == image_url:
                print(f"Skipping {image_code}: Already exists with same URL")
                continue
                
            # Prepare document with timezone-aware timestamps
            current_time = datetime.now(UTC)
            doc = {
                'code': image_code,
                'number': image_number,
                'url': image_url,
                'folder': folder_path,
                'created_at': current_time,
                'updated_at': current_time
            }
            
            # Add created_at only for new documents
            if not existing_doc:
                doc['created_at'] = current_time
            
            # Prepare upsert operation
            operations.append(
                UpdateOne(
                    {'code': image_code},
                    {'$set': doc},
                    upsert=True
                )
            )
        
        if operations:
            # Execute bulk write
            result = collection.bulk_write(operations)
            print(f"Processed {len(operations)} images: {result.upserted_count} inserted, {result.modified_count} modified")
        else:
            print("No new or updated images to process")
            
    except Exception as e:
        print(f"Error processing images: {e}")
        return False
    
    return True

def main(folder_path):
    """Main function that can be called directly or through __main__"""
    # Debug environment variables
    print("\nEnvironment variables:")
    for key, value in os.environ.items():
        if 'URL' in key or 'MONGO' in key:
            print(f"{key}: {'*' * (len(value) if value else 0)}")  # Hide actual value for security
    
    # Get required environment variables
    mongodb_url = os.environ.get('MONGODB_URL')
    repo_owner = os.environ.get('REPO_OWNER')
    repo_name = os.environ.get('REPO_NAME')
    
    if not mongodb_url:
        print("\nError: MongoDB URL not found in environment variables")
        print("Available environment variables:", sorted(list(os.environ.keys())))
        return False
    
    print("\nAttempting to connect to MongoDB...")
    collection = connect_to_mongodb(mongodb_url, repo_name)
    if collection is None:
        return False
    
    print(f"\nProcessing images from folder: {folder_path}")
    success = process_images(
        folder_path, 
        collection,
        repo_owner=repo_owner,
        repo_name=repo_name
    )
    
    return success

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_to_db.py <folder_path>")
        sys.exit(1)
        
    folder_path = sys.argv[1]
    success = main(folder_path)
    if not success:
        sys.exit(1) 