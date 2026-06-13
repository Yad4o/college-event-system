from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetItemCreate,
    BudgetItemUpdate,
    BudgetRead,
    BudgetUpdate,
)
from app.services import budget_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


# ── Budget CRUD ───────────────────────────────────────────────────────────────

@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a budget for an event or a club.
    Provide exactly one of event_id or club_id.
    Club president or college_admin only.
    """
    return budget_service.create_budget(db, data, current_user)


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a budget with all its line items. President, faculty advisor, or college_admin."""
    return budget_service.get_budget(db, budget_id, current_user)


@router.get("/events/{event_id}", response_model=BudgetRead)
def get_budget_by_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convenience: fetch the budget for a specific event."""
    return budget_service.get_budget_by_event(db, event_id, current_user)


@router.get("/clubs/{club_id}", response_model=list[BudgetRead])
def get_budgets_by_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all budgets directly attached to a club (not via events)."""
    return budget_service.get_budgets_by_club(db, club_id, current_user)


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update total_allocated or notes. Club president or college_admin only."""
    return budget_service.update_budget(db, budget_id, data, current_user)


# ── Line items ────────────────────────────────────────────────────────────────

@router.post("/{budget_id}/items", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def add_item(
    budget_id: int,
    data: BudgetItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add an expense line item to a budget.
    Pass receipt_url if the receipt was already uploaded to Cloudinary by the client.
    Returns the full updated budget.
    """
    return budget_service.add_item(db, budget_id, data, current_user)


@router.patch("/{budget_id}/items/{item_id}", response_model=BudgetRead)
def update_item(
    budget_id: int,
    item_id: int,
    data: BudgetItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a line item. Returns the full updated budget."""
    return budget_service.update_item(db, budget_id, item_id, data, current_user)


@router.delete("/{budget_id}/items/{item_id}", response_model=BudgetRead)
def delete_item(
    budget_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a line item and recompute total_spent. Returns the updated budget."""
    return budget_service.delete_item(db, budget_id, item_id, current_user)
