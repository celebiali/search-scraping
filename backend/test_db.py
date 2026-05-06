
from models import SessionLocal, TrackedProduct, init_db

def test():
    print("Initializing DB...")
    init_db()
    db = SessionLocal()
    try:
        print("Adding a test product...")
        product = TrackedProduct(query="Test Product", category="elektronik")
        db.add(product)
        db.commit()
        print("Success! Product ID:", product.id)
    except Exception as e:
        print("Error:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test()
