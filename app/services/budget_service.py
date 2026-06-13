"""
Budget service — Phase 30.

Access rules
------------
- college_admin   : any budget
- club president  : budgets belonging to their club (event or club-level)
- faculty_advisor : budgets belonging to clubs they advise  (read-only via get_budget)

Budget lifecycle
----------------
  create_budget  — one budget per event (unique constraint on event_id)
  get_budget     — fetch with items; compute total_spent from item rows
  update_budget  — change total_allocated / notes
  add_item       — append a line item and recompute total_spent
  update_item    — patch a line item and recompute total_spent
  delete_item    — remove a line item and recompute total_spent
"""

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.budget import Budget, BudgetItem
from app.models.club import Club, ClubMembership, ClubMemberRole
from app.models.user import User, UserRole
from app.schemas.budget import (
    BudgetCreate,
    BudgetItemCreate,
    BudgetItemRead,
    BudgetItemUpdate,
    BudgetRead,
    BudgetUpdate,
)
from app.utils.club_repo import get_club_by_id
from app.utils.event_repo import get_event_by_id


# ── access helpers ────────────────────────────────────────────────────────────

def _resolve_club_id(db: Session, budget: Budget) -> int:
    """Return the club_id that owns this budget (via event or directly)."""
    if budget.club_id:
        return budget.club_id
    event = get_event_by_id(db, budget.event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event.club_id


def _assert_write_access(db: Session, user: User, budget: Budget) -> None:
    """college_admin or club president may write."""
    if user.role == UserRole.college_admin:
        return
    club_id = _resolve_club_id(db, budget)
    mem = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.user_id == user.id,
            ClubMembership.club_id == club_id,
            ClubMembership.role == ClubMemberRole.president,
        )
        .first()
    )
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the club president or college admin can manage budgets",
        )


def _assert_read_access(db: Session, user: User, budget: Budget) -> None:
    """college_admin, club president, or faculty_advisor of that club may read."""
    if user.role == UserRole.college_admin:
        return
    club_id = _resolve_club_id(db, budget)
    if user.role == UserRole.faculty_advisor:
        club = db.get(Club, club_id)
        if club and club.faculty_advisor_id == user.id:
            return
    # For president (and other roles) fall back to write-access check
    mem = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.user_id == user.id,
            ClubMembership.club_id == club_id,
            ClubMembership.role == ClubMemberRole.president,
        )
        .first()
    )
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this budget",
        )


def _get_budget_or_404(db: Session, budget_id: int) -> Budget:
    b = db.get(Budget, budget_id)
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return b


