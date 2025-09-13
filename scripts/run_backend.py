#!/usr/bin/env python3

import uvicorn
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting M32 BI backend...")
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("Auto-reload: ON")
    print("-" * 30)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
