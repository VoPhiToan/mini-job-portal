from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
) -> Category:
    existing_category = (
        db.query(Category).filter(Category.name == category_data.name).first()
    )
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category already exists",
        )

    category = Category(name=category_data.name)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category already exists",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        ) from exc

    return category


@router.get("", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)) -> list[Category]:
    return db.query(Category).order_by(Category.id.asc()).all()
