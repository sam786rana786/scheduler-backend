from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any
from ...db.database import get_db
from ...core.auth import get_current_user
from ...models.user import User
from ...models.settings import Settings as SettingsModel
from ...schemas.settings import Settings
from ...schemas.email import EmailTest, EmailSettings
from ...schemas.smsSubscription import SMSSubscription
from ...schemas.sms import SMSTest
from ...core.emails import send_test_email
from ...core.sms import SMSService
from ...core.config import Settings as AppSettings, get_settings
import paypalrestsdk

router = APIRouter()

@router.get("/settings", response_model=Settings)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user settings"""
    settings = db.query(SettingsModel).filter(SettingsModel.user_id == current_user.id).first()
    if not settings:
        # Create default settings
        settings = SettingsModel(
            user_id=current_user.id,
            working_hours={
                "monday": {"start": "09:00", "end": "17:00", "enabled": True},
                "tuesday": {"start": "09:00", "end": "17:00", "enabled": True},
                "wednesday": {"start": "09:00", "end": "17:00", "enabled": True},
                "thursday": {"start": "09:00", "end": "17:00", "enabled": True},
                "friday": {"start": "09:00", "end": "17:00", "enabled": True},
                "saturday": {"start": "09:00", "end": "17:00", "enabled": False},
                "sunday": {"start": "09:00", "end": "17:00", "enabled": False}
            },
            notification_settings={
                "email": {
                    "enabled": False,
                    "newBooking": True,
                    "canceledBooking": True,
                    "reminders": True
                },
                "sms": {
                    "enabled": False,
                    "provider": None,
                    "usePayAsYouGo": False
                }
            },
            email_settings={},
            sms_settings={}
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.put("/settings", response_model=Settings)
async def update_settings(
    settings_update: Settings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update user settings"""
    settings = db.query(SettingsModel).filter(SettingsModel.user_id == current_user.id).first()
    if not settings:
        settings = SettingsModel(user_id=current_user.id)
        db.add(settings)
    
    settings.working_hours = settings_update.working_hours
    settings.notification_settings = settings_update.notification_settings
    settings.email_settings = settings_update.email_settings
    settings.sms_settings = settings_update.sms_settings
    
    try:
        db.commit()
        db.refresh(settings)
        return settings
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/test-email")
async def test_email(
    email_test: EmailTest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Test email settings"""
    try:
        # Get settings for the current user
        settings = db.query(SettingsModel).filter(SettingsModel.user_id == current_user.id).first()
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settings not found"
            )
            
        if not settings.email_settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email settings not configured"
            )

        # Validate required email settings
        required_fields = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email', 'from_name']
        for field in required_fields:
            if field not in settings.email_settings or not settings.email_settings[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required email setting: {field}"
                )

        # Send test email
        await send_test_email(
            to_email=email_test.email,
            smtp_settings={
                'MAIL_SERVER': settings.email_settings['smtp_server'],
                'MAIL_PORT': settings.email_settings['smtp_port'],
                'MAIL_USERNAME': settings.email_settings['smtp_username'],
                'MAIL_PASSWORD': settings.email_settings['smtp_password'],
                'MAIL_FROM': settings.email_settings['from_email'],
                'MAIL_FROM_NAME': settings.email_settings['from_name']
            }
        )
        
        return {"message": "Test email sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/test-sms")
async def test_sms(
    sms_test: SMSTest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Test SMS settings"""
    try:
        # Get settings for current user
        settings = db.query(SettingsModel).filter(SettingsModel.user_id == current_user.id).first()
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settings not found"
            )

        if not settings.sms_settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS settings not configured"
            )

        # Validate SMS provider configuration
        provider = settings.sms_settings.get('provider')
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS provider not configured"
            )

        # Initialize SMS service with settings
        sms_service = SMSService(settings.sms_settings)
        
        # Send test SMS
        success = await sms_service.send_sms(
            to=sms_test.phone,
            message="This is a test SMS from your scheduling application."
        )

        if success:
            return {"message": "Test SMS sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send test SMS"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/settings/subscribe-sms")
async def subscribe_to_sms(
    settings: AppSettings = Depends(get_settings),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create PayPal subscription for SMS service"""
    try:
        # Initialize PayPal
        paypalrestsdk.configure({
            "mode": "sandbox" if settings.PAYPAL_SANDBOX else "live",  # sandbox or live
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_SECRET
        })

        # Create billing plan
        billing_plan = paypalrestsdk.BillingPlan({
            "name": "SMS Notification Service",
            "description": "Monthly subscription for SMS notification service",
            "type": "INFINITE",
            "payment_definitions": [{
                "name": "Regular monthly payment",
                "type": "REGULAR",
                "frequency": "MONTH",
                "frequency_interval": "1",
                "amount": {
                    "currency": "USD",
                    "value": "50"
                },
                "cycles": "0"
            }],
            "merchant_preferences": {
                "return_url": f"{settings.FRONTEND_URL}/dashboard/settings?success=true",
                "cancel_url": f"{settings.FRONTEND_URL}/dashboard/settings?success=false",
                "auto_bill_amount": "YES",
                "initial_fail_amount_action": "CONTINUE",
                "max_fail_attempts": "3"
            }
        })

        if billing_plan.create():
            # Create subscription record
            subscription = SMSSubscription(
                user_id=current_user.id,
                subscription_id=billing_plan.id,
                status="pending",
                created_at=datetime.now().isoformat(),
                next_billing_date=(datetime.now() + timedelta(days=30)).isoformat()
            )
            db.add(subscription)
            db.commit()

            return {
                "id": billing_plan.id,
                "approval_url": billing_plan.links[1].href  # The approval URL for the user
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=billing_plan.error
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/settings/verify-subscription")
async def verify_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Verify PayPal subscription status"""
    subscription = db.query(SMSSubscription).filter(
        SMSSubscription.subscription_id == subscription_id,
        SMSSubscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    try:
        paypal_subscription = paypalrestsdk.BillingPlan.find(subscription_id)
        subscription.status = paypal_subscription.state
        db.commit()

        return {"status": subscription.status}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/settings/webhook")
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Handle PayPal webhooks"""
    try:
        event_json = await request.json()
        event_type = event_json.get("event_type")
        resource = event_json.get("resource")

        if event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            subscription = db.query(SMSSubscription).filter(
                SMSSubscription.subscription_id == resource["id"]
            ).first()
            if subscription:
                subscription.status = "cancelled"
                db.commit()

        elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
            subscription = db.query(SMSSubscription).filter(
                SMSSubscription.subscription_id == resource["id"]
            ).first()
            if subscription:
                subscription.status = "suspended"
                db.commit()

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )