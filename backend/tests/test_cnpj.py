"""IAudit - CNPJ validation tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.cnpj import validate_cnpj, format_cnpj, clean_cnpj


def test_valid_cnpjs():
    """Test known valid CNPJs."""
    valid = [
        "11222333000181",
        "11.222.333/0001-81",
        "00623904000173",
    ]
    for cnpj in valid:
        assert validate_cnpj(cnpj), f"Expected {cnpj} to be valid"


def test_invalid_cnpjs():
    """Test known invalid CNPJs."""
    invalid = [
        "00000000000000",  # all same digits
        "11111111111111",
        "12345678901234",  # bad check digits
        "1234567890",      # too short
        "123456789012345", # too long
        "",                # empty
        "abcdefghijklmn",  # non-numeric
    ]
    for cnpj in invalid:
        assert not validate_cnpj(cnpj), f"Expected {cnpj} to be invalid"


def test_format_cnpj():
    """Test CNPJ formatting."""
    assert format_cnpj("11222333000181") == "11.222.333/0001-81"
    assert format_cnpj("00623904000173") == "00.623.904/0001-73"


def test_clean_cnpj():
    """Test CNPJ cleaning."""
    assert clean_cnpj("11.222.333/0001-81") == "11222333000181"
    assert clean_cnpj("  11-222-333/0001.81  ") == "11222333000181"


if __name__ == "__main__":
    test_valid_cnpjs()
    print("✅ test_valid_cnpjs passed")

    test_invalid_cnpjs()
    print("✅ test_invalid_cnpjs passed")

    test_format_cnpj()
    print("✅ test_format_cnpj passed")

    test_clean_cnpj()
    print("✅ test_clean_cnpj passed")

    print("\n🎉 All tests passed!")
