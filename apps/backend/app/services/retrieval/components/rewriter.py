import re
from app.services.retrieval.models import QueryContext


class QueryRewriter:
    def __init__(self):
        # Configurable expansion dictionary for Enterprise terminology
        self.expansions = {
            "aem": ["autonomous enterprise manager"],
            "k8s": ["kubernetes", "container orchestration"],
            "aws": ["amazon web services", "cloud infrastructure"],
            "ci": ["continuous integration", "github actions", "pipeline"],
            "db": ["database", "postgres", "sql"],
            "ui": ["user interface", "frontend", "react"],
        }

    def rewrite(self, context: QueryContext) -> QueryContext:
        """
        Generate optimized search queries: keyword expansion, acronym resolution,
        and multi-query generation.
        """
        rewritten = set()

        # 1. Acronym & Terminology Expansion
        words = context.raw_query.lower().split()
        expanded_query = []
        has_expansion = False

        for w in words:
            clean_w = re.sub(r"[^\w\s]", "", w)
            if clean_w in self.expansions:
                expanded_query.extend(self.expansions[clean_w])
                has_expansion = True
            else:
                expanded_query.append(w)

        if has_expansion:
            rewritten.add(" ".join(expanded_query))

        # 2. Intent-based sub-queries
        if context.intent == "troubleshooting":
            # Strip question words to create a strict error search
            stripped = re.sub(
                r"^(why|how|what|when|where|who)\s+(does|is|are|did|will)?\s*",
                "",
                context.raw_query,
                flags=re.IGNORECASE,
            )
            if stripped != context.raw_query:
                rewritten.add(stripped + " error fix solution")

        if context.intent == "architecture":
            rewritten.add(
                context.raw_query + " system design architecture diagram overview"
            )

        context.rewritten_queries = list(rewritten)
        return context
