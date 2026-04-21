pytest_plugins = ["pytester"]


# Example functions used by direct (non-pytester) tests


def process_payment(amount: float) -> bool:
    if amount <= 0:
        raise ValueError("Invalid amount")
    return True


def send_email(to: str, subject: str) -> bool:
    return True


def validate_user(user_id: str) -> bool:
    return user_id != "invalid"


class PaymentService:
    def charge(self, amount: float) -> dict:
        return {"success": True, "amount": amount}
