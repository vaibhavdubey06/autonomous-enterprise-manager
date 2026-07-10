import logging
from typing import Dict, List, Optional
from app.services.a2a.models import OrganizationProfile, RemoteAgentProfile, TrustLevel

logger = logging.getLogger(__name__)


class EnterpriseDirectory:
    """
    Manages the Enterprise Directory of organizations, their endpoints, and discovered agents.
    Provides the foundation for enterprise federation.
    """

    def __init__(self):
        self._organizations: Dict[str, OrganizationProfile] = {}

        # Load some default trusted orgs (In reality this would come from a DB or config)
        self.register_organization(
            OrganizationProfile(
                org_id="org-partner-abc",
                name="Partner ABC Logistics",
                trust_level=TrustLevel.PARTNER,
                endpoints=["https://api.partner-abc.com/a2a"],
            )
        )

    def register_organization(self, org: OrganizationProfile):
        self._organizations[org.org_id] = org
        logger.info(
            f"Registered organization in Directory: {org.name} ({org.trust_level})"
        )

    def get_organization(self, org_id: str) -> Optional[OrganizationProfile]:
        return self._organizations.get(org_id)

    def list_organizations(self) -> List[OrganizationProfile]:
        return list(self._organizations.values())

    def update_organization_agents(self, org_id: str, agents: List[RemoteAgentProfile]):
        org = self.get_organization(org_id)
        if org:
            org.agents = agents
            logger.info(f"Updated {len(agents)} agents for organization {org.name}")
        else:
            logger.warning(f"Attempted to update agents for unknown org: {org_id}")

    def get_all_remote_agents(self) -> List[RemoteAgentProfile]:
        agents = []
        for org in self._organizations.values():
            agents.extend(org.agents)
        return agents
