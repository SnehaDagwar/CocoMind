"""RBAC models — roles, permissions, and user identity."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    """Six personas from the RBAC spec."""

    SUPER_ADMIN = "SuperAdmin"
    PROCUREMENT_OFFICER = "ProcurementOfficer"
    EVALUATOR = "Evaluator"
    HITL_REVIEWER = "HITLReviewer"
    AUDITOR = "Auditor"
    EXTERNAL_OBSERVER = "ExternalObserver"


class Permission(StrEnum):
    """Fine-grained permissions enforced at the API layer."""

    MANAGE_USERS = "manage_users"
    MANAGE_CONFIG = "manage_config"
    UPLOAD_NIT = "upload_nit"
    UPLOAD_BID = "upload_bid"
    TRIGGER_EVALUATION = "trigger_evaluation"
    VIEW_VTM = "view_vtm"
    RESOLVE_HITL = "resolve_hitl"
    SIGN_DECISION = "sign_decision"
    EXPORT_RTI = "export_rti"
    VERIFY_AUDIT = "verify_audit"
    VIEW_AUDIT_LOG = "view_audit_log"


# Role → permissions mapping (least privilege)
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: {
        Permission.MANAGE_USERS,
        Permission.MANAGE_CONFIG,
    },
    Role.PROCUREMENT_OFFICER: {
        Permission.UPLOAD_NIT,
        Permission.UPLOAD_BID,
        Permission.TRIGGER_EVALUATION,
        Permission.VIEW_VTM,
    },
    Role.EVALUATOR: {
        Permission.VIEW_VTM,
        Permission.TRIGGER_EVALUATION,
    },
    Role.HITL_REVIEWER: {
        Permission.VIEW_VTM,
        Permission.RESOLVE_HITL,
        Permission.SIGN_DECISION,
    },
    Role.AUDITOR: {
        Permission.VIEW_VTM,
        Permission.VIEW_AUDIT_LOG,
        Permission.VERIFY_AUDIT,
        Permission.EXPORT_RTI,
    },
    Role.EXTERNAL_OBSERVER: set(),  # receive signed exports only
}


class User(BaseModel):
    """A system user with role-based identity."""

    user_id: str
    name: str
    email: str = ""
    role: Role
    procurement_circle_id: str | None = Field(
        default=None,
        description="Scopes VTM access to a specific CRPF circle"
    )
    is_active: bool = True

    @property
    def permissions(self) -> set[Permission]:
        return ROLE_PERMISSIONS.get(self.role, set())

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions
