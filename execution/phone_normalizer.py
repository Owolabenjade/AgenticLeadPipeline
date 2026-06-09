"""Phone number normalisation to E.164 format — supports 190+ countries."""

import phonenumbers


def normalise_phone(raw: str, default_country: str) -> str:
    """
    Parse any phone number format and return E.164.

    Args:
        raw: The raw phone number string in any format.
        default_country: ISO 3166-1 alpha-2 fallback (e.g. 'NG', 'GB', 'US').

    Returns:
        E.164-formatted phone number string (e.g. '+2348031234567').

    Raises:
        ValueError: If the phone number is invalid after parsing.
    """
    try:
        parsed = phonenumbers.parse(raw, default_country)
    except phonenumbers.NumberParseException as exc:
        raise ValueError(f"Invalid phone number format: {raw}") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise ValueError(f"Invalid phone number: {raw}")
    return phonenumbers.format_number(
        parsed, phonenumbers.PhoneNumberFormat.E164
    )
