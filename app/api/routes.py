from fastapi import APIRouter, Depends, Query, Request

from ..security.permissions import PRODUCTION_TIER_ENABLED, Principal
from .deps import get_principal
from .schemas import CompareRequest, NoteRequest, PrepareRequest

router = APIRouter(prefix="/api")


def svc(request: Request):
    return request.app.state.services


@router.get("/health")
def health(request: Request):
    return {"status": "ok", "app": "TuitionBridge", "mode": "SANDBOX_SIMULATED",
            "llm_configured": svc(request).explainer.configured, "production_tier_enabled": PRODUCTION_TIER_ENABLED}


@router.get("/accounts/{account_id}")
def get_account(account_id: str, request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).account_view(principal, account_id)


@router.get("/rates")
def get_rates(request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).rates_view(principal)


@router.get("/providers")
def get_providers(request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).providers_view(principal)


@router.post("/quotes/compare")
def compare(body: CompareRequest, request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).compare(principal, **body.model_dump())


@router.post("/transfers/prepare")
def prepare(body: PrepareRequest, request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).prepare(principal, **body.model_dump())


@router.get("/transfers")
def list_transfers(request: Request, account_id: str = Query(...), principal: Principal = Depends(get_principal)):
    return svc(request).list_transfers(principal, account_id)


@router.get("/transfers/{transfer_id}")
def get_transfer(transfer_id: str, request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).get_transfer(principal, transfer_id)


@router.post("/transfers/{transfer_id}/approve")
def approve(transfer_id: str, request: Request, body: NoteRequest | None = None,
            principal: Principal = Depends(get_principal)):
    return svc(request).approve(principal, transfer_id, body.note if body else None)


@router.post("/transfers/{transfer_id}/reject")
def reject(transfer_id: str, request: Request, body: NoteRequest | None = None,
           principal: Principal = Depends(get_principal)):
    return svc(request).reject(principal, transfer_id, body.note if body else None)


@router.post("/transfers/{transfer_id}/execute")
def execute(transfer_id: str, request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).execute(principal, transfer_id)


@router.post("/transfers/{transfer_id}/production-execute")
def production_execute(transfer_id: str, request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).production_execute(principal, transfer_id)


@router.get("/audit")
def audit(request: Request, account_id: str | None = Query(default=None),
          principal: Principal = Depends(get_principal)):
    return svc(request).audit_entries(principal, account_id or principal.account_id)


@router.get("/audit/verify")
def audit_verify(request: Request, principal: Principal = Depends(get_principal)):
    return svc(request).audit_verify(principal)
