from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register")
def user_registration():
    """User registration"""
    pass


@router.post("/login")
def user_login():
    """User Login (JWT)"""
    pass


@router.post("/logout")
def logout():
    """Logout"""
    pass
