# hr_access/tokens/tokens.py
#
#
# from hr_common.security.signing import generate_token, verify_token
# from hr_common.utils.email import normalize_email
#
# # ============================================================
# # Salts (token intent separation)
# # ============================================================
# ACCOUNT_SIGNUP_SALT = 'account-signup-confirmation'
# EMAIL_CHANGE_SALT = "account-email-change"
#
# # ============================================================
# # Expiry windows (seconds)
# # ============================================================
# DEFAULT_ACCOUNT_SIGNUP_TOKEN_MAX_AGE = 3600
# DEFAULT_EMAIL_CHANGE_TOKEN_MAX_AGE = 3600
#
#
# def generate_account_signup_token(user_id: int, email: str) -> str:
#     payload = {
#         "user_id": int(user_id),
#         "email": normalize_email(email)
#     }
#     return generate_token(payload, salt=ACCOUNT_SIGNUP_SALT)
#
#
# def verify_account_signup_token(
#     token: str,
#     max_age: int = DEFAULT_ACCOUNT_SIGNUP_TOKEN_MAX_AGE,
# ) -> dict | None:
#     data = verify_token(
#         token,
#         salt=ACCOUNT_SIGNUP_SALT,
#         max_age=max_age
#     )
#     if not data:
#         return None
#     if "user_id" not in data or "email" not in data:
#         return None
#     return data
#
#
# def generate_email_change_token(user_id: int, new_email: str) -> str:
#     payload = {
#         "user_id": int(user_id),
#         "email": normalize_email(new_email)
#     }
#     return generate_token(payload, salt=EMAIL_CHANGE_SALT)
#
#
# def verify_email_change_token(
#     token: str,
#     max_age: int = DEFAULT_EMAIL_CHANGE_TOKEN_MAX_AGE,
# ) -> dict | None:
#     data = verify_token(
#         token,
#         salt=EMAIL_CHANGE_SALT,
#         max_age=max_age
#     )
#     if not data:
#         return None
#     if "user_id" not in data or "email" not in data:
#         return None
#     return data
