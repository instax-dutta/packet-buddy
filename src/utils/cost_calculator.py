"""Cost calculation utilities for PacketBuddy."""

# Indian mobile data costs (as of 2026)
# Based on average across Jio, Airtel, Vi
DEFAULT_COST_PER_GB_INR = 7.50  # ₹7.50 per GB (average)

# Alternative pricing tiers
COST_TIERS = {
    "budget": 7.0,      # Budget plans (₹7/GB)
    "standard": 7.5,    # Standard plans (₹7.50/GB)
    "premium": 10.0,    # Premium/5G plans (₹10/GB)
    "broadband": 5.0,   # Home fiber broadband (₹5/GB effective)
}


def calculate_cost(bytes_used: int, cost_per_gb: float = DEFAULT_COST_PER_GB_INR) -> dict:
    """
    Calculate cost for given data usage.
    
    Args:
        bytes_used: Total bytes used
        cost_per_gb: Cost per GB in INR (default: ₹7.50)
        
    Returns:
        Dict with gb_used and cost in INR
    """
    gb_used = bytes_used / (1024 ** 3)  # Convert bytes to GB
    cost_inr = gb_used * cost_per_gb
    
    return {
        "gb_used": round(gb_used, 2),
        "cost_inr": round(cost_inr, 2),
        "cost_formatted": f"₹{cost_inr:,.2f}"
    }


def get_cost_breakdown(bytes_sent: int, bytes_received: int, cost_per_gb: float = DEFAULT_COST_PER_GB_INR) -> dict:
    """
    Get detailed cost breakdown for upload/download.
    
    Args:
        bytes_sent: Bytes uploaded
        bytes_received: Bytes downloaded
        cost_per_gb: Cost per GB in INR
        
    Returns:
        Dict with detailed breakdown
    """
    upload_cost = calculate_cost(bytes_sent, cost_per_gb)
    download_cost = calculate_cost(bytes_received, cost_per_gb)
    total_cost = calculate_cost(bytes_sent + bytes_received, cost_per_gb)
    
    return {
        "upload": upload_cost,
        "download": download_cost,
        "total": total_cost,
        "cost_per_gb": cost_per_gb,
        "currency": "INR"
    }


def format_currency_inr(amount: float) -> str:
    """
    Format amount as Indian currency.
    
    Args:
        amount: Amount in INR
        
    Returns:
        Formatted string like ₹1,234.56
    """
    return f"₹{amount:,.2f}"


def estimate_monthly_cost(daily_bytes: int, days_in_month: int = 30, cost_per_gb: float = DEFAULT_COST_PER_GB_INR) -> dict:
    """
    Estimate monthly cost based on daily average.
    
    Args:
        daily_bytes: Average daily usage in bytes
        days_in_month: Days in month (default: 30)
        cost_per_gb: Cost per GB in INR
        
    Returns:
        Dict with monthly estimate
    """
    monthly_bytes = daily_bytes * days_in_month
    monthly_cost = calculate_cost(monthly_bytes, cost_per_gb)
    
    return {
        "estimated_monthly_gb": monthly_cost["gb_used"],
        "estimated_monthly_cost": monthly_cost["cost_inr"],
        "formatted": monthly_cost["cost_formatted"],
        "daily_average_gb": round(daily_bytes / (1024 ** 3), 2),
        "daily_average_cost": round(monthly_cost["cost_inr"] / days_in_month, 2)
    }
