from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from app.db_models.organizations import Organization as OrganizationModel
from app.database import get_db
from app.models.organization_model import (
    OrganizationResponse, OrganizationPostRequest,
    OrganizationPutRequest
)

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse
)
async def read_organization(
    organization_id: str,
    db=Depends(get_db)
) -> OrganizationResponse:
    """
    Retrieves an organization by its ID.

    Args:
        organization_id: The ID of the organization.

    Returns:
        The organization with the specified ID.

    Raises:
        HTTPException: If the organization is not found.
    """
    try:
        organization = db.query(OrganizationModel).filter(OrganizationModel.id == organization_id).first()
        if organization:
            return organization
        raise HTTPException(status_code=404, detail="Organization Not Found")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "",
    response_model=OrganizationResponse
)
async def create_organization(
    payload: OrganizationPostRequest,
    db=Depends(get_db)
) -> OrganizationResponse:
    """
    Creates a new organization.

    Args:
        organization: The organization to create.

    Returns:
        The created organization.

    Raises:
        HTTPException: If the organization cannot be created.
    """
    try:
        new_organization = OrganizationModel(
            **payload.model_dump(exclude_unset=True)
        )
        db.add(new_organization)
        db.commit()
        db.refresh(new_organization)
        return new_organization
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse
)
async def update_organization(
    organization_id: str,
    payload: OrganizationPutRequest,
    db=Depends(get_db)
) -> OrganizationResponse:
    """
    Updates an organization.

    Args:
        organization_id: The ID of the organization to update.
        organization: The updated organization.

    Returns:
        The updated organization.

    Raises:
        HTTPException: If the organization cannot be updated.
    """
    try:
        organization = db.query(OrganizationModel).filter(OrganizationModel.id == organization_id).first()
        if organization:
            for key, value in payload.model_dump(exclude_unset=True).items():
                setattr(organization, key, value)
            db.commit()
            db.refresh(organization)
            return organization
        raise HTTPException(status_code=404, detail="Organization Not Found")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete(
    "/{organization_id}",
    response_model=OrganizationResponse
)
async def delete_organization(
    organization_id: str,
    db=Depends(get_db)
) -> OrganizationResponse:
    """
    Deletes an organization.

    Args:
        organization_id: The ID of the organization to delete.

    Returns:
        The deleted organization.

    Raises:
        HTTPException: If the organization cannot be deleted.
    """
    try:
        organization = db.query(OrganizationModel).filter(OrganizationModel.id == organization_id).first()
        if organization:
            db.delete(organization)
            db.commit()
            return organization
        raise HTTPException(status_code=404, detail="Organization Not Found")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
