"""Practice topics, and a guess at the right topics for a role title."""

TOPICS: dict[str, str] = {
    "docker": "Docker & containers",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform & IaC",
    "aws": "AWS",
    "cicd": "CI/CD",
    "linux": "Linux & scripting",
    "networking": "Networking",
    "observability": "Monitoring & SRE",
    "security": "DevSecOps",
    "behavioral": "Behavioral",
}

# Keyword in the role title -> topics to practise (checked in order; first matches win).
_ROLE_RULES: list[tuple[tuple[str, ...], list[str]]] = [
    (("sre", "reliability"), ["observability", "kubernetes", "linux", "networking"]),
    (("platform",), ["kubernetes", "terraform", "cicd", "observability"]),
    (("build", "release"), ["cicd", "docker", "linux", "security"]),
    (("security", "devsecops"), ["security", "cicd", "aws", "docker"]),
    (("cloud", "aws", "azure", "infrastructure"), ["aws", "terraform", "networking", "security"]),
    (("devops",), ["docker", "kubernetes", "cicd", "terraform"]),
]
_DEFAULT_TOPICS = ["docker", "kubernetes", "cicd", "linux"]


def infer_topics(role: str) -> list[str]:
    """Technical topics for a role title, always followed by one behavioral question."""
    title = role.lower()
    for keywords, topics in _ROLE_RULES:
        if any(keyword in title for keyword in keywords):
            return [*topics, "behavioral"]
    return [*_DEFAULT_TOPICS, "behavioral"]


def valid_topics(topics: list[str]) -> list[str]:
    """Known topics only, de-duplicated, order kept."""
    return list(dict.fromkeys(topic for topic in topics if topic in TOPICS))
