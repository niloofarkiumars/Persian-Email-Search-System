"""
Email data model
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from Source_code.utils.persian_normalizer import normalize_persian_text, normalize_persian_no_space


@dataclass
class Email:
    """Email data model"""

    # Core fields - customize these based on your team's database schema
    message_id: Optional[str] = None
    subject: str = ""
    body: str = ""
    from_address: str = ""
    to_addresses: List[str] = field(default_factory=list)
    cc_addresses: List[str] = field(default_factory=list)
    bcc_addresses: List[str] = field(default_factory=list)
    date: Optional[datetime] = None
    has_attachment: bool = False
    attachment_names: List[str] = field(default_factory=list)
    attachment_sizes: List[int] = field(default_factory=list)
    folder: str = "inbox"
    is_read: bool = False
    priority: str = "normal"
    labels: List[str] = field(default_factory=list)
    semantic_vector: Optional[List[float]] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_mongodb(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        return {
            "message_id": self.message_id,
            "subject": self.subject,
            "body": self.body,
            "from": self.from_address,
            "to": self.to_addresses,
            "cc": self.cc_addresses,
            "bcc": self.bcc_addresses,
            "date": self.date or datetime.now(),
            "has_attachment": self.has_attachment,
            "attachment_names": self.attachment_names,
            "attachment_sizes": self.attachment_sizes,
            "folder": self.folder,
            "is_read": self.is_read,
            "priority": self.priority,
            "labels": self.labels,
            "created_at": self.created_at or datetime.now(),
            "updated_at": self.updated_at or datetime.now()
        }

    def to_elasticsearch(self) -> Dict[str, Any]:
        """Convert to Elasticsearch document"""
        subject = normalize_persian_text(self.subject)
        body = normalize_persian_text(self.body)
        from_address = normalize_persian_text(self.from_address)
        to_addresses = normalize_persian_text(self.to_addresses)
        cc_addresses = normalize_persian_text(self.cc_addresses)

        document = {
            "messageId": self.message_id,
            "subject": subject,
            "body": body,
            "from": from_address,
            "to": to_addresses,
            "cc": cc_addresses,
            "subjectExact": normalize_persian_no_space(subject),
            "bodyExact": normalize_persian_no_space(body),
            "fromExact": normalize_persian_no_space(from_address),
            "toExact": normalize_persian_no_space(to_addresses),
            "ccExact": normalize_persian_no_space(cc_addresses),
            "date": self.date or datetime.now(),
            "hasAttachment": self.has_attachment,
            "priority": self.priority,
            "folder": self.folder,
            "isRead": self.is_read
        }

        if self.semantic_vector:
            document["semanticVector"] = self.semantic_vector

        return document

    @classmethod
    def from_mongodb(cls, doc: Dict[str, Any]) -> 'Email':
        """Create Email from MongoDB document"""
        return cls(
            message_id=doc.get('message_id'),
            subject=doc.get('subject', ''),
            body=doc.get('body', ''),
            from_address=doc.get('from', ''),
            to_addresses=doc.get('to', []),
            cc_addresses=doc.get('cc', []),
            bcc_addresses=doc.get('bcc', []),
            date=doc.get('date'),
            has_attachment=doc.get('has_attachment', False),
            attachment_names=doc.get('attachment_names', []),
            attachment_sizes=doc.get('attachment_sizes', []),
            folder=doc.get('folder', 'inbox'),
            is_read=doc.get('is_read', False),
            priority=doc.get('priority', 'normal'),
            labels=doc.get('labels', []),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )


class EmailMapper:
    """
    Map between database fields and application fields
    Your team can customize this based on their actual database schema
    """

    # Define field mappings between your team's DB and this application
    FIELD_MAPPINGS = {
        # Application field -> Database field
        'message_id': 'message_id',  # Change this to match your DB column
        'subject': 'subject',  # Change this to match your DB column
        'body': 'body',  # Change this to match your DB column
        'from_address': 'from',  # Change this to match your DB column
        'to_addresses': 'to',  # Change this to match your DB column
        'date': 'date',  # Change this to match your DB column
        'has_attachment': 'has_attachment',  # Change this to match your DB column
    }

    @classmethod
    def map_from_db(cls, db_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map database fields to application fields
        Your team should customize this based on their actual column names
        """
        mapped = {}

        # Example mappings - ADJUST THESE!
        field_conversions = {
            'message_id': db_doc.get('message_id') or db_doc.get('_id'),
            'subject': db_doc.get('subject') or db_doc.get('title', ''),
            'body': db_doc.get('body') or db_doc.get('content', ''),
            'from_address': db_doc.get('from') or db_doc.get('sender', ''),
            'to_addresses': db_doc.get('to') or db_doc.get('recipients', []),
            'date': db_doc.get('date') or db_doc.get('sent_date'),
            'has_attachment': db_doc.get('has_attachment') or db_doc.get('attachments', False),
        }

        return field_conversions
