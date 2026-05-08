"""Comprehensive test suite for ATS Resume app."""
import os
import sys
import tempfile

def test(name, fn):
    try:
        fn()
        print(f"✅ {name}")
        return True
    except AssertionError as e:
        print(f"❌ {name}: {e}")
        return False
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}: {e}")
        return False

results = []

# Test 1: All Python files compile
def test_compile():
    import py_compile
    files = [
        "dashboard.py", "ai_client.py", "ats_scorer.py", "job_parser.py",
        "resume_parser.py", "resume_optimizer.py", "cover_letter_generator.py",
        "interview_prep.py", "database.py", "error_handler.py"
    ]
    for f in files:
        if os.path.exists(f):
            py_compile.compile(f, doraise=True)
results.append(test("All files compile", test_compile))

# Test 2: All imports work
def test_imports():
    import dashboard, ai_client, ats_scorer, job_parser
    import resume_parser, resume_optimizer, cover_letter_generator
    import interview_prep, database, error_handler
results.append(test("All imports work", test_imports))

# Test 3: ATSScorer returns expected keys
def test_ats():
    from ats_scorer import ATSScorer
    result = ATSScorer("python developer with aws experience", "looking for python aws engineer").score()
    assert "overall" in result
    assert "keywords" in result
    assert isinstance(result["overall"], int)
    assert 0 <= result["overall"] <= 100
results.append(test("ATSScorer works", test_ats))

# Test 4: ATSScorer handles empty input
def test_ats_empty():
    from ats_scorer import ATSScorer
    result = ATSScorer("", "").score()
    assert "overall" in result
results.append(test("ATSScorer handles empty input", test_ats_empty))

# Test 5: JobParser works
def test_job():
    from job_parser import JobParser
    result = JobParser("Senior Python Developer at TechCorp").parse()
    assert "job_title" in result
    assert "required_skills" in result
results.append(test("JobParser works", test_job))

# Test 6: ResumeParser handles missing file
def test_resume_missing():
    from resume_parser import ResumeParser
    result = ResumeParser("/nonexistent/file.pdf").parse()
    assert "error" in result
results.append(test("ResumeParser handles missing file", test_resume_missing))

# Test 7: AI client handles no key
def test_ai_no_key():
    from ai_client import call_ai
    result = call_ai("test", None, None)
    assert "error" in result
results.append(test("AI client errors gracefully without key", test_ai_no_key))

# Test 8: AI client provider detection
def test_provider_detection():
    from ai_client import detect_provider
    assert "Gemini" in detect_provider("AIzaSyTest123")
    assert "YepAPI" in detect_provider("yep_test")
    assert "Anthropic" in detect_provider("sk-ant-test")
    assert "OpenAI" in detect_provider("sk-test")
    assert detect_provider("") == "None"
results.append(test("Provider detection works", test_provider_detection))

# Test 9: Database initialization
def test_db():
    from database import init_db, get_session, ApplicationRecord
    init_db()
    session = get_session()
    count = session.query(ApplicationRecord).count()
    session.close()
    assert isinstance(count, int)
results.append(test("Database works", test_db))

# Test 10: has_any_key function
def test_has_key():
    from ai_client import has_any_key
    assert has_any_key("yep_test", None) == True
    assert has_any_key(None, "AIzaTest") == True
    assert has_any_key(None, None) == False
    assert has_any_key("", "") == False
    assert has_any_key("  ", "  ") == False
results.append(test("has_any_key works", test_has_key))

# Test 11: Error handler
def test_error_handler():
    from error_handler import handle_error
    try:
        raise ValueError("test error")
    except Exception as e:
        result = handle_error(e, "test context")
        assert "error" in result
        assert "suggestion" in result
results.append(test("Error handler works", test_error_handler))

# Test 12: Streamlit can import dashboard without errors
def test_streamlit_dryrun():
    import subprocess
    # Use -m streamlit to ensure environment is set up
    proc = subprocess.run(
        [sys.executable, "-c", "import streamlit; import dashboard"],
        capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 0, proc.stderr
results.append(test("Dashboard imports without runtime errors", test_streamlit_dryrun))

print(f"\n{'='*50}")
print(f"Results: {sum(results)}/{len(results)} passed")
if all(results):
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
    sys.exit(1)
