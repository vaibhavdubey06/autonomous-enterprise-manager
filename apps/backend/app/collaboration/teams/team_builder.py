from typing import List
from app.collaboration.teams.team_registry import TeamRegistry
from app.collaboration.teams.agent_roles import AgentCollaborationProfile, AgentRole


class TeamBuilder:
    def __init__(self, registry: TeamRegistry):
        self.registry = registry

    def build_team(self, objective: str) -> List[AgentCollaborationProfile]:
        """
        Dynamically select an optimal team of executive agents based on the objective.
        This uses basic keyword matching, but in a real enterprise system,
        an LLM agent might analyze the objective to pick the exact roles.
        """
        objective_lower = objective.lower()
        selected_team = []

        # Scenario mapping based on user requirements
        if (
            "repository" in objective_lower
            or "architecture" in objective_lower
            and "cost" not in objective_lower
        ):
            # Need CTO
            ctos = self.registry.find_agents_by_expertise("Architecture")
            if ctos:
                cto = ctos[0]
                cto.assigned_role = AgentRole.LEADER
                selected_team.append(cto)

        elif "architecture" in objective_lower and "cost" in objective_lower:
            # CTO + CFO
            ctos = self.registry.find_agents_by_expertise("Architecture")
            cfos = self.registry.find_agents_by_expertise("Finance")
            if ctos:
                cto = ctos[0]
                cto.assigned_role = AgentRole.LEADER
                selected_team.append(cto)
            if cfos:
                cfo = cfos[0]
                cfo.assigned_role = AgentRole.REVIEWER
                selected_team.append(cfo)

        elif "incident" in objective_lower:
            # CTO + COO + Security
            for exp, role in [
                ("Architecture", AgentRole.LEADER),
                ("Operations", AgentRole.CONTRIBUTOR),
                ("Security", AgentRole.CONTRIBUTOR),
            ]:
                agents = self.registry.find_agents_by_expertise(exp)
                if agents:
                    a = agents[0]
                    a.assigned_role = role
                    selected_team.append(a)

        elif "hiring" in objective_lower:
            # HR + CTO
            hrs = self.registry.find_agents_by_expertise("HR")
            ctos = self.registry.find_agents_by_expertise("Architecture")
            if hrs:
                hr = hrs[0]
                hr.assigned_role = AgentRole.LEADER
                selected_team.append(hr)
            if ctos:
                cto = ctos[0]
                cto.assigned_role = AgentRole.CONTRIBUTOR
                selected_team.append(cto)

        # Default fallback
        if not selected_team:
            all_agents = self.registry.get_all_agents()
            if all_agents:
                leader = all_agents[0]
                leader.assigned_role = AgentRole.LEADER
                selected_team.append(leader)

        return selected_team
