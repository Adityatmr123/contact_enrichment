"""Data models for contact enrichment"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Company:
    """Company data"""
    name: str
    domain: str


@dataclass
class Contact:
    """Individual contact"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    company_name: Optional[str] = None
    domain: Optional[str] = None


@dataclass
class EnrichedContact:
    """Contact enriched with API data"""
    contact: Contact
    enriched_email: Optional[str] = None
    enriched_phone: Optional[str] = None
    email_status: Optional[str] = None
    email_quality_score: Optional[str] = None
    is_valid_email: bool = False
    enrichment_source: str = "unknown"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.contact.name,
            'email': self.contact.email,
            'phone': self.contact.phone,
            'linkedin_url': self.contact.linkedin_url,
            'job_title': self.contact.job_title,
            'department': self.contact.department,
            'seniority': self.contact.seniority,
            'company_name': self.contact.company_name,
            'domain': self.contact.domain,
            'enriched_email': self.enriched_email,
            'enriched_phone': self.enriched_phone,
            'email_status': self.email_status,
            'email_quality_score': self.email_quality_score,
            'is_valid_email': self.is_valid_email,
            'enrichment_source': self.enrichment_source,
        }


__all__ = ['Company', 'Contact', 'EnrichedContact']
