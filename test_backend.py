import requests
import sys

# Test health endpoint
try:
    response = requests.get('http://localhost:5000/api/health')
    if response.status_code == 200:
        data = response.json()
        print("✅ Backend is running!")
        print(f"📂 Categories: {data['categories']}")
    else:
        print("❌ Backend returned error")
except:
    print("❌ Cannot connect to backend. Make sure it's running on port 5000")
    print("   Run: python backend/app.py")
    sys.exit(1)

# Test with a sample image (if you provide one)
if len(sys.argv) > 1:
    image_path = sys.argv[1]
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://localhost:5000/api/test-image', files=files)
            
        if response.status_code == 200:
            result = response.json()
            print(f"\n🎯 Prediction: {result['prediction']}")
            print(f"📊 Confidence: {result['confidence']}%")
            print("\n📈 Top predictions:")
            for pred in result['top_predictions']:
                print(f"   {pred['class']}: {pred['confidence']}%")
        else:
            print(f"\n❌ Prediction failed: {response.json()}")
    except Exception as e:
        print(f"\n❌ Error testing image: {e}")