from rapidfuzz import fuzz

from src.data.models.postgres.employee_model import Employee


def _exact_email_match(employees: list[Employee], email: str) -> Employee | None:
    email_lower = email.strip().lower()
    for emp in employees:
        if emp.emp_email and emp.emp_email.strip().lower() == email_lower:
            return emp
    return None


def _normalized_name_match(employees: list[Employee], name: str) -> Employee | None:
    normalized = _normalize(name)
    for emp in employees:
        full_name = _normalize(f"{emp.first_name} {emp.last_name}")
        if full_name == normalized:
            return emp
        reversed_name = _normalize(f"{emp.last_name} {emp.first_name}")
        if reversed_name == normalized:
            return emp
    return None


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


FUZZY_MATCH_THRESHOLD = 80


def _fuzzy_name_match(employees: list[Employee], name: str) -> Employee | None:
    best_match = None
    best_score = 0

    normalized_input = _normalize(name)

    for emp in employees:
        full_name = _normalize(f"{emp.first_name} {emp.last_name}")
        score = fuzz.token_sort_ratio(normalized_input, full_name)
        if score > best_score and score >= FUZZY_MATCH_THRESHOLD:
            best_score = score
            best_match = emp

    return best_match


def _get_fuzzy_score(name: str, employee: Employee) -> int:
    """Get fuzzy match score between name and employee full name."""
    normalized_input = _normalize(name)
    full_name = _normalize(f"{employee.first_name} {employee.last_name}")
    return fuzz.token_sort_ratio(normalized_input, full_name)


def _is_client_match(extracted_name: str, system_name: str) -> bool:
    """Check if extracted client name matches system client name."""
    # Exact match (case-insensitive)
    if extracted_name.lower().strip() == system_name.lower().strip():
        return True

    # Normalized match
    extracted_normalized = _normalize(extracted_name)
    system_normalized = _normalize(system_name)
    if extracted_normalized == system_normalized:
        return True

    # Fuzzy match (high threshold for client names)
    score = fuzz.token_sort_ratio(extracted_normalized, system_normalized)
    return score >= 85
