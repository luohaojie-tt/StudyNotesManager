"""Simple test runner to bypass uv issues."""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try importing the modules to verify they're syntactically correct
try:
    from app.models.note import Note
    print("OK - Note model imported successfully")
    
    from app.api.notes import router
    print("OK - Notes API router imported successfully")
    
    from app.schemas.note import NoteResponse, NoteUploadResponse, OCRResponse
    print("OK - Note schemas imported successfully")
    
    from app.services.note_service import NoteService
    print("OK - NoteService imported successfully")
    
    # Check Note model has required fields
    import inspect
    note_attrs = Note.__table__.columns.keys()
    print(f"\nOK - Note model has {len(note_attrs)} fields")
    
    if 'is_favorited' in note_attrs:
        print("OK - is_favorited field exists")
    else:
        print("ERROR - is_favorited field missing")
        sys.exit(1)
        
    if 'tags' in note_attrs:
        print("OK - tags field exists")
    else:
        print("ERROR - tags field missing")
        sys.exit(1)
        
    if 'meta_data' in note_attrs:
        print("OK - meta_data field exists")
    else:
        print("ERROR - meta_data field missing")
        sys.exit(1)
    
    # Check API routes
    routes = [route.path for route in router.routes]
    print(f"\nOK - API has {len(routes)} routes")
    
    if '/api/notes/upload' in routes:
        print("OK - /upload endpoint exists")
    else:
        print("ERROR - /upload endpoint missing")
        sys.exit(1)
        
    if '/api/notes/ocr' in routes:
        print("OK - /ocr endpoint exists")
    else:
        print("ERROR - /ocr endpoint missing")
        sys.exit(1)
    
    print("\nSUCCESS - All imports successful! Code is syntactically correct.")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
