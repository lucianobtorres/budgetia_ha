from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..dependencies import get_current_user

router = APIRouter(prefix="/subscription", tags=["Subscription"])

class SubscriptionStatus(BaseModel):
    plan_tier: str
    status: str
    trial_end: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False

@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """
    Returns the subscription status for the current user.
    Logic:
    - If user has 'trial_ends_at' in the future -> 'trialing'
    - If user has 'role' == 'admin' -> 'pro' (active)
    - Otherwise -> 'free' (active)
    """
    
    # Check Trial
    trial_ends = current_user.get("trial_ends_at")
    
    if trial_ends:
        # User dict has it as string typically, but let's parse if needed or pass through
        # Assuming security.py returns datetime objects or ISO strings.
        # Let's ensure we return datetime for Pydantic
        if isinstance(trial_ends, str):
            trial_dt = datetime.fromisoformat(trial_ends)
        else:
            trial_dt = trial_ends

        if trial_dt > datetime.now():
            return SubscriptionStatus(
                plan_tier="pro",
                status="trialing",
                trial_end=trial_dt,
                current_period_end=None,
                cancel_at_period_end=False
            )
        else:
            # Trial expired
             return SubscriptionStatus(
                plan_tier="free",
                status="expired", # or 'active' on free tier? Let's say expired trial -> 'active' free tier for now? 
                # Actually user asked for "gratuto" instead of correct info.
                # If trial expired, they might be on free tier now.
                trial_end=trial_dt, # keep showing when it ended
                current_period_end=None,
                cancel_at_period_end=False
            )

    # Check Admin/Pro
    role = str(current_user.get("role", "user")).lower()
    username = str(current_user.get("username", "")).lower()

    if role == "admin" or username == "admin":
        return SubscriptionStatus(
            plan_tier="lifetime",
            status="active",
            trial_end=None,
            current_period_end=None, 
            cancel_at_period_end=False
        )

    # Default Free
    return SubscriptionStatus(
        plan_tier="free",
        status="active",
        trial_end=None,
        current_period_end=None,
        cancel_at_period_end=False
    )

class CheckoutRequest(BaseModel):
    plan_id: str

@router.post("/checkout")
async def create_checkout_session(req: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    # Mock checkout URL
    return {"url": f"https://checklist.stripe.com/mock-checkout/{req.plan_id}?user={current_user.get('username')}"}

@router.post("/portal")
async def create_portal_session(current_user: dict = Depends(get_current_user)):
    return {"url": "https://billing.stripe.com/p/login/mock"}
