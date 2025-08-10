# Fix bcrypt compatibility issue with passlib
import bcrypt
import types
if not hasattr(bcrypt, '__about__'):
    about_module = types.ModuleType('__about__')
    about_module.__version__ = bcrypt.__version__
    bcrypt.__about__ = about_module

# Re-export all functions from specialized services for backward compatibility
from app.auth.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)

from app.auth.registration_service import (
    check_existing_user,
    create_development_user,
    create_production_pending_user
)

from app.auth.verification_service import (
    verify_pending_registration,
    resend_verification_to_pending_user
)

from app.auth.cleanup_service import (
    cleanup_expired_pending_registrations,
    delete_user_data
)

# This file now serves as:
# 1. Bcrypt compatibility fix
# 2. Centralized import point for all auth utilities
# Individual services can be imported directly for better organization