"""
Sprint 0 Verification Script: Validate All Psychometric & Telemetry Toolchains
Group Member Onboarding Diagnostic
"""
import sys

def test_all():
    print("=== Testing IVRAR Evaluation Toolchains ===")
    try:
        import sus_calculator
        sus_calculator.evaluate_cohort()
        print("[OK] SUS Calculator operational.")
    except Exception as e:
        print(f"[FAIL] SUS Calculator failed: {e}")
        return False
        
    try:
        import nasa_tlx_calculator
        nasa_tlx_calculator.evaluate_tlx_comparison()
        print("[OK] NASA-TLX Calculator operational.")
    except Exception as e:
        print(f"[FAIL] NASA-TLX Calculator failed: {e}")
        return False
        
    try:
        import kennedy_ssq_calculator
        kennedy_ssq_calculator.evaluate_ssq_safety()
        print("[OK] Kennedy SSQ Calculator operational.")
    except Exception as e:
        print(f"[FAIL] Kennedy SSQ Calculator failed: {e}")
        return False
        
    print("[SUCCESS] ALL PSYCHOMETRIC EVALUATION ENGINES VERIFIED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = test_all()
    if not success: sys.exit(1)
