"""
Phase 4 — Buyers API.
Extends Phase 1 /api/buyers with:
  GET  /api/buyers/matches           — ranked buyer matches for a crop
  POST /api/buyers/request           — farmer sends connection request
  GET  /api/buyers/requests          — list requests (by farmer or buyer)
  PATCH /api/buyers/requests/{id}    — buyer accepts/rejects request
"""
from __future__ import annotations

from typing import Optional, List
from datetime import date, datetime

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.buyer import BuyerListItem
from app.schemas.matching import (
    BuyerMatchResponse, MatchedBuyerSchema, ScoreBreakdownSchema,
    ConnectionRequestCreate, ConnectionRequestOut, ConnectionRequestStatusUpdate,
)
from app.services.demo_data import get_buyers, get_best_buyer
from app.agents.buyer_matching import get_buyer_matching_service
from app.models.connection_request import BuyerConnectionRequest, RequestStatus
from app.database.base import get_db

router = APIRouter(prefix="/buyers", tags=["Buyers"])


# ── Phase 1 preserved endpoints ───────────────────────────────────────────────

@router.get(
    "",
    response_model=List[BuyerListItem],
    summary="List buyers",
    description="Returns buyers optionally filtered by crop. ⚠️ DEMO DATA",
)
async def list_buyers(
    crop: Optional[str] = Query(default=None, description="Filter: cotton or groundnut"),
):
    return get_buyers(crop=crop)


@router.get(
    "/best",
    response_model=Optional[BuyerListItem],
    summary="Get best buyer for a crop",
)
async def best_buyer(
    crop: str = Query(default="cotton", description="cotton or groundnut"),
):
    return get_best_buyer(crop=crop)


# ── Phase 4: Buyer Matching ───────────────────────────────────────────────────

