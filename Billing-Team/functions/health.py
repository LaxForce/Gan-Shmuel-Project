def check_health():
    try:
        # Check database or other dependencies
        return {"status": "OK"}, 200
    except Exception:
        return {"status": "Failure"}, 500