def _get_item_or_404(db: Session, budget_id: int, item_id: int) -> BudgetItem:
    item = (
        db.query(BudgetItem)
        .filter(BudgetItem.id == item_id, BudgetItem.budget_id == budget_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget item not found")
    return item


def _recompute_total_spent(db: Session, budget: Budget) -> None:
    """Recalculate total_spent from BudgetItem rows and persist."""
    total = (
        db.query(func.sum(BudgetItem.amount))
        .filter(BudgetItem.budget_id == budget.id)
        .scalar()
        or 0.0
    )
    budget.total_spent = round(total, 2)


def _to_read(budget: Budget) -> BudgetRead:
    return BudgetRead(
        id=budget.id,
        event_id=budget.event_id,
        club_id=budget.club_id,
        total_allocated=budget.total_allocated,
        total_spent=budget.total_spent,
        notes=budget.notes,
        items=[
            BudgetItemRead(
                id=i.id,
                category=i.category,
                description=i.description,
                amount=i.amount,
                receipt_url=i.receipt_url,
                created_at=i.created_at,
            )
            for i in budget.items
        ],
        created_at=budget.created_at,
    )


# ── public API ────────────────────────────────────────────────────────────────

def create_budget(db: Session, data: BudgetCreate, current_user: User) -> BudgetRead:
    # Validate target exists and derive club_id for access check
    if data.event_id:
        event = get_event_by_id(db, data.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        club_id_for_check = event.club_id
        # One budget per event
        existing = db.query(Budget).filter(Budget.event_id == data.event_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A budget already exists for this event",
            )
    else:
        club = get_club_by_id(db, data.club_id)
        if not club or club.is_suspended:
            raise HTTPException(status_code=404, detail="Club not found")
        club_id_for_check = data.club_id

    # Build a temporary Budget to reuse _assert_write_access
    tmp = Budget(event_id=data.event_id, club_id=data.club_id)
    tmp.club_id = data.club_id  # may be None if event-based
    # For access check, patch club_id temporarily when event-based
    if data.event_id and not data.club_id:
        tmp.club_id = club_id_for_check
    _assert_write_access(db, current_user, tmp)

    budget = Budget(
        event_id=data.event_id,
        club_id=data.club_id if not data.event_id else None,
        total_allocated=data.total_allocated,
        total_spent=0.0,
        notes=data.notes,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return _to_read(budget)


def get_budget(db: Session, budget_id: int, current_user: User) -> BudgetRead:
    budget = _get_budget_or_404(db, budget_id)
    _assert_read_access(db, current_user, budget)
    return _to_read(budget)


def get_budget_by_event(db: Session, event_id: int, current_user: User) -> BudgetRead:
    budget = db.query(Budget).filter(Budget.event_id == event_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="No budget found for this event")
    _assert_read_access(db, current_user, budget)
    return _to_read(budget)


def get_budgets_by_club(db: Session, club_id: int, current_user: User) -> list[BudgetRead]:
    # Validate club exists
    club = get_club_by_id(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    tmp = Budget(club_id=club_id, event_id=None)
    _assert_read_access(db, current_user, tmp)
    budgets = db.query(Budget).filter(Budget.club_id == club_id).all()
    return [_to_read(b) for b in budgets]


def update_budget(
    db: Session, budget_id: int, data: BudgetUpdate, current_user: User
) -> BudgetRead:
    budget = _get_budget_or_404(db, budget_id)
    _assert_write_access(db, current_user, budget)
    if data.total_allocated is not None:
        budget.total_allocated = data.total_allocated
    if data.notes is not None:
        budget.notes = data.notes
    db.commit()
    db.refresh(budget)
    return _to_read(budget)


# ── items ─────────────────────────────────────────────────────────────────────

def add_item(
    db: Session, budget_id: int, data: BudgetItemCreate, current_user: User
) -> BudgetRead:
    budget = _get_budget_or_404(db, budget_id)
    _assert_write_access(db, current_user, budget)

    item = BudgetItem(
        budget_id=budget_id,
        category=data.category,
        description=data.description,
        amount=data.amount,
        receipt_url=data.receipt_url,
        added_by=current_user.id,
    )
    db.add(item)
    db.flush()
    _recompute_total_spent(db, budget)
    db.commit()
    db.refresh(budget)
    return _to_read(budget)


def update_item(
    db: Session,
    budget_id: int,
    item_id: int,
    data: BudgetItemUpdate,
    current_user: User,
) -> BudgetRead:
    budget = _get_budget_or_404(db, budget_id)
    _assert_write_access(db, current_user, budget)
    item = _get_item_or_404(db, budget_id, item_id)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)

    _recompute_total_spent(db, budget)
    db.commit()
    db.refresh(budget)
    return _to_read(budget)


def delete_item(
    db: Session, budget_id: int, item_id: int, current_user: User
) -> BudgetRead:
    budget = _get_budget_or_404(db, budget_id)
    _assert_write_access(db, current_user, budget)
    item = _get_item_or_404(db, budget_id, item_id)

    db.delete(item)
    db.flush()
    _recompute_total_spent(db, budget)
    db.commit()
    db.refresh(budget)
    return _to_read(budget)