@router.get(
    "/matches",
    response_model=BuyerMatchResponse,
    summary="Ranked buyer matches for a farmer's crop",
    description=(
        "Returns buyers ranked by a 100-point deterministic match score.\n\n"
        "Score breakdown: Crop(30) + Quality(20) + Price(20) + Location(15) + Quantity(10) + Delivery(5)\n\n"
        "Market price reference comes from Phase 2 demo data provider.\n\n"
        "⚠️ DEMO DATA — Distance estimates only. Not verified routes."
    ),
)
async def get_buyer_matches(
    crop:        str            = Query(...,    description="Crop: cotton or groundnut"),
    quantity:    Optional[float]= Query(None,  description="Farmer quantity in quintals"),
    quality:     Optional[str]  = Query(None,  description="Farmer quality grade: A, B, C"),
    district:    Optional[str]  = Query(None,  description="Farmer district (Gujarat)"),
    harvest_date:Optional[date] = Query(None,  description="Expected harvest date (YYYY-MM-DD)"),
    top_n:       int            = Query(10,    ge=1, le=20, description="Max results"),
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")

    svc = get_buyer_matching_service()
    matched = svc.find_matches(
        crop=crop,
        quantity=quantity,
        quality_grade=quality,
        farmer_district=district,
        harvest_date=harvest_date,
        top_n=top_n,
    )

    # Get market price from first match (all same crop)
    market_price = matched[0].market_price if matched else None

    return BuyerMatchResponse(
        crop=crop.lower(),
        quantity=quantity,
        district=district,
        market_price=market_price,
        total_found=len(matched),
        matches=[
            MatchedBuyerSchema(
                **{k: v for k, v in m.to_dict().items() if k != "breakdown"},
                breakdown=ScoreBreakdownSchema(**m.breakdown),
            )
            for m in matched
        ],
    )


# ── Phase 4: Connection Requests ─────────────────────────────────────────────

@router.post(
    "/request",
    response_model=ConnectionRequestOut,
    summary="Farmer sends a connection request to a buyer",
    description=(
        "Creates a purchase/connection request from a farmer to a buyer.\n\n"
        "Prevents duplicate PENDING requests for the same (farmer, buyer, crop).\n\n"
        "⚠️ DEMO DATA — No real authentication in Phase 4."
    ),
    status_code=201,
)
async def create_connection_request(
    payload: ConnectionRequestCreate,
    db: Session = Depends(get_db),
):
    crop_lower = payload.crop.lower()

    # Validate crop
    if crop_lower not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")

    # Validate buyer exists in demo data
    from app.services.demo_data import DEMO_BUYERS
    buyer_ids = {b.id for b in DEMO_BUYERS}
    if payload.buyer_id not in buyer_ids:
        raise HTTPException(404, detail=f"Buyer {payload.buyer_id} not found")

    # Check for duplicate active (PENDING) request
    existing = (
        db.query(BuyerConnectionRequest)
        .filter(
            BuyerConnectionRequest.farmer_id == payload.farmer_id,
            BuyerConnectionRequest.buyer_id  == payload.buyer_id,
            BuyerConnectionRequest.crop      == crop_lower,
            BuyerConnectionRequest.status    == RequestStatus.PENDING,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            409,
            detail=(
                f"A PENDING request already exists (id={existing.id}) for this "
                "farmer–buyer–crop combination. Cancel it before creating a new one."
            ),
        )

    req = BuyerConnectionRequest(
        farmer_id     = payload.farmer_id,
        buyer_id      = payload.buyer_id,
        crop          = crop_lower,
        crop_id       = payload.crop_id,
        quantity      = payload.quantity,
        offered_price = payload.offered_price,
        message       = payload.message,
        match_score   = payload.match_score,
        status        = RequestStatus.PENDING,
        created_at    = datetime.utcnow(),
        updated_at    = datetime.utcnow(),
    )
    db.add(req)
    try:
        db.commit()
        db.refresh(req)
    except Exception as exc:
        db.rollback()
        # Unique constraint violation (race condition)
        if "UNIQUE" in str(exc).upper() or "unique" in str(exc).lower():
            raise HTTPException(409, detail="Duplicate request — already pending.")
        raise HTTPException(500, detail=f"Database error: {exc}")

    return req


@router.get(
    "/requests",
    response_model=List[ConnectionRequestOut],
    summary="List connection requests",
    description=(
        "Filter by farmer_id or buyer_id.\n\n"
        "Returns most recent first."
    ),
)
async def list_requests(
    farmer_id: Optional[int] = Query(None, description="Filter by farmer user id"),
    buyer_id:  Optional[int] = Query(None, description="Filter by buyer id"),
    status:    Optional[str] = Query(None, description="Filter by status: PENDING, ACCEPTED, REJECTED, COMPLETED"),
    db: Session = Depends(get_db),
):
    q = db.query(BuyerConnectionRequest)
    if farmer_id:
        q = q.filter(BuyerConnectionRequest.farmer_id == farmer_id)
    if buyer_id:
        q = q.filter(BuyerConnectionRequest.buyer_id == buyer_id)
    if status:
        try:
            q = q.filter(BuyerConnectionRequest.status == RequestStatus(status.upper()))
        except ValueError:
            raise HTTPException(400, detail=f"Invalid status: {status}")
    return q.order_by(BuyerConnectionRequest.created_at.desc()).all()


@router.patch(
    "/requests/{request_id}",
    response_model=ConnectionRequestOut,
    summary="Buyer accepts or rejects a connection request",
)
async def update_request_status(
    request_id: int,
    payload:    ConnectionRequestStatusUpdate,
    db:         Session = Depends(get_db),
):
    req = db.query(BuyerConnectionRequest).filter(
        BuyerConnectionRequest.id == request_id
    ).first()

    if not req:
        raise HTTPException(404, detail=f"Request {request_id} not found")

    if req.status not in (RequestStatus.PENDING, RequestStatus.ACCEPTED):
        raise HTTPException(
            400,
            detail=f"Cannot update request in status '{req.status}'. Only PENDING or ACCEPTED requests can be updated.",
        )

    req.status     = RequestStatus(payload.status)
    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req


@router.get(
    "/requests/{request_id}",
    response_model=ConnectionRequestOut,
    summary="Get a single connection request by id",
)
async def get_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    req = db.query(BuyerConnectionRequest).filter(
        BuyerConnectionRequest.id == request_id
    ).first()
    if not req:
        raise HTTPException(404, detail=f"Request {request_id} not found")
    return req
